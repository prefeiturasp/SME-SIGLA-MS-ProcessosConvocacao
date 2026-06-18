# Generated manually

import uuid
from pathlib import Path

from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


CORPO_POR_TIPO = {
    'CONVOCACAO': 'email_convocacao_padrao.html',
    'VAGAS': 'email_vagas_padrao.html',
    'RESULTADOS': 'email_resultados_padrao.html',
}


def _ler_corpo_template(nome_arquivo: str) -> str:
    path = Path(settings.BASE_DIR) / 'templates' / 'email' / nome_arquivo
    return path.read_text(encoding='utf-8')


def criar_conteudos_iniciais(apps, schema_editor):
    EnvioEmailConteudo = apps.get_model('processos', 'EnvioEmailConteudo')
    agora = timezone.now()
    for tipo, arquivo in CORPO_POR_TIPO.items():
        EnvioEmailConteudo.objects.create(
            uuid=uuid.uuid4(),
            tipo=tipo,
            conteudo=_ler_corpo_template(arquivo),
            criado_em=agora,
            atualizado_em=agora,
        )


def remover_conteudos_iniciais(apps, schema_editor):
    EnvioEmailConteudo = apps.get_model('processos', 'EnvioEmailConteudo')
    EnvioEmailConteudo.objects.filter(
        tipo__in=['CONVOCACAO', 'VAGAS', 'RESULTADOS'],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('processos', '0012_envioemail_envioemailcandidato_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='EnvioEmailConteudo',
            fields=[
                (
                    'uuid',
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    'criado_em',
                    models.DateTimeField(auto_now_add=True, verbose_name='Criado em'),
                ),
                (
                    'atualizado_em',
                    models.DateTimeField(auto_now=True, verbose_name='Atualizado em'),
                ),
                (
                    'tipo',
                    models.CharField(
                        choices=[
                            ('CONVOCACAO', 'Convocação'),
                            ('VAGAS', 'Vagas'),
                            ('RESULTADOS', 'Resultados'),
                        ],
                        max_length=20,
                        unique=True,
                        verbose_name='Tipo de envio',
                    ),
                ),
                (
                    'conteudo',
                    models.TextField(
                        help_text=(
                            'Fragmento HTML do corpo com variáveis Django '
                            '(ex.: {{ cargo }}, {{ data_publicacao }})'
                        ),
                        verbose_name='Corpo do e-mail (HTML)',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Conteúdo de e-mail por tipo',
                'verbose_name_plural': 'Conteúdos de e-mail por tipo',
                'db_table': 'processos_envio_email_conteudo',
                'ordering': ['tipo'],
            },
        ),
        migrations.RunPython(criar_conteudos_iniciais, remover_conteudos_iniciais),
    ]
