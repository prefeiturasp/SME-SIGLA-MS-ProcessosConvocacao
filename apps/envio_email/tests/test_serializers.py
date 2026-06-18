"""Testes unitários para os serializers do app envio_email."""

import uuid

import pytest

from envio_email.models import EnvioEmail, EnvioEmailCandidato
from envio_email.models.envio_email import TIPO_CONVOCACAO
from envio_email.models.envio_email_candidato import (
    ENVIO_STATUS_ERRO,
    ENVIO_STATUS_SUCESSO,
)
from envio_email.serializers import (
    EnvioEmailCandidatoSerializer,
    EnvioEmailDetalheSerializer,
    EnvioEmailEnvioSerializer,
    EnvioEmailSerializer,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def envio_email(processo_convocacao):
    """Fixture para EnvioEmail."""
    return EnvioEmail.objects.create(
        processo_uuid=processo_convocacao.uuid,
        processo_nome=processo_convocacao.concurso_nome,
        tipo=TIPO_CONVOCACAO,
        quantidade_candidatos=2,
    )


@pytest.fixture
def envio_email_candidatos(envio_email):
    """Fixture para EnvioEmailCandidato vinculados ao envio."""
    EnvioEmailCandidato.objects.create(
        envio_email=envio_email,
        nome="Fulano",
        rf="1234567",
        email="fulano@test.com",
        status=ENVIO_STATUS_SUCESSO,
        conteudo="<p>Conteúdo email 1</p>",
    )
    EnvioEmailCandidato.objects.create(
        envio_email=envio_email,
        nome="Ciclano",
        rf="7654321",
        email="ciclano@test.com",
        status=ENVIO_STATUS_ERRO,
        conteudo="<p>Conteúdo email 2</p>",
    )
    return list(envio_email.candidatos.all())


def test_envio_email_serializer_campos(envio_email):
    """Testa os campos do EnvioEmailSerializer."""
    serializer = EnvioEmailSerializer(envio_email)
    dados = serializer.data
    assert dados["uuid"] == str(envio_email.uuid)
    assert dados["processo_nome"] == envio_email.processo_nome
    assert dados["processo_uuid"] == str(envio_email.processo_uuid)
    assert dados["tipo"] == TIPO_CONVOCACAO
    assert "criado_em" in dados
    assert dados["quantidade_candidatos"] == envio_email.quantidade_candidatos


def test_envio_email_candidato_serializer_campos(envio_email_candidatos):
    """Testa os campos do EnvioEmailCandidatoSerializer."""
    destinatario = envio_email_candidatos[0]
    serializer = EnvioEmailCandidatoSerializer(destinatario)
    dados = serializer.data
    assert dados["nome"] == destinatario.nome
    assert dados["rf"] == destinatario.rf
    assert dados["email"] == destinatario.email
    assert dados["status"] == destinatario.status
    assert dados["conteudo"] == destinatario.conteudo


def test_envio_email_detalhe_serializer_campos(
    envio_email, envio_email_candidatos
):
    """Testa os campos do EnvioEmailDetalheSerializer incluindo candidatos."""
    serializer = EnvioEmailDetalheSerializer(envio_email)
    dados = serializer.data
    assert dados["uuid"] == str(envio_email.uuid)
    assert dados["processo_nome"] == envio_email.processo_nome
    assert dados["quantidade_candidatos"] == envio_email.quantidade_candidatos
    assert "candidatos" in dados
    assert len(dados["candidatos"]) == 2
    nomes = [c["nome"] for c in dados["candidatos"]]
    assert "Fulano" in nomes
    assert "Ciclano" in nomes


def test_envio_email_envio_serializer_valido(processo_convocacao):
    """Testa EnvioEmailEnvioSerializer com dados válidos."""
    dados = {
        "processo_uuid": str(processo_convocacao.uuid),
        "processo_nome": "Processo Teste",
        "tipo": TIPO_CONVOCACAO,
        "conteudo": "<p>Conteúdo</p>",
    }
    serializer = EnvioEmailEnvioSerializer(data=dados)
    assert serializer.is_valid()
    assert serializer.validated_data["processo_nome"] == "Processo Teste"
    assert (
        serializer.validated_data["processo_uuid"] == processo_convocacao.uuid
    )


def test_envio_email_envio_serializer_aceita_assunto_e_conteudo_opcionais(
    processo_convocacao,
):
    """Testa corpo de envio com assunto e conteúdo em branco."""
    dados = {
        "processo_uuid": str(processo_convocacao.uuid),
        "processo_nome": "Processo Teste",
        "tipo": TIPO_CONVOCACAO,
        "conteudo": "",
        "assunto": "",
    }
    serializer = EnvioEmailEnvioSerializer(data=dados)
    assert serializer.is_valid()
    assert serializer.validated_data["conteudo"] == ""
    assert serializer.validated_data["assunto"] == ""


def test_envio_email_envio_serializer_aceita_assunto_personalizado(
    processo_convocacao,
):
    """Testa corpo de envio com assunto personalizado."""
    dados = {
        "processo_uuid": str(processo_convocacao.uuid),
        "processo_nome": "Processo Teste",
        "tipo": TIPO_CONVOCACAO,
        "conteudo": "<p>Conteúdo</p>",
        "assunto": "Meu assunto",
    }
    serializer = EnvioEmailEnvioSerializer(data=dados)
    assert serializer.is_valid()
    assert serializer.validated_data["assunto"] == "Meu assunto"


def test_envio_email_envio_serializer_processo_nao_encontrado():
    """Testa EnvioEmailEnvioSerializer quando processo não existe."""
    dados = {
        "processo_uuid": str(uuid.uuid4()),
        "processo_nome": "Processo Inexistente",
        "tipo": TIPO_CONVOCACAO,
        "conteudo": "<p>Conteúdo</p>",
    }
    serializer = EnvioEmailEnvioSerializer(data=dados)
    assert not serializer.is_valid()
    assert "processo_uuid" in serializer.errors
