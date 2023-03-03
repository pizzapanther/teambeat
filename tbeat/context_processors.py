from django.conf import settings


def app(request):
  return {
    "APP_HOME": settings.APP_HOME,
    "LOCALHOST": settings.DEBUG,
  }
