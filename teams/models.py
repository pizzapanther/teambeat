import datetime
import textwrap
import traceback

from functools import cached_property

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone

import jwt
from loguru import logger
from timezone_field import TimeZoneField


def days_default():
  return []


def default_days():
  return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']


def DEFAULT_QUESTIONS():
  return (
    {'question': 'What did you do yesterday?'},
    {'question': 'What will you do today?'},
    {'question': 'Are there any blockers or impediments preventing you from doing your work?'},
    {'rating': 'Rate the day'},
  )


class Team(models.Model):
  class TeamTypes(models.TextChoices):
    EMAIL = 'EMAIL', 'E-Mail'

  DAYS = (
    ('Monday', 'Monday'),
    ('Tuesday', 'Tuesday'),
    ('Wednesday', 'Wednesday'),
    ('Thursday', 'Thursday'),
    ('Friday', 'Friday'),
    ('Saturday', 'Saturday'),
    ('Sunday', 'Sunday'),
  )

  name = models.CharField(max_length=150)

  team_type = models.CharField(max_length=10, choices=TeamTypes.choices, default=TeamTypes.EMAIL)

  send_time = models.TimeField()
  next_send = models.DateTimeField()
  next_report = models.DateTimeField(blank=True, null=True)
  hours_open = models.DecimalField(max_digits=4, decimal_places=2, default=1)

  timezone = TimeZoneField(default="America/Chicago", use_pytz=False, choices_display="STANDARD")

  days_of_week = ArrayField(models.CharField(max_length=25, choices=DAYS), default=default_days)
  questions = models.JSONField(default=DEFAULT_QUESTIONS)

  active = models.BooleanField(default=True)

  created = models.DateTimeField(auto_now_add=True)
  modified = models.DateTimeField(auto_now=True)

  org = models.ForeignKey('account.Organization', on_delete=models.CASCADE, blank=True, null=True)

  class Meta:
    verbose_name = "scrum team"

  def __str__(self):
    return self.name

  @cached_property
  def latest_scrum(self):
    return Scrum.objects.filter(team=self).latest()

  @cached_property
  def member_count(self):
    return self.member_set.filter(active=True).count()

  @cached_property
  def members(self):
    ret = []
    for m in self.member_set.filter(active=True).order_by('user__username'):
      ret.append(m)

    return ret

  def set_next_send(self, now=None):
    if now is None:
      now = timezone.now()

    now = now.astimezone(self.timezone)

    self.next_send = datetime.datetime(
      now.year, now.month, now.day,
      self.send_time.hour, self.send_time.minute,
      tzinfo=self.timezone
    )
    while 1:
      self.next_send = self.next_send + datetime.timedelta(days=1)
      if self.next_send > now and self.next_send.strftime('%A') in self.days_of_week:
        break

  def send_email(self):
    scrum = Scrum(team=self)
    scrum.save()

    now = timezone.now()
    self.next_report = now + datetime.timedelta(hours=int(self.hours_open))
    self.save()

    for member in self.member_set.filter(active=True, report_status=True):
      status = Status(scrum=scrum, member=member)
      status.save()
      status.send_email(self.next_send)

    self.set_next_send(now)
    self.save()

  def send_report(self):
    report = Scrum.objects.filter(team=self).latest()

    if report:
      members = Member.objects.filter(team=self, active=True)
      subject = report.created.astimezone(self.timezone).strftime(self.name + ': Report %a, %b %d, %Y')

      for m in members:
        context = {'report': report, 'tz': self.timezone, 'member': m, 'table': report.table(m)}
        text = render_to_string('teams/report.txt', context)
        msg = EmailMultiAlternatives(subject, text, settings.DEFAULT_FROM_EMAIL, [m.user.email])
        msg.send()

    self.next_report = None
    self.save()

  @property
  def question_data(self):
    ret = []
    for q in self.questions:
      key = list(q.keys())[0]
      ret.append({'type': key, 'text': q[key]})

    return ret


