from django.db import models

from apps.accounts.models import Employee
from apps.organizations.models import Workplace


class Schedule(models.Model):
    year = models.IntegerField(verbose_name='Rok')
    month = models.IntegerField(verbose_name='Miesiąc')
    workplace = models.ForeignKey(Workplace, on_delete=models.CASCADE, verbose_name="Dział")

    def __str__(self):
        return str(self.year) + ' ' + str(self.month) + ' ' + self.workplace.__str__()


class ShiftType(models.Model):
    hour_start = models.TimeField(verbose_name="Czas rozpoczęcia zmiany")
    hour_end = models.TimeField(verbose_name="Czas zakończenia zmiany")
    name = models.CharField(max_length=512, verbose_name="Etykieta zmiany")
    workplace = models.ForeignKey(Workplace, verbose_name="Dział", on_delete=models.CASCADE)
    demand = models.IntegerField(verbose_name='Liczba pracowników', default=1)
    color = models.CharField(max_length=7, verbose_name="Kolor zmiany", default="#BEDAFF")
    active_days = models.TextField(verbose_name="Aktywne dni")
    is_used = models.BooleanField(default=False)
    is_archive = models.BooleanField(default=False)

    def __str__(self):
        return self.workplace.name + ' ' + self.name


class Preference(models.Model):
    shift_type = models.ForeignKey(ShiftType, on_delete=models.CASCADE, verbose_name="Typ zmiany")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Pracownik")
    active_days = models.TextField(verbose_name="Aktywne dni")

    def __str__(self):
        return self.shift_type.name + ' ' + self.employee.username


class Assignment(models.Model):
    shift_type = models.ForeignKey(ShiftType, on_delete=models.CASCADE, verbose_name="Typ zmiany")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Pracownik")
    start = models.DateField(verbose_name="Początek przypisania", null=True, blank=True)
    end = models.DateField(verbose_name="Koniec przypisania", null=True, blank=True)
    negative_flag = models.BooleanField(verbose_name="Zakaz", default=False)

    def __str__(self):
        return self.shift_type.name + ' ' + self.employee.username + ' ' + str(self.negative_flag)


class Shift(models.Model):
    date = models.DateField(verbose_name='Data zmiany')
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, verbose_name="Grafik")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Pracownik")
    shift_type = models.ForeignKey(ShiftType, on_delete=models.CASCADE, verbose_name="Typ zmiany")

    def __str__(self):
        return str(self.date) + ' ' + self.employee.__str__() + ' ' + self.shift_type.__str__()


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

    def __str__(self):
        return self.employee.__str__() + ' ' + str(self.start) + '/' + str(self.end) + ' ' + self.type
