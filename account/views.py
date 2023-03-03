import datetime
import json
import time

from django import http
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from account.decorators import require_org_admin
from account.forms import ResetForm, ResetFinishForm, SignUpForm, EditAccountForm, OrgForm, MemberForm
from account.models import User, PasswordReset, Organization, OrgMember, Credit
from teams.models import Member

import pendulum
import stripe
stripe.api_key = settings.STRIPE_API_KEY


def login_view(request):
  form = AuthenticationForm(request, request.POST or None)

  if request.method == 'POST':
    next_url = request.POST.get('next', settings.APP_HOME)
    if form.is_valid():
      login(request, form.user_cache)
      return http.HttpResponseRedirect(next_url)

  else:
    next_url = request.GET.get('next', settings.APP_HOME)

  context = {'form': form, 'next': next_url}
  return TemplateResponse(request, 'account/login.html', context)


def logout_view(request):
  logout(request)
  return http.HttpResponseRedirect("/")


def home(request):
  return TemplateResponse(request, 'account/home.html', {})


def favicon(request):
  return http.HttpResponseRedirect('/static/favicon-32x32.png')


def reset(request):
  form = ResetForm(request.POST or None)
  if request.method == 'POST':
    if form.is_valid():
      pr = PasswordReset(user=form.user_cache)
      pr.save()
      pr.send()
      return TemplateResponse(request, 'account/reset-sent.html', {})

  return TemplateResponse(request, 'account/reset.html', {'form': form})


def reset_finish(request):
  if request.method == 'POST':
    token = request.POST.get('token', None)

  else:
    token = request.GET.get('token', None)

  if token is None:
    raise http.Http404

  pr = PasswordReset.get_from_token(token)
  if pr is None:
    raise http.Http404

  form = ResetFinishForm(pr.user, request.POST or None)
  if request.method == 'POST':
    if form.is_valid():
      pr.user.set_password(form.cleaned_data['password'])
      pr.user.save()
      pr.used = True
      pr.save()
      return TemplateResponse(request, 'account/reset-success.html', {'reset': pr})

  return TemplateResponse(request, 'account/reset-finish.html', {'form': form, 'reset': pr, 'token': token})


def signup(request):
  form = SignUpForm(request.POST or None)
  if request.method == 'POST':
    if form.is_valid():
      user = User(
        username=form.cleaned_data['email'],
        first_name=form.cleaned_data['first_name'],
        last_name=form.cleaned_data['last_name'],
      )
      user.set_password(form.cleaned_data['password'])
      user.save()

      # associate to new org
      org = Organization(name='My Organization')
      org.save()

      member = OrgMember(user=user, org=org, role='admin')
      member.save()

      # free trial setup
      expire = timezone.now() + datetime.timedelta(days=30)
      credit = Credit(org=org, expiration=expire, amount=0, level='trial')
      credit.save()

      login(request, user)
      return http.HttpResponseRedirect(settings.APP_HOME)

  context = {'form': form}
  return TemplateResponse(request, 'account/account-signup.html', context)


@login_required
def edit_account(request):
  form = EditAccountForm(request.POST or None, instance=request.user)
  if request.method == 'POST':
    if form.is_valid():
      form.save()
      return http.HttpResponseRedirect(settings.APP_HOME)

  context = {'form': form}
  return TemplateResponse(request, 'account/account-edit.html', context)


@login_required
def edit_password(request):
  form = ResetFinishForm(request.user, request.POST or None)
  form['password'].label = 'New password'
  if request.method == 'POST':
    if form.is_valid():
      request.user.set_password(form.cleaned_data['password'])
      request.user.save()
      login(request, request.user)
      return http.HttpResponseRedirect(settings.APP_HOME)

  context = {'form': form}
  return TemplateResponse(request, 'account/account-password.html', context)


@login_required
def dashboard(request):
  context = {}
  return TemplateResponse(request, 'account/dashboard.html', context)


@login_required
@require_org_admin
def edit_org(request):
  form = OrgForm(request.POST or None, instance=request.user.org)

  if request.method == 'POST':
    if form.is_valid():
      form.save()
      return http.HttpResponseRedirect(settings.APP_HOME)

  context = {'form': form, 'title': 'Edit Organization', 'action': 'Save'}
  return TemplateResponse(request, 'generic-form.html', context)


@login_required
@require_org_admin
def list_members(request):
  members = OrgMember.objects.filter(org=request.user.org).order_by('user__username')
  paginator = Paginator(members, 50)
  page_number = request.GET.get('page')
  page_obj = paginator.get_page(page_number)
  context = {'page': page_obj, 'org': request.user.org}
  return TemplateResponse(request, 'account/members-list.html', context)


@login_required
@require_org_admin
def edit_member(request, member_id=None):
  action = 'Add'
  title = 'Add Member'
  member = None
  initial = None
  if member_id:
    member = get_object_or_404(OrgMember, org=request.user.org, id=member_id)

    title = f'Edit Member: {member.user.name}'
    action = 'Save'
    initial = {'email': member.user.email, 'first_name': member.user.first_name, 'last_name': member.user.last_name}

  else:
    if not request.user.org.can_add_members:
      return TemplateResponse(request, 'account/overlimit.html', {})

  form = MemberForm(request.POST or None, instance=member, initial=initial)

  if request.method == 'POST':
    if form.is_valid():
      if action == 'Add':
        user, created = User.objects.get_or_create(
          username=form.cleaned_data['email'].lower(),
          defaults={'first_name': form.cleaned_data['first_name'], 'last_name': form.cleaned_data['last_name']},
        )
        if created:
          user.save()

        member = form.save(commit=False)
        member.user = user
        member.org = request.user.org
        member.save()

      else:
        form.save()
        member.user.username = form.cleaned_data['email'].lower()
        member.user.first_name = form.cleaned_data['first_name']
        member.user.last_name = form.cleaned_data['last_name']
        member.user.save()

      return http.HttpResponseRedirect('../')

  context = {'form': form, 'title': title, 'action': action}
  return TemplateResponse(request, 'generic-form.html', context)