class Member(models.Model):
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT)
  team = models.ForeignKey(Team, on_delete=models.CASCADE)

  active = models.BooleanField(default=True)
  view_ratings = models.BooleanField(default=False)
  report_status = models.BooleanField(default=True)

  created = models.DateTimeField(auto_now_add=True)
  modified = models.DateTimeField(auto_now=True)

  class Meta:
    verbose_name = "scrum member"

  def __str__(self):
    return self.name

  @property
  def name(self):
    return self.user.name

  @property
  def email(self):
    return self.user.email


class Scrum(models.Model):
  team = models.ForeignKey(Team, on_delete=models.CASCADE)

  created = models.DateTimeField(auto_now_add=True)
  modified = models.DateTimeField(auto_now=True)

  class Meta:
    get_latest_by = 'created'
    ordering = ['-created']

  def __str__(self):
    return str(self.team)

  @property
  def completed(self):
    count = 0
    for status in self.status_set.all():
      if status.status:
        count += 1

    return count

  @property
  def rating_key(self):
    for i, q in enumerate(self.team.question_data):
      if q['type'] == 'rating':
        return f'question{i}'

  @property
  def rating(self):
    count = 0
    total = 0
    ret = {'min': None, 'max': None, 'avg': None}

    key = self.rating_key
    if key:
      for status in self.status_set.all():
        if status.status and key in status.status:
          r = int(status.status[key])
          total += r
          count += 1

          if ret['min'] is None or r < ret['min']:
            ret['min'] = r

          if ret['max'] is None or r > ret['max']:
            ret['max'] = r

    if count:
      ret['avg'] = total / count

    return ret

  @property
  def ordered_status(self):
    return self.status_set.all().select_related().order_by('member__user__username')


  def table(self, member):
    text = ''

    for status in self.ordered_status:
      questions = f'{status.member.name}\n\n'
      for i, q in enumerate(status.questions, start=1):
        if q['type'] == 'rating':
          if member.view_ratings:
            questions += f"{i}. {q['text']}:  {q['ans']}\n\n"

        else:
          questions += f"{i}. {q['text']}\n"
          for line in textwrap.wrap(q['ans'], initial_indent='    ', subsequent_indent='    '):
            questions += line + "\n"

          questions += "\n"

      text += questions + "\n"
      text += "-" * 80
      text += "\n\n"

    return text

  @property
  def url(self):
    return f'{settings.BASE_URL}/status/{self.id}/'

  def get_member(self, user):
    return Member.objects.filter(team=self.team, user=user).first()


class Status(models.Model):
  scrum = models.ForeignKey(Scrum, on_delete=models.CASCADE)
  member = models.ForeignKey(Member, on_delete=models.RESTRICT)

  status = models.JSONField(blank=True, null=True)

  created = models.DateTimeField(auto_now_add=True)
  modified = models.DateTimeField(auto_now=True)

  active = models.BooleanField(default=True)

  def __str__(self):
    return str(self.member)

  def send_email(self, timestamp):
    subject = timestamp.strftime(self.scrum.team.name + ' Status %a, %b %d, %Y')
    text = render_to_string('teams/scrum.txt', {'status': self})
    msg = EmailMultiAlternatives(subject, text, settings.DEFAULT_FROM_EMAIL, [self.member.email])
    msg.send()

  @property
  def token(self):
    return jwt.encode(
      {"sid": self.id, "exp": self.scrum.team.next_report},
      settings.SECRET_KEY,
      algorithm="HS256"
    )

  @property
  def token_url(self):
    return f'{settings.BASE_URL}/status/save/?token={self.token}'

  @classmethod
  def get_from_token(cls, token):
    if token:
      try:
        data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

      except:
        logger.info(traceback.format_exc())

      else:
        status = Status.objects.filter(id=data['sid'], active=True).first()
        return status

  @property
  def questions(self):
    ret = []
    if self.status:
      for i, q in enumerate(self.scrum.team.question_data):
        key = f'question{i}'
        if key in self.status:
          ret.append({'text': q['text'], 'ans': self.status[key], 'type': q['type']})

    return ret
