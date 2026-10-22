# Documentação Técnica

Este documento descreve a arquitetura, os módulos e as decisões técnicas do projeto **Concat Excel**.

---

## Stack Tecnológica

| Camada | Tecnologia | Versão mínima |
|---|---|---|
| Linguagem | Python | 3.12 |
| UI | CustomTkinter | 5.2.2 |
| Manipulação de dados | pandas | 2.2.0 |
| Leitura/escrita de xlsx | openpyxl | 3.1.2 |
| Empacotamento | PyInstaller | 6.10.0 |

---

## Estrutura do Projeto

```
concat-excel/
├── main.py                          # Entry point
├── requirements.txt
├── docs/
│   ├── business-rules.md            # Regras de negócio
│   └── technical.md                 # Este documento
└── app/
    ├── models/
    │   └── models.py                # Dataclasses de domínio
    ├── config/
    │   └── settings_manager.py      # Persistência JSON
    ├── core/
    │   ├── backup_manager.py        # Gerenciamento de backups
    │   └── importer.py              # Motor de importação
    └── ui/
        ├── app_window.py            # Janela principal (CTk)
        ├── views/
        │   ├── home_view.py         # Tela de importação
        │   ├── mappings_view.py     # CRUD de mapeamentos
        │   └── settings_view.py     # Configurações
        └── dialogs/
            └── mapping_editor_dialog.py  # Dialog de edição de mapeamento
```

---

## Módulos

### `app/models/models.py`

Define as estruturas de dados centrais usando `dataclasses`:

| Classe | Responsabilidade |
|---|---|
| `ColumnMapping` | Um par `(source: str, target: str)` representando uma coluna fonte mapeada para uma coluna destino |
| `Mapping` | Conjunto nomeado de `ColumnMapping`, com `id` (UUID) e `name` gerado pelo usuário |
| `AppSettings` | Estado global persistido: `master_sheet_path`, `backup_dir`, `theme`, lista de `Mapping` |

---

### `app/config/settings_manager.py`

Gerencia a persistência de `AppSettings` em disco.

**Formato:** JSON  
**Localização:** `~/.concat-excel/settings.json`

> **Por que JSON?** Suporte nativo na stdlib Python (sem dependências extras), estrutura hierárquica (ideal para listas de mapeamentos), legível e editável manualmente.

**Interface pública:**

```python
class SettingsManager:
    def load(self) -> AppSettings: ...   # Carrega do disco; retorna padrão se ausente/corrompido
    def save(self, settings: AppSettings) -> None: ...  # Serializa e grava
```

O arquivo é criado automaticamente no primeiro uso. Erros de desserialização resultam em configurações padrão (nunca travam o app).

---

### `app/core/backup_manager.py`

Cria e rotaciona backups da planilha mestre antes de cada importação.

**Organização dos backups:**
```
<backup_dir>/
└── <nome_da_planilha>/
    ├── relatorio_2024-01-15_08-30-00.xlsx
    ├── relatorio_2024-01-16_08-31-10.xlsx
    └── ...  (máximo 10 arquivos por planilha)
```

**Interface pública:**

```python
class BackupManager:
    MAX_BACKUPS: int = 10

    def create_backup(self, master_path: str) -> Path:
        """Copia o arquivo e poda backups antigos. Lança OSError/FileNotFoundError em falha."""
```

A poda (`_prune_old_backups`) ordena os arquivos por `mtime` e remove os mais antigos até restar no máximo `MAX_BACKUPS`.

---

### `app/core/importer.py`

Motor de importação. Executa em uma **thread de background** para não travar a UI.

**Fluxo de execução:**

```
1. Carrega planilha mestre (pandas)
2. Carrega planilha fonte (pandas)
3. Valida mapeamento (todos os nomes de colunas existem?)
   └── Se inválido → cancela, registra erro no log
4. Indexa hashes de todas as linhas existentes na mestre (deduplicação)
5. Para cada linha da fonte:
   a. Monta novo_row com valores das colunas mapeadas
   b. Computa hash MD5 dos valores nas colunas destino
   c. Se hash já existe → ignora (duplicata)
   d. Se hash novo → adiciona à lista de linhas a inserir
6. Concatena novas linhas ao DataFrame da mestre
7. Salva planilha mestre com openpyxl
```

**Deduplicação:**

O hash é computado sobre os valores das colunas **destino** (mestre), ordenadas alfabeticamente, separadas por `|`:

```python
values = "|".join(str(row.get(col, "")) for col in sorted(target_columns))
hash   = hashlib.md5(values.encode("utf-8")).hexdigest()
```

