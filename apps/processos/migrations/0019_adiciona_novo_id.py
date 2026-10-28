"""Adiciona a coluna provisória ``novo_id`` em ``ProcessoConvocacao``."""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Cria ``novo_id``, que a troca de PK transforma no ``id``."""

    dependencies = [
        ("processos", "0018_consolida_historico_auditlog"),
    ]

    operations = [
        migrations.AddField(
            model_name="processoconvocacao",
            name="novo_id",
            field=models.BigIntegerField(editable=False, null=True),
        ),
    ]
