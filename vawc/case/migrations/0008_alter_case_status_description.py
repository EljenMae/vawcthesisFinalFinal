# Generated by Django 5.0.1 on 2024-02-17 07:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0007_case_status_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='status_description',
            field=models.TextField(default='No Status Yet.'),
        ),
    ]
