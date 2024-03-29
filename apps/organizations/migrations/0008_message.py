# Generated by Django 4.0.3 on 2023-01-11 11:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('organizations', '0007_alter_workplaceclosing_unique_together'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.CharField(max_length=512, verbose_name='Treść')),
                ('type',
                 models.CharField(choices=[('SCHEDULE', 'Grafik')], max_length=256, verbose_name='Typ wiadomości')),
                ('organization',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='organizations.organization',
                                   verbose_name='Organizacja')),
            ],
        ),
    ]
