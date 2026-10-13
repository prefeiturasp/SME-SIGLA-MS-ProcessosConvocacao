"""Serializers do app processos."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from cargos.repository import CargoProcessoRepository
from cargos.serializers import CargoProcessoSerializer
from processos.models import ProcessoConvocacao
from rest_framework import serializers

DESCRICOES_CAMPOS = {
    "uuid": {"help_text": "Identificador único do processo de convocação."},
    "concurso_uuid": {
        "help_text": (
            "UUID do concurso (MS-Concursos) ao qual o processo pertence."
        )
    },
    "concurso_nome": {
        "help_text": (
            "Nome do concurso, guardado no processo para exibição e busca."
        )
    },
    "descricao": {
        "help_text": "Descrição que identifica o processo de convocação."
    },
    "tipo_escolha": {
        "help_text": (
            "Tipo de escolha da convocação. Na criação, o padrão é "
            "`NOVA_AUTORIZACAO`."
        )
    },
    "status": {
        "help_text": (
            "Situação do processo no ciclo de vida. Na criação, o padrão é "
            "`PENDENTE`."
        )
    },
    "data_convocacao": {
        "help_text": (
            "Data e hora da convocação. Na criação, o padrão é o momento "
            "atual."
        )
    },
    "data_corte_vagas": {
        "help_text": (
            "Data e hora de corte das vagas consideradas no processo. Na "
            "criação, o padrão é o momento atual."
        )
    },
    "passo": {
        "help_text": (
            "Etapa do fluxo de criação da convocação em que o processo "
            "está, de 1 a 4. Na criação, o padrão é 1."
        )
    },
    "criado_em": {"help_text": "Data e hora de criação do registro."},
    "atualizado_em": {
        "help_text": "Data e hora da última atualização do registro."
    },
}


class ProcessoConvocacaoSerializer(serializers.ModelSerializer):
    """Processo de convocação com os cargos vinculados."""

    cargos_processo = CargoProcessoSerializer(
        many=True,
        read_only=True,
        help_text="Cargos vinculados ao processo.",
    )

    class Meta:
        model = ProcessoConvocacao
        fields = [
            "uuid",
            "concurso_uuid",
            "concurso_nome",
            "descricao",
            "tipo_escolha",
            "status",
            "data_convocacao",
            "data_corte_vagas",
            "passo",
            "cargos_processo",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["uuid", "criado_em", "atualizado_em"]
        extra_kwargs = DESCRICOES_CAMPOS


class ProcessoConvocacaoCreateSerializer(serializers.ModelSerializer):
    """Dados para criar um processo de convocação."""

    class Meta:
        model = ProcessoConvocacao
        fields = [
            "uuid",
            "concurso_uuid",
            "concurso_nome",
            "descricao",
            "tipo_escolha",
            "status",
            "data_convocacao",
            "data_corte_vagas",
            "passo",
        ]
        read_only_fields = ["uuid"]
        extra_kwargs = DESCRICOES_CAMPOS

    def validate_concurso_uuid(self, value: UUID | str) -> UUID | str:
        try:
            UUID(str(value))
            return value
        except ValueError:
            raise serializers.ValidationError(
                "UUID do concurso inválido."
            ) from None


class ProcessoConvocacaoListSerializer(serializers.ModelSerializer):
    """Processo de convocação resumido, como aparece na listagem."""

    quantidade_cargos = serializers.SerializerMethodField(
        help_text="Quantidade de cargos vinculados ao processo."
    )
    pode_deletar = serializers.SerializerMethodField(
        help_text=(
            "Indica se o processo pode ser excluído: verdadeiro quando não "
            "está em andamento nem finalizado."
        )
    )

    class Meta:
        model = ProcessoConvocacao
        fields = [
            "uuid",
            "concurso_nome",
            "concurso_uuid",
            "descricao",
            "tipo_escolha",
            "status",
            "passo",
            "data_convocacao",
            "data_corte_vagas",
            "quantidade_cargos",
            "pode_deletar",
            "criado_em",
        ]
        extra_kwargs = DESCRICOES_CAMPOS

    def get_quantidade_cargos(self, obj: ProcessoConvocacao) -> int:
        return CargoProcessoRepository.contar_por_processo(obj)

    def get_pode_deletar(self, obj: ProcessoConvocacao) -> bool:
        return bool(obj.pode_deletar())


class ProcessoConvocacaoUpdateSerializer(serializers.ModelSerializer):
    """Dados editáveis de um processo de convocação."""

    class Meta:
        model = ProcessoConvocacao
        fields = [
            "concurso_nome",
            "concurso_uuid",
            "descricao",
            "tipo_escolha",
            "status",
            "data_convocacao",
            "data_corte_vagas",
        ]
        extra_kwargs = DESCRICOES_CAMPOS


class ProcessoConvocacaoPassoSerializer(serializers.ModelSerializer):
    """Etapa do fluxo de criação em que o processo está."""

    class Meta:
        model = ProcessoConvocacao
        fields = ["passo"]
        extra_kwargs = DESCRICOES_CAMPOS


class ProcessoConvocacaoSelectSerializer(serializers.ModelSerializer):
    """Processo de convocação como opção de um campo de seleção."""

    value = serializers.UUIDField(
        source="uuid", help_text="UUID do processo de convocação."
    )
    label = serializers.CharField(
        source="descricao",
        help_text="Descrição do processo, para exibição na lista.",
    )

    class Meta:
        model = ProcessoConvocacao
        fields = ["value", "label", "concurso_uuid", "status"]
        extra_kwargs = DESCRICOES_CAMPOS


class LinksPaginacaoSerializer(serializers.Serializer):
    """Links de navegação entre as páginas da listagem."""

    next = serializers.URLField(
        allow_null=True,
        help_text="URL da próxima página, ou nulo na última página.",
    )
    previous = serializers.URLField(
        allow_null=True,
        help_text="URL da página anterior, ou nulo na primeira página.",
    )


class ProcessoConvocacaoPaginadoSerializer(serializers.Serializer):
    """Página da listagem de processos de convocação."""

    links = LinksPaginacaoSerializer(
        help_text="Links para as páginas vizinhas."
    )
    count = serializers.IntegerField(
        help_text="Total de processos que atendem aos filtros."
    )
    page = serializers.IntegerField(help_text="Número da página retornada.")
    page_size = serializers.IntegerField(
        help_text="Quantidade de processos por página aplicada."
    )
    results = ProcessoConvocacaoListSerializer(
        many=True, help_text="Processos da página."
    )


class OpcaoFiltroSerializer(serializers.Serializer):
    """Opção de um filtro: valor a enviar e texto a exibir."""

    value = serializers.CharField(
        help_text="Valor a enviar no filtro: UUID ou código."
    )
    label = serializers.CharField(help_text="Texto para exibição.")


class FiltrosProcessosSerializer(serializers.Serializer):
    """Opções disponíveis para filtrar a listagem de processos."""

    concursos = OpcaoFiltroSerializer(
        many=True,
        help_text=(
            "Concursos que têm processo de convocação. `value` é o "
            "`concurso_uuid`."
        ),
    )
    cargos = OpcaoFiltroSerializer(
        many=True,
        help_text=(
            "Cargos vinculados a processos, sem repetição de nome. `value` "
            "é o `cargo_uuid`."
        ),
    )
    tipos_escolha = OpcaoFiltroSerializer(
        many=True,
        help_text="Tipos de escolha existentes. `value` é o código do tipo.",
    )


class HistoricoCandidatosRequisicaoSerializer(serializers.Serializer):
    """Processos cujo histórico de candidatos será montado."""

    processos_uuids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        help_text=("UUIDs dos processos de convocação. Informe ao menos um."),
    )


class ContagemCategoriasSerializer(serializers.Serializer):
    """Quantidade de candidatos, total e por categoria."""

    total = serializers.IntegerField(help_text="Soma das três categorias.")
    geral = serializers.IntegerField(help_text="Candidatos da lista geral.")
    nna = serializers.IntegerField(
        help_text=(
            "Candidatos da lista de negros, negras ou afrodescendentes "
            "(NNA)."
        )
    )
    pcd = serializers.IntegerField(
        help_text="Candidatos da lista de pessoas com deficiência (PCD)."
    )


class HistoricoCandidatosItemSerializer(serializers.Serializer):
    """Totais de candidatos de um processo, por situação e por categoria."""

    descricao = serializers.CharField(
        help_text="Descrição do processo de convocação."
    )
    data_convocacao = serializers.DateTimeField(
        allow_null=True, help_text="Data e hora da convocação."
    )
    candidatos = ContagemCategoriasSerializer(
        help_text="Habilitados convocados no processo."
    )
    escolha = ContagemCategoriasSerializer(
        help_text="Convocados com escolha de vaga registrada."
    )
    nao_escolha = ContagemCategoriasSerializer(
        help_text="Convocados com não escolha registrada."
    )
    reconvocacao = ContagemCategoriasSerializer(
        help_text="Convocados com reconvocação registrada."
    )

    def get_fields(self) -> dict[str, Any]:
        """Publica ``nao_escolha`` com a chave real da resposta."""
        return {
            "nao-escolha" if nome == "nao_escolha" else nome: campo
            for nome, campo in super().get_fields().items()
        }
