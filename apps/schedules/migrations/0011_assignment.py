# Generated by Django 4.0.3 on 2022-11-15 15:17

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('schedules', '0010_rename_employee_needed_shifttype_demand'),
    ]

    operations = [
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateField(blank=True, null=True, verbose_name='Początek przypisania')),
                ('end', models.DateField(blank=True, null=True, verbose_name='Koniec przypisania')),
                ('negative_flag', models.BooleanField(default=False, verbose_name='Zakaz')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL,
                                               verbose_name='Pracownik')),
                ('shift_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='schedules.shifttype',
                                                 verbose_name='Typ zmiany')),
            ],
        ),
    ]
