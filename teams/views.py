from django import http
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from teams.models import Status, Scrum, Member, Team
from teams.forms import status_form, TeamForm, add_member_form
from account.decorators import require_org_manager
from account.models import User


def save_status(request):
  if request.method == 'GET':
    token = request.GET.get('token')
    next = request.GET.get('next')

  else:
    token = request.POST.get('token')
    next = request.POST.get('next')

  form_class, status = status_form(token)
  initial = None
  if status and status.status:
    initial = status.status

  if status is None:
    raise http.Http404

  form = form_class(request.POST or None, initial=initial)
  if request.method == 'POST':
    if form.is_valid():
      form.save_status(status)
      if next:
        return http.HttpResponseRedirect(next)

      return TemplateResponse(request, 'teams/save_status_success.html', {'team': status.scrum.team})

  context = {'status': status, 'form': form, 'next': next}
  return TemplateResponse(request, 'teams/save_status.html', context)


@login_required
def user_save_status(request, status_id):
  status = get_object_or_404(Status, member__user=request.user, id=status_id)
  return http.HttpResponseRedirect(f'/status/save/?token={status.token}&next=/status/open/')


@login_required
def list_reports(request):
  reports = Scrum.objects.filter(team__org=request.user.org).order_by('-created')
  paginator = Paginator(reports, 25)
  page_number = request.GET.get('page')
  page_obj = paginator.get_page(page_number)

  can_see_ratings = Member.objects.filter(view_ratings=True, user=request.user).count()

  context = {'page': page_obj, 'can_see_ratings': can_see_ratings, 'user': request.user}
  return TemplateResponse(request, 'teams/report_list.html', context)


@login_required
def report_detail(request, report_id):
  report = get_object_or_404(Scrum, id=report_id, team__org=request.user.org)
  context = {'report': report, 'viewer': report.get_member(request.user)}
  return TemplateResponse(request, 'teams/report_detail.html', context)


@login_required
@require_org_manager
def list_teams(request):
  reports = Team.objects.filter(org=request.user.org).order_by('name')
  paginator = Paginator(reports, 25)
  page_number = request.GET.get('page')
  page_obj = paginator.get_page(page_number)

  context = {'page': page_obj}
  return TemplateResponse(request, 'teams/team-list.html', context)


@login_required
@require_org_manager
def edit_team(request, team_id=None):
  action = 'Add'
  title = 'Add Team'
  team = None
  includes = [
    'teams/partials/member-edit.html',
  ]

  if team_id:
    team = get_object_or_404(Team, id=team_id, org=request.user.org)
    action = 'Save'
    title = f'Edit Team: {team.name}'

  form = TeamForm(request.POST or None, instance=team)
  if request.method == 'POST':
    if form.instance.id:
      for m in form.instance.members:
        for field in ['view_ratings', 'report_status', 'active']:
          checked = request.POST.get(f'{field}_{m.id}', None)
          if checked:
            checked = True

          else:
            checked = False

          setattr(m, field, checked)

    if form.is_valid():
      if not form.instance.id:
        form.instance.set_next_send()
        form.instance.org = request.user.org

      form.save()
      for m in form.instance.members:
        m.save()

      return http.HttpResponseRedirect('/teams/list/')

  context = {'form': form, 'title': title, 'action': action, 'includes': includes}
  return TemplateResponse(request, 'generic-form.html', context)


@login_required
@require_org_manager
def team_add_member(request, team_id):
  team = get_object_or_404(Team, id=team_id, org=request.user.org)

  form_class = add_member_form(User.objects.filter(orgmember__org=team.org))

  form = form_class(request.POST or None)
  if request.method == 'POST':
    if form.is_valid():
      member = Member.objects.filter(user=form.cleaned_data['user'], team=team).first()

      if member is None:
        member = Member(user=form.cleaned_data['user'], team=team)

      member.active = True
      member.view_ratings = form.cleaned_data['view_ratings']
      member.report_status = form.cleaned_data['report_status']
      member.save()

      return http.HttpResponseRedirect('../#membership')

  context = {'form': form, 'title': f'Add Member: {team.name}', 'action': 'Add'}
  return TemplateResponse(request, 'generic-form.html', context)


@login_required
def open_status(request):
  teams = Team.objects.filter(org=request.user.org, next_report__isnull=False, member__user=request.user).order_by('name')
  count = teams.count()
  if count:
    return TemplateResponse(request, 'teams/open-reports.html', {'teams': teams})

  return TemplateResponse(request, 'teams/not-opened.html', {})
