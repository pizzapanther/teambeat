# Generated by Django 4.1.5 on 2023-03-06 14:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0016_remove_team_days_team_days_of_week'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='team',
            options={'verbose_name': 'scrum team'},
        ),
    ]
