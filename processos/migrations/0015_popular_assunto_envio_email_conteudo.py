# Generated manually

from django.db import migrations


ASSUNTO_POR_TIPO = {
    "CONVOCACAO": "Ciência de Convocação de Escolha de Vaga - PMSP",
    "VAGAS": "Comunicado de Vagas - PMSP",
    "RESULTADOS": "Comunicado de Resultados - PMSP",
}


def popular_assuntos(apps, schema_editor):
    EnvioEmailConteudo = apps.get_model("processos", "EnvioEmailConteudo")
    for registro in EnvioEmailConteudo.objects.all():
        assunto = ASSUNTO_POR_TIPO.get(registro.tipo, "")
        if assunto and not registro.assunto:
            EnvioEmailConteudo.objects.filter(pk=registro.pk).update(assunto=assunto)


def reverter_assuntos(apps, schema_editor):
    EnvioEmailConteudo = apps.get_model("processos", "EnvioEmailConteudo")
    for tipo, assunto in ASSUNTO_POR_TIPO.items():
        EnvioEmailConteudo.objects.filter(tipo=tipo, assunto=assunto).update(assunto="")


class Migration(migrations.Migration):
    dependencies = [
        ("processos", "0014_envioemailconteudo_assunto_and_more"),
    ]

    operations = [
        migrations.RunPython(popular_assuntos, reverter_assuntos),
    ]
