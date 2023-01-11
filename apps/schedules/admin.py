from django.contrib import admin

from .models import FreeDay, Schedule, ShiftType, Preference, Assignment, Shift, Absence, JobTime

admin.site.register(Schedule)
admin.site.register(ShiftType)
admin.site.register(Preference)


class ShiftAdmin(admin.ModelAdmin):
    list_filter = ('employee', 'schedule')


admin.site.register(Shift, ShiftAdmin)
admin.site.register(Absence)
admin.site.register(Assignment)
admin.site.register(FreeDay)
admin.site.register(JobTime)
