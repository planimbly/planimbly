# Generated by Django 4.0.3 on 2022-11-28 22:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('schedules', '0013_alter_absence_unique_together'),
    ]

    operations = [
        migrations.CreateModel(
            name='FreeDay',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.DateField(verbose_name='Dzień wolny')),
            ],
        ),
    ]
