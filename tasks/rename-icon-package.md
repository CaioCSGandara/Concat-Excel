# Task: Renomear, Adicionar Ícone e Empacotar para Windows

Este guia instrui o agente sobre como realizar as três tarefas de finalização do projeto **Concat Excel**.

> **Contexto do projeto:** aplicação desktop Python com CustomTkinter, empacotada via PyInstaller.  
> Raiz do projeto: `concat-excel/`

---

## Parte 1 — Trocar o Nome do Sistema

O nome "Concat Excel" aparece em dois lugares na UI e deve ser alterado em ambos.

### 1.1 — Título da barra de janela

**Arquivo:** [`app/ui/app_window.py`](../app/ui/app_window.py)  
**Linha 32:**

```python
# ANTES
_WINDOW_TITLE: str = "Concat Excel"

# DEPOIS
_WINDOW_TITLE: str = "Concatenador de Dados"
```

Essa constante é usada em `_setup_window()` via `self.title(self._WINDOW_TITLE)`.

### 1.2 — Texto na sidebar (logo)

**Arquivo:** [`app/ui/app_window.py`](../app/ui/app_window.py)  

```python
# ANTES
ctk.CTkLabel(
    title_frame,
    text="Concat Excel",
    ...
)

# DEPOIS
ctk.CTkLabel(
    title_frame,
    text="Concatenador de Dados",
    font=ctk.CTkFont(size=14, weight="bold"),
    ...
)
```

O subtítulo logo abaixo ("Importador de planilhas") também pode ser ajustado se necessário:

```python
text="Importador de planilhas",
```

### 1.3 — Diretório de configurações (opcional)

Se o nome interno da pasta de dados do usuário também deve mudar (atualmente `~/.concat-excel/`):

**Arquivo:** [`app/config/settings_manager.py`](../app/config/settings_manager.py)  
**Linha 16:**

```python
# ANTES
_APP_DIR: str = ".concat-excel"

# DEPOIS
_APP_DIR: str = ".concatenador-dados"   # use kebab-case, com ponto inicial
```

> ⚠️ Atenção: alterar esse valor fará o app não encontrar as configurações já salvas em `~/.concat-excel/`. Se o sistema já estiver em uso, faça a migração dos dados antes.

---

## Parte 2 — Adicionar Ícone ao Sistema

O ícone deve estar no formato `.ico` (Windows) e `.png` (sidebar da UI, opcional).

### 2.1 — Preparar o arquivo de ícone

1. Obtenha ou gere o ícone no formato `.ico` (256×256 px recomendado, com múltiplos tamanhos embutidos).
2. Salve em:
   ```
   concat-excel/assets/icon.ico
   ```
   Crie a pasta `assets/` na raiz se não existir:
   ```bash
   mkdir -p assets
   ```

### 2.2 — Ícone na janela (barra de título)

**Arquivo:** [`app/ui/app_window.py`](../app/ui/app_window.py)  
**Método `_setup_window()`**:

```python
def _setup_window(self) -> None:
    self.title(self._WINDOW_TITLE)
    self.geometry(self._WINDOW_SIZE)
    self.minsize(*self._WINDOW_MIN)

    # ── Ícone da janela ──────────────────────────────────
    import sys
    from pathlib import Path

    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base_path = Path(__file__).parent.parent.parent  # raiz do projeto

    icon_path = base_path / "assets" / "icon.ico"
    png_path = base_path / "assets" / "icon.png"

    if icon_path.exists():
        self.iconbitmap(str(icon_path))
    if png_path.exists():
        self._icon_photo = tk.PhotoImage(file=str(png_path))
        self.wm_iconphoto(True, self._icon_photo)
```

### 2.3 — Ícone na barra de tarefas do Windows (AppUserModelID)

No Windows, quando um script Python é executado via `python.exe`, o sistema operacional agrupa a janela sob o processo genérico do Python na barra de tarefas e exibe o ícone padrão do Python.  
Para exibir o ícone customizado na **barra de tarefas**, é necessário definir um `AppUserModelID` explícito no `main.py` antes de instanciar a janela:

```python
import sys
import ctypes

def _setup_windows_app_id() -> None:
    if sys.platform == "win32":
        app_id = "concat_excel.concatenador_dados.1.0"
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception:
            pass
```

Para rodar em desenvolvimento sem abrir a janela preta de console do terminal, use:
```powershell
.\.venv\Scripts\pythonw.exe main.py
```

### 2.4 — Ícone no empacotamento PyInstaller

O ícone precisa ser referenciado tanto na flag `--icon` quanto como dado embutido (`--add-data`). Veja a Parte 3.

---

## Parte 3 — Empacotar para Windows (.exe)

O empacotamento deve ser feito **em uma máquina Windows** (ou VM/Wine com Python instalado), pois o PyInstaller gera binários nativos para a plataforma em que é executado.

### 3.1 — Pré-requisitos (na máquina Windows)

```powershell
# Instalar Python 3.12 (inclui tkinter por padrão no Windows)
# Download: https://www.python.org/downloads/

# Criar e ativar ambiente virtual
python -m venv .venv
.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
pip install pyinstaller
```

### 3.2 — Comando de empacotamento

```powershell
pyinstaller `
  --onefile `
  --windowed `
  --name "ConcatenadorDeDados" `
  --icon "assets\icon.ico" `
  --add-data "assets\icon.ico;assets" `
  --add-data "assets\icon.png;assets" `
  main.py
```

| Flag | Descrição |
|---|---|
| `--onefile` | Gera um único `.exe` (mais fácil de distribuir) |
| `--windowed` | Suprime o terminal/console ao abrir o app |
| `--name` | Nome do arquivo `.exe` gerado |
| `--icon` | Ícone exibido no arquivo `.exe` e na barra de tarefas |
| `--add-data` | Embute os arquivos de ícone dentro do `.exe` |

---

## Resumo das Alterações

```
main.py
  → _setup_windows_app_id() (AppUserModelID para barra de tarefas no Windows)

app/ui/app_window.py
  → _WINDOW_TITLE = "Concatenador de Dados"
  → sidebar width=265 (evita truncamento do nome)
  → text="Concatenador de Dados" na CTkLabel
  → método _setup_window() → iconbitmap() e wm_iconphoto()

assets/
  icon.ico  → ícone do sistema (7 camadas multi-resolução)
  icon.png  → ícone em PNG (com padding recortado)
```
