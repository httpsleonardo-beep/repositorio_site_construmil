# 📂 Repositório de Scripts — Construmil

Plataforma web para execução de scripts Python com interface gráfica, construída com **Streamlit**.

## 🚀 Como Executar

### Pré-requisitos
- Python 3.10+
- pip

### Instalação

```bash
# Instale as dependências
pip install -r requirements.txt

# Execute a aplicação
streamlit run app.py
```

### Acesso
- **URL**: http://localhost:8501
- **Usuário**: `admin` | **Senha**: `admin123`
- **Usuário**: `leonardo` | **Senha**: `admin123`

> ⚠️ Altere as senhas padrão em `config/auth_config.yaml` antes de usar em produção.

---

## 📁 Estrutura do Projeto

```
repositorio_site_construmil/
├── app.py                        # Aplicação principal Streamlit
├── requirements.txt              # Dependências Python
├── README.md                     # Este arquivo
│
├── config/
│   └── auth_config.yaml          # Configurações de autenticação
│
├── assets/
│   ├── Logo.jpeg                 # Logo do sistema
│   └── style.css                 # CSS customizado
│
├── scripts/
│   ├── __init__.py
│   └── comparar_amanco.py        # Script: Comparador de preços Amanco
│
├── modules/
│   ├── __init__.py
│   ├── auth.py                   # Módulo de autenticação
│   ├── script_loader.py          # Carregador dinâmico de scripts
│   └── ui_components.py          # Componentes reutilizáveis de UI
│
└── logs/
    └── execution_log.csv         # Log de execuções
```

---

## ➕ Adicionar Novos Scripts

1. Crie o arquivo `.py` na pasta `scripts/`
2. Implemente a função `run(inputs: dict) -> dict`
3. Registre o script em `modules/script_loader.py` — lista `SCRIPTS_REGISTRY`
4. O sistema criará automaticamente a interface de execução

---

## 🛠️ Tecnologias

| Tecnologia | Versão | Uso |
|-----------|--------|-----|
| Streamlit | ≥ 1.32 | Framework web |
| streamlit-authenticator | ≥ 0.3.2 | Login / logout |
| streamlit-option-menu | ≥ 0.3.12 | Menu com ícones |
| Pandas | ≥ 2.0 | Manipulação de dados |
| Plotly | ≥ 5.18 | Gráficos interativos |
| pdfplumber | ≥ 0.10 | Leitura de PDFs |
| openpyxl | ≥ 3.1 | Geração de Excel |

---

## 📜 Licença

Uso interno — Construmil.
