from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.organizations.models import Organization, Workplace, Unit


class MyAccountManager(BaseUserManager):
    def create_user(self, email, username, first_name, last_name, password=None, user_org=None, is_supervisor=None):
        if not email:
            raise ValueError("Users must have email")
        if not username:
            raise ValueError("Users must have an username")
        if not first_name:
            raise ValueError("Users must have a name")
        if not last_name:
            raise ValueError("Users must have a surname")
        # TODO automatyczne tworzenie username
        user = self.model(email=self.normalize_email(email), username=username, first_name=first_name,
                          last_name=last_name, user_org=user_org, is_supervisor=is_supervisor)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password):
        user = self.create_user(email=self.normalize_email(email),
                                username=username,
                                password=password,
                                first_name="admin",
                                last_name="admin")
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class Employee(AbstractUser):
    email = models.EmailField(verbose_name="Adres email")
    username = models.CharField(max_length=50, unique=True, verbose_name="Nazwa użytkownika")
    first_name = models.CharField(max_length=50, verbose_name="Imię")
    last_name = models.CharField(max_length=50, verbose_name="Nazwisko")
    job_time = models.IntegerField(verbose_name="Wymiar etatu", default=0)
    is_supervisor = models.BooleanField(verbose_name="Czy jest kierownikiem?", default=False)
    user_org = models.ForeignKey(Organization, on_delete=models.CASCADE, blank=True, null=True,
                                 verbose_name="Organizacja użytkownika")
    user_unit = models.ManyToManyField(Unit, verbose_name="Jednostki użytkownika")
    user_workplace = models.ManyToManyField(Workplace, verbose_name="Działy użytkownika")

    objects = MyAccountManager()

    def __str__(self):
        return self.username


class Absence(models.Model):
    start = models.DateField(verbose_name="Początek nieobecności")
    end = models.DateField(verbose_name="Koniec nieobecności")
    employee = models.ForeignKey(Employee, verbose_name="Pracownik", on_delete=models.CASCADE)
    # TODO Typ do uzupełnienia
    type = models.CharField(max_length=256, verbose_name="Typ nieobecności")
    hours_number = models.IntegerField(verbose_name="Liczba godzin nieobecności")
