# Generated by Django 5.0.1 on 2024-02-22 06:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0024_remove_case_status_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='status_history',
            name='status_date_added',
            field=models.DateTimeField(),
        ),
    ]
