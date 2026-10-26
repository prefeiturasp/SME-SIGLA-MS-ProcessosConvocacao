"""Leva o histórico do auditlog para o ContentType do app atual.

Depois da 0017 de ``processos`` e das ``0001_initial`` de ``cargos`` e
``envio_email``, ``CargoProcesso`` e os modelos de e-mail pertencem aos
apps atuais, e o auditlog busca o histórico pelos ContentTypes
``(cargos, cargoprocesso)`` e ``(envio_email, ...)``. As entradas
gravadas quando os modelos ainda eram de ``processos`` ficaram nos
ContentTypes ``(processos, ...)``: não aparecem no histórico e um
``remove_stale_contenttypes`` as apagaria em cascata. Esta migration
passa essas entradas para o ContentType do app atual.

Os ContentTypes antigos não são apagados. O reverse é ``noop`` de
propósito: o código usa os labels novos tanto antes quanto depois desta
migration, então devolver as entradas ao ContentType antigo só voltaria
a escondê-las.
"""

from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps

APP_ANTIGO = "processos"
APP_ATUAL_POR_MODELO = {
    "cargoprocesso": "cargos",
    "envioemail": "envio_email",
    "envioemailcandidato": "envio_email",
    "envioemailconteudo": "envio_email",
}


def consolidar_historico(
    apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
) -> None:
    """Passa as ``LogEntry`` dos modelos movidos para o ContentType atual.

    Para cada modelo movido, garante o ContentType do app atual e, se o
    ContentType ``(processos, <modelo>)`` existir, move todas as entradas
    dele num único ``UPDATE``.

    Args:
        apps: Registro dos modelos históricos.
        schema_editor: Editor de schema da migration, usado para saber em
            qual banco gravar.
    """
    banco = schema_editor.connection.alias
    ContentType = apps.get_model("contenttypes", "ContentType")
    LogEntry = apps.get_model("auditlog", "LogEntry")
    for modelo, app_atual in APP_ATUAL_POR_MODELO.items():
        tipo_atual, _ = ContentType.objects.using(banco).get_or_create(
            app_label=app_atual, model=modelo
        )
        tipo_antigo = (
            ContentType.objects.using(banco)
            .filter(app_label=APP_ANTIGO, model=modelo)
            .first()
        )
        if tipo_antigo is not None:
            LogEntry.objects.using(banco).filter(
                content_type=tipo_antigo
            ).update(content_type=tipo_atual)


class Migration(migrations.Migration):
    """Consolida o histórico do auditlog no ContentType do app atual."""

    dependencies = [
        ("processos", "0017_move_modelos_para_apps"),
        ("cargos", "0001_initial"),
        ("envio_email", "0001_initial"),
        ("auditlog", "0017_add_actor_email"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(consolidar_historico, migrations.RunPython.noop),
    ]
