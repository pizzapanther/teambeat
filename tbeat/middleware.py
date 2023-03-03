from django import http
from django.conf import settings


class HostRedirect:
  def __init__(self, get_response):
    self.get_response = get_response

  def __call__(self, request):
    host = request.get_host()
    if host in settings.EXTRA_HOSTS:
      path = request.get_full_path()
      return http.HttpResponseRedirect(f'{settings.BASE_URL}{path}')

    response = self.get_response(request)
    return response
