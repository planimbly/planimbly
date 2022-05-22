from django.db import models


# Organizacja
class Organization(models.Model):
    name = models.CharField(max_length=512, verbose_name='Nazwa organizacji')

    def __str__(self):
        return self.name


# TODO LISTA PREFERENCJI W ORGANIZACJI DO STWORZENIA:


# Jednostka
class Unit(models.Model):
    name = models.CharField(max_length=512)
    unit_org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    allow_preferences = models.BooleanField(default=False)

    def __str__(self):
        return self.name


# Dział
class Workplace(models.Model):
    name = models.CharField(max_length=512)
    workplace_unit = models.ForeignKey(Unit, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
