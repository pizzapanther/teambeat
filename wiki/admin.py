from django.contrib import admin
from django.utils.safestring import mark_safe

from wiki.models import Wiki, WikiGroup, WikiMember, Page, Version


@admin.register(Wiki)
class WikiAdmin(admin.ModelAdmin):
  list_display = ('name', 'org', 'modified')
  list_filter = ('modified',)
  search_fields = ('name',)
  date_hierarchy = 'modified'
  raw_id_fields = ('org',)


class MemberInline(admin.TabularInline):
  model = WikiMember
  raw_id_fields = ('user',)


@admin.register(WikiGroup)
class WikiGroupAdmin(admin.ModelAdmin):
  list_display = ('name', '_paths', 'wiki', 'modified')
  list_filter = ('modified',)
  search_fields = ('name', 'wiki__name')
  raw_id_fields = ('wiki',)
  inlines = [MemberInline]

  def _paths(self, obj):
    if obj:
      return mark_safe('<br>'.join(obj.paths))


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
  list_display = ('path', 'wiki', 'org', 'modified')
  list_filter = ('modified',)
  date_hierarchy = 'modified'
  search_fields = ('name', 'wiki__name')
  raw_id_fields = ('wiki',)


@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
  list_display = ('path', 'wiki', 'org', 'publish_on', 'modified')
  list_filter = ('modified',)
  date_hierarchy = 'modified'
  search_fields = ('page__path', 'page__path__wiki__name')
  raw_id_fields = ('page', 'approved_by', 'created_by', 'modified_by')
