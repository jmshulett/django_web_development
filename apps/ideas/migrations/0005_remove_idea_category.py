# Generated by Django 3.0.14 on 2021-09-18 17:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ideas', '0004_copy_categories'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='idea',
            name='category',
        ),
    ]
