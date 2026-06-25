Regras de negócio
=================

Esta seção descreve as **regras que o sistema aplica automaticamente** — ou seja, o que pode e o que não pode acontecer em um processo de convocação.

Processo de convocação
----------------------

O que é
~~~~~~~

Um **processo de convocação** representa um ciclo completo de convocação de candidatos de **um concurso**. Cada processo guarda:

- Qual concurso está vinculado (identificador e nome)
- Uma descrição para identificação interna
- Datas importantes (convocação e corte de vagas)
- O tipo de escolha (nova autorização, reposição ou reconvocação)
- O status atual e em qual **passo** (etapa) o processo se encontra
- Percentuais de cotas para **PCD** e **NNA**

Tipos de escolha
~~~~~~~~~~~~~~~~

.. list-table:: Tipos de escolha
   :header-rows: 1
   :widths: 30 70

   * - Tipo
     - Quando usar
   * - **Nova Autorização**
     - Primeira convocação de candidatos para escolha de vaga
   * - **Reposição**
     - Preenchimento de vaga deixada por quem desistiu
   * - **Reconvocação**
     - Nova chamada de candidatos que ainda não escolheram

Status do processo
------------------

O processo passa por diferentes **status** ao longo da vida:

.. list-table:: Status do processo
   :header-rows: 1
   :widths: 25 75

   * - Status
     - Significado
   * - **Pendente**
     - Processo criado, ainda não iniciado formalmente
   * - **Em andamento**
     - Processo em execução; candidatos sendo convocados e acompanhados
   * - **Concluído**
     - Todos os convocados registraram escolha; processo encerrado
   * - **Cancelado**
     - Processo interrompido antes da conclusão

Regras importantes sobre status
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Um processo **concluído não pode ser alterado** (dados ficam bloqueados para edição).
- Apenas processos **em andamento** podem ser **finalizados**.
- Não é possível finalizar um processo que **já está concluído** ou **cancelado**.

Etapas (passos)
---------------

O processo é conduzido em **4 passos** (numerados de 1 a 4). O passo indica em qual fase da convocação o analista está — por exemplo, configuração inicial, convocação de candidatos, acompanhamento de escolhas ou encerramento.

O passo pode ser atualizado conforme o trabalho avança, permitindo que a equipe saiba exatamente onde parou.

Finalização do processo
-----------------------

Para **finalizar** um processo, o sistema verifica:

1. O processo precisa estar com status **Em andamento**.
2. Todos os candidatos convocados (vinculados aos cargos do processo) precisam ter registrado escolha no **Módulo Escolhas** — seja escolhendo vaga, declarando reconvocação ou informando que não escolheu.

Se ainda existir candidato pendente, a finalização é **bloqueada** com a mensagem:

   *"Existem candidatos convocados que ainda não fizeram escolha."*

Exclusão e inativação
---------------------

Um processo **não pode ser excluído** se estiver **em andamento** ou **concluído**.

Quando a exclusão é permitida (processo pendente ou cancelado), o sistema:

1. Remove agendas vinculadas no **Módulo Agenda**
2. Limpa vínculos no **Módulo Candidatos**
3. Limpa vínculos no **Módulo Escolhas**
4. **Inativa** o processo localmente (exclusão lógica — o registro não some do banco, mas deixa de aparecer nas listagens)

Cargos do processo
------------------

Cada processo pode ter **um ou mais cargos** associados. Para cada cargo, o sistema registra:

- Nome e identificador do cargo (vindos do concurso)
- **Quantidade de vagas** disponíveis naquele processo
- Quantidade de candidatos por categoria: geral, PCD e NNA
- Lista de candidatos convocados (identificadores)

Regras de cargos
~~~~~~~~~~~~~~~~

- A **prioridade** de um cargo deve estar entre **1 e 100** (quanto menor, mais prioritário).
- O número de **vagas** deve estar entre **1 e 10.000**.
- Um mesmo cargo **não pode ser duplicado** dentro do mesmo processo.
- Ao atualizar cargos, o sistema pode **criar, atualizar ou remover** cargos conforme a lista enviada — a lista enviada passa a ser a lista oficial.

Cotas PCD e NNA
---------------

Cada processo define percentuais para reserva de vagas:

- **PCD** (Pessoa com Deficiência): padrão de **5%** (0,05)
- **NNA** (Negro, Não declarado ou Amarelo): padrão de **20%** (0,20)

Esses valores podem ser ajustados por processo conforme a necessidade do concurso.

Envio de e-mails
----------------

O sistema envia comunicados aos candidatos em **três tipos**:

.. list-table:: Tipos de e-mail
   :header-rows: 1
   :widths: 25 75

   * - Tipo
     - Finalidade
   * - **Convocação**
     - Informar ao candidato que foi convocado para escolher vaga
   * - **Vagas**
     - Comunicar vagas disponíveis para escolha
   * - **Resultados**
     - Comunicar resultados da escolha

Como funciona o envio
~~~~~~~~~~~~~~~~~~~~~

1. O analista solicita o envio informando o processo e o tipo de e-mail.
2. O sistema busca os candidatos habilitados no **Módulo Candidatos**.
3. Monta o conteúdo do e-mail (modelo padrão ou conteúdo personalizado).
4. Enfileira cada e-mail para envio **em segundo plano** (Celery).
5. Registra o **histórico** do lote enviado (quantidade de candidatos, tipo, data).

Assim, mesmo com centenas de candidatos, a tela do usuário não trava — os e-mails saem aos poucos pela fila.

Conteúdo dos e-mails
~~~~~~~~~~~~~~~~~~~~

Os e-mails podem usar **modelos padrão** (convocação, vagas, resultados) ou **conteúdo personalizado** cadastrado previamente. O conteúdo inclui informações como nome do cargo, classificação do candidato e dados do processo.

Auditoria
---------

Alterações em processos, cargos e envios de e-mail são **registradas automaticamente** (quem alterou, quando e o que mudou). Isso garante rastreabilidade para auditorias e consultas futuras.
