# Generated by Django 5.0.6 on 2024-07-08 19:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bdFerremax", "0011_pedido"),
    ]

    operations = [
        migrations.RenameField(
            model_name="pedido",
            old_name="transaccion",
            new_name="webpay_transaction",
        ),
        migrations.AlterField(
            model_name="pedido",
            name="estado",
            field=models.CharField(
                choices=[
                    ("enviando", "Enviando"),
                    ("enviado", "Enviado"),
                    ("entregado", "Entregado"),
                ],
                default="enviando",
                max_length=10,
            ),
        ),
    ]
