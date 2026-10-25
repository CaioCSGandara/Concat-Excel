# Regras de Negócio

Este documento descreve todas as regras de negócio que regem o comportamento do sistema **Concat Excel**.

---

## 1. Planilha Mestre

- **RN-01** — O usuário deve poder selecionar um arquivo `.xlsx` do sistema de arquivos para atuar como **planilha mestre**.
- **RN-02** — O caminho da planilha mestre é **persistido entre sessões**. Ao reabrir o programa (mesmo após desligar o computador), o caminho é restaurado automaticamente.
- **RN-03** — O usuário pode **alterar** a planilha mestre a qualquer momento, antes de iniciar uma importação.
- **RN-04** — A **primeira linha** da planilha mestre é sempre tratada como cabeçalho (nomes das colunas). Nenhuma linha de cabeçalho é importada como dado.

---

## 2. Planilha Fonte

- **RN-05** — O usuário deve selecionar uma **planilha fonte** (arquivo `.xlsx`) a cada sessão de importação.
- **RN-06** — O caminho da planilha fonte **não é persistido**. Após uma importação concluída (com sucesso ou erro) ou ao fechar e reabrir o programa, o usuário deve selecionar a fonte novamente.
- **RN-07** — A **primeira linha** da planilha fonte é sempre tratada como cabeçalho. Nenhuma linha de cabeçalho é importada como dado.

---

## 3. Mapeamentos de Colunas

- **RN-08** — Um **mapeamento** é um conjunto nomeado de pares `(coluna fonte → coluna mestre)` que define como os dados da planilha fonte são transferidos para a planilha mestre.
- **RN-09** — O usuário pode **criar**, **editar** e **excluir** mapeamentos. Os mapeamentos são persistidos localmente.
- **RN-10** — Um mapeamento deve ter um **nome único** e ao menos **um par de colunas completo** para ser salvo. Linhas vazias ou parcialmente preenchidas são ignoradas na persistência.
- **RN-11** — **Desvinculação e Seleção Independente:** a criação e edição de mapeamentos não dependem da planilha mestre configurada na tela principal. O usuário pode carregar arquivos `.xlsx`/`.xls` de referência diretamente no diálogo de mapeamento para ambos os lados:
  - **Planilha de Origem (Fonte)**
  - **Planilha de Destino (Mestre)**
- **RN-12** — **Auto-população de Colunas:**
  - Ao carregar a planilha de destino, são geradas linhas correspondentes a todos os cabeçalhos dessa planilha; o lado de origem permanece vazio (`""`).
  - Ao carregar a planilha de origem, seus cabeçalhos preenchem as colunas de origem na ordem existente; se houver menos colunas na origem, os slots excedentes de origem ficam vazios. Se houver mais colunas na origem, novas linhas são geradas com destino vazio.
  - Quando um dos lados não tiver correspondente na ordem das linhas, o campo correspondente permanece vazio para edição manual ou reordenação.
- **RN-13** — **Reordenação por Clicar e Arrastar (Drag and Drop):**
  - O usuário pode clicar e arrastar (`⠿`) qualquer coluna para trocá-la de lugar com outra coluna da **mesma planilha** (Origem ↔ Origem ou Destino ↔ Destino).
  - É **estritamente proibido** arrastar e soltar colunas entre planilhas distintas (ex.: campo de origem não pode ser trocado com destino).
  - São disponibilizados botões rápidos de apoio (▲ / ▼) para troca ágil com linhas adjacentes.
- **RN-14** — Os nomes das colunas no mapeamento são comparados por **nome exato** (case-sensitive) com os cabeçalhos das planilhas no momento da importação.

---

## 4. Backup

- **RN-15** — Antes de qualquer importação, o sistema **obrigatoriamente** cria um backup da planilha mestre.
- **RN-16** — Os backups são armazenados em um **diretório de backup configurável** pelo usuário (em Configurações). O diretório padrão é `~/Documents/ConcatExcel/Backups`.
- **RN-17** — Dentro do diretório de backup, os arquivos são organizados em **subdiretórios por nome da planilha mestre**:
  ```
  <backup_dir>/<nome_da_planilha>/<nome_da_planilha>_YYYY-MM-DD_HH-MM-SS.xlsx
  ```
- **RN-18** — São mantidos apenas os **últimos 10 backups** por planilha mestre. Backups mais antigos são excluídos automaticamente.
- **RN-19** — Se o backup **falhar** por qualquer motivo (permissão negada, disco cheio, arquivo não encontrado), uma mensagem de erro é exibida e o procedimento de importação é **cancelado imediatamente**, sem modificar a planilha mestre.

---

## 5. Importação

- **RN-20** — A importação só pode ser iniciada quando **os três elementos** estão selecionados: planilha mestre, planilha fonte e mapeamento.
- **RN-21** — Antes de importar qualquer linha, o sistema **valida o mapeamento**: verifica se todas as colunas fonte existem na planilha fonte e se todas as colunas destino existem na planilha mestre. Em caso de inconsistência, o erro é registrado no log e a importação é **cancelada** sem modificar nenhum arquivo.
- **RN-22** — O sistema detecta e **ignora linhas duplicadas**. Uma linha da planilha fonte é considerada duplicata se já existir na planilha mestre uma linha com os mesmos valores em todas as colunas mapeadas (destino).
- **RN-23** — Nenhum dado existente na planilha mestre é **sobrescrito ou removido**. A importação apenas **acrescenta** linhas novas ao final.
- **RN-24** — Durante a importação, o usuário visualiza uma **barra de progresso** e um **log em tempo real** com o status de cada linha processada.
- **RN-25** — Se a importação for concluída com sucesso, a planilha mestre é salva e uma mensagem de confirmação é exibida ao usuário.
- **RN-26** — Se ocorrer um erro durante a importação (após o backup), o erro é registrado no log, uma mensagem é exibida e a planilha mestre **não é salva** com dados parciais.

---

## 6. Configurações

- **RN-27** — O usuário pode configurar o **diretório de backup** a qualquer momento, via tela de Configurações.
- **RN-28** — O **tema da interface** (claro / escuro) é persistido entre sessões.
- **RN-29** — Todas as configurações são armazenadas localmente em `~/.concat-excel/settings.json`.
