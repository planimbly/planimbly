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
from django.urls import path, include
from rest_framework import routers

from .views import EmployeesImportView, OrganizationCreateView, EmployeesManageView, UnitsManageView, UnitViewSet, \
    WorkplaceManageView, WorkplaceViewSet, EmployeeToWorkplaceView, EmployeeToUnitApiView, \
    EmployeeToWorkplaceApiView, EmployeeToUnitView

unit_router = routers.DefaultRouter()
unit_router.register(r'unit', UnitViewSet, basename='unit')
workplace_router = routers.DefaultRouter()
workplace_router.register(r'workplace', WorkplaceViewSet, basename='workplace')

urlpatterns = [
    path('create/', OrganizationCreateView.as_view(template_name='organizations/organization_create.html'),
         name='organization_create'),
    path('employees_import/', EmployeesImportView.as_view(), name='employees_import'),
    path('employees_manage/', EmployeesManageView.as_view(), name='employees_manage'),
    path('units_manage/', UnitsManageView.as_view(), name='units_manage'),
    path('<int:unit_pk>/workplace_manage/', WorkplaceManageView.as_view(), name='workplace_manage'),
    path('<int:unit_workplace_pk>/employees_to_unit/', EmployeeToUnitView.as_view(), name='employee_to_unit'),
    path('<int:unit_workplace_pk>/employees_to_workplace/', EmployeeToWorkplaceView.as_view(),
         name='employee_to_workplace'),

    # API urls
    path('api/', include(unit_router.urls)),
    path('api/<int:unit_pk>/', include(workplace_router.urls)),
    path('api/<int:unit_workplace_pk>/employees_to_unit/', EmployeeToUnitApiView.as_view(),
         name='employee_to_unit_api'),
    path('api/<int:unit_workplace_pk>/employees_to_workplace/', EmployeeToWorkplaceApiView.as_view(),
         name='employee_to_workplace_api')
]
