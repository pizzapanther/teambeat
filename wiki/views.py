import logging

from django import http
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from wiki.forms import VersionForm
from wiki.models import Wiki, Page


class Wiki404(Exception):
  def __init__(self, wiki, path, *args, **kwargs):
    self.wiki = wiki
    self.path = path

    super().__init__(*args, **kwargs)


def get_or_wiki_404(request, wiki_slug, path):
  fullpath = path
  if path.endswith("/") or path == "":
    fullpath += "_index"

  if request.user.org:
    wiki = get_object_or_404(Wiki, slug=wiki_slug, org=request.user.org)
    page = Page.objects.filter(wiki=wiki, path=fullpath).first()
    if page:
      return page

    raise Wiki404(wiki, fullpath)

  raise http.Http404


def page_edit(request, wiki_slug, path):
  action = request.POST['action'].lower()
  form = VersionForm(request.POST)

  context = {'form': form, 'action': action}
  try:
    page = get_or_wiki_404(request, wiki_slug, path)

  except Wiki404 as e404:
    page = Page(path=e404.path, wiki=e404.wiki)

  context['path'] = page.path
  context['wiki'] = page.wiki

  if form.is_valid():
    version = form.save(commit=False)
    if page.id is None:
      page.save()

    if version.id is None:
      version.created_by = request.user

    version.modified_by = request.user
    version.page = page
    version.save()
    return TemplateResponse(request, 'wiki/page.html', {'page': page})

  else:
    if action == "publish now":
      action = "edit"

  return TemplateResponse(request, 'wiki/page-edit.html', context)


@login_required
def page_viewer(request, wiki_slug, path=""):
  if request.method == 'POST':
    return page_edit(request, wiki_slug, path)

  action = request.GET.get('action', '').lower()
  try:
    page = get_or_wiki_404(request, wiki_slug, path)

  except Wiki404 as e404:
    if action == 'create':
      form = VersionForm()
      context = {'form': form, 'path': e404.path, 'wiki': e404.wiki, 'action': action}
      return TemplateResponse(request, 'wiki/page-edit.html', context)

    return TemplateResponse(request, 'wiki/404.html', {'error': e404})

  if action == 'edit':
    version = request.GET.get('version')
    instance = None
    if version:
      instance = page.version_set.filter(id=version).first()

    form = VersionForm(instance=instance)
    context = {'form': form, 'path': page.path, 'wiki': page.wiki, 'action': action, 'version': version}
    return TemplateResponse(request, 'wiki/page-edit.html', context)

  return TemplateResponse(request, 'wiki/page.html', {'page': page})


@login_required
def versions_viewer(request, wiki_slug, path):
  pass
