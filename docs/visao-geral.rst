Visão geral
===========

O que é este módulo?
--------------------

O **Módulo Processos de Convocação** é o sistema responsável por organizar e conduzir os **processos de convocação** de candidatos aprovados em concursos públicos da SME (Secretaria Municipal de Educação de São Paulo).

Em termos simples: depois que um concurso aprova candidatos, ainda é necessário **convocá-los** para escolherem vagas. Este módulo cuida de todo esse ciclo — desde a abertura do processo até o envio de comunicados por e-mail.

Para que serve?
---------------

O sistema permite que a equipe da SME:

- **Abra um processo de convocação** vinculado a um concurso específico
- **Defina quais cargos e vagas** participam daquele processo
- **Acompanhe o andamento** em etapas (passos) e por status
- **Comunique os candidatos** por e-mail (convocação, vagas disponíveis e resultados)
- **Finalize o processo** somente quando todos os convocados tiverem registrado sua escolha

Onde ele se encaixa no ecossistema SIGLA?
-----------------------------------------

Este módulo **não trabalha sozinho**. Ele se integra com outros sistemas:

.. list-table:: Integrações do ecossistema
   :header-rows: 1
   :widths: 25 75

   * - Sistema
     - Papel na convocação
   * - **Módulo Candidatos**
     - Fornece a lista de candidatos habilitados por cargo
   * - **Módulo Agenda**
     - Gerencia agendas de convocação vinculadas ao processo
   * - **Módulo Escolhas**
     - Registra se o candidato fez escolha de vaga ou não
   * - **Frontend SIGLA**
     - Interface usada pela equipe para operar o processo

O Módulo Processos de Convocação é o **ponto central** que coordena essas informações e mantém o histórico do que aconteceu em cada convocação.

Exemplo prático do dia a dia
----------------------------

Imagine o seguinte cenário:

1. O **Concurso Público 2026** para Professor de Educação Básica foi homologado.
2. A SME precisa convocar os primeiros classificados para escolherem vagas nas escolas.
3. Um analista acessa o sistema e **cria um processo de convocação** ligado a esse concurso.
4. Ele **associa os cargos** (ex.: Professor I, Professor II) e define quantas vagas cada um tem.
5. O sistema **convoca os candidatos** e dispara **e-mails de convocação** informando datas e orientações.
6. Conforme os candidatos vão escolhendo vagas, o analista acompanha o passo a passo.
7. Quando **todos os convocados registraram escolha**, o processo pode ser **finalizado**.

Fluxo resumido
--------------

.. code-block:: text

   Concurso homologado
          |
          v
   Criar processo de convocação  ----->  Associar cargos e vagas
          |
          v
   Conduzir etapas (passos 1 a 4)  ----->  Enviar e-mails aos candidatos
          |
          v
   Candidatos fazem escolha (Módulo Escolhas)
          |
          v
   Finalizar processo (quando não há pendências)

Tecnologias utilizadas (referência rápida)
------------------------------------------

Para quem precisa de contexto técnico sem entrar no código:

- **Django** — framework web que estrutura o projeto
- **Django REST Framework** — expõe a API consumida pelo frontend
- **PostgreSQL** — banco de dados onde ficam processos, cargos e histórico de e-mails
- **Celery + Redis** — fila para envio de e-mails em segundo plano (sem travar a tela do usuário)
