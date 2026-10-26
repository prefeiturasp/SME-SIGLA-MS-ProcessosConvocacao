"""Testes dos repositórios do app envio_email."""

from uuid import uuid4

import pytest
from envio_email.models import EnvioEmail, EnvioEmailCandidato
from envio_email.models.envio_email import TIPO_CONVOCACAO
from envio_email.repository import EnvioEmailCandidatoRepository

pytestmark = pytest.mark.django_db


def test_criar_candidato_do_envio_pelo_id():
    """O candidato é vinculado ao envio resolvido pelo id."""
    envio = EnvioEmail.objects.create(
        processo_uuid=uuid4(),
        processo_nome="Processo",
        tipo=TIPO_CONVOCACAO,
        quantidade_candidatos=1,
    )

    dados = EnvioEmailCandidatoRepository.criar(
        envio_email_id=envio.id,
        nome="Fulano",
        rf="1234567",
        email="fulano@test.com",
        conteudo="<p>Olá</p>",
    )

    candidato = EnvioEmailCandidato.objects.get(uuid=dados["uuid"])
    assert candidato.envio_email_id == envio.id
