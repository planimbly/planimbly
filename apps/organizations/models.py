from django.db import models


# Organizacja
class Organization(models.Model):
    name = models.CharField(max_length=512, unique=True, verbose_name='Nazwa organizacji')

    def __str__(self):
        return self.name


# Jednostka
class Unit(models.Model):
    name = models.CharField(max_length=512, unique=True, verbose_name='Nazwa jednostki')
    unit_org = models.ForeignKey(Organization, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


# Dział
class Workplace(models.Model):
    name = models.CharField(max_length=512, verbose_name='Nazwa działu')
    workplace_unit = models.ForeignKey(Unit, on_delete=models.CASCADE)

    def __str__(self):
        return self.workplace_unit.name + ' ' + self.name


class WorkplaceClosing(models.Model):
    workplace = models.ForeignKey(Workplace, on_delete=models.CASCADE, verbose_name="Dział")
    start = models.DateField(verbose_name="Początek zamknięcia", null=True, blank=True)
    end = models.DateField(verbose_name="Koniec zamknięcia", null=True, blank=True)

    def __str__(self):
        return self.workplace.__str__() + ' ' + str(self.start) + '/' + str(self.end)
