"""tbeat URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

import account.views
import teams.views
import wiki.views


urlpatterns = [
    path('admin/', admin.site.urls),

    path('accounts/login/', account.views.login_view),
    path('accounts/logout/', account.views.logout_view),
    path('accounts/reset/', account.views.reset),
    path('accounts/reset-finish/', account.views.reset_finish),

    path('accounts/signup/', account.views.signup),
    path('accounts/edit/', account.views.edit_account),
    path('accounts/password/', account.views.edit_password),

    path('dashboard/', account.views.dashboard),

    path('payments/subscribe/success/', account.views.subscribe_success),
    path('payments/subscribe/<str:level>/', account.views.subscibe_to_level),
    path('payments/subscribe/', account.views.subscribe),
    path('payments/webhook/', account.views.webhook),
    path('payments/cancel/', account.views.cancel_plan),
    path('payments/change/', account.views.change_plan),
    path('payments/', account.views.payments),

    path('org/edit/', account.views.edit_org),
    path('org/members/', account.views.list_members),
    path('org/members/add/', account.views.edit_member),
    path('org/members/remove/<int:member_id>/', account.views.rm_member),
    path('org/members/<int:member_id>/', account.views.edit_member),

    path('status/open/', teams.views.open_status),
    path('status/save/', teams.views.save_status),
    path('status/save/<int:status_id>/', teams.views.user_save_status),
    path('status/reports/', teams.views.list_reports),
    path('status/<int:report_id>/', teams.views.report_detail),

    path('teams/list/', teams.views.list_teams),
    path('teams/add/', teams.views.edit_team),
    path('teams/edit/<int:team_id>/add-member/', teams.views.team_add_member),
    path('teams/edit/<int:team_id>/', teams.views.edit_team),

    path('wiki/<slug:wiki_slug>/<path:path>/__versions__/', wiki.views.versions_viewer),

    path('wiki/<slug:wiki_slug>/', wiki.views.page_viewer),
    path('wiki/<slug:wiki_slug>/<path:path>', wiki.views.page_viewer),

    path('favicon.ico', account.views.favicon),
    path('', account.views.home),
]
