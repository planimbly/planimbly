from django.db import models

from apps.accounts.models import Employee
from apps.organizations.models import Workplace


class Schedule(models.Model):
    date_start = models.DateField(verbose_name='Data rozpoczęcia')
    date_end = models.DateField(verbose_name='Data zakończenia')
    workplace = models.ForeignKey(Workplace, on_delete=models.CASCADE, verbose_name="Dział")


class ShiftType(models.Model):
    hour_start = models.TimeField(verbose_name="Czas rozpoczęcia zmiany")
    hour_end = models.TimeField(verbose_name="Czas zakończenia zmiany")
    name = models.CharField(max_length=512, verbose_name="Etykieta zmiany")
    workplace = models.ForeignKey(Workplace, verbose_name="Dział", on_delete=models.CASCADE)
    active_days = models.TextField(verbose_name="Aktywne dni")
    is_used = models.BooleanField(default=False)
    is_archive = models.BooleanField(default=False)


class Shift(models.Model):
    date = models.DateField(verbose_name='Data zmiany')
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, verbose_name="Grafik")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Pracownik")
    shift_type = models.ForeignKey(ShiftType, on_delete=models.CASCADE, verbose_name="Typ zmiany")

    def __str__(self):
        return 'Data:' + str(self.date) + ' Pracownik: ' + self.employee + 'Zmiana: ' + self.shift_type.name
