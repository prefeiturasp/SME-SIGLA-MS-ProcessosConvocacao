"""Adiciona o tipo de escolha MANDADO_JUDICIAL."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("processos", "0015_popular_assunto_envio_email_conteudo"),
    ]

    operations = [
        migrations.AlterField(
            model_name="processoconvocacao",
            name="tipo_escolha",
            field=models.CharField(
                choices=[
                    ("NOVA_AUTORIZACAO", "Nova Autorização"),
                    ("REPOSICAO", "Reposição"),
                    ("RECONVOCAO", "Reconvocação"),
                    ("MANDADO_JUDICIAL", "Mandado Judicial"),
                ],
                default="NOVA_AUTORIZACAO",
                max_length=20,
                verbose_name="Tipo de Escolha",
            ),
        ),
    ]
