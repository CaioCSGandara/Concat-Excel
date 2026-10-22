# Task: Renomear, Adicionar Ícone e Empacotar para Windows

Este guia instrui o agente sobre como realizar as três tarefas de finalização do projeto **Concat Excel**.

> **Contexto do projeto:** aplicação desktop Python com CustomTkinter, empacotada via PyInstaller.  
> Raiz do projeto: `concat-excel/`

---

## Parte 1 — Trocar o Nome do Sistema

O nome "Concat Excel" aparece em dois lugares na UI e deve ser alterado em ambos.

### 1.1 — Título da barra de janela

**Arquivo:** [`app/ui/app_window.py`](../app/ui/app_window.py)  
**Linha 29:**

```python
# ANTES
_WINDOW_TITLE: str = "Concat Excel"

# DEPOIS (substitua pelo novo nome)
_WINDOW_TITLE: str = "Novo Nome Aqui"
```

Essa constante é usada em `_setup_window()` (linha 52) via `self.title(self._WINDOW_TITLE)`. Alterar apenas a constante é suficiente.

### 1.2 — Texto na sidebar (logo)

**Arquivo:** [`app/ui/app_window.py`](../app/ui/app_window.py)  
**Linha 88:**

```python
# ANTES
ctk.CTkLabel(
    title_frame,
    text="Concat Excel",       # ← alterar aqui
    ...
)

# DEPOIS
ctk.CTkLabel(
    title_frame,
    text="Novo Nome Aqui",     # ← novo nome
    ...
)
```

O subtítulo logo abaixo ("Importador de planilhas") está na **linha 94** e também pode ser ajustado se necessário:

```python
text="Importador de planilhas",  # linha 94 — opcional alterar
```

### 1.3 — Diretório de configurações (opcional)

Se o nome interno da pasta de dados do usuário também deve mudar (atualmente `~/.concat-excel/`):

**Arquivo:** [`app/config/settings_manager.py`](../app/config/settings_manager.py)  
**Linha 16:**

```python
# ANTES
_APP_DIR: str = ".concat-excel"

# DEPOIS
_APP_DIR: str = ".novo-nome"   # use kebab-case, com ponto inicial
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
**Método `_setup_window()`** (a partir da linha 51). Adicione `self.iconbitmap(...)` após `self.title(...)`:

```python
def _setup_window(self) -> None:
    self.title(self._WINDOW_TITLE)
    self.geometry(self._WINDOW_SIZE)
    self.minsize(*self._WINDOW_MIN)

    # ── Ícone da janela ──────────────────────────────────
    import sys
    from pathlib import Path

    if getattr(sys, "frozen", False):
        # Executando como .exe gerado pelo PyInstaller
        base_path = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        # Executando em desenvolvimento
        base_path = Path(__file__).parent.parent.parent  # raiz do projeto

    icon_path = base_path / "assets" / "icon.ico"
    if icon_path.exists():
        self.iconbitmap(str(icon_path))
```

> O bloco `sys.frozen` é necessário porque o PyInstaller extrai os assets para um diretório temporário (`_MEIPASS`) durante a execução do `.exe`.

### 2.3 — Ícone no empacotamento PyInstaller

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
  --name "NomeDoSistema" `
  --icon "assets\icon.ico" `
  --add-data "assets\icon.ico;assets" `
  main.py
```

| Flag | Descrição |
|---|---|
| `--onefile` | Gera um único `.exe` (mais fácil de distribuir) |
| `--windowed` | Suprime o terminal/console ao abrir o app |
| `--name` | Nome do arquivo `.exe` gerado |
| `--icon` | Ícone exibido no arquivo `.exe` e na barra de tarefas |
| `--add-data` | Embute o arquivo de ícone dentro do `.exe` (necessário para `iconbitmap` funcionar) |

> **Separador de path no Windows:** use `;` em `--add-data` (Linux/Mac usam `:`).

### 3.3 — Saída

O executável gerado estará em:
```
dist\NomeDoSistema.exe
```

### 3.4 — Testar antes de distribuir

```powershell
.\dist\NomeDoSistema.exe
```

Verifique:
- [ ] Janela abre sem console
- [ ] Ícone aparece na barra de título e na barra de tarefas
- [ ] Nome correto na barra de título
- [ ] Configurações são salvas em `%USERPROFILE%\.concat-excel\settings.json` (ou novo nome)
- [ ] Seleção de arquivo `.xlsx` funciona via diálogo de arquivo
- [ ] Backup é criado corretamente
- [ ] Importação funciona de ponta a ponta

### 3.5 — Troubleshooting comum

| Problema | Causa provável | Solução |
|---|---|---|
| Ícone não aparece na janela | Path do `.ico` errado no `_MEIPASS` | Verifique o bloco `sys.frozen` em `_setup_window` |
| App abre e fecha imediatamente | Exceção não tratada | Remova `--windowed` temporariamente para ver o traceback no console |
| `ModuleNotFoundError` no `.exe` | Dependência oculta não detectada | Adicione `--hidden-import nome_do_modulo` ao comando |
| Antivírus bloqueia o `.exe` | Falso positivo comum com PyInstaller | Use `--onedir` em vez de `--onefile` (menos suspeito) |

---

## Resumo das Alterações

```
app/ui/app_window.py
  linha 29  → _WINDOW_TITLE (título da janela)
  linha 88  → text= na CTkLabel (sidebar)
  método _setup_window() → adicionar iconbitmap()

app/config/settings_manager.py
  linha 16  → _APP_DIR (pasta de dados — somente se necessário)

assets/
  icon.ico  → ícone do sistema (criar pasta e arquivo)
```
