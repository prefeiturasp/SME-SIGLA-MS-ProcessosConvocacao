Estrutura do projeto
====================

Esta seção explica **cada pasta do repositório** e o papel de cada módulo dentro de ``apps/``.

Visão da árvore principal
-------------------------

.. code-block:: text

   ms-processos-convocacao/
   ├── apps/              # Módulos de negócio (Django apps)
   ├── config/            # Configurações do projeto Django
   ├── docs/              # Documentação Sphinx (este material)
   ├── requirements/      # Dependências Python por ambiente
   ├── templates/         # Modelos HTML de e-mails
   ├── manage.py          # Ponto de entrada do Django
   ├── Dockerfile         # Imagem Docker da API
   ├── docker-compose.yml # Ambiente local (API + banco + Redis + worker)
   └── Makefile           # Comandos úteis de desenvolvimento

Pasta ``apps/``
---------------

É onde ficam os **módulos de negócio**. Cada subpasta é um "app" Django com responsabilidade bem definida.

``apps/core/``
~~~~~~~~~~~~~~

**O que faz:** Fornece a base comum usada por todos os outros apps.

**Para que serve:** Evita repetir código. Todo modelo do sistema herda de ``BaseModel``, que já traz:

- Identificador único (UUID)
- Data de criação
- Data da última atualização

**Analogia:** É a "ficha padrão" que todo cadastro do sistema usa — como um formulário com campos obrigatórios no topo.

``apps/processos/``
~~~~~~~~~~~~~~~~~~~

**O que faz:** É o **coração** do microserviço. Gerencia o ciclo de vida dos processos de convocação.

**Para que serve:**

- Criar, listar, editar e excluir processos de convocação
- Controlar status, passo (etapa) e datas
- Integrar com Módulo Agenda, Módulo Candidatos e Módulo Escolhas
- Expor a API principal consumida pelo frontend

**Principais partes internas:**

.. list-table:: Módulos do app processos
   :header-rows: 1
   :widths: 35 65

   * - Subpasta / arquivo
     - Função
   * - ``models.py``
     - Define o modelo ``ProcessoConvocacao``
   * - ``api/views.py``
     - Endpoints REST (listar, criar, finalizar, excluir)
   * - ``services/``
     - Regras que envolvem outros microserviços
   * - ``repository.py``
     - Acesso ao banco de dados (consultas e persistência)
   * - ``serializers.py``
     - Validação e conversão dos dados da API
   * - ``constants.py``
     - Status, tipos de escolha e mensagens de erro
   * - ``management/commands/``
     - Comandos de apoio (criar/limpar processos em dev)
   * - ``tests/``
     - Testes automatizados do app

**Exemplo:** Quando o analista clica em "Finalizar processo", é o ``processos`` que valida se todos os candidatos escolheram vaga e atualiza o status para Concluído.

``apps/cargos/``
~~~~~~~~~~~~~~~~

**O que faz:** Gerencia os **cargos e vagas** vinculados a cada processo de convocação.

**Para que serve:**

- Associar cargos do concurso a um processo específico
- Definir quantas vagas cada cargo tem naquele processo
- Registrar quantos candidatos (geral, PCD, NNA) estão vinculados
- Manter a lista de candidatos convocados por cargo

**Principais partes internas:**

.. list-table:: Módulos do app cargos
   :header-rows: 1
   :widths: 35 65

   * - Subpasta / arquivo
     - Função
   * - ``models/cargo_processo.py``
     - Modelo ``CargoProcesso``
   * - ``services.py``
     - Lógica de criar, atualizar e remover cargos em lote
   * - ``api/views.py``
     - Endpoints REST de cargos
   * - ``repository.py``
     - Consultas e persistência no banco

**Exemplo:** No processo de convocação do Concurso 2026, o analista associa os cargos "Professor I" (10 vagas) e "Professor II" (5 vagas). Essas informações ficam no app ``cargos``.

``apps/envio_email/``
~~~~~~~~~~~~~~~~~~~~~

**O que faz:** Cuida do **envio de e-mails** aos candidatos e do histórico desses envios.

**Para que serve:**

- Disparar e-mails de convocação, vagas ou resultados
- Processar envios em fila (sem travar a interface)
- Guardar histórico de cada lote enviado
- Permitir conteúdo personalizado de e-mail por processo

**Principais partes internas:**

