from django import forms

from teams.models import Status, Team, Member, default_days


RATINGS = [(str(i), str(i)) for i in range(1, 11)]


class SaveStatusMixin:
  def save_status(self, status):
    answers = {}

    for i, q in enumerate(status.scrum.team.question_data):
      key = f'question{i}'
      answers[key] = self.cleaned_data[key]

    status.status = answers
    status.save()


def status_form(token):
  status = Status.get_from_token(token)

  attrs = {
    'token': forms.CharField(widget=forms.HiddenInput, initial=token)
  }

  if status:
    for i, q in enumerate(status.scrum.team.question_data):
      if q['type'] == 'question':
        attrs[f'question{i}'] = forms.CharField(max_length=255, label=q['text'])

      elif q['type'] == 'rating':
        attrs[f'question{i}'] = forms.ChoiceField(
          choices=RATINGS,
          label=q['text'],
          widget=forms.RadioSelect(attrs={'class': 'inline'})
        )

  return type('StatusForm', (SaveStatusMixin, forms.Form), attrs), status


class TeamForm(forms.ModelForm):
  days_of_week = forms.MultipleChoiceField(
    choices=Team.DAYS, widget=forms.CheckboxSelectMultiple, initial=default_days)

  class Meta:
    model = Team
    fields = ['name', 'send_time', 'hours_open', 'timezone', 'days_of_week', 'active']


def add_member_form(queryset):
  class AddMemberForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=queryset, empty_label="Choose A User")

    class Meta:
      model = Member
      fields = ['user', 'view_ratings', 'report_status']

  return AddMemberForm
