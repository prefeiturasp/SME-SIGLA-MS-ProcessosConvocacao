"""Contrato da documentação OpenAPI (Swagger) do microsserviço."""

from io import StringIO

import pytest
from django.core.management import call_command
from drf_spectacular.drainage import GENERATOR_STATS
from drf_spectacular.generators import SchemaGenerator

METODOS_HTTP = {"get", "post", "put", "patch", "delete"}
CABECALHO_CORRELACAO = "X-Correlation-ID"

RESPOSTAS_ESPERADAS = {
    "listar_processos_convocacao": {"200", "400", "403", "404", "500"},
    "criar_processo_convocacao": {"201", "400", "403", "500"},
    "detalhar_processo_convocacao": {"200", "403", "404", "500"},
    "atualizar_processo_convocacao": {"200", "400", "403", "404", "500"},
    "atualizar_parcial_processo_convocacao": {
        "200",
        "400",
        "403",
        "404",
        "500",
    },
    "excluir_processo_convocacao": {"204", "400", "403", "404", "500"},
    "finalizar_processo_convocacao": {"200", "400", "403", "404", "500"},
    "atualizar_passo_processo_convocacao": {
        "200",
        "400",
        "403",
        "404",
        "500",
    },
    "listar_filtros_processos_convocacao": {"200", "403", "500"},
    "consultar_historico_candidatos": {"200", "400", "403", "500"},
    "listar_cargos_processo": {"200", "403", "404", "500"},
    "substituir_cargos_processo": {
        "200",
        "207",
        "400",
        "403",
        "404",
        "500",
    },
    "detalhar_cargo_processo": {"200", "403", "404", "500"},
    "atualizar_cargo_processo": {"200", "400", "403", "404", "500"},
    "atualizar_parcial_cargo_processo": {"200", "400", "403", "404", "500"},
    "excluir_cargo_processo": {"204", "400", "403", "404", "500"},
    "listar_envios_email": {"200", "403", "500"},
    "iniciar_envio_email": {"200", "400", "403", "500"},
    "detalhar_envio_email": {"200", "403", "404", "500"},
    "listar_conteudos_email": {"200", "403", "500"},
    "detalhar_conteudo_email": {"200", "403", "404", "500"},
    "atualizar_conteudo_email": {"200", "400", "403", "404", "500"},
}
ERRO_INTERNO_COM_CORPO = {"iniciar_envio_email"}

TIPOS_JSON = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "object": dict,
    "array": list,
}

COMPONENTES_TESTE = {
    "Situacao": {"type": "string", "enum": ["ABERTO", "FECHADO"]},
    "Item": {
        "type": "object",
        "properties": {
            "uuid": {"type": "string", "readOnly": True},
            "nome": {"type": "string"},
            "vagas": {"type": "integer"},
            "situacao": {
                "allOf": [{"$ref": "#/components/schemas/Situacao"}],
                "description": "Situação do item.",
            },
            "observacao": {"type": "string", "nullable": True},
        },
        "required": ["uuid", "nome", "situacao"],
    },
}
REF_ITEM = {"$ref": "#/components/schemas/Item"}
ITEM_VALIDO = {"uuid": "u", "nome": "n", "situacao": "ABERTO"}


def _sem_pendencias(pendencias):
    assert not pendencias, "\n" + "\n".join(pendencias)


def _corpos_json(operacao):
    """Devolve (origem, conteúdo JSON, é requisição) de cada corpo."""
    corpos = []
    requisicao = (
        operacao.get("requestBody", {})
        .get("content", {})
        .get("application/json")
    )
    if requisicao:
        corpos.append(("requisição", requisicao, True))
    for codigo, resposta in operacao["responses"].items():
        conteudo = resposta.get("content", {}).get("application/json")
        if conteudo:
            corpos.append((f"resposta {codigo}", conteudo, False))
    return corpos


