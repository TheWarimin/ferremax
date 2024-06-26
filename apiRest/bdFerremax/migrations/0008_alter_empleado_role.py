# Generated by Django 5.0.6 on 2024-06-23 21:35

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bdFerremax", "0007_customuser_employee_role_customuser_is_employee_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="empleado",
            name="role",
            field=models.CharField(
                choices=[
                    ("bodeguero", "Bodeguero"),
                    ("cajero", "Cajero"),
                    ("contador", "Contador"),
                    ("administrador", "Administrador"),
                ],
                max_length=50,
            ),
        ),
    ]
