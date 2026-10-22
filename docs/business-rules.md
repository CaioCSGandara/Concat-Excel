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
- **RN-10** — Um mapeamento deve ter um **nome único** e ao menos **um par de colunas** para ser salvo.
- **RN-11** — Ao criar ou editar um mapeamento, o usuário pode carregar uma planilha fonte de referência para obter os nomes das colunas disponíveis do lado de origem.
- **RN-12** — Os nomes das colunas no mapeamento são comparados por **nome exato** (case-sensitive) com os cabeçalhos das planilhas no momento da importação.

---

## 4. Backup

- **RN-13** — Antes de qualquer importação, o sistema **obrigatoriamente** cria um backup da planilha mestre.
- **RN-14** — Os backups são armazenados em um **diretório de backup configurável** pelo usuário (em Configurações). O diretório padrão é `~/Documents/ConcatExcel/Backups`.
- **RN-15** — Dentro do diretório de backup, os arquivos são organizados em **subdiretórios por nome da planilha mestre**:
  ```
  <backup_dir>/<nome_da_planilha>/<nome_da_planilha>_YYYY-MM-DD_HH-MM-SS.xlsx
  ```
- **RN-16** — São mantidos apenas os **últimos 10 backups** por planilha mestre. Backups mais antigos são excluídos automaticamente.
- **RN-17** — Se o backup **falhar** por qualquer motivo (permissão negada, disco cheio, arquivo não encontrado), uma mensagem de erro é exibida e o procedimento de importação é **cancelado imediatamente**, sem modificar a planilha mestre.

---

## 5. Importação

- **RN-18** — A importação só pode ser iniciada quando **os três elementos** estão selecionados: planilha mestre, planilha fonte e mapeamento.
- **RN-19** — Antes de importar qualquer linha, o sistema **valida o mapeamento**: verifica se todas as colunas fonte existem na planilha fonte e se todas as colunas destino existem na planilha mestre. Em caso de inconsistência, o erro é registrado no log e a importação é **cancelada** sem modificar nenhum arquivo.
- **RN-20** — O sistema detecta e **ignora linhas duplicadas**. Uma linha da planilha fonte é considerada duplicata se já existir na planilha mestre uma linha com os mesmos valores em todas as colunas mapeadas (destino).
- **RN-21** — Nenhum dado existente na planilha mestre é **sobrescrito ou removido**. A importação apenas **acrescenta** linhas novas ao final.
- **RN-22** — Durante a importação, o usuário visualiza uma **barra de progresso** e um **log em tempo real** com o status de cada linha processada.
- **RN-23** — Se a importação for concluída com sucesso, a planilha mestre é salva e uma mensagem de confirmação é exibida ao usuário.
- **RN-24** — Se ocorrer um erro durante a importação (após o backup), o erro é registrado no log, uma mensagem é exibida e a planilha mestre **não é salva** com dados parciais.

---

## 6. Configurações

- **RN-25** — O usuário pode configurar o **diretório de backup** a qualquer momento, via tela de Configurações.
- **RN-26** — O **tema da interface** (claro / escuro) é persistido entre sessões.
- **RN-27** — Todas as configurações são armazenadas localmente em `~/.concat-excel/settings.json`.
