from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.organizations.models import Organization, Workplace, Unit


class MyAccountManager(BaseUserManager):
    def create_user(self, email, username, first_name, last_name, order_number, job_time=None, password=None,
                    user_org=None, is_supervisor=False):
        if not email:
            raise ValueError("Users must have email")
        if not username:
            raise ValueError("Users must have an username")
        if not first_name:
            raise ValueError("Users must have a name")
        if not last_name:
            raise ValueError("Users must have a surname")
        # TODO automatyczne tworzenie username
        if job_time is None:
            job_time = '1'
        user = self.model(email=self.normalize_email(email), username=username, first_name=first_name,
                          last_name=last_name, order_number=order_number, user_org=user_org, is_supervisor=is_supervisor
                          , job_time=job_time)
        user.set_password(password)
        user.save(using=self._db)
        return user

    # TODO DO PRZEMYŚLENIA
    def create_superuser(self, email, username, password):
        user = self.create_user(email=self.normalize_email(email),
                                username=username,
                                password=password,
                                first_name="admin",
                                last_name="admin",
                                order_number="0")
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class Employee(AbstractUser):
    email = models.EmailField(verbose_name="Adres email")
    username = models.CharField(max_length=50, unique=True, verbose_name="Nazwa użytkownika")
    first_name = models.CharField(max_length=50, verbose_name="Imię")
    last_name = models.CharField(max_length=50, verbose_name="Nazwisko")
    JOBTIME_TYPE = [
        ('1', '1'),
        ('3/4', '3/4'),
        ('1/2', '1/2'),
        ('1/4', '1/4'),
    ]
    job_time = models.CharField(verbose_name="Wymiar etatu", max_length=3, choices=JOBTIME_TYPE, default='1')
    order_number = models.IntegerField(verbose_name="Liczba porządkowa", default=0, null=True, blank=True)
    is_supervisor = models.BooleanField(verbose_name="Czy jest kierownikiem?", default=False)
    user_org = models.ForeignKey(Organization, on_delete=models.CASCADE, blank=True, null=True,
                                 verbose_name="Organizacja użytkownika")
    user_unit = models.ManyToManyField(Unit, verbose_name="Jednostki użytkownika", blank=True)
    user_workplace = models.ManyToManyField(Workplace, verbose_name="Działy użytkownika", blank=True)

    objects = MyAccountManager()

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "Pracownik"
        ordering = ['order_number']
