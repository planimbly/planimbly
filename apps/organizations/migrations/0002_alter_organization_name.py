# Generated by Django 4.0.3 on 2022-04-29 21:00

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('organizations', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='name',
            field=models.CharField(max_length=512, verbose_name='Nazwa organizacji'),
        ),
    ]