.. list-table:: Módulos do app envio_email
   :header-rows: 1
   :widths: 35 65

   * - Subpasta / arquivo
     - Função
   * - ``models/``
     - Modelos de envio, candidato e conteúdo personalizado
   * - ``services.py``
     - Monta e-mails e inicia processamento
   * - ``tasks/``
     - Tarefas Celery que enviam cada e-mail individualmente
   * - ``api/views/``
     - Endpoints de disparo e consulta de histórico
   * - ``utils/``
     - Montagem de HTML e imagens inline dos e-mails

**Exemplo:** O analista solicita envio de 200 e-mails de convocação. O ``envio_email`` enfileira os 200 envios; o worker Celery processa um a um em segundo plano.

Pasta ``config/``
-----------------

**O que faz:** Configurações centrais do projeto Django.

**Para que serve:**

.. list-table:: Arquivos de configuração
   :header-rows: 1
   :widths: 25 75

   * - Arquivo
     - Função
   * - ``settings.py``
     - Banco de dados, apps instalados, CORS, Celery, URLs de outros microserviços, idioma e fuso horário
   * - ``urls.py``
     - Rotas da API (``/api/v1/``), admin, healthcheck e Swagger
   * - ``celery.py``
     - Configuração do worker de filas (envio de e-mails)
   * - ``wsgi.py``
     - Ponto de entrada para servidores de produção

**Exemplo:** A variável ``CANDIDATOS_API_URL`` em ``settings.py`` diz ao sistema onde buscar a lista de candidatos habilitados.

Pasta ``templates/``
--------------------

**O que faz:** Armazena os **modelos HTML** dos e-mails enviados aos candidatos.

**Para que serve:** Define a aparência e o texto base dos e-mails de convocação, vagas e resultados. O sistema preenche os campos dinâmicos (nome do candidato, cargo, classificação) ao enviar.

Pasta ``requirements/``
-----------------------

**O que faz:** Lista as **dependências Python** do projeto, separadas por ambiente.

**Para que serve:**

.. list-table:: Arquivos de dependências
   :header-rows: 1
   :widths: 25 75

   * - Arquivo
     - Conteúdo
   * - ``base.txt``
     - Dependências essenciais (Django, DRF, PostgreSQL)
   * - ``local.txt``
     - Desenvolvimento (testes, lint, Sphinx, debug toolbar)
   * - ``production.txt``
     - Produção (gunicorn, monitoramento, segurança)

Pasta ``docs/``
---------------

**O que faz:** Contém esta documentação em formato reStructuredText (``.rst``) e a configuração do Sphinx.

**Para que serve:** Gerar o site HTML de documentação com ``make docs`` ou ``sphinx-build``.

Arquivos na raiz
----------------

.. list-table:: Arquivos na raiz do projeto
   :header-rows: 1
   :widths: 25 75

   * - Arquivo
     - Função
   * - ``manage.py``
     - Comando Django (migrações, servidor, superusuário)
   * - ``docker-compose.yml``
     - Sobe API, PostgreSQL, Redis e worker Celery juntos
   * - ``Dockerfile``
     - Constrói a imagem Docker da API
   * - ``Makefile``
     - Atalhos: testes, lint, migrações e documentação
   * - ``README.md``
     - Visão técnica rápida e instruções de execução
   * - ``env.example``
     - Modelo de variáveis de ambiente necessárias

API — endpoints principais (referência)
---------------------------------------

Para consulta rápida, os principais caminhos da API (prefixo ``/api/v1/``):

**Processos de convocação**

- ``GET /processos-convocacao/`` — Listar processos
- ``POST /processos-convocacao/`` — Criar processo
- ``GET /processos-convocacao/{uuid}/`` — Detalhes
- ``POST /processos-convocacao/{uuid}/finalizar/`` — Finalizar
- ``PATCH /processos-convocacao/{uuid}/passo/`` — Atualizar etapa
- ``DELETE /processos-convocacao/{uuid}/`` — Excluir (quando permitido)

**Cargos**

- ``GET /cargos-processo/`` — Listar cargos
- Endpoints de criação e atualização vinculados ao processo

**Envio de e-mail**

- ``POST /envio-email/`` — Disparar lote de e-mails
- ``GET /envio-email/`` — Histórico de envios

A documentação interativa da API (Swagger) está disponível em ``/api/docs/`` quando o servidor está rodando.
