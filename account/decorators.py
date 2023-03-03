from django import http


class require_org_admin:
  def __init__(self, target_func):
    self.target_func = target_func

  def __call__(self, request, *args, **kwargs):
    if request.user.is_org_admin:
      return self.target_func(request, *args, **kwargs)

    raise http.Http404


class require_org_manager:
  def __init__(self, target_func):
    self.target_func = target_func

  def __call__(self, request, *args, **kwargs):
    if request.user.is_org_manager:
      return self.target_func(request, *args, **kwargs)

    raise http.Http404
