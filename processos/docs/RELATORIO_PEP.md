# Relatório de conformidade PEP — app `processos`

Gerado em: **2026-05-18 16:19:23 UTC**  
Comando: `python manage.py gerar_relatorio_pep`  
Commit: `6560d9a`  
Escopo: código de aplicação (sem `tests/` e `migrations/`)  
Limite de linha (PEP 8): **79** caracteres

## Resumo executivo

| Métrica | Valor | % |
| --- | ---: | ---: |
| Arquivos analisados | 31 | — |
| Linhas de código (LOC) | 2311 | — |
| Linhas com mais de 79 caracteres | 150 | 6.5% |
| Funções/métodos | 46 | — |
| Funções/métodos com docstring (PEP 257) | 22 | 47.8% |
| Funções/métodos sem docstring | 24 | 52.2% |
| Classes | 42 | — |
| Classes com docstring | 33 | 78.6% |
| Módulos com docstring no topo | 12 | 38.7% |
| Type hints completos (PEP 484) | 13 | 28.3% |
| Type hints parciais | 1 | 2.2% |
| Sem type hints | 32 | 69.6% |
| Violações flake8 (PEP 8) | 311 | — |

## PEP 8 — Style Guide

- **Linhas acima de 79 chars** (código/comentários, exceto linha vazia): **150**
- **Total flake8** (views, services, models, tasks, etc.): **311**

### Top códigos flake8

| Código | Ocorrências |
| --- | ---: |
| `E501` | 211 |
| `W293` | 42 |
| `W291` | 13 |
| `F401` | 11 |
| `W292` | 8 |
| `F541` | 7 |
| `E122` | 6 |
| `E302` | 3 |
| `W391` | 2 |
| `F403` | 1 |

<details><summary>Primeiras 30 linhas flake8</summary>

```
processos/admin.py:5:1: F401 'auditlog.admin.LogEntryAdmin' imported but unused
processos/admin.py:6:1: F401 'auditlog.models.LogEntry' imported but unused
processos/admin.py:25:1: W293 blank line contains whitespace
processos/admin.py:27:64: W291 trailing whitespace
processos/admin.py:28:47: W291 trailing whitespace
processos/admin.py:30:80: E501 line too long (83 > 79 characters)
processos/admin.py:35:1: W293 blank line contains whitespace
processos/admin.py:51:1: W293 blank line contains whitespace
processos/admin.py:54:80: E501 line too long (80 > 79 characters)
processos/admin.py:60:1: W293 blank line contains whitespace
processos/admin.py:68:1: W293 blank line contains whitespace
processos/admin.py:78:1: W293 blank line contains whitespace
processos/admin.py:96:80: E501 line too long (99 > 79 characters)
processos/admin.py:109:80: E501 line too long (83 > 79 characters)
processos/apps.py:12:17: W292 no newline at end of file
processos/management/commands/__init__.py:1:33: W291 trailing whitespace
processos/management/commands/__init__.py:1:34: W292 no newline at end of file
processos/management/commands/criar_processos.py:7:80: E501 line too long (84 > 79 characters)
processos/management/commands/criar_processos.py:13:80: E501 line too long (82 > 79 characters)
processos/management/commands/criar_processos.py:32:1: W293 blank line contains whitespace
processos/management/commands/criar_processos.py:34:80: E501 line too long (101 > 79 characters)
processos/management/commands/criar_processos.py:36:1: W293 blank line contains whitespace
processos/management/commands/criar_processos.py:39:80: E501 line too long (92 > 79 characters)
processos/management/commands/criar_processos.py:40:80: E501 line too long (83 > 79 characters)
processos/management/commands/criar_processos.py:41:80: E501 line too long (89 > 79 characters)
processos/management/commands/criar_processos.py:42:80: E501 line too long (86 > 79 characters)
processos/management/commands/criar_processos.py:43:80: E501 line too long (88 > 79 characters)
processos/management/commands/criar_processos.py:44:80: E501 line too long (81 > 79 characters)
processos/management/commands/criar_processos.py:45:80: E501 line too long (85 > 79 characters)
processos/management/commands/criar_processos.py:46:80: E501 line too long (82 > 79 characters)
```
</details>

## PEP 257 — Docstring Conventions

- Funções/métodos **com** docstring: **22**
- Funções/métodos **sem** docstring: **24**
- Classes **com** docstring: **33** / 42
- Módulos **sem** docstring no topo: **19**

### Principais símbolos sem docstring

