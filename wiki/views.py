from django import http
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from wiki.models import Wiki, Page


@login_required
def page_viewer(request, wiki_slug, path=""):
  path = "/" + path
  if request.user.org:
    wiki = get_object_or_404(Wiki, slug=wiki_slug, org=request.user.org)
    # todo: wiki 404
    page = get_object_or_404(Page, wiki=wiki, path=path)

  raise http.Http404