**Tipos:**

```python
@dataclass
class ImportResult:
    success: bool
    rows_imported: int
    rows_skipped: int
    error_message: Optional[str]
    log_entries: list[str]

ProgressCallback = Callable[[float, str], None]
# float: progresso 0.0–1.0 (valor negativo indica erro)
# str:   mensagem para o log
```

---

### `app/ui/app_window.py`

Janela raiz (`CTk`). Gerencia:

- **Layout:** sidebar (230 px fixo) + área de conteúdo (expansível)
- **Navegação:** instanciação lazy das views; chama `view.refresh()` ao navegar
- **Tema:** toggle dark/light via `CTkSwitch`; persiste no `SettingsManager`
- **Persistência:** expõe `_persist_settings()` como callback passado a todas as views

---

### `app/ui/views/home_view.py`

Tela principal de importação. Responsabilidades:

- Exibe cards para seleção de planilha mestre (persistente), fonte (sessão) e mapeamento
- Controla estado do botão "Importar" (habilitado somente quando os 3 estão selecionados)
- Dispara importação em **thread background** com `threading.Thread(daemon=True)`
- Comunica progresso à UI via `queue.Queue` + polling com `widget.after(80ms)`
- Reseta a planilha fonte após importação concluída (RN-06)

**Threading:**

```
Thread principal (UI)          Thread background (importação)
      │                                  │
      │── start Thread ─────────────────>│
      │                                  │── BackupManager.create_backup()
      │<── after(80ms) ── poll queue ────│── Importer.import_data()
      │      │                           │      │── progress_queue.put(progress, msg)
      │      └── update progress bar     │
      │<────────────── ("done", result) ─┘
      │── handle_done()
```

---

### `app/ui/views/mappings_view.py`

CRUD de mapeamentos. Operações:

| Operação | Comportamento |
|---|---|
| Criar | Abre `MappingEditorDialog`; se confirmado, append em `settings.mappings` |
| Editar | Abre `MappingEditorDialog` com o mapping existente; edita in-place |
| Excluir | Confirmação via `messagebox.askyesno`; filtra da lista por `id` |

Após cada operação, chama `on_settings_change()` (persiste) e re-renderiza a lista.

---

### `app/ui/dialogs/mapping_editor_dialog.py`

`CTkToplevel` modal para criar/editar um mapeamento.

- **Colunas destino (mestre):** carregadas da planilha mestre atual (se configurada) via `pd.read_excel(..., nrows=0)`
- **Colunas fonte:** carregadas de um arquivo `.xlsx` de referência selecionado pelo usuário no próprio dialog
- **Pares de colunas:** lista scrollável de `(CTkComboBox fonte, CTkComboBox destino, botão remover)`
- **Resultado:** atributo `dialog.result: Optional[Mapping]` — `None` se cancelado

---

## Persistência de Dados

```
~/.concat-excel/
└── settings.json
```

**Exemplo completo:**

```json
{
  "master_sheet_path": "/home/usuario/Documentos/relatorio_mestre.xlsx",
  "backup_dir": "/home/usuario/Documents/ConcatExcel/Backups",
  "theme": "dark",
  "mappings": [
    {
      "id": "a1b2c3d4-...",
      "name": "Relatório Diário",
      "columns": [
        { "source": "Data",    "target": "Data Registro" },
        { "source": "Valor",   "target": "Valor Total"   },
        { "source": "Cliente", "target": "Nome Cliente"  }
      ]
    }
  ]
}
```

---

## Empacotamento (PyInstaller)

Para gerar o executável:

```bash
source .venv/bin/activate
pip install pyinstaller
pyinstaller --onefile --windowed --name "ConcatExcel" main.py
```

O binário gerado fica em `dist/ConcatExcel` (Linux/Mac) ou `dist/ConcatExcel.exe` (Windows).

> **Importante:** o `.venv` deve ter sido criado com `--system-site-packages` se o `tkinter` for instalado via sistema (Linux). No Windows, o `tkinter` já vem embutido no instalador oficial do Python.

---

## Padrões de Código

| Padrão | Descrição |
|---|---|
| Nomenclatura | `snake_case` para variáveis, funções e arquivos |
| Tipagem | Forte — sem uso de `Any` exceto em dados JSON deserializados |
| Docstrings | Google-style em todas as classes e métodos públicos |
| Formatação | PEP 8 |
| Modularidade | Uma responsabilidade por classe; UI completamente separada do domínio |
