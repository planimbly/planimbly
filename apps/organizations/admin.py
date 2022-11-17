from django.contrib import admin

from .models import Organization, Unit, Workplace, WorkplaceClosing

admin.site.register(Organization)
admin.site.register(Unit)
admin.site.register(Workplace)
admin.site.register(WorkplaceClosing)
