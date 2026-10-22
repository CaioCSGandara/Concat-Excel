# Concat Excel

> Automatize a consolidação diária de planilhas Excel — sem esforço manual.

---

## O Problema

Um profissional recebe diariamente uma planilha de um cliente e precisa inserir seus dados em uma planilha mestre central. Feito manualmente, esse processo é repetitivo, demorado e sujeito a erros.

## A Solução

**Concat Excel** é uma aplicação desktop que automatiza esse fluxo:

1. Define-se **uma vez** qual é a planilha mestre e como as colunas se mapeiam
2. A cada dia, basta selecionar a planilha do dia e clicar em **Importar**
3. O sistema valida os dados, cria um backup automático e acrescenta apenas as linhas novas — sem duplicatas, sem perda de dados

---

## Funcionalidades

- 🗂️ **Planilha mestre persistente** — lembrada entre sessões, mesmo após reiniciar o computador
- 📄 **Planilha fonte por sessão** — selecionada a cada importação
- 🔗 **Mapeamentos reutilizáveis** — crie, edite e exclua configurações de colunas com nome
- 💾 **Backup automático** — cópia da planilha mestre criada antes de cada importação, com rotação dos últimos 10 arquivos por planilha
- ⏭️ **Deduplicação** — linhas já existentes são detectadas e ignoradas automaticamente
- 📊 **Progresso em tempo real** — barra de progresso e log linha a linha durante a importação
- 🌙 **Modo claro / escuro** — tema persistido entre sessões

---

## Documentação

| Documento | Descrição |
|---|---|
| [📋 Regras de Negócio](docs/business-rules.md) | Todas as regras que governam o comportamento do sistema |
| [⚙️ Documentação Técnica](docs/technical.md) | Arquitetura, módulos, decisões técnicas e guia de empacotamento |

---

## Como Executar

### Pré-requisitos

- Python 3.12+
- `python3-tk` instalado no sistema (Linux: `sudo apt install python3-tk`)

### Setup

```bash
# Clone ou extraia o projeto
cd concat-excel

# Crie o ambiente virtual (com acesso ao tkinter do sistema no Linux)
python3 -m venv .venv --system-site-packages
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Inicie o aplicativo
python main.py
```

### Gerar executável (.exe / binário)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "ConcatExcel" main.py
# Saída: dist/ConcatExcel (Linux/Mac) ou dist/ConcatExcel.exe (Windows)
```

---

## Stack

`Python 3.12` · `CustomTkinter` · `pandas` · `openpyxl` · `PyInstaller`
