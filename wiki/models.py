from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField


class Wiki(models.Model):
  name = models.CharField(max_length=150)
  slug = models.SlugField(unique=True)

  created = models.DateTimeField(auto_now_add=True)
  modified = models.DateTimeField(auto_now=True)

  class Meta:
    ordering = ['name']

  def __str__(self):
    return self.name


def default_paths():
    return ["**/*"]


class WikiGroup(models.Model):
  name = models.CharField(max_length=150)

  wiki = models.ForeignKey(Wiki, on_delete=models.CASCADE)

  paths = ArrayField(models.CharField(max_length=150), default=default_paths)

  can_view = models.BooleanField(default=True)
  can_edit = models.BooleanField(default=False)
  can_approve = models.BooleanField(default=False)
  can_publish = models.BooleanField(default=False)

  created = models.DateTimeField(auto_now_add=True)
  modified = models.DateTimeField(auto_now=True)

  class Meta:
    ordering = ['name']

  def __str__(self):
    return self.name


class WikiMember(models.Model):
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  group = models.ForeignKey(WikiGroup, on_delete=models.CASCADE)

  created = models.DateTimeField(auto_now_add=True)
  modified = models.DateTimeField(auto_now=True)

  def __str__(self):
    return self.name

  @property
  def name(self):
    return self.user.name

  @property
  def email(self):
    return self.user.email


class Page(models.Model):
  path = models.CharField(max_length=150)

  wiki = models.ForeignKey(Wiki, on_delete=models.CASCADE)

  created = models.DateTimeField(auto_now_add=True)
  modified = models.DateTimeField(auto_now=True)

  class Meta:
    ordering = ['path']
    unique_together = [['path', 'wiki']]


class Version(models.Model):
  content = models.TextField()

  page = models.ForeignKey(Page, on_delete=models.CASCADE)

  publish_on = models.DateTimeField(blank=True, null=True)

  approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, blank=True, null=True, related_name="+")

  created = models.DateTimeField(auto_now_add=True)
  created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, related_name="+")

  modified = models.DateTimeField(auto_now=True)
  modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, related_name="+")

  def __str__(self):
    return str(self.page)