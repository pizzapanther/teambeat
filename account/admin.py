from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from account.models import User, PasswordReset, Organization, OrgMember, Credit


@admin.register(User)
class UserAdmin(UserAdmin):
  list_display = ("username", "first_name", "last_name", "is_staff")
  list_filter = ("is_staff", "is_superuser", "is_active", "groups")
  search_fields = ("username", "first_name", "last_name")
  fieldsets = (
    (None, {"fields": ("username", "password")}),
    ("Personal info", {"fields": ("first_name", "last_name")}),
    (
      "Permissions",
      {
        "fields": (
          "is_active",
          "is_staff",
          "is_superuser",
          "groups",
          "user_permissions",
        ),
      },
    ),
    ("Important dates", {"fields": ("last_login", "date_joined")}),
  )


@admin.register(PasswordReset)
class ResetAdmin(admin.ModelAdmin):
  list_display = ('user', 'used', 'created')
  list_filter = ('created', 'used')
  search_fields = ('user__username',)
  date_hierarchy = 'created'

  raw_id_fields = ('user',)


class MemberInline(admin.TabularInline):
  model = OrgMember
  raw_id_fields = ('user',)


@admin.register(Organization)
class OrgAdmin(admin.ModelAdmin):
  list_display = ('name', 'created')
  list_filter = ('created',)
  search_fields = ('name',)

  inlines = [MemberInline]


@admin.register(Credit)
class CreditAdmin(admin.ModelAdmin):
  list_display = ('org', 'level', 'cancelled', 'expiration', 'created')
  list_filter = ('created', 'cancelled')
  search_fields = ('org__name',)
  raw_id_fields = ('org',)
