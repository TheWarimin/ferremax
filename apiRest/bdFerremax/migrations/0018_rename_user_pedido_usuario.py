# Generated by Django 5.0.6 on 2024-07-15 04:49

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("bdFerremax", "0017_rename_fecha_creacion_pedido_fecha_pedido_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="pedido",
            old_name="user",
            new_name="usuario",
        ),
    ]