@login_required
@require_org_admin
def rm_member(request, member_id):
  member = get_object_or_404(OrgMember, org=request.user.org, id=member_id)

  Member.objects.filter(team__org=request.user.org, user=member.user).update(active=False)
  member.delete()

  return http.HttpResponseRedirect('../../')


@login_required
@require_org_admin
def payments(request):
  credits = Credit.objects.filter(org=request.user.org)
  paginator = Paginator(credits, 50)
  page_number = request.GET.get('page')
  page_obj = paginator.get_page(page_number)

  context = {'org': request.user.org, 'page': page_obj}
  return TemplateResponse(request, 'account/payments.html', context)


@login_required
@require_org_admin
def subscribe(request):
  products = []
  for prod in settings.PRODUCTS:
    products.append({
      'name': prod['name'],
      'url': f"/payments/subscribe/{prod['type']}/",
      'price': prod['price'] / 100,
      'users': prod['users'],
    })

  context = {'org': request.user.org, 'products': products}
  return TemplateResponse(request, 'account/subscribe.html', context)


@login_required
@require_org_admin
def subscibe_to_level(request, level):
  base = '{}://{}'.format(request.scheme, request.get_host())
  for prod in settings.PRODUCTS:
    if prod['type'] == level:
      session = stripe.checkout.Session.create(
        success_url=base + '/payments/subscribe/success/?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=f'{base}/payments/subscribe/',
        payment_method_types=['card'],
        mode='subscription',
        line_items=[{
          'price': prod['api_id'],
          'quantity': 1
        }],
        metadata={'org_id': request.user.org.id, 'level': prod['type']}
      )
      return http.HttpResponseRedirect(session.url)

  raise http.Http404


@csrf_exempt
def webhook(request):
  try:
    event = stripe.Event.construct_from(json.loads(request.body), stripe.api_key)

  except ValueError as e:
    return http.HttpResponse(status=400)

  if event.type == 'payment_intent.succeeded':
    pass

  elif event.type == 'invoice.payment_succeeded':
    subs = stripe.Subscription.retrieve(event.data.object.subscription)
    cs = stripe.checkout.Session.list(subscription=event.data.object.subscription)
    if cs and cs.data:
      past_credit = Credit.objects.filter(org_id=cs.data[0].metadata['org_id']).first()
      level = cs.data[0].metadata['level']
      if past_credit and past_credit.upgraded_level and not past_credit.cancelled:
        level = past_credit.upgraded_level

      credit = Credit(
        org_id = cs.data[0].metadata['org_id'],
        expiration = pendulum.from_timestamp(subs["current_period_end"]),
        amount = event.data.object.amount_paid,
        level = level,
        subscription = event.data.object.subscription,
      )
      credit.save()

    else:
      past_credit = Credit.objects.filter(subscription=event.data.object.subscription).first()
      if past_credit:
        level = past_credit.level
        if past_credit.upgraded_level and not past_credit.cancelled:
          level = past_credit.upgraded_level

        credit = Credit(
          amount=event.data.object.amount_paid,
          org=past_credit.org,
          level=level,
          expiration=pendulum.from_timestamp(subs["current_period_end"]),
          subscription=event.data.object.subscription,
        )
        credit.save()

  return http.HttpResponse('OK', status=200, content_type="text/plain")


@login_required
@require_org_admin
def subscribe_success(request):
  now = timezone.now() - datetime.timedelta(minutes=10)
  if Credit.objects.filter(org=request.user.org, created__gt=now).count():
    return http.HttpResponseRedirect('/payments/')

  time.sleep(1)
  return TemplateResponse(request, 'account/stripe-success.html', {})


@login_required
@require_org_admin
def cancel_plan(request):
  credit = Credit.objects.filter(org=request.user.org).first()
  stripe.Subscription.modify(credit.subscription, cancel_at_period_end=True)

  credit.cancelled = True
  credit.save()

  return http.HttpResponseRedirect('/payments/')


@login_required
@require_org_admin
def change_plan(request):
  upgrade = request.GET.get('upgrade', None)

  products = []
  credit = Credit.objects.filter(org=request.user.org).first()

  for prod in settings.PRODUCTS:
    if upgrade and upgrade == prod['type']:
      subscription = stripe.Subscription.retrieve(credit.subscription)
      stripe.Subscription.modify(
        subscription.id,
        cancel_at_period_end=False,
        proration_behavior='always_invoice',
        items=[{
          'id': subscription['items']['data'][0].id,
          'price': prod['api_id'],
        }],
        metadata={'org_id': request.user.org.id, 'level': upgrade},
      )

      credit.upgraded_level = upgrade
      credit.save()

      time.sleep(3)
      return http.HttpResponseRedirect('/payments/')

    if credit and prod['type'] != credit.level:
      products.append({
        'name': prod['name'],
        'url': f"./?upgrade={prod['type']}",
        'price': prod['price'] / 100,
        'users': prod['users'],
      })

  context = {'org': request.user.org, 'products': products, 'extra_confirm': True}
  return TemplateResponse(request, 'account/subscribe.html', context)
