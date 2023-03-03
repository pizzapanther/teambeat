from django import forms
from django.contrib.auth import password_validation

from account.models import User, Organization, OrgMember


class ResetForm(forms.Form):
  email = forms.EmailField()

  def clean_email(self):
    data = self.cleaned_data['email']
    self.user_cache = User.objects.filter(username=data.lower()).first()
    if not self.user_cache:
      self.add_error('email', "Not Found")

    return data


class ResetFinishForm(forms.Form):
  password = forms.CharField(widget=forms.PasswordInput)
  confirm_password = forms.CharField(widget=forms.PasswordInput)

  def __init__(self, user, *args, **kwargs):
    self.user = user
    super().__init__(*args, **kwargs)

  def clean(self):
    cleaned_data = super().clean()
    password = cleaned_data.get("password")
    confirm_password = cleaned_data.get("confirm_password")
    if password != confirm_password:
      self.add_error('confirm_password', 'Passwords do not match')

    password_validation.validate_password(password, self.user)

    return cleaned_data


class SignUpForm(forms.Form):
  email = forms.EmailField()
  first_name = forms.CharField(max_length=150)
  last_name = forms.CharField(max_length=150)
  password = forms.CharField(widget=forms.PasswordInput)

  def clean_email(self):
    data = self.cleaned_data['email']
    data = data.lower()
    if User.objects.filter(username=data).count() > 0:
      self.add_error('email', "E-Mail already found.")

    return data


class EditAccountForm(forms.ModelForm):
  class Meta:
    model = User
    fields = ['username', 'first_name', 'last_name']


class OrgForm(forms.ModelForm):
  class Meta:
    model = Organization
    fields = ['name']


class MemberForm(forms.ModelForm):
  email = forms.EmailField()
  first_name = forms.CharField(max_length=150)
  last_name = forms.CharField(max_length=150)

  class Meta:
    model = OrgMember
    fields = ['role']
