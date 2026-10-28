"""Adiciona as colunas provisórias de ``CargoProcesso``."""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Cria ``novo_id`` e ``processo_novo`` (FK provisória do processo)."""

    dependencies = [
        ("cargos", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="cargoprocesso",
            name="novo_id",
            field=models.BigIntegerField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name="cargoprocesso",
            name="processo_novo",
            field=models.BigIntegerField(null=True),
        ),
    ]
