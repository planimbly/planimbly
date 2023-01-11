from django.db import models


# Organizacja
class Organization(models.Model):
    name = models.CharField(max_length=512, unique=True, verbose_name='Nazwa organizacji')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


# Jednostka
class Unit(models.Model):
    name = models.CharField(max_length=512, unique=True, verbose_name='Nazwa jednostki')
    unit_org = models.ForeignKey(Organization, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


# Dział
class Workplace(models.Model):
    name = models.CharField(max_length=512, verbose_name='Nazwa działu')
    workplace_unit = models.ForeignKey(Unit, on_delete=models.CASCADE)

    def __str__(self):
        return self.workplace_unit.name + ' ' + self.name

    class Meta:
        ordering = ['name']


class WorkplaceClosing(models.Model):
    workplace = models.ForeignKey(Workplace, on_delete=models.CASCADE, verbose_name="Dział")
    start = models.DateField(verbose_name="Początek zamknięcia")
    end = models.DateField(verbose_name="Koniec zamknięcia")

    def __str__(self):
        return self.workplace.__str__() + ' ' + str(self.start) + '/' + str(self.end)

    class Meta:
        ordering = ['start']
        unique_together = ('workplace', 'start', 'end')


class Message(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name="Organizacja")
    content = models.CharField(max_length=512, verbose_name="Treść")
    MESSAGE_TYPE = [
        ('SCHEDULE', 'Grafik'),
    ]
    type = models.CharField(max_length=256, verbose_name="Typ wiadomości", choices=MESSAGE_TYPE)
