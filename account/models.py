import datetime
import traceback
from functools import cached_property

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone

import jwt
from loguru import logger

class User(AbstractUser):
  username = models.EmailField('E-Mail', unique=True)

  REQUIRED_FIELDS = []

  def __init__(self, *args, **kwargs):
    if 'email' in kwargs:
      del kwargs['email']

    super().__init__(*args, **kwargs)

  def __str__(self):
    return f'{self.name}, {self.username}'

  @property
  def email(self):
    return self.username

  @email.setter
  def email(self, value):
    self.username = value

  @property
  def name(self):
    if self.first_name and self.last_name:
      return '{} {}'.format(self.first_name, self.last_name)

    elif self.first_name:
      return self.first_name

    elif self.last_name:
      return self.last_name

    return self.username

  @cached_property
  def org_member(self):
    return OrgMember.objects.filter(user=self).first()

  @cached_property
  def org(self):
    if self.org_member:
      return self.org_member.org

  @cached_property
  def is_org_admin(self):
    if self.org_member:
      return self.org_member.role == 'admin'

    return False

  @cached_property
  def is_org_manager(self):
    if self.org_member:
      return self.org_member.role in ['manager', 'admin']

    return False


class PasswordReset(models.Model):
  user = models.ForeignKey(User, on_delete=models.CASCADE)
  used = models.BooleanField(default=False)
  created = models.DateTimeField(auto_now_add=True)

  class Meta:
    ordering = ['-created']

  def __str__(self):
    return self.user.name

  @property
  def token(self):
    return jwt.encode(
      {"rid": self.id, "exp": timezone.now() + datetime.timedelta(minutes=30)},
      settings.SECRET_KEY,
      algorithm="HS256"
    )

  def send(self):
    subject = 'Password Reset'
    text = render_to_string('account/reset-email.txt', {'reset': self})
    msg = EmailMultiAlternatives(subject, text, settings.DEFAULT_FROM_EMAIL, [self.user.email])
    msg.send()

  @property
  def url(self):
    return f'{settings.BASE_URL}/accounts/reset-finish/?token={self.token}'

  @classmethod
  def get_from_token(cls, token):
    if token:
      try:
        data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

      except:
        logger.info(traceback.format_exc())

      else:
        pr = cls.objects.filter(id=data['rid'], used=False).first()
        return pr


class Organization(models.Model):
  name = models.CharField(max_length=150)
  created = models.DateTimeField(auto_now_add=True)
  modified = models.DateTimeField(auto_now=True)

  def __str__(self):
    return self.name

  @cached_property
  def credit(self):
    now = timezone.now()
    credit = self.credit_set.filter(expiration__gte=now).first()
    if credit:
      return credit

  @cached_property
  def can_add_members(self):
    if self.credit:
      total = OrgMember.objects.filter(org=self).count()
      if self.credit.level in ['trial', 'level-0']:
        return total < 25

      elif self.credit.level == 'level-1':
        return total < 50

      elif self.credit.level == 'level-2':
        return total < 100

      elif self.credit.level == 'level-3':
        return total < 200

    return False


class OrgMember(models.Model):
  ROLES = (
    ('member', 'Member'),
    ('manager', 'Manager'),
    ('admin', 'Admin'),
  )

  user = models.ForeignKey(User, on_delete=models.CASCADE)
  org = models.ForeignKey(Organization, on_delete=models.CASCADE)

  role = models.CharField(choices=ROLES, max_length=10)

  created = models.DateTimeField(auto_now_add=True)
  modified = models.DateTimeField(auto_now=True)


class Credit(models.Model):
  LEVELS = (
    ('trial', 'Trial'),
    ('level-0', 'Level 0'),
    ('level-1', 'Level 1'),
    ('level-2', 'Level 2'),
    ('level-3', 'Level 3'),
  )

  org = models.ForeignKey(Organization, on_delete=models.CASCADE)
  expiration = models.DateTimeField()
  amount = models.IntegerField(default=0)

  level = models.CharField(default='trial', max_length=10, choices=LEVELS)
  upgraded_level = models.CharField(max_length=10, choices=LEVELS, blank=True, null=True)
  cancelled = models.BooleanField(default=False)
  subscription = models.CharField(max_length=155, blank=True, null=True)

  created = models.DateTimeField(auto_now_add=True)

  class Meta:
    ordering = ['-expiration', '-created']

  def __str__(self):
    return f"{self.org} - {self.expiration}"

  @property
  def price(self):
    return self.amount / 100

  @property
  def max_members(self):
    for product in settings.PRODUCTS:
      if product['type'] == self.level:
        return product['users']

    return 25
