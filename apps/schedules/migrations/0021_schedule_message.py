# Generated by Django 4.0.3 on 2023-01-04 21:33

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('schedules', '0020_shifttype_shift_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedule',
            name='message',
            field=models.CharField(blank=True, max_length=512, null=True,
                                   verbose_name='Wiadomość po wygenerowaniu grafiku'),
        ),
    ]
