from django import forms
from django.contrib import admin

from teams.models import Team, Member, Status, Scrum


class MemberInline(admin.TabularInline):
  model = Member
  raw_id_fields = ('user',)


class TeamForm(forms.ModelForm):
  days_of_week = forms.MultipleChoiceField(choices=Team.DAYS, widget=forms.CheckboxSelectMultiple)

  class Meta:
    model = Team
    fields = '__all__'


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
  list_display = ('name', 'org', 'next_send', 'next_report', 'created')
  list_filter = ('created', 'next_send', 'next_report')
  search_fields = ('name',)
  date_hierarchy = 'next_send'
  raw_id_fields = ('org',)
  form = TeamForm

  inlines = [MemberInline]


class StatusInline(admin.TabularInline):
  model = Status
  raw_id_fields = ('member',)


@admin.register(Scrum)
class ScrumAdmin(admin.ModelAdmin):
  list_display = ('team', 'created')
  list_filter = ('created',)
  search_fields = ('team__name',)
  date_hierarchy = 'created'

  inlines = [StatusInline]
  raw_id_fields = ('team',)
