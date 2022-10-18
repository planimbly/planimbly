from django.db import models

from apps.accounts.models import Employee
from apps.organizations.models import Workplace


class Schedule(models.Model):
    year = models.IntegerField(verbose_name='Rok')
    month = models.IntegerField(verbose_name='Miesiąc')
    workplace = models.ForeignKey(Workplace, on_delete=models.CASCADE, verbose_name="Dział")


class ShiftType(models.Model):
    hour_start = models.TimeField(verbose_name="Czas rozpoczęcia zmiany")
    hour_end = models.TimeField(verbose_name="Czas zakończenia zmiany")
    name = models.CharField(max_length=512, verbose_name="Etykieta zmiany")
    workplace = models.ForeignKey(Workplace, verbose_name="Dział", on_delete=models.CASCADE)
    active_days = models.TextField(verbose_name="Aktywne dni")
    is_used = models.BooleanField(default=False)
    is_archive = models.BooleanField(default=False)

    def __str__(self):
        return self.workplace.name + ' ' + self.name


class Preference(models.Model):
    shift_type = models.ForeignKey(ShiftType, on_delete=models.CASCADE, verbose_name="Typ zmiany")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Pracownik")
    active_days = models.TextField(verbose_name="Aktywne dni")


class Shift(models.Model):
    date = models.DateField(verbose_name='Data zmiany')
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, verbose_name="Grafik")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Pracownik")
    shift_type = models.ForeignKey(ShiftType, on_delete=models.CASCADE, verbose_name="Typ zmiany")


class Absence(models.Model):
    start = models.DateField(verbose_name="Początek nieobecności")
    end = models.DateField(verbose_name="Koniec nieobecności")
    employee = models.ForeignKey(Employee, verbose_name="Pracownik", on_delete=models.CASCADE)
    ABSENCE_TYPE = [
        ('SICK', 'Zwolnienie L4'),
        ('VAC', 'Urlop wypoczynkowy')
    ]
    type = models.CharField(max_length=256, verbose_name="Typ nieobecności", choices=ABSENCE_TYPE)
    hours_number = models.IntegerField(verbose_name="Liczba godzin nieobecności")
