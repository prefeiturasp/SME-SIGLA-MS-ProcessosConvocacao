"""Registra ``CargoProcesso`` no app ``cargos``, sem tocar na tabela.

A tabela ``processos_cargos`` foi criada pelas migrations de
``processos`` e continua com os dados. Esta migration só cria o modelo
no estado do app ``cargos``, logo depois de a 0017 de ``processos``
tirá-lo de lá.
"""

import uuid

import django.contrib.postgres.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Cria ``CargoProcesso`` no estado, sem SQL."""

    initial = True

    dependencies = [
        ("processos", "0017_move_modelos_para_apps"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="CargoProcesso",
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
                            "cargo_nome",
                            models.CharField(
                                max_length=200, verbose_name="Nome do Cargo"
                            ),
                        ),
                        (
                            "cargo_uuid",
                            models.UUIDField(verbose_name="UUID do Cargo"),
                        ),
                        (
                            "cargo_codigo",
                            models.CharField(
                                default="",
                                max_length=20,
                                verbose_name="Código do Cargo",
                            ),
                        ),
                        (
                            "vagas",
                            models.IntegerField(
                                default=0,
                                help_text=(
                                    "Total de vagas disponíveis para este"
                                    " cargo no processo"
                                ),
                                verbose_name="Quantidade de Vagas",
                            ),
                        ),
                        (
                            "candidatos_geral",
                            models.IntegerField(
                                default=0,
                                help_text=(
                                    "Quantidade de candidatos habilitados"
                                    " geral"
                                ),
                                verbose_name="Candidatos Gerais",
                            ),
                        ),
                        (
                            "candidatos_pcd",
                            models.IntegerField(
                                default=0,
                                help_text=(
                                    "Quantidade de candidatos habilitados"
                                    " pessoas             com deficiência"
                                ),
                                verbose_name="Candidatos PCD",
                            ),
                        ),
                        (
                            "candidatos_nna",
                            models.IntegerField(
                                default=0,
                                help_text=(
                                    "Quantidade de candidatos habilitados"
                                    " nna"
                                ),
                                verbose_name="Candidatos NNA",
                            ),
                        ),
                        (
                            "total_candidatos",
                            models.IntegerField(
                                default=0,
                                help_text=(
                                    "Total de candidatos classificados para"
                                    " este cargo"
                                ),
                                verbose_name="Total de Candidatos",
                            ),
                        ),
                        (
                            "candidatos_uuids",
                            django.contrib.postgres.fields.ArrayField(
                                base_field=models.UUIDField(),
                                blank=True,
                                default=list,
                                size=None,
                                verbose_name="UUIDs de Candidatos",
                            ),
                        ),
                        (
                            "processo",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="cargos_processo",
                                to="processos.processoconvocacao",
                                verbose_name="Processo de Convocação",
                            ),
                        ),
                    ],
                    options={
                        "verbose_name": "Cargo do Processo",
                        "verbose_name_plural": "Cargos do Processo",
                        "db_table": "processos_cargos",
                        "ordering": ["cargo_nome"],
                        "unique_together": {("processo", "cargo_nome")},
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
