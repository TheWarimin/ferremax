# Generated by Django 5.0.6 on 2024-07-15 19:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bdFerremax", "0018_rename_user_pedido_usuario"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductoPedido",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("cantidad", models.IntegerField()),
                (
                    "pedido",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="bdFerremax.pedido",
                    ),
                ),
                (
                    "producto",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="bdFerremax.producto",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="pedido",
            name="productos",
            field=models.ManyToManyField(
                through="bdFerremax.ProductoPedido", to="bdFerremax.producto"
            ),
        ),
    ]
