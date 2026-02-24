# Convocação SIGLA Backend

Backend Django para gerenciamento de processos de convocação da SIGLA.

## 🚀 Funcionalidades

### Processos de Convocação
- **CRUD completo** de processos de convocação
- **Gestão de status**: Em Andamento, Finalizado, Cancelado
- **Tipos de processo**: Convocação, Seleção, Avaliação
- **Vinculação com concursos** via UUID
- **Controle de datas** (publicação, convocação, limite)

### 🎯 Gestão de Cargos por Processo
- **Seleção flexível** de cargos para cada processo
- **Controle de vagas** específicas por processo
- **Priorização** de cargos
- **Acompanhamento** de vagas disponíveis vs. preenchidas
- **Salários personalizados** por processo

## 🏗️ Arquitetura

### Modelos Principais

#### `ProcessoConvocacao`
- Representa um processo de convocação
- Vinculado a um concurso específico
- Pode ter múltiplos cargos associados
- Controle de status e datas

#### `CargoProcesso`
- Representa um cargo selecionado para um processo
- Controle granular de vagas por processo
- Priorização e observações específicas
- Estatísticas de preenchimento

### Relacionamentos
- **ProcessoConvocacao** ↔ **CargoProcesso** (1:N)
- Cada processo pode ter múltiplos cargos
- Cada cargo pode ter configurações específicas por processo
- **Sem duplicação** de dados principais

## 📊 API Endpoints

### Processos de Convocação
- `GET /api/processos/processos-convocacao/` - Listar processos
- `POST /api/processos/processos-convocacao/` - Criar processo
- `GET /api/processos/processos-convocacao/{uuid}/` - Detalhes do processo
- `PUT /api/processos/processos-convocacao/{uuid}/` - Atualizar processo
- `DELETE /api/processos/processos-convocacao/{uuid}/` - Excluir processo

### Ações Especiais
- `POST /api/processos/processos-convocacao/{uuid}/finalizar/` - Finalizar processo
- `POST /api/processos/processos-convocacao/{uuid}/cancelar/` - Cancelar processo
- `GET /api/processos/processos-convocacao/{uuid}/cargos/` - Listar cargos do processo
- `POST /api/processos/processos-convocacao/{uuid}/adicionar_cargo/` - Adicionar cargo
- `DELETE /api/processos/processos-convocacao/{uuid}/remover_cargo/` - Remover cargo

### Filtros e Consultas
- `GET /api/processos/processos-convocacao/em_andamento/` - Processos em andamento
- `GET /api/processos/processos-convocacao/finalizados/` - Processos finalizados
- `GET /api/processos/processos-convocacao/por_concurso/?concurso_uuid={uuid}` - Por concurso
- `GET /api/processos/processos-convocacao/por_tipo/?tipo_processo={tipo}` - Por tipo

### Cargos do Processo
- `GET /api/processos/cargos-processo/` - Listar cargos
- `POST /api/processos/cargos-processo/` - Criar cargo
- `PUT /api/processos/cargos-processo/{uuid}/` - Atualizar cargo
- `DELETE /api/processos/cargos-processo/{uuid}/` - Excluir cargo

### Ações de Cargos
- `POST /api/processos/cargos-processo/{uuid}/atualizar_vagas_disponiveis/` - Atualizar vagas
- `POST /api/processos/cargos-processo/{uuid}/alterar_prioridade/` - Alterar prioridade
- `GET /api/processos/cargos-processo/por_processo/?processo_uuid={uuid}` - Por processo

## 🛠️ Tecnologias

- **Django 5.2.5** - Framework web
- **Django REST Framework 3.15.2** - API REST
- **PostgreSQL** - Banco de dados principal
- **Celery** - Filas para envio assíncrono de e-mails (Carta de Convocação)
- **Redis** - Broker e result backend do Celery
- **django-cors-headers** - CORS para frontend
- **django-filter** - Filtros avançados

## 🚀 Como Executar

