from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=512, verbose_name='Nazwa organizacji')


class Unit(models.Model):
    name = models.CharField(max_length=512)
    unit_org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    allow_preferences = models.BooleanField(default=False)


class Workplace(models.Model):
    name = models.CharField(max_length=512)
    workplace_unit = models.ForeignKey(Unit, on_delete=models.CASCADE)