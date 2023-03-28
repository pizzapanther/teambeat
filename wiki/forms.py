from django import forms
from wiki.models import Version


class VersionForm(forms.ModelForm):
  publish_on = forms.DateTimeField(
    required=False,
    widget=forms.DateTimeInput(attrs={'type': "datetime-local"})
  )

  class Meta:
    model = Version
    fields = ['title', 'content', 'publish_on']
