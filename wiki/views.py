import logging

from django import http
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from wiki.models import Wiki, Page


class Wiki404(Exception):
  def __init__(self, wiki, path, *args, **kwargs):
    self.wiki = wiki
    self.path = path

    super().__init__(*args, **kwargs)


def get_or_wiki_404(request, wiki_slug, path):
  fullpath = "/" + path
  if request.user.org:
    wiki = get_object_or_404(Wiki, slug=wiki_slug, org=request.user.org)
    page = Page.objects.filter(wiki=wiki, path=fullpath).first()
    if page:
      return page

    raise Wiki404(wiki, fullpath)

  raise http.Http404


@login_required
def page_viewer(request, wiki_slug, path=""):
  action = request.GET.get('action')

  try:
    page = get_or_wiki_404(request, wiki_slug, path)

  except Wiki404 as e404:
    if action == 'create':
      return TemplateResponse(request, 'wiki/page-edit.html', {'path': e404.path, 'wiki': e404.wiki})

    return TemplateResponse(request, 'wiki/404.html', {'error': e404})

  return TemplateResponse(request, 'wiki/page.html', {'page': page})