| Arquivo | Linha | Símbolo | Tipo |
| --- | ---: | --- | --- |
| `apps.py` | 4 | `ProcessosConfig` | class |
| `apps.py` | 8 | `ProcessosConfig.ready` | function |
| `management/commands/criar_processos.py` | 12 | `Command` | class |
| `management/commands/criar_processos.py` | 15 | `Command.add_arguments` | function |
| `management/commands/criar_processos.py` | 29 | `Command.handle` | function |
| `management/commands/limpar_processos.py` | 9 | `Command` | class |
| `management/commands/limpar_processos.py` | 12 | `Command.handle` | function |
| `models/cargo_processo.py` | 60 | `CargoProcesso.__str__` | function |
| `models/carta_convocacao_candidato.py` | 50 | `CartaConvocacaoCandidato.__str__` | function |
| `models/carta_convocacao_historico.py` | 24 | `CartaConvocacaoHistorico.__str__` | function |
| `models/processo_convocacao.py` | 54 | `ProcessoConvocacao.__str__` | function |
| `models/processo_convocacao.py` | 57 | `ProcessoConvocacao.pode_deletar` | function |
| `models/processo_convocacao.py` | 60 | `ProcessoConvocacao.inativar` | function |
| `serializers.py` | 111 | `ProcessoConvocacaoListSerializer.get_quantidade_cargos` | function |
| `serializers.py` | 114 | `ProcessoConvocacaoListSerializer.get_pode_deletar` | function |
| `services/agenda_api_service.py` | 14 | `AgendaApiService` | class |
| `services/candidatos_api_url.py` | 18 | `CandidatosApiService` | class |
| `services/candidatos_api_url.py` | 28 | `CandidatosApiService._candidatos_api_url` | function |
| `services/cargos_service.py` | 13 | `SubstituirCargosResult` | class |
| `services/cargos_service.py` | 21 | `CargosProcessoService` | class |
| `services/cargos_service.py` | 23 | `CargosProcessoService.salvar_cargos` | function |
| `services/escolhas_service.py` | 17 | `EscolhasApiService` | class |
| `services/processo_service.py` | 28 | `ProcessoConvocacaoService.__init__` | function |
| `utils.py` | 8 | `CustomPagination` | class |
| `utils.py` | 13 | `CustomPagination.get_paginated_response` | function |

## PEP 484 — Type Hints

- **Completo** (args + return): **13** (28.3%)
- **Parcial**: **1** (2.2%)
- **Sem anotações**: **32** (69.6%)

## PEP 440 — Dependências do microsserviço

_Aplica-se a `requirements/`, não ao código do app._

- Arquivos: base.txt, local.txt, production.txt
- Linhas de dependência: **25**
- PyPI válidas (packaging): **24**
- Pins `git+...`: **1**
- Com especificador `==`: **24**
- Linhas inválidas: **0**

## Métricas por arquivo

| Arquivo | LOC | Linhas >79 | Funções | Docstring % | Hints completos % |
| --- | ---: | ---: | ---: | ---: | ---: |
| `__init__.py` | 1 | 0 | 0 | — | — |
| `admin.py` | 115 | 4 | 2 | 100.0% | 0.0% |
| `apps.py` | 12 | 0 | 1 | 0.0% | 0.0% |
| `management/__init__.py` | 1 | 0 | 0 | — | — |
| `management/commands/__init__.py` | 1 | 0 | 0 | — | — |
| `management/commands/criar_processos.py` | 210 | 29 | 2 | 0.0% | 0.0% |
| `management/commands/limpar_processos.py` | 63 | 4 | 1 | 0.0% | 0.0% |
| `models/__init__.py` | 22 | 0 | 0 | — | — |
| `models/base.py` | 17 | 3 | 0 | — | — |
| `models/cargo_processo.py` | 64 | 3 | 1 | 0.0% | 0.0% |
| `models/carta_convocacao_candidato.py` | 54 | 0 | 1 | 0.0% | 0.0% |
| `models/carta_convocacao_historico.py` | 28 | 2 | 1 | 0.0% | 0.0% |
| `models/constants.py` | 36 | 1 | 0 | — | — |
| `models/processo_convocacao.py` | 66 | 5 | 3 | 0.0% | 0.0% |
| `serializers.py` | 190 | 20 | 4 | 50.0% | 0.0% |
| `services/__init__.py` | 12 | 0 | 0 | — | — |
| `services/agenda_api_service.py` | 61 | 2 | 1 | 100.0% | 100.0% |
| `services/candidatos_api_url.py` | 155 | 10 | 4 | 75.0% | 100.0% |
| `services/cargos_service.py` | 85 | 8 | 1 | 0.0% | 100.0% |
| `services/carta_convocacao_service.py` | 191 | 6 | 2 | 100.0% | 100.0% |
| `services/escolhas_service.py` | 162 | 11 | 3 | 100.0% | 100.0% |
| `services/exceptions.py` | 15 | 0 | 0 | — | — |
| `services/processo_service.py` | 87 | 2 | 2 | 50.0% | 50.0% |
| `tasks/__init__.py` | 4 | 0 | 0 | — | — |
| `tasks/enviar_email_task.py` | 93 | 11 | 1 | 100.0% | 100.0% |
| `urls.py` | 17 | 2 | 0 | — | — |
| `utils.py` | 23 | 1 | 1 | 0.0% | 0.0% |
| `views/__init__.py` | 4 | 0 | 0 | — | — |
| `views/cargos.py` | 134 | 6 | 4 | 0.0% | 0.0% |
| `views/carta_convocacao.py` | 86 | 7 | 2 | 0.0% | 0.0% |
| `views/processos.py` | 302 | 13 | 9 | 77.8% | 0.0% |

## Recomendações

1. Priorizar docstrings em `views/` e `services/` nos endpoints públicos.
2. Reduzir linhas >79 ou quebrar strings/imports longos (E501).
3. Estender type hints nos services que ainda estão em nível `sem` ou `parcial`.
4. Rodar `flake8` e `black` no CI com `max-line-length=79`.
5. Manter pins PEP 440 explícitos em `requirements/base.txt`.

---

*Relatório gerado por `python manage.py gerar_relatorio_pep`*
