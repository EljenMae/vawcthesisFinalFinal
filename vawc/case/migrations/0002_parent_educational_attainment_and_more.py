# Generated by Django 5.0.1 on 2024-02-16 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='parent',
            name='educational_attainment',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='perpetrator',
            name='educational_attainment',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='victim',
            name='educational_attainment',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
