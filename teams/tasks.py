from django.utils import timezone

import dramatiq
from loguru import logger
from timezone_field import TimeZoneField

from teams.models import Team


def send_things():
  logger.info('Sending Things')
  send_scrums.send()
  send_reports.send()


@dramatiq.actor
def send_scrums(teams=None):
  now = timezone.now()

  filters = {
    'team_type': 'EMAIL',
    'active': True,
    'next_send__lte': now,
  }

  if teams:
    filters['team__id__in'] = teams

  qs = Team.objects.filter(**filters)
  count = qs.count()
  logger.info('Scrums Found: {}', count)
  if count:
    for team in qs:
      if team.org.credit:
        send_email.send(team.id)


@dramatiq.actor
def send_email(team_id):
  team = Team.objects.get(id=team_id)
  logger.info('Sending: {} ', team.id, team)
  team.send_email()


@dramatiq.actor
def send_reports(teams=None):
  now = timezone.now()

  filters = {
      'team_type': 'EMAIL',
      'active': True,
      'next_report__lte': now,
    }

  if teams:
    if teams:
      filters['team__id__in'] = teams

  qs = Team.objects.filter(**filters)
  count = qs.count()
  logger.info('Reports Found: {}', count)
  if count:
    for team in qs:
      if team.org.credit:
        send_report.send(team.id)


@dramatiq.actor
def send_report(team_id):
  team = Team.objects.get(id=team_id)
  logger.info('Sending Report: {} {}', team.id, team)
  team.send_report()
