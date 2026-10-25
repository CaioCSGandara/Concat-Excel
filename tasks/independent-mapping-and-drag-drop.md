# Task: Desvinculação de Planilhas e Reordenação por Arrastar (Drag and Drop) no Mapeamento

Este guia descreve os requisitos, a arquitetura e os passos de implementação para aprimorar o módulo de mapeamento de colunas do **Concat Excel**.

---

## 1. Contexto e Motivação

Atualmente, a criação/edição de mapeamentos depende da planilha mestre selecionada na tela principal (`HomeView`), e apenas a planilha fonte pode ser selecionada como referência no modal.  
Para planilhas corporativas com dezenas de colunas, esse fluxo é inflexível e trabalhoso:
1. Obriga o usuário a configurar a tela principal antes de poder criar mapeamentos reutilizáveis.
2. Não gera automaticamente a estrutura de mapeamento ao carregar os arquivos.
3. Não permite trocar posições de colunas facilmente para alinhamento rápido.

---

## 2. Requisitos da Feature

### 2.1 Desvinculação e Seletores Independentes
- O editor de mapeamento não deve depender da planilha mestre configurada na tela principal.
- No próprio editor de mapeamento, devem existir dois seletores de arquivo dedicados:
  - **Planilha de Origem (Fonte)**
  - **Planilha de Destino (Mestre)**
- Cada seletor permite carregar um arquivo `.xlsx`/`.xls` diretamente no diálogo e exibe o nome do arquivo e a quantidade de colunas lidas.

### 2.2 Geração Automática de Linhas de Mapeamento
- **Ao carregar a Planilha de Destino:**
  - São geradas linhas para todos os cabeçalhos da planilha de destino.
  - As posições correspondentes da coluna de origem ficam vazias (`""`).
- **Ao carregar a Planilha de Origem:**
  - Os cabeçalhos da planilha de origem preenchem a coluna de origem em ordem.
  - Caso a planilha de destino já tenha sido carregada, as colunas de origem são associadas linha a linha por ordem.
  - Se a planilha de origem tiver mais colunas que a de destino, novas linhas são criadas com o lado de destino vazio.
- **Caso apenas uma seja carregada:**
  - O lado carregado fica preenchido e o lado oposto fica com campos vazios prontos para preenchimento ou associação.
- **Adição e exclusão manual:**
  - O usuário ainda pode adicionar pares manualmente e excluir linhas individuais.

### 2.3 Clicar e Arrastar (Drag and Drop) para Troca de Lugar
- Permitir clicar e arrastar uma coluna para **trocá-la de lugar** com outra coluna.
- **Restrição estrita à mesma planilha:**
  - Colunas de Origem só podem ser arrastadas e trocadas com colunas de Origem.
  - Colunas de Destino só podem ser arrastadas e trocadas com colunas de Destino.
  - Não é permitido arrastar um campo de origem para destino (ou vice-versa).
- **Feedback visual:**
  - Ícone de pegador (*drag handle* `⠿`).
  - Destaque visual (borda / cor de foco) no slot de destino enquanto o mouse estiver sobre ele.
  - *Badge* flutuante acompanhando o ponteiro do mouse com o nome da coluna durante o arraste.
- **Botões de apoio (▲ / ▼):**
  - Botões para subir/descer um nível para trocas pontuais rápidas em listas longas.

### 2.4 Salvamento e Validação
- Apenas pares com ambos os lados preenchidos (origem e destino) são salvos no `Mapping`.
- Campos que permanecerem vazios são desconsiderados no salvamento, permitindo que o usuário mantenha espaços vazios durante o alinhamento sem gerar erros.
- É exigido nome do mapeamento e pelo menos um par completo para salvar.

---

## 3. Arquivos Modificados / Impactados

1. `app/ui/dialogs/mapping_editor_dialog.py`:
   - Adicionar seletores de Origem e Destino independentes.
   - Implementar método de auto-população assimétrica de colunas.
   - Implementar subsistema de Drag and Drop com eventos Tkinter (`<ButtonPress-1>`, `<B1-Motion>`, `<ButtonRelease-1>`) e botões de reordenação.
2. `app/ui/views/mappings_view.py`:
   - Atualizar a instanciação de `MappingEditorDialog` para refletir o desacoplamento.
3. `docs/business-rules.md`:
   - Atualizar regras de negócio (RN-08, RN-11, etc.).
4. `docs/technical.md`:
   - Atualizar a documentação técnica e diagramas/descrições de fluxo de UI.

---

## 4. Plano de Testes e Validação
- Carregar apenas planilha de destino: verificar se colunas de destino são criadas e origem fica vazia.
- Carregar apenas planilha de origem: verificar se colunas de origem são criadas e destino fica vazia.
- Carregar destino com 5 colunas e origem com 3 colunas: verificar se as 3 primeiras alinham e as 2 últimas têm origem vazia.
- Carregar origem com 5 colunas e destino com 3 colunas: verificar se 5 linhas existem, com as 2 últimas tendo destino vazio.
- Arrastar origem para outra origem: verificar troca exata de valores.
- Arrastar destino para outro destino: verificar troca exata de valores.
- Tentar arrastar origem para destino: verificar que a operação é bloqueada sem efeitos colaterais.
- Salvar mapeamento e verificar que os dados persistem em `settings.json`.
