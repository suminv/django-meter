# Generated by Django 4.1.7 on 2023-03-26 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('add_meters', '0002_profile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='email',
            field=models.EmailField(max_length=254),
        ),
    ]