### 1. Configuração do Ambiente
```bash
# Clonar o repositório
git clone <repository-url>
cd convocacao-sigla-backend

# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements/base.txt
```

### 2. Configuração do Banco
```bash
# Copiar arquivo de exemplo
cp env.example .env

# Editar variáveis de ambiente
# DB_NAME, DB_USER, DB_PASSWORD, etc.
```

### 3. Migrações e Setup
```bash
# Aplicar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver
```

### 4. Rodar com fila (Docker Compose)

Para testar localmente com API + worker Celery + Redis (igual ao fluxo de ambiente):

```bash
# Subir todos os serviços (db, redis, api, celery_worker)
docker-compose up -d
```

A API ficará em `http://localhost:8001`. O worker consome a fila e processa o envio dos e-mails da Carta de Convocação.

### 5. Execução em ambiente (QA / Homologação)

Em QA e Homologação é necessário **dois** deployments no Rancher/Kubernetes:

1. **API** (Django) – já existente.
2. **Worker Celery** – consome a fila (comando: `celery -A config worker --loglevel=info --concurrency=2 -n worker1@%h`).

A variável **CELERY_REDIS_URL** já é configurada pela Infra. Detalhes para a Infra (comando exato, nome do workload, pipeline): ver **[DEPLOY.md](DEPLOY.md)**.

## 📝 Exemplos de Uso

### Criar Processo com Cargos
```json
POST /api/processos/processos-convocacao/
{
    "concurso_uuid": "123e4567-e89b-12d3-a456-426614174000",
    "concurso_nome": "Concurso Público 2024",
    "descricao": "DESCRICAO_CONVOCACAO",
    "tipo_processo": "CONVOCACAO",
    "data_convocacao": "2024-12-01T10:00:00Z",
    "data_limite": "2024-12-31T23:59:59Z",
    "numero_convocados": 1,
    "observacoes": "Processo para preenchimento de vagas",
    "cargos": [
        {
            "cargo_uuid": "456e7890-e89b-12d3-a456-426614174001",
            "cargo_nome": "Analista de Sistemas",
            "vagas_processo": 5,
            "salario_processo": 5000.00,
            "prioridade": 1
        },
        {
            "cargo_uuid": "789e0123-e89b-12d3-a456-426614174002",
            "cargo_nome": "Desenvolvedor",
            "vagas_processo": 3,
            "salario_processo": 4000.00,
            "prioridade": 2
        }
    ]
}
```

### Adicionar Cargo a um Processo
```json
POST /api/processos/processos-convocacao/{uuid}/adicionar_cargo/
{
    "cargo_uuid": "999e8888-e89b-12d3-a456-426614174999",
    "cargo_nome": "Técnico de TI",
    "vagas_processo": 2,
    "salario_processo": 3000.00,
    "prioridade": 3
}
```

## 🔧 Configurações

### Variáveis de Ambiente
- `SECRET_KEY` - Chave secreta do Django
- `DEBUG` - Modo debug (True/False)
- `DB_ENGINE` - Engine do banco (postgresql/sqlite3)
- `DB_NAME` - Nome do banco
- `DB_USER` - Usuário do banco
- `DB_PASSWORD` - Senha do banco
- `DB_HOST` - Host do banco
- `DB_PORT` - Porta do banco
- `CELERY_REDIS_URL` - URL do Redis para Celery (broker e result backend); em ambiente é configurada pela Infra
- `CANDIDATOS_API_URL` - URL do MS de Candidatos (habilitados)
- `MS_URL` - URL base do microserviço (logos, etc.)

### Configurações Django
- **Idioma**: Português (pt-br)
- **Fuso horário**: America/Sao_Paulo
- **Paginação**: 20 itens por página
- **Permissões**: Leitura para todos, escrita para autenticados
- **CORS**: Habilitado para desenvolvimento

## 📚 Documentação da API

A API inclui documentação automática via Django REST Framework:
- **Browsable API**: `/api/processos/processos-convocacao/`
- **Endpoints exploráveis** com interface web
- **Testes de endpoints** diretamente no navegador

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes. 