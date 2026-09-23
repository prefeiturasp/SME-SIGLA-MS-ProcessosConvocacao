"""Monta o histórico de candidatos por processos de convocação."""

from __future__ import annotations

import logging
from typing import Any

from processos.repository import ProcessoConvocacaoRepository
from processos.services.candidatos_api_url import CandidatosApiService
from processos.services.escolhas_service import EscolhasApiService
from sigla_sdk.context import get_correlation_id

logger = logging.getLogger(__name__)

CATEGORIAS = ["GERAL", "NNA", "PCD"]
SITUACOES = ["escolha", "nao-escolha", "reconvocacao"]


class HistoricoCandidatosService:
    """Cruza habilitados (MS-Candidatos) com escolhas (MS-Escolhas)."""

    def __init__(
        self,
        *,
        candidatos_api: CandidatosApiService | None = None,
        escolhas_api: EscolhasApiService | None = None,
    ) -> None:
        """Inicializa dependências dos microsserviços."""
        self.candidatos_api = candidatos_api or CandidatosApiService()
        self.escolhas_api = escolhas_api or EscolhasApiService()

    @staticmethod
    def _bloco_contagem_vazio() -> dict[str, int]:
        return {"total": 0, "geral": 0, "nna": 0, "pcd": 0}

    @classmethod
    def _montar_contagem_candidatos(
        cls, por_categoria: dict[str, Any] | None
    ) -> dict[str, int]:
        dados = por_categoria or {}
        geral = int((dados.get("GERAL") or {}).get("total") or 0)
        nna = int((dados.get("NNA") or {}).get("total") or 0)
        pcd = int((dados.get("PCD") or {}).get("total") or 0)
        return {
            "total": geral + nna + pcd,
            "geral": geral,
            "nna": nna,
            "pcd": pcd,
        }

    @classmethod
    def _cruzar_situacao(
        cls,
        escolhas_por_situacao: dict[str, Any],
        habilitados: dict[str, Any],
    ) -> dict[str, int]:
        uuids_escolha = {
            str(uid)
            for uid in (escolhas_por_situacao.get("candidatos_uuids") or [])
        }

        def _intersect(categoria: str) -> int:
            uuids_cat = {
                str(uid)
                for uid in (habilitados.get(categoria) or {}).get(
                    "candidatos_uuids"
                )
                or []
            }
            return len(uuids_escolha & uuids_cat)

        geral = _intersect("GERAL")
        nna = _intersect("NNA")
        pcd = _intersect("PCD")
        return {
            "total": geral + nna + pcd,
            "geral": geral,
            "nna": nna,
            "pcd": pcd,
        }

    def historico_candidatos_por_processos(
        self, processos_uuids: list[str]
    ) -> list[dict[str, Any]]:
        """Monta o histórico cruzando candidatos e escolhas.

        Args:
            processo_uuids: Lista de UUIDs de processos.

        Returns:
            Lista de itens com totais por categoria e situação.
        """
        processos = ProcessoConvocacaoRepository.buscar_por_uuids(
            processos_uuids
        )
        if not processos:
            return []

        uuids_encontrados = [str(p.uuid) for p in processos]
        logger.info(
            "Montando histórico de candidatos por convocação",
            extra={
                "correlation_id": get_correlation_id(),
                "processo_uuids": uuids_encontrados,
            },
        )

        habilitados_por_processo = (
            self.candidatos_api.buscar_habilitados_por_processos_e_tipo_vaga(
                uuids_encontrados
            )
        )
        escolhas_por_processo = (
            self.escolhas_api.buscar_escolhas_por_convocacao(uuids_encontrados)
        )
        resultado: list[dict[str, Any]] = []
        for processo in processos:
            processo_key = str(processo.uuid)
            habilitados = habilitados_por_processo.get(processo_key) or {}
            escolhas = escolhas_por_processo.get(processo_key) or {}
            item: dict[str, Any] = {
                "descricao": processo.descricao,
                "data_convocacao": (
                    processo.data_convocacao.isoformat()
                    if processo.data_convocacao
                    else None
                ),
                "candidatos": self._montar_contagem_candidatos(habilitados),
            }
            for situacao in SITUACOES:
                escolhas_por_situacao = escolhas.get(situacao) or {}
                item[situacao] = self._cruzar_situacao(
                    escolhas_por_situacao, habilitados or {}
                )

            resultado.append(item)

        return resultado
