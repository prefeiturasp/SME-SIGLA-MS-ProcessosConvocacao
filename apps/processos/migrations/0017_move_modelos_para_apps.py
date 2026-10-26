"""Tira do estado de ``processos`` os modelos que mudaram de app.

A reorganização de pastas levou ``CargoProcesso`` para o app ``cargos``
e ``EnvioEmail``, ``EnvioEmailCandidato`` e ``EnvioEmailConteudo`` para
``envio_email``, mas as migrations seguiam registrando os quatro em
``processos``. Esta migration só muda o estado: as tabelas
``processos_cargos`` e ``processos_envio_email*`` e os seus dados ficam
como estão. As ``0001_initial`` de ``cargos`` e de ``envio_email``
registram os modelos nos apps atuais, sobre as mesmas tabelas.
"""

from django.db import migrations


class Migration(migrations.Migration):
    """Remove os quatro modelos do estado, sem SQL."""

    dependencies = [
        ("processos", "0016_alter_processoconvocacao_tipo_escolha"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterUniqueTogether(
                    name="cargoprocesso",
                    unique_together=None,
                ),
                migrations.RemoveField(
                    model_name="cargoprocesso",
                    name="processo",
                ),
                migrations.RemoveField(
                    model_name="envioemailcandidato",
                    name="envio_email",
                ),
                migrations.DeleteModel(
                    name="EnvioEmailConteudo",
                ),
                migrations.DeleteModel(
                    name="CargoProcesso",
                ),
                migrations.DeleteModel(
                    name="EnvioEmail",
                ),
                migrations.DeleteModel(
                    name="EnvioEmailCandidato",
                ),
            ],
            database_operations=[],
        ),
    ]
