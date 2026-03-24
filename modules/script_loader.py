"""
Script Loader — Carrega e registra scripts dinamicamente.
Cada script é descrito por um dicionário de metadados.
"""

from pathlib import Path

# Registro central dos scripts disponíveis.
# Para adicionar um novo script, basta incluir um novo dicionário nesta lista.
SCRIPTS_REGISTRY = [
    {
        "id": "comparar_amanco",
        "name": "Comparar Preços Amanco",
        "icon": "📊",
        "category": "Financeiro",
        "description": (
            "Compara preços entre uma planilha Excel e um arquivo PDF de "
            "fornecedor (Amanco). Gera relatório Excel com diferenças de "
            "quantidade e preço, incluindo formatação condicional."
        ),
        "module": "scripts.comparar_amanco",
        "inputs": [
            {
                "key": "excel_file",
                "label": "Arquivo Excel (.xlsx)",
                "type": "file_uploader",
                "file_types": ["xlsx", "xls"],
                "help": "Planilha com a lista de produtos e preços internos.",
            },
            {
                "key": "pdf_file",
                "label": "Arquivo PDF",
                "type": "file_uploader",
                "file_types": ["pdf"],
                "help": "PDF do fornecedor com preços de cotação.",
            },
        ],
        "outputs": ["dataframe", "excel_download", "chart"],
        "doc": """
## 📋 Comparador de Preços Amanco

### O que faz
Compara automaticamente os preços e quantidades de produtos 
entre sua **planilha interna (Excel)** e o **PDF de cotação** do fornecedor Amanco.

### Inputs necessários
| Input | Formato | Descrição |
|-------|---------|-----------| 
| Planilha Excel | `.xlsx` / `.xls` | Lista interna de produtos com colunas: Produto, Compra, Preço |
| PDF Fornecedor | `.pdf` | Cotação do fornecedor com tabela de preços |

### Output gerado
- **Tabela comparativa** com todas as diferenças encontradas
- **Gráfico de barras** com os itens que possuem maior divergência
- **Arquivo Excel** para download com formatação condicional (verde = OK, vermelho = divergente)

### Lógica especial
- Extrai códigos de 4-6 dígitos dos nomes de produtos
- Converte eletrodutos vendidos em rolo para preço unitário
- Aplica formatação condicional no arquivo gerado

> ⚠️ **Atenção:** Verifique se o PDF possui tabelas estruturadas. PDFs escaneados podem não funcionar corretamente.
""",
    },
    {
        "id": "sugestao_compras",
        "name": "Sugestão de Compras",
        "icon": "🛒",
        "category": "Compras",
        "description": (
            "Gera sugestões de compra por loja (PV09, PV13, PV30, PV37) "
            "com base em estoque, vendas dos últimos 6 meses, lead time "
            "e estoque de segurança. Inclui curva ABC/PQR e filtros por "
            "comprador e fornecedor."
        ),
        "module": "scripts.sugestao_compras",
        "multi_stage": True,
        "inputs": [
            {
                "key": "estoque_file",
                "label": "Planilha de Estoque (.xlsx)",
                "type": "file_uploader",
                "file_types": ["xlsx"],
                "help": "Arquivo Excel com abas: PRODUTO&TRIB, PRODUTO&COMPRADOR, PRODUTO&FORN., PRODUTO&LOJA, EMBALAGENS, LEADTIME.",
            },
            {
                "key": "venda_file",
                "label": "Planilha de Vendas (.xlsx)",
                "type": "file_uploader",
                "file_types": ["xlsx"],
                "help": "Arquivo Excel com abas: VENDA&DIA PV09, PV13, PV30, 2EM1.",
            },
            {
                "key": "entrada_file",
                "label": "Planilha de Entradas (.xlsx)",
                "type": "file_uploader",
                "file_types": ["xlsx"],
                "help": "Arquivo Excel com aba: PRODUTO&DTEMISSAO E P37.",
            },
        ],
        "outputs": ["dataframe", "excel_download"],
        "doc": """
## 🛒 Sugestão de Compras

### O que faz
Calcula automaticamente sugestões de compra por loja com base em:
- **Vendas dos últimos 6 meses** (média diária, desvio padrão)
- **Estoque atual** e pedidos pendentes
- **Lead time** (tempo de entrega + negociação + intervalo)
- **Estoque de Segurança** (Z-Score 1.645 = 95%)
- **Ponto de Pedido (PP)** e cobertura de +30 dias

### Fluxo de Uso
1. **Carregar dados** — Envie as 3 planilhas (Estoque, Vendas, Entradas)
2. **Filtrar** — Selecione Lojas, Compradores e Fornecedores
3. **Gerar relatórios** — Baixe os arquivos Excel por loja

### Inputs necessários
| Input | Formato | Descrição |
|-------|---------|-----------|
| Estoque | `.xlsx` | Abas de produto, tributação, comprador, fornecedor, loja, embalagem, leadtime |
| Vendas | `.xlsx` | Abas de venda por dia (PV09, PV13, PV30, 2EM1) |
| Entradas | `.xlsx` | Aba de entradas com data de emissão |

### Output gerado
- **Relatório Excel por loja** com sugestões PP e PP+30
- **Tabela comparativa** com métricas de venda, estoque, dias de cobertura
- **Curva ABC** (faturamento) e **PQR** (popularidade)
- **Margem no sistema** calculada automaticamente

### Regras especiais
- **Pisos**: Lead time fixo de 7 dias, cobertura de 14 dias
- **Miudezas**: Usa venda de 2EM1 ao invés do total
- **Abastecimento**: Sugere transferência do PV37 quando disponível
""",
    },
    {
        "id": "profissional_nota_mil",
        "name": "Profissional Nota Mil",
        "icon": "⭐",
        "category": "Externo",
        "description": (
            "Acesse o sistema Profissional Nota Mil — plataforma externa "
            "para avaliação e gestão de profissionais."
        ),
        "type": "external_link",
        "url": "https://profissionalnotamil.appmil.workers.dev/",
        "inputs": [],
        "outputs": [],
        "doc": """
## ⭐ Profissional Nota Mil

### O que é
Plataforma externa para avaliação e gestão de profissionais.

### Acesso
Clique no botão **"Acessar Site"** para abrir em uma nova aba.
""",
    },
]


def get_all_scripts():
    """Retorna todos os scripts registrados."""
    return SCRIPTS_REGISTRY


def get_script_by_id(script_id: str):
    """Retorna um script pelo seu ID."""
    for script in SCRIPTS_REGISTRY:
        if script["id"] == script_id:
            return script
    return None


def get_scripts_by_category():
    """Agrupa scripts por categoria."""
    categories = {}
    for script in SCRIPTS_REGISTRY:
        cat = script.get("category", "Outros")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(script)
    return categories


def discover_scripts():
    """
    Descobre novos scripts na pasta scripts/ que não estão registrados.
    Retorna lista de nomes de arquivo não registrados (para futuro uso).
    """
    scripts_dir = Path(__file__).parent.parent / "scripts"
    if not scripts_dir.exists():
        return []

    registered_modules = {s["module"].split(".")[-1] for s in SCRIPTS_REGISTRY if "module" in s}
    unregistered = []

    for py_file in scripts_dir.glob("*.py"):
        if py_file.stem.startswith("_"):
            continue
        if py_file.stem not in registered_modules:
            unregistered.append(py_file.stem)

    return unregistered
