"""Adiciona as colunas provisórias dos modelos de envio de e-mail."""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Cria ``novo_id`` nos 3 modelos e ``envio_email_novo`` no candidato."""

    dependencies = [
        ("envio_email", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="envioemail",
            name="novo_id",
            field=models.BigIntegerField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name="envioemailcandidato",
            name="novo_id",
            field=models.BigIntegerField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name="envioemailconteudo",
            name="novo_id",
            field=models.BigIntegerField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name="envioemailcandidato",
            name="envio_email_novo",
            field=models.BigIntegerField(null=True),
        ),
    ]
