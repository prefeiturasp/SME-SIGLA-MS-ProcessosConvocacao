"""
Gera relatório de conformidade PEP 8, 257, 484 e 440 para o app processos.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from django.conf import settings
from django.core.management.base import BaseCommand

COMMAND_NAME = "gerar_relatorio_pep"
EXCLUDE_DIRS = {"tests", "migrations", "__pycache__"}
EXCLUDE_COMMAND_FILES = {"gerar_relatorio_pep.py"}
TOP_MISSING_DOCSTRINGS = 25


@dataclass
class SymbolMetrics:
    kind: str
    name: str
    lineno: int
    has_docstring: bool
    hint_level: str  # completo | parcial | sem


@dataclass
class FileMetrics:
    path: str
    loc: int = 0
    lines_over_max: int = 0
    lines_length_eligible: int = 0
    module_has_docstring: bool = False
    symbols: List[SymbolMetrics] = field(default_factory=list)

    @property
    def functions_and_methods(self) -> List[SymbolMetrics]:
        return [s for s in self.symbols if s.kind in ("function", "async_function")]

    @property
    def classes(self) -> List[SymbolMetrics]:
        return [s for s in self.symbols if s.kind == "class"]


def _repo_root() -> Path:
    return Path(settings.BASE_DIR)


def _processos_app_dir() -> Path:
    return _repo_root() / "processos"


def discover_app_python_files(app_dir: Path) -> List[Path]:
    files: List[Path] = []
    for path in sorted(app_dir.rglob("*.py")):
        parts = set(path.relative_to(app_dir).parts)
        if parts & EXCLUDE_DIRS:
            continue
        if path.name in EXCLUDE_COMMAND_FILES:
            continue
        files.append(path)
    return files


def _hint_level(node: ast.AST) -> str:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return "sem"
    args = [
        a
        for a in node.args.args
        if a.arg not in ("self", "cls")
    ]
    kwonly = list(node.args.kwonlyargs)
    posonly = list(getattr(node.args, "posonlyargs", []))
    all_args = posonly + args + kwonly

    has_return = node.returns is not None
    if not all_args:
        return "completo" if has_return else "sem"

    annotated_args = sum(1 for a in all_args if a.annotation is not None)
    if annotated_args == len(all_args) and has_return:
        return "completo"
    if annotated_args > 0 or has_return:
        return "parcial"
    return "sem"


def _walk_symbols(tree: ast.AST, filepath: Path) -> List[SymbolMetrics]:
    symbols: List[SymbolMetrics] = []

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            symbols.append(
                SymbolMetrics(
                    kind="function",
                    name=node.name,
                    lineno=node.lineno,
                    has_docstring=bool(ast.get_docstring(node)),
                    hint_level=_hint_level(node),
                )
            )
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            symbols.append(
                SymbolMetrics(
                    kind="async_function",
                    name=node.name,
                    lineno=node.lineno,
                    has_docstring=bool(ast.get_docstring(node)),
                    hint_level=_hint_level(node),
                )
            )
            self.generic_visit(node)

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            symbols.append(
                SymbolMetrics(
                    kind="class",
                    name=node.name,
                    lineno=node.lineno,
                    has_docstring=bool(ast.get_docstring(node)),
                    hint_level="sem",
                )
            )
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    kind = (
                        "function"
                        if isinstance(item, ast.FunctionDef)
                        else "async_function"
                    )
                    symbols.append(
                        SymbolMetrics(
                            kind=kind,
                            name=f"{node.name}.{item.name}",
                            lineno=item.lineno,
                            has_docstring=bool(ast.get_docstring(item)),
                            hint_level=_hint_level(item),
                        )
                    )

    Visitor().visit(tree)
    return symbols


def analyze_file(path: Path, app_dir: Path, max_line_length: int) -> FileMetrics:
    rel = str(path.relative_to(app_dir))
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    metrics = FileMetrics(path=rel, loc=len(lines))

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        metrics.lines_length_eligible += 1
        if len(line) > max_line_length:
            metrics.lines_over_max += 1

    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return metrics

    metrics.module_has_docstring = bool(ast.get_docstring(tree))
    metrics.symbols = _walk_symbols(tree, path)
    return metrics


def run_flake8(app_dir: Path, repo_root: Path) -> Tuple[Counter, List[str]]:
    paths = [
        "processos/views",
        "processos/services",
        "processos/models",
        "processos/tasks",
        "processos/management/commands",
        "processos/serializers.py",
        "processos/admin.py",
        "processos/utils.py",
        "processos/urls.py",
        "processos/apps.py",
    ]
    existing = [p for p in paths if (repo_root / p).exists()]
    if not existing:
        return Counter(), []

    cmd = [
        sys.executable,
        "-m",
        "flake8",
        "--max-line-length=79",
        "--extend-exclude=migrations,tests",
        *existing,
    ]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return Counter(), ["flake8 não disponível no ambiente"]

    codes: Counter = Counter()
    raw_lines: List[str] = []
    for line in result.stdout.splitlines():
        raw_lines.append(line)
        msg = line.rsplit(":", 1)[-1].strip() if ":" in line else ""
        if msg:
            code = msg.split()[0]
            if len(code) >= 4 and code[0] in "EWFN":
                codes[code] += 1
    return codes, raw_lines


def analyze_pep440(requirements_dir: Path) -> Dict[str, Any]:
    from packaging.requirements import InvalidRequirement, Requirement

    files = sorted(requirements_dir.glob("*.txt"))
    entries: List[Dict[str, Any]] = []
    invalid: List[str] = []
    git_pins = 0
    pinned_eq = 0
    total = 0

    for req_file in files:
        for raw_line in req_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("-r"):
                continue
            total += 1
            entry = {"file": req_file.name, "line": line}
            if line.startswith("git+"):
                git_pins += 1
                entry["type"] = "git"
                entries.append(entry)
                continue
            try:
                req = Requirement(line)
                entry["type"] = "pypi"
                entry["name"] = req.name
                if any(str(s).startswith("==") for s in req.specifier):
                    pinned_eq += 1
                entries.append(entry)
            except InvalidRequirement:
                invalid.append(f"{req_file.name}: {line}")
                entry["type"] = "invalid"
                entries.append(entry)

    return {
        "files_analyzed": [f.name for f in files],
        "total_dependency_lines": total,
        "pypi_valid": sum(1 for e in entries if e.get("type") == "pypi"),
        "git_pins": git_pins,
        "pinned_with_eq": pinned_eq,
        "invalid_lines": invalid,
        "entries": entries,
    }


def _pct_float(part: int, whole: int) -> float:
    if whole <= 0:
        return 100.0
    return 100.0 * part / whole


def render_simplified_markdown(
    summary: Dict[str, Any],
    flake8_total: int,
    pep440: Dict[str, Any],
    meta: Dict[str, str],
    max_line_length: int,
) -> str:
    """
    Quatro seções (PEP 8, 257, 484, 440) com % de aderência e critério explícito.
    """
    agg = summary
    elig = agg["lines_length_eligible"]
    over = agg["lines_over_79"]
    within = elig - over
    pep8_lines = _pct_float(within, elig)

    sym_total = agg["functions_methods_total"] + agg["classes_total"]
    pep257 = _pct_float(agg["symbols_with_docstring"], sym_total)

    ft = agg["functions_methods_total"]
    pep484_full = _pct_float(agg["hints_completo"], ft)
    pep484_partial = _pct_float(
        agg["hints_completo"] + agg["hints_parcial"], ft
    )

    dep_lines = pep440.get("total_dependency_lines") or 0
    inv_n = len(pep440.get("invalid_lines") or [])
    pep440_pct = _pct_float(dep_lines - inv_n, dep_lines)

    lines = [
        "# Resumo PEP — app `processos`",
        "",
        f"Gerado em: **{meta['generated_at']}** · Commit: `{meta.get('git_commit', 'N/A')}`  ",
        f"Comando: `{meta['command']}`",
        "",
        "---",
        "",
        "## PEP 8 — Style Guide for Python Code",
        "",
        f"**Aderência (comprimento de linha):** **{pep8_lines:.1f}%**  ",
        f"_(linhas não vazias e não só comentário com até {max_line_length} "
        f"caracteres; {within} de {elig} linhas elegíveis.)_",
        "",
        f"**Obs.:** o flake8 encontrou **{flake8_total}** avisos/erros de estilo "
        f"no escopo analisado (E501, imports não usados, espaços em branco, etc.); "
        f"isso não entra no % acima, que é só largura de linha.",
        "",
        "---",
        "",
        "## PEP 257 — Docstring Conventions",
        "",
        f"**Aderência:** **{pep257:.1f}%**  ",
        f"_(funções, métodos e classes com docstring: "
        f"{agg['symbols_with_docstring']} de {sym_total} símbolos.)_",
        "",
        "---",
        "",
        "## PEP 484 — Type Hints",
        "",
        f"**Aderência (anotações completas em args + retorno):** **{pep484_full:.1f}%**  ",
        f"_{agg['hints_completo']} de {ft} funções/métodos._",
        "",
        f"**Aderência (completo ou parcial):** **{pep484_partial:.1f}%**  ",
        f"_{agg['hints_completo'] + agg['hints_parcial']} de {ft} funções/métodos._",
        "",
        "---",
        "",
        "## PEP 440 — Version Identification",
        "",
        f"**Aderência (linhas de dependência parseáveis):** **{pep440_pct:.1f}%**  ",
        f"_{dep_lines - inv_n} de {dep_lines} linhas em `requirements/*.txt` "
        f"(excl. `-r` e comentários); linhas inválidas: {inv_n}._",
        "",
        "---",
        "",
        f"*Versão detalhada: ver o arquivo `RELATORIO_PEP.md` na mesma pasta.*",
        "",
    ]
    return "\n".join(lines) + "\n"


def _status_palavra(pct: float) -> str:
    if pct >= 80:
        return "Bom"
    if pct >= 60:
        return "Regular"
    return "Precisa melhorar"


def _estimar_horas_ajuste(summary: Dict[str, Any], flake8_total: int) -> int:
    """Estimativa grossa para leigos (não é compromisso de prazo)."""
    horas = (
        flake8_total * 0.005
        + summary["functions_methods_without_docstring"] * 0.05
        + summary["hints_sem"] * 0.03
        + summary["lines_over_79"] * 0.005
    )
    return max(1, round(horas))


def render_simplified_txt(
    summary: Dict[str, Any],
    flake8_total: int,
    pep440: Dict[str, Any],
    meta: Dict[str, str],
    max_line_length: int,
    *,
    service_name: str = "MS-ProcessoConvocacao",
) -> str:
    """Resumo em texto puro, linguagem acessível."""
    agg = summary
    elig = agg["lines_length_eligible"]
    over = agg["lines_over_79"]
    within = elig - over
    pep8_lines = _pct_float(within, elig)

    sym_total = agg["functions_methods_total"] + agg["classes_total"]
    pep257 = _pct_float(agg["symbols_with_docstring"], sym_total)

    ft = agg["functions_methods_total"]
    pep484_full = _pct_float(agg["hints_completo"], ft)
    pep484_partial = _pct_float(
        agg["hints_completo"] + agg["hints_parcial"], ft
    )

    dep_lines = pep440.get("total_dependency_lines") or 0
    inv_n = len(pep440.get("invalid_lines") or [])
    pep440_pct = _pct_float(dep_lines - inv_n, dep_lines)
    horas = _estimar_horas_ajuste(agg, flake8_total)

    return (
        "================================================================\n"
        "  RESUMO DE BOAS PRÁTICAS DO CÓDIGO PYTHON (PEPs)\n"
        f"  {service_name}\n"
        "================================================================\n"
        "\n"
        "O que é este relatório?\n"
        "---------------------\n"
        "PEP significa \"Python Enhancement Proposal\" — são recomendações oficiais\n"
        "de como escrever código Python de forma clara, uniforme e fácil de manter.\n"
        "Este arquivo resume o quanto o módulo de processos de convocação segue\n"
        "essas recomendações. Quanto maior o percentual, melhor.\n"
        "\n"
        f"Data da análise: {meta['generated_at']}\n"
        f"Versão do código (commit): {meta.get('git_commit', 'não informado')}\n"
        "\n"
        "----------------------------------------------------------------\n"
        "PEP 8 — Organização e leitura do código\n"
        "----------------------------------------------------------------\n"
        "Significado: regras de formatação — tamanho de linha, espaços, nomes\n"
        "e estrutura — para o código ficar parecido em todo o projeto e mais fácil\n"
        "de ler na tela e em revisões.\n"
        "\n"
        f"  Resultado: {pep8_lines:.1f}% das linhas respeitam até {max_line_length} caracteres\n"
        f"  Situação: {_status_palavra(pep8_lines)}\n"
        f"  Detalhe: {over} linha(s) ainda passam desse limite (de {elig} linhas analisadas).\n"
        "\n"
        "----------------------------------------------------------------\n"
        "PEP 257 — Documentação dentro do código (docstrings)\n"
        "----------------------------------------------------------------\n"
        "Significado: cada função, método e classe deve ter um texto curto\n"
        "explicando o que faz — ajuda quem mantém o sistema sem precisar adivinhar.\n"
        "\n"
        f"  Resultado: {pep257:.1f}% dos trechos importantes têm essa explicação\n"
        f"  Situação: {_status_palavra(pep257)}\n"
        f"  Detalhe: {agg['symbols_with_docstring']} de {sym_total} funções, métodos e classes documentados.\n"
        "\n"
        "----------------------------------------------------------------\n"
        "PEP 484 — Indicação de tipos de dados (type hints)\n"
        "----------------------------------------------------------------\n"
        "Significado: informar se um dado é texto, número, lista etc. reduz erros\n"
        "e facilita ferramentas de apoio ao desenvolvimento.\n"
        "\n"
        f"  Resultado (anotação completa): {pep484_full:.1f}%\n"
        f"  Resultado (completa ou parcial): {pep484_partial:.1f}%\n"
        f"  Situação: {_status_palavra(pep484_partial)}\n"
        f"  Detalhe: {agg['hints_completo']} de {ft} funções/métodos com tipagem completa.\n"
        "\n"
        "----------------------------------------------------------------\n"
        "PEP 440 — Versões das bibliotecas usadas pelo sistema\n"
        "----------------------------------------------------------------\n"
        "Significado: o arquivo de dependências (requirements) deve declarar\n"
        "versões de forma padronizada, para instalar sempre o mesmo ambiente.\n"
        "\n"
        f"  Resultado: {pep440_pct:.1f}% das dependências com versão bem definida\n"
        f"  Situação: {_status_palavra(pep440_pct)}\n"
        f"  Detalhe: {dep_lines - inv_n} de {dep_lines} linhas em requirements/; "
        f"problemas encontrados: {inv_n}.\n"
        "\n"
        "----------------------------------------------------------------\n"
        "Próximos passos\n"
        "----------------------------------------------------------------\n"
        f"Estimativa grosseira para alinhar o código às PEPs: ~{horas}h\n"
        "(valor orientativo; o relatório técnico completo está em RELATORIO_PEP.md)\n"
        "\n"
    )


def _pct(part: int, whole: int) -> str:
    if whole == 0:
        return "—"
    return f"{100 * part / whole:.1f}%"


def aggregate(file_metrics: List[FileMetrics]) -> Dict[str, Any]:
    funcs: List[SymbolMetrics] = []
    classes: List[SymbolMetrics] = []
    modules_with_doc = 0
    modules_without_doc = 0
    lines_over = 0
    loc_total = 0
    missing_docstrings: List[Tuple[str, SymbolMetrics]] = []

    for fm in file_metrics:
        loc_total += fm.loc
        lines_over += fm.lines_over_max
        if fm.module_has_docstring:
            modules_with_doc += 1
        else:
            modules_without_doc += 1
        funcs.extend(fm.functions_and_methods)
        classes.extend(fm.classes)
        for s in fm.symbols:
            if not s.has_docstring and s.kind != "class":
                missing_docstrings.append((fm.path, s))
            elif not s.has_docstring and s.kind == "class":
                missing_docstrings.append((fm.path, s))

    all_callables = funcs
    all_classes = classes
    doc_with = sum(1 for s in all_callables + all_classes if s.has_docstring)
    doc_without = len(all_callables) + len(all_classes) - doc_with

    hints = Counter(s.hint_level for s in all_callables)

    return {
        "files_count": len(file_metrics),
        "loc_total": loc_total,
        "lines_over_79": lines_over,
        "lines_length_eligible": sum(fm.lines_length_eligible for fm in file_metrics),
        "modules_with_docstring": modules_with_doc,
        "modules_without_docstring": modules_without_doc,
        "functions_methods_total": len(all_callables),
        "functions_methods_with_docstring": sum(1 for s in all_callables if s.has_docstring),
        "functions_methods_without_docstring": len(all_callables)
        - sum(1 for s in all_callables if s.has_docstring),
        "classes_total": len(all_classes),
        "classes_with_docstring": sum(1 for s in all_classes if s.has_docstring),
        "classes_without_docstring": len(all_classes)
        - sum(1 for s in all_classes if s.has_docstring),
        "symbols_with_docstring": doc_with,
        "symbols_without_docstring": doc_without,
        "hints_completo": hints.get("completo", 0),
        "hints_parcial": hints.get("parcial", 0),
        "hints_sem": hints.get("sem", 0),
        "missing_docstrings_top": [
            {
                "path": path,
                "lineno": sym.lineno,
                "name": sym.name,
                "kind": sym.kind,
            }
            for path, sym in sorted(
                missing_docstrings, key=lambda x: (x[0], x[1].lineno)
            )[:TOP_MISSING_DOCSTRINGS]
        ],
    }


def render_markdown(
    summary: Dict[str, Any],
    file_metrics: List[FileMetrics],
    flake8_codes: Counter,
    flake8_lines: List[str],
    pep440: Dict[str, Any],
    meta: Dict[str, str],
    max_line_length: int,
) -> str:
    agg = summary
    lines = [
        "# Relatório de conformidade PEP — app `processos`",
        "",
        f"Gerado em: **{meta['generated_at']}**  ",
        f"Comando: `{meta['command']}`  ",
        f"Commit: `{meta.get('git_commit', 'N/A')}`  ",
        f"Escopo: código de aplicação (sem `tests/` e `migrations/`)  ",
        f"Limite de linha (PEP 8): **{max_line_length}** caracteres",
        "",
        "## Resumo executivo",
        "",
        "| Métrica | Valor | % |",
        "| --- | ---: | ---: |",
        f"| Arquivos analisados | {agg['files_count']} | — |",
        f"| Linhas de código (LOC) | {agg['loc_total']} | — |",
        f"| Linhas com mais de {max_line_length} caracteres | {agg['lines_over_79']} | "
        f"{_pct(agg['lines_over_79'], agg['loc_total'])} |",
        f"| Funções/métodos | {agg['functions_methods_total']} | — |",
        f"| Funções/métodos com docstring (PEP 257) | "
        f"{agg['functions_methods_with_docstring']} | "
        f"{_pct(agg['functions_methods_with_docstring'], agg['functions_methods_total'])} |",
        f"| Funções/métodos sem docstring | "
        f"{agg['functions_methods_without_docstring']} | "
        f"{_pct(agg['functions_methods_without_docstring'], agg['functions_methods_total'])} |",
        f"| Classes | {agg['classes_total']} | — |",
        f"| Classes com docstring | {agg['classes_with_docstring']} | "
        f"{_pct(agg['classes_with_docstring'], agg['classes_total'])} |",
        f"| Módulos com docstring no topo | {agg['modules_with_docstring']} | "
        f"{_pct(agg['modules_with_docstring'], agg['files_count'])} |",
        f"| Type hints completos (PEP 484) | {agg['hints_completo']} | "
        f"{_pct(agg['hints_completo'], agg['functions_methods_total'])} |",
        f"| Type hints parciais | {agg['hints_parcial']} | "
        f"{_pct(agg['hints_parcial'], agg['functions_methods_total'])} |",
        f"| Sem type hints | {agg['hints_sem']} | "
        f"{_pct(agg['hints_sem'], agg['functions_methods_total'])} |",
        f"| Violações flake8 (PEP 8) | {sum(flake8_codes.values())} | — |",
        "",
        "## PEP 8 — Style Guide",
        "",
        f"- **Linhas acima de {max_line_length} chars** (código/comentários, exceto linha vazia): "
        f"**{agg['lines_over_79']}**",
        f"- **Total flake8** (views, services, models, tasks, etc.): "
        f"**{sum(flake8_codes.values())}**",
        "",
    ]
    if flake8_codes:
        lines.append("### Top códigos flake8")
        lines.append("")
        lines.append("| Código | Ocorrências |")
        lines.append("| --- | ---: |")
        for code, count in flake8_codes.most_common(10):
            lines.append(f"| `{code}` | {count} |")
        lines.append("")
    if flake8_lines:
        lines.append("<details><summary>Primeiras 30 linhas flake8</summary>")
        lines.append("")
        lines.append("```")
        lines.extend(flake8_lines[:30])
        lines.append("```")
        lines.append("</details>")
        lines.append("")

    lines.extend(
        [
            "## PEP 257 — Docstring Conventions",
            "",
            f"- Funções/métodos **com** docstring: **{agg['functions_methods_with_docstring']}**",
            f"- Funções/métodos **sem** docstring: **{agg['functions_methods_without_docstring']}**",
            f"- Classes **com** docstring: **{agg['classes_with_docstring']}** / "
            f"{agg['classes_total']}",
            f"- Módulos **sem** docstring no topo: **{agg['modules_without_docstring']}**",
            "",
            "### Principais símbolos sem docstring",
            "",
            "| Arquivo | Linha | Símbolo | Tipo |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for item in agg["missing_docstrings_top"]:
        lines.append(
            f"| `{item['path']}` | {item['lineno']} | `{item['name']}` | {item['kind']} |"
        )
    lines.extend(["", "## PEP 484 — Type Hints", ""])
    lines.append(
        f"- **Completo** (args + return): **{agg['hints_completo']}** "
        f"({_pct(agg['hints_completo'], agg['functions_methods_total'])})"
    )
    lines.append(
        f"- **Parcial**: **{agg['hints_parcial']}** "
        f"({_pct(agg['hints_parcial'], agg['functions_methods_total'])})"
    )
    lines.append(
        f"- **Sem anotações**: **{agg['hints_sem']}** "
        f"({_pct(agg['hints_sem'], agg['functions_methods_total'])})"
    )
    lines.extend(
        [
            "",
            "## PEP 440 — Dependências do microsserviço",
            "",
            "_Aplica-se a `requirements/`, não ao código do app._",
            "",
            f"- Arquivos: {', '.join(pep440.get('files_analyzed', []))}",
            f"- Linhas de dependência: **{pep440.get('total_dependency_lines', 0)}**",
            f"- PyPI válidas (packaging): **{pep440.get('pypi_valid', 0)}**",
            f"- Pins `git+...`: **{pep440.get('git_pins', 0)}**",
            f"- Com especificador `==`: **{pep440.get('pinned_with_eq', 0)}**",
            f"- Linhas inválidas: **{len(pep440.get('invalid_lines', []))}**",
            "",
        ]
    )
    if pep440.get("invalid_lines"):
        lines.append("Linhas inválidas:")
        for inv in pep440["invalid_lines"]:
            lines.append(f"- `{inv}`")
        lines.append("")

    lines.extend(["## Métricas por arquivo", ""])
    lines.append(
        "| Arquivo | LOC | Linhas >79 | Funções | Docstring % | Hints completos % |"
    )
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for fm in sorted(file_metrics, key=lambda x: x.path):
        funcs = fm.functions_and_methods
        n = len(funcs)
        doc_pct = _pct(sum(1 for s in funcs if s.has_docstring), n) if n else "—"
        hint_pct = _pct(sum(1 for s in funcs if s.hint_level == "completo"), n) if n else "—"
        lines.append(
            f"| `{fm.path}` | {fm.loc} | {fm.lines_over_max} | {n} | {doc_pct} | {hint_pct} |"
        )

    lines.extend(
        [
            "",
            "## Recomendações",
            "",
            "1. Priorizar docstrings em `views/` e `services/` nos endpoints públicos.",
            "2. Reduzir linhas >79 ou quebrar strings/imports longos (E501).",
            "3. Estender type hints nos services que ainda estão em nível `sem` ou `parcial`.",
            "4. Rodar `flake8` e `black` no CI com `max-line-length=79`.",
            "5. Manter pins PEP 440 explícitos em `requirements/base.txt`.",
            "",
            "---",
            "",
            f"*Relatório gerado por `python manage.py {COMMAND_NAME}`*",
        ]
    )
    return "\n".join(lines) + "\n"


def build_simple_summary(
    summary: Dict[str, Any],
    flake8_total: int,
    pep440: Dict[str, Any],
    max_line_length: int,
) -> Dict[str, Any]:
    agg = summary
    elig = agg["lines_length_eligible"]
    over = agg["lines_over_79"]
    within = elig - over
    dep_lines = pep440.get("total_dependency_lines") or 0
    inv_n = len(pep440.get("invalid_lines") or [])
    sym_total = agg["functions_methods_total"] + agg["classes_total"]
    ft = agg["functions_methods_total"]
    return {
        "pep8_line_width_compliance_pct": round(_pct_float(within, elig), 2),
        "pep8_line_width_eligible_lines": elig,
        "pep8_lines_over_max": over,
        "pep8_flake8_violations": flake8_total,
        "pep257_docstring_compliance_pct": round(
            _pct_float(agg["symbols_with_docstring"], sym_total), 2
        ),
        "pep257_symbols_total": sym_total,
        "pep484_full_hints_pct": round(_pct_float(agg["hints_completo"], ft), 2),
        "pep484_full_or_partial_pct": round(
            _pct_float(agg["hints_completo"] + agg["hints_parcial"], ft), 2
        ),
        "pep484_functions_methods_total": ft,
        "pep440_requirement_lines_parseable_pct": round(
            _pct_float(dep_lines - inv_n, dep_lines), 2
        ),
        "pep440_requirement_lines_total": dep_lines,
        "pep440_invalid_lines": inv_n,
        "max_line_length": max_line_length,
    }


def build_json_payload(
    summary: Dict[str, Any],
    file_metrics: List[FileMetrics],
    flake8_codes: Counter,
    pep440: Dict[str, Any],
    meta: Dict[str, str],
    max_line_length: int,
) -> Dict[str, Any]:
    by_file = []
    for fm in file_metrics:
        funcs = fm.functions_and_methods
        by_file.append(
            {
                "path": fm.path,
                "loc": fm.loc,
                "lines_over_max": fm.lines_over_max,
                "module_has_docstring": fm.module_has_docstring,
                "functions_count": len(funcs),
                "functions_with_docstring": sum(1 for s in funcs if s.has_docstring),
                "hints_completo": sum(1 for s in funcs if s.hint_level == "completo"),
                "hints_parcial": sum(1 for s in funcs if s.hint_level == "parcial"),
                "hints_sem": sum(1 for s in funcs if s.hint_level == "sem"),
            }
        )
    simple = build_simple_summary(summary, sum(flake8_codes.values()), pep440, max_line_length)
    return {
        "generated_at": meta["generated_at"],
        "command": meta["command"],
        "git_commit": meta.get("git_commit"),
        "scope": "processos app code (no tests, no migrations)",
        "max_line_length": max_line_length,
        "summary": summary,
        "simple": simple,
        "flake8": dict(flake8_codes.most_common()),
        "pep440": pep440,
        "by_file": by_file,
    }


class Command(BaseCommand):
    help = "Gera relatório PEP 8/257/484/440 do app processos (MD + JSON)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            default="processos/docs",
            help="Diretório de saída relativo à raiz do projeto",
        )
        parser.add_argument(
            "--max-line-length",
            type=int,
            default=79,
            help="Limite PEP 8 para contagem de linhas longas",
        )

    def handle(self, *args, **options):
        repo_root = _repo_root()
        app_dir = _processos_app_dir()
        output_dir = repo_root / options["output_dir"]
        max_len = options["max_line_length"]
        output_dir.mkdir(parents=True, exist_ok=True)

        py_files = discover_app_python_files(app_dir)
        file_metrics = [analyze_file(p, app_dir, max_len) for p in py_files]
        summary = aggregate(file_metrics)

        flake8_codes, flake8_lines = run_flake8(app_dir, repo_root)
        flake8_total = sum(flake8_codes.values())
        pep440 = analyze_pep440(repo_root / "requirements")

        git_commit = None
        try:
            r = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                check=True,
            )
            git_commit = r.stdout.strip()
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

        meta = {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "command": f"python manage.py {COMMAND_NAME}",
            "git_commit": git_commit,
        }

        md_path = output_dir / "RELATORIO_PEP.md"
        md_simple_path = output_dir / "RELATORIO_PEP_RESUMIDO.md"
        txt_simple_path = output_dir / "RELATORIO_PEP_RESUMIDO.txt"
        json_path = output_dir / "relatorio_pep.json"

        md_content = render_markdown(
            summary, file_metrics, flake8_codes, flake8_lines, pep440, meta, max_len
        )
        md_simple_content = render_simplified_markdown(
            summary, flake8_total, pep440, meta, max_len
        )
        txt_simple_content = render_simplified_txt(
            summary, flake8_total, pep440, meta, max_len
        )
        json_payload = build_json_payload(
            summary, file_metrics, flake8_codes, pep440, meta, max_len
        )

        md_path.write_text(md_content, encoding="utf-8")
        md_simple_path.write_text(md_simple_content, encoding="utf-8")
        txt_simple_path.write_text(txt_simple_content, encoding="utf-8")
        json_path.write_text(
            json.dumps(json_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        self.stdout.write(self.style.SUCCESS(f"Relatório MD: {md_path}"))
        self.stdout.write(self.style.SUCCESS(f"Resumo MD: {md_simple_path}"))
        self.stdout.write(self.style.SUCCESS(f"Resumo TXT: {txt_simple_path}"))
        self.stdout.write(self.style.SUCCESS(f"Relatório JSON: {json_path}"))
        self.stdout.write(
            f"Arquivos: {summary['files_count']} | "
            f"Funções/métodos: {summary['functions_methods_total']} | "
            f"Sem docstring: {summary['functions_methods_without_docstring']} | "
            f"Linhas >{max_len}: {summary['lines_over_79']} | "
            f"flake8: {flake8_total}"
        )
