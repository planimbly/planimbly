# Generated by Django 4.0.3 on 2022-05-16 15:17

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('schedules', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shifttype',
            name='active_days',
            field=models.TextField(verbose_name='Aktywne dni'),
        ),
    ]
