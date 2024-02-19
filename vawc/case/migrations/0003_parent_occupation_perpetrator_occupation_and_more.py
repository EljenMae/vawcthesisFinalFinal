# Generated by Django 5.0.1 on 2024-02-16 12:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0002_parent_educational_attainment_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='parent',
            name='occupation',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='perpetrator',
            name='occupation',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='victim',
            name='occupation',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]