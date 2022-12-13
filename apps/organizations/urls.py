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
from django.contrib.auth.decorators import login_required
from django.urls import path, include
from rest_framework import routers

from .views import OrganizationCreateView, EmployeesManageView, UnitsManageView, UnitViewSet, \
    WorkplaceManageView, WorkplaceViewSet, EmployeeToUnitApiView, \
    EmployeeToWorkplaceApiView, EmployeeToUnitWorkplaceView, EmployeesImportApiView, WorkplaceClosingViewSet, \
    WorkplaceClosingView

default_router = routers.DefaultRouter()
default_router.register(r'unit', UnitViewSet, basename='unit')
default_router.register(r'workplace_closing', WorkplaceClosingViewSet, basename='workplace_closing')
workplace_router = routers.DefaultRouter()
workplace_router.register(r'workplace', WorkplaceViewSet, basename='workplace')

urlpatterns = [
    path('create/', OrganizationCreateView.as_view(template_name='organizations/organization_create.html'),
         name='organization_create'),

    path('employees_manage/', EmployeesManageView.as_view(), name='employees_manage'),
    path('units_manage/', UnitsManageView.as_view(), name='units_manage'),
    path('', login_required(UnitsManageView.as_view(), login_url='/accounts/login/'), name='units_manage'),
    path('workplace_manage/', WorkplaceManageView.as_view(), name='workplace_manage'),
    path('employees_to_unit_workplace/', EmployeeToUnitWorkplaceView.as_view(), name='employee_to_unit_workplace'),
    path('workplace_closing/', WorkplaceClosingView.as_view(), name='workplace_closing'),

    # API urls
    path('api/', include(default_router.urls)),
    path('api/<int:unit_pk>/', include(workplace_router.urls)),
    path('api/<int:unit_workplace_pk>/employees_to_unit/', EmployeeToUnitApiView.as_view(),
         name='employee_to_unit_api'),
    path('api/<int:unit_workplace_pk>/employees_to_workplace/', EmployeeToWorkplaceApiView.as_view(),
         name='employee_to_workplace_api'),
    path('api/employees_import/', EmployeesImportApiView.as_view(), name='employees_import_api'),
]
