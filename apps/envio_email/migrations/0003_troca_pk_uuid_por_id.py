"""Troca a PK UUID pelo ``id`` inteiro carregado na 0020 de ``processos``.

Vale para os 3 modelos de envio de e-mail. A FK ``envio_email`` do
candidato sai primeiro, para o banco deixar remover a PK do ``uuid`` de
``EnvioEmail``, e volta no fim a partir de ``envio_email_novo``.

Na volta, a FK é recriada como coluna NOT NULL sem default, o que só
funciona com a tabela de candidatos vazia.
"""

import uuid

import django.db.models.deletion
from django.core.management.color import no_style
from django.db import migrations, models

MODELOS = ["EnvioEmail", "EnvioEmailCandidato", "EnvioEmailConteudo"]


def reiniciar_sequencias(apps, schema_editor):
    """Faz a sequência de cada ``id`` continuar depois do maior valor.

    No PostgreSQL a coluna vira identity começando em 1, e sem este passo
    o primeiro INSERT colidiria com os ids da carga. No SQLite a lista de
    comandos vem vazia.

    Args:
        apps: Registro de modelos históricos da migration.
        schema_editor: Editor de esquema da conexão em uso.
    """
    conexao = schema_editor.connection
    modelos = [apps.get_model("envio_email", nome) for nome in MODELOS]
    with conexao.cursor() as cursor:
        for sql in conexao.ops.sequence_reset_sql(no_style(), modelos):
            cursor.execute(sql)


class Migration(migrations.Migration):
    """Promove ``novo_id`` a PK ``id`` e refaz a FK apontando para ele.

    O nome provisório ``novo_id`` evita colidir com o ``id`` que o Django
    cria no estado intermediário, quando o modelo fica sem PK.
    ``novo_id`` vira NOT NULL antes de virar PK: na volta, o PostgreSQL
    só aceita o DROP NOT NULL depois que a PK sai.
    """

    dependencies = [
        ("envio_email", "0002_adiciona_novo_id"),
        ("processos", "0020_popula_novo_id"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="envioemailcandidato",
            name="envio_email",
        ),
        *[
            migrations.AlterField(
                model_name=nome.lower(),
                name="uuid",
                field=models.UUIDField(
                    default=uuid.uuid4, editable=False, unique=True
                ),
            )
            for nome in MODELOS
        ],
        *[
            migrations.AlterField(
                model_name=nome.lower(),
                name="novo_id",
                field=models.BigIntegerField(editable=False),
            )
            for nome in MODELOS
        ],
        *[
            migrations.AlterField(
                model_name=nome.lower(),
                name="novo_id",
                field=models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name="ID",
                ),
            )
            for nome in MODELOS
        ],
        *[
            migrations.RenameField(
                model_name=nome.lower(), old_name="novo_id", new_name="id"
            )
            for nome in MODELOS
        ],
        migrations.RenameField(
            model_name="envioemailcandidato",
            old_name="envio_email_novo",
            new_name="envio_email",
        ),
        migrations.AlterField(
            model_name="envioemailcandidato",
            name="envio_email",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="candidatos",
                to="envio_email.envioemail",
                verbose_name="Envio de e-mail",
            ),
        ),
        migrations.RunPython(reiniciar_sequencias, migrations.RunPython.noop),
    ]
