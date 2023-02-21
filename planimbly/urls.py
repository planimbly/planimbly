"""planimbly URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
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
from django.urls import path, include
from environs import Env

from apps.accounts.views import RedirectUrlView

env = Env()
env.read_env()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('organizations/', include('apps.organizations.urls')),
    path('schedules/', include('apps.schedules.urls')),
    path('', RedirectUrlView.as_view(), name='redirect_url'),
    path('', include('django_prometheus.urls')),  # /metrics
]

if env.bool("DEBUG_TOOLBAR", default=False):
    urlpatterns.insert(len(urlpatterns) - 1, path('__debug__/', include('debug_toolbar.urls')))
