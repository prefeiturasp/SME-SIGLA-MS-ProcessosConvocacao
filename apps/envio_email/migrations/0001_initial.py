"""Registra os modelos de e-mail no app ``envio_email``, sem SQL.

As tabelas ``processos_envio_email``, ``processos_envio_email_candidato``
e ``processos_envio_email_conteudo`` foram criadas pelas migrations de
``processos`` e continuam com os dados. Esta migration só cria os
modelos no estado do app ``envio_email``, logo depois de a 0017 de
``processos`` tirá-los de lá.
"""

import uuid

import django.db.models.deletion
from django.db import migrations, models

TIPOS_DE_ENVIO = [
    ("CONVOCACAO", "Convocação"),
    ("VAGAS", "Vagas"),
    ("RESULTADOS", "Resultados"),
]
AJUDA_CORPO_HTML = (
    "Fragmento HTML do corpo (sem cabeçalho PMSP). Variáveis Django:"
    " {{ cargo }}, {{ classificacao }}, {{ data_publicacao }}, etc. O"
    " layout base vem de templates/email/envio_email.html."
)


class Migration(migrations.Migration):
    """Cria os três modelos de e-mail no estado, sem SQL."""

    initial = True

    dependencies = [
        ("processos", "0017_move_modelos_para_apps"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="EnvioEmail",
                    fields=[
                        (
                            "uuid",
                            models.UUIDField(
                                default=uuid.uuid4,
                                editable=False,
                                primary_key=True,
                                serialize=False,
                            ),
                        ),
                        (
                            "criado_em",
                            models.DateTimeField(
                                auto_now_add=True, verbose_name="Criado em"
                            ),
                        ),
                        (
                            "atualizado_em",
                            models.DateTimeField(
                                auto_now=True, verbose_name="Atualizado em"
                            ),
                        ),
                        (
                            "processo_uuid",
                            models.UUIDField(verbose_name="UUID do Processo"),
                        ),
                        (
                            "processo_nome",
                            models.CharField(
                                max_length=200,
                                verbose_name="Nome do Processo",
                            ),
                        ),
                        (
                            "tipo",
                            models.CharField(
                                choices=TIPOS_DE_ENVIO,
                                max_length=20,
                                verbose_name="Tipo de envio",
                            ),
                        ),
                        (
                            "quantidade_candidatos",
                            models.IntegerField(
                                default=0,
                                verbose_name="Quantidade de candidatos",
                            ),
                        ),
                    ],
                    options={
                        "verbose_name": "Envio de e-mail",
                        "verbose_name_plural": "Envios de e-mail",
                        "db_table": "processos_envio_email",
                        "ordering": ["-criado_em"],
                    },
                ),
                migrations.CreateModel(
                    name="EnvioEmailConteudo",
                    fields=[
                        (
                            "uuid",
                            models.UUIDField(
                                default=uuid.uuid4,
                                editable=False,
                                primary_key=True,
                                serialize=False,
                            ),
                        ),
                        (
                            "criado_em",
                            models.DateTimeField(
                                auto_now_add=True, verbose_name="Criado em"
                            ),
                        ),
                        (
                            "atualizado_em",
                            models.DateTimeField(
                                auto_now=True, verbose_name="Atualizado em"
                            ),
                        ),
                        (
                            "tipo",
                            models.CharField(
                                choices=TIPOS_DE_ENVIO,
                                max_length=20,
                                unique=True,
                                verbose_name="Tipo de envio",
                            ),
                        ),
                        (
                            "assunto",
                            models.CharField(
                                blank=True,
                                default="",
                                max_length=255,
                                verbose_name="Assunto do e-mail",
                            ),
                        ),
                        (
                            "conteudo",
                            models.TextField(
                                help_text=AJUDA_CORPO_HTML,
                                verbose_name="Corpo do e-mail (HTML)",
                            ),
                        ),
                        (
                            "conteudo_gabarito",
                            models.TextField(
                                help_text=AJUDA_CORPO_HTML,
                                verbose_name="Corpo do e-mail (HTML)",
                            ),
                        ),
                    ],
                    options={
                        "verbose_name": "Conteúdo de e-mail por tipo",
                        "verbose_name_plural": "Conteúdos de e-mail por tipo",
                        "db_table": "processos_envio_email_conteudo",
                        "ordering": ["tipo"],
                    },
                ),
                migrations.CreateModel(
                    name="EnvioEmailCandidato",
                    fields=[
                        (
                            "uuid",
                            models.UUIDField(
                                default=uuid.uuid4,
                                editable=False,
                                primary_key=True,
                                serialize=False,
                            ),
                        ),
                        (
                            "criado_em",
                            models.DateTimeField(
                                auto_now_add=True, verbose_name="Criado em"
                            ),
                        ),
                        (
                            "atualizado_em",
                            models.DateTimeField(
                                auto_now=True, verbose_name="Atualizado em"
                            ),
                        ),
                        (
                            "nome",
                            models.CharField(
                                max_length=200, verbose_name="Nome"
                            ),
                        ),
                        (
                            "rf",
                            models.CharField(
                                blank=True, max_length=20, verbose_name="RF"
                            ),
                        ),
                        (
                            "email",
                            models.EmailField(
                                max_length=254, verbose_name="Email"
                            ),
                        ),
                        (
                            "status",
                            models.CharField(
                                choices=[
                                    ("PENDENTE", "Pendente"),
                                    ("SUCESSO", "Sucesso"),
                                    ("ERRO", "Erro"),
                                ],
                                max_length=20,
                                verbose_name="Status do envio",
                            ),
                        ),
                        (
                            "status_detalhe",
                            models.TextField(
                                blank=True,
                                help_text=(
                                    "Mensagem de erro ou detalhe do envio"
                                ),
                                verbose_name="Detalhe do status",
                            ),
                        ),
                        (
                            "conteudo",
                            models.TextField(
                                blank=True,
                                verbose_name="Conteúdo do email enviado",
                            ),
                        ),
                        (
                            "envio_email",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="candidatos",
                                to="envio_email.envioemail",
                                verbose_name="Envio de e-mail",
                            ),
                        ),
                    ],
                    options={
                        "verbose_name": "Envio de e-mail - Candidato",
                        "verbose_name_plural": "Envio de e-mail - Candidatos",
                        "db_table": "processos_envio_email_candidato",
                        "ordering": ["-criado_em"],
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
