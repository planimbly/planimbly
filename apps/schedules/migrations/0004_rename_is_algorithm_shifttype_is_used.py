# Generated by Django 4.0.3 on 2022-05-17 15:07

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('schedules', '0003_rename_id_workplace_schedule_workplace_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='shifttype',
            old_name='is_algorithm',
            new_name='is_used',
        ),
    ]
