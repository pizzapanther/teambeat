from django import template

from teams.models import Status, Scrum


register = template.Library()

@register.filter
def filter_none(value):
  if value is None:
    return '---'

  return value


@register.filter
def can_view_ratings(user, report):
  viewer = report.get_member(user)
  return viewer.view_ratings


@register.filter
def completed_by(team, user):
  status = Status.objects.filter(scrum=team.latest_scrum, member__user=user).first()
  if status:
    if status.status:
      return True

  return False


@register.filter
def my_status(team, user):
  status = Status.objects.filter(scrum=team.latest_scrum, member__user=user).first()
  if status:
    return status.id

  return '-'