def _violacoes(valor, esquema, componentes, caminho="$", *, requisicao=False):
    """Lista o que impede ``valor`` de seguir ``esquema`` (OpenAPI 3.0)."""
    if "$ref" in esquema:
        alvo = componentes[esquema["$ref"].rsplit("/", 1)[-1]]
        return _violacoes(
            valor, alvo, componentes, caminho, requisicao=requisicao
        )
    if "oneOf" in esquema:
        tentativas = [
            _violacoes(
                valor, alternativa, componentes, caminho, requisicao=requisicao
            )
            for alternativa in esquema["oneOf"]
        ]
        if any(not tentativa for tentativa in tentativas):
            return []
        return [f"{caminho}: não segue nenhuma alternativa de oneOf"]
    if valor is None and esquema.get("nullable"):
        return []
    if "allOf" in esquema:
        return [
            violacao
            for parte in esquema["allOf"]
            for violacao in _violacoes(
                valor, parte, componentes, caminho, requisicao=requisicao
            )
        ]
    if "enum" in esquema:
        if valor in esquema["enum"]:
            return []
        return [f"{caminho}: {valor!r} fora do enum {esquema['enum']}"]
    if valor is None:
        return [f"{caminho}: nulo não permitido"]
    tipo = esquema.get("type")
    if tipo is None:
        return []
    booleano_indevido = isinstance(valor, bool) and tipo != "boolean"
    if booleano_indevido or not isinstance(valor, TIPOS_JSON[tipo]):
        return [f"{caminho}: esperado {tipo}, veio {type(valor).__name__}"]
    if tipo == "array":
        return [
            violacao
            for indice, item in enumerate(valor)
            for violacao in _violacoes(
                item,
                esquema.get("items", {}),
                componentes,
                f"{caminho}[{indice}]",
                requisicao=requisicao,
            )
        ]
    propriedades = esquema.get("properties")
    if tipo != "object" or propriedades is None:
        return []
    somente_leitura = {
        nome for nome, campo in propriedades.items() if campo.get("readOnly")
    }
    obrigatorios = set(esquema.get("required", []))
    if requisicao:
        obrigatorios -= somente_leitura
    violacoes = [
        f"{caminho}.{nome}: obrigatório ausente"
        for nome in sorted(obrigatorios - set(valor))
    ]
    violacoes += [
        f"{caminho}.{nome}: campo fora do modelo"
        for nome in sorted(set(valor) - set(propriedades))
    ]
    for nome in sorted(set(valor) & set(propriedades)):
        violacoes += _violacoes(
            valor[nome],
            propriedades[nome],
            componentes,
            f"{caminho}.{nome}",
            requisicao=requisicao,
        )
    return violacoes


@pytest.fixture(scope="module")
def schema():
    """Gera o schema OpenAPI completo a partir das rotas reais."""
    return SchemaGenerator().get_schema(request=None, public=True)


@pytest.fixture(scope="module")
def operacoes(schema):
    """Reúne (rótulo, operação) de todas as operações do schema."""
    return [
        (f"{metodo.upper()} {caminho}", operacao)
        for caminho, item in schema["paths"].items()
        for metodo, operacao in item.items()
        if metodo in METODOS_HTTP
    ]


@pytest.mark.parametrize(
    ("valor", "requisicao", "esperado"),
    [
        (ITEM_VALIDO, False, []),
        ({"nome": "n", "situacao": "ABERTO"}, True, []),
        (
            {"nome": "n", "situacao": "ABERTO"},
            False,
            ["$.uuid: obrigatório ausente"],
        ),
        (
            {**ITEM_VALIDO, "situacao": "X"},
            False,
            ["$.situacao: 'X' fora do enum ['ABERTO', 'FECHADO']"],
        ),
        (
            {**ITEM_VALIDO, "vagas": "3"},
            False,
            ["$.vagas: esperado integer, veio str"],
        ),
        (
            {**ITEM_VALIDO, "vagas": True},
            False,
            ["$.vagas: esperado integer, veio bool"],
        ),
        (
            {**ITEM_VALIDO, "extra": 1},
            False,
            ["$.extra: campo fora do modelo"],
        ),
        (
            {**ITEM_VALIDO, "nome": None},
            False,
            ["$.nome: nulo não permitido"],
        ),
        ({**ITEM_VALIDO, "observacao": None}, False, []),
    ],
)
def test_violacoes_apontam_divergencia_entre_exemplo_e_modelo(
    valor, requisicao, esperado
):
    """Exemplo fora do modelo é apontado com o caminho do campo."""
    assert (
        _violacoes(valor, REF_ITEM, COMPONENTES_TESTE, requisicao=requisicao)
        == esperado
    )


def test_violacoes_percorrem_listas_e_alternativas():
    """Itens de lista e alternativas de ``oneOf`` também são conferidos."""
    lista = {"type": "array", "items": REF_ITEM}
    alternativas = {"oneOf": [REF_ITEM, lista]}

    assert _violacoes([ITEM_VALIDO], alternativas, COMPONENTES_TESTE) == []
    assert _violacoes(
        [ITEM_VALIDO, {**ITEM_VALIDO, "vagas": 1.5}],
        lista,
        COMPONENTES_TESTE,
    ) == ["$[1].vagas: esperado integer, veio float"]
    assert _violacoes("texto", alternativas, COMPONENTES_TESTE) == [
        "$: não segue nenhuma alternativa de oneOf"
    ]


def test_schema_valido_sem_avisos():
    """Toda view é introspectável e o documento é OpenAPI válido."""
    GENERATOR_STATS.reset()
    call_command(
        "spectacular", "--validate", "--fail-on-warn", stdout=StringIO()
    )


def test_inventario_de_operacoes(operacoes):
    """Todo endpoint exposto está no inventário documentado."""
    identificadores = sorted(
        operacao["operationId"] for _, operacao in operacoes
    )
    assert identificadores == sorted(RESPOSTAS_ESPERADAS)


def test_operacao_tem_resumo_descricao_e_tag(schema, operacoes):
    """Toda operação tem resumo, descrição e uma tag declarada."""
    tags_declaradas = {tag["name"] for tag in schema.get("tags", [])}
    pendencias = []
    for rotulo, operacao in operacoes:
        tags = operacao.get("tags", [])
        if not operacao.get("summary"):
            pendencias.append(f"{rotulo}: sem resumo")
        if not operacao.get("description"):
            pendencias.append(f"{rotulo}: sem descrição")
        if len(tags) != 1 or tags[0] not in tags_declaradas:
            pendencias.append(f"{rotulo}: tag não declarada {tags}")
    _sem_pendencias(pendencias)


def test_parametros_tem_tipo_e_descricao(operacoes):
    """Todo parâmetro de rota, query e header tem tipo e descrição."""
    pendencias = []
    for rotulo, operacao in operacoes:
        for parametro in operacao.get("parameters", []):
            nome = f"{rotulo} › {parametro['in']} {parametro['name']}"
            if not parametro.get("description"):
                pendencias.append(f"{nome}: sem descrição")
            if "type" not in parametro.get("schema", {}):
                pendencias.append(f"{nome}: sem tipo")
    _sem_pendencias(pendencias)


def test_cabecalho_de_correlacao_fica_fora_das_operacoes(operacoes):
    """O header de correlação não consta na requisição nem nas respostas."""
    pendencias = []
    for rotulo, operacao in operacoes:
        cabecalhos = {
            parametro["name"]
            for parametro in operacao.get("parameters", [])
            if parametro["in"] == "header"
        }
        if CABECALHO_CORRELACAO in cabecalhos:
            pendencias.append(f"{rotulo}: requisição com o header")
        for codigo, resposta in operacao["responses"].items():
            if CABECALHO_CORRELACAO in resposta.get("headers", {}):
                pendencias.append(f"{rotulo} [{codigo}]: com o header")
    _sem_pendencias(pendencias)


def test_campos_dos_modelos_tem_descricao(schema):
    """Todo campo de todo modelo de request e response tem descrição."""
    pendencias = [
        f"{nome}.{campo}"
        for nome, componente in schema["components"]["schemas"].items()
        for campo, definicao in componente.get("properties", {}).items()
        if not definicao.get("description")
    ]
    _sem_pendencias(pendencias)


def test_modelos_tem_descricao_para_quem_consome(schema):
    """Todo modelo é descrito sem expor termos de implementação."""
    pendencias = []
    for nome, componente in schema["components"]["schemas"].items():
        if "properties" not in componente:
            continue
        descricao = componente.get("description", "")
        if not descricao:
            pendencias.append(f"{nome}: sem descrição")
        elif "serializer" in descricao.lower():
            pendencias.append(f"{nome}: cita implementação ({descricao})")
    _sem_pendencias(pendencias)


def test_codigos_de_resposta(operacoes):
    """Cada operação documenta exatamente os códigos HTTP que retorna."""
    pendencias = []
    for rotulo, operacao in operacoes:
        esperados = RESPOSTAS_ESPERADAS.get(operacao["operationId"], set())
        obtidos = set(operacao["responses"])
        if obtidos != esperados:
            pendencias.append(
                f"{rotulo}: {sorted(obtidos)} != {sorted(esperados)}"
            )
    _sem_pendencias(pendencias)


def test_respostas_tem_descricao_e_modelo(operacoes):
    """Toda resposta é descrita e traz modelo, salvo 204 e 500 genérico."""
    pendencias = []
    for rotulo, operacao in operacoes:
        for codigo, resposta in operacao["responses"].items():
            if not resposta.get("description"):
                pendencias.append(f"{rotulo} [{codigo}]: sem descrição")
            sem_corpo = codigo == "204" or (
                codigo == "500"
                and operacao["operationId"] not in ERRO_INTERNO_COM_CORPO
            )
            conteudo = resposta.get("content", {}).get("application/json")
            if sem_corpo and conteudo:
                pendencias.append(f"{rotulo} [{codigo}]: modelo inesperado")
            if not sem_corpo and "schema" not in (conteudo or {}):
                pendencias.append(f"{rotulo} [{codigo}]: sem modelo")
    _sem_pendencias(pendencias)


def test_corpos_tem_exemplos(operacoes):
    """Todo corpo de requisição e de resposta traz ao menos um exemplo."""
    pendencias = [
        f"{rotulo} › {origem}: sem exemplo"
        for rotulo, operacao in operacoes
        for origem, conteudo, _ in _corpos_json(operacao)
        if not conteudo.get("examples")
    ]
    _sem_pendencias(pendencias)


def test_exemplos_seguem_os_modelos(schema, operacoes):
    """Os exemplos publicados obedecem ao modelo que ilustram."""
    componentes = schema["components"]["schemas"]
    exemplos = [
        (f"{rotulo} › {origem} › {nome}", exemplo, conteudo, requisicao)
        for rotulo, operacao in operacoes
        for origem, conteudo, requisicao in _corpos_json(operacao)
        for nome, exemplo in conteudo.get("examples", {}).items()
    ]
    assert exemplos, "nenhum exemplo publicado"
    pendencias = [
        f"{rotulo} › {violacao}"
        for rotulo, exemplo, conteudo, requisicao in exemplos
        for violacao in _violacoes(
            exemplo["value"],
            conteudo["schema"],
            componentes,
            requisicao=requisicao,
        )
    ]
    _sem_pendencias(pendencias)
