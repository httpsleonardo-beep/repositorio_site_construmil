import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image
import threading
import sys
import os
import pandas as pd
import numpy as np
import datetime
import math
from dateutil.relativedelta import relativedelta
import traceback
import unicodedata
import re
from openpyxl.styles import PatternFill, Border, Side
from openpyxl.utils import get_column_letter
import warnings

# Ignorar avisos do Excel/Pandas
warnings.simplefilter("ignore")


# =============================================================================
# REDIRECIONADOR DE PRINT SEGURO E THREAD-SAFE (PROTETOR DE PRINT)
# =============================================================================
class SafePrintRedirector:
    """ Captura prints e erros para evitar crash em executáveis --noconsole e threads """

    def __init__(self, widget=None):
        self.widget = widget
        self.buffer = []

    def write(self, s):
        if self.widget:
            # Usa o .after para garantir que a atualização ocorra na thread principal
            try:
                self.widget.after(0, self._update_widget, s)
            except:
                pass
        else:
            self.buffer.append(s)

        # Tenta escrever no console original se ele existir (útil para debug no PyCharm)
        if sys.__stdout__ is not None:
            sys.__stdout__.write(s)

    def _update_widget(self, s):
        try:
            self.widget.configure(state="normal")
            self.widget.insert("end", s)
            self.widget.see("end")
            self.widget.configure(state="disabled")
        except:
            pass

    def flush(self):
        if sys.__stdout__ is not None:
            sys.__stdout__.flush()

    def set_widget(self, widget):
        """ Acopla o widget de log e descarrega o que foi printado antes dele existir """
        self.widget = widget
        if self.buffer:
            temp_content = "".join(self.buffer)
            self.buffer = []
            self.write(temp_content)


# ATIVAÇÃO IMEDIATA DO PROTETOR (Crucial para o executável não dar erro de NoneType)
safe_redirector = SafePrintRedirector()
sys.stdout = safe_redirector
sys.stderr = safe_redirector


# =============================================================================
# FUNÇÕES DE RECURSO
# =============================================================================
def resource_path(relative_path):
    """ Retorna o caminho absoluto para o recurso, funciona para dev e para PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# =============================================================================
# CONSTANTES VISUAIS
# =============================================================================
COLOR_PRIMARY = "#006cb5"
COLOR_SECONDARY = "#91d8f6"
COLOR_DANGER = "#ec3237"
COLOR_BG = "#fefefe"
COLOR_DARK = "#0A1931"
Z_SCORE = 1.645


# =============================================================================
# LÓGICA DE NEGÓCIO (SANEAMENTO E CÁLCULO)
# =============================================================================

def clean_column_names(df):
    """Corrige nomes de colunas."""
    rename_map = {}
    expected_names = {
        "Código Produto": ["CÃ³digo Produto", "Codigo Produto"],
        "Produto : Tributação": ["Produto : TributaÃ§Ã£o"],
        "Produto : Comprador": ["Produto : Comprador"],
        "Produto : Fornecedor Principal": ["Produto : Fornecedor Principal"],
        "Produto : Empresa": ["Produto : Empresa"],
        "Produto : Dia": ["Produto : Dia"],
        "Produto : Data Emissão": ["Produto : Data EmissÃ£o"],
        "Preço Vda Unitário": ["PreÃ§o Vda UnitÃ¡rio", "Preço Vda Unitário"],
        "Custo Liq. Unitário": ["Custo Liq. UnitÃ¡rio", "Custo Liq. Unitário"],
        "Quantidade em Estoque": ["Quantidade em Estoque"],
        "Qtd. Pend. Ped.Compra": ["Qtd. Pend. Ped.Compra"],
        "Lead time": ["Lead time"],
        "Lead time CD": ["Lead time CD"],
        "Tempo de Negociação": ["Tempo de NegociaÃ§Ã£o"],
        "Intervalo de compra": ["Intervalo de compra"],
        "Miudeza?": ["Miudeza?"],
        "Venda Quantidade": ["Venda Quantidade"],
        "Embalagem": ["Embalagem"],
        "Quantidade": ["Quantidade"],
        "Total do Produto": ["Total do Produto"],
        "Abastece?": ["Abastece?"],
        "Ativo?": ["Ativo?"]
    }
    current_columns = df.columns.tolist()
    for correct_name, possible_encoded_names in expected_names.items():
        if correct_name in current_columns:
            continue
        for encoded_name in possible_encoded_names:
            if encoded_name in current_columns:
                rename_map[encoded_name] = correct_name
                break
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def clean_number_br_strict(val):
    if pd.isna(val) or val == '': return 0.0
    val_str = str(val).strip()
    if val_str.endswith('.000'):
        val_str = val_str[:-4]
    elif val_str.endswith('.00'):
        val_str = val_str[:-3]
    elif val_str.endswith('.0'):
        val_str = val_str[:-2]
    if ',' in val_str:
        val_str = val_str.replace('.', '').replace(',', '.')
    elif '.' in val_str:
        parts = val_str.split('.')
        if len(parts) > 1 and len(parts[-1]) == 3: val_str = val_str.replace('.', '')
    try:
        return float(val_str)
    except:
        return 0.0


def safe_load_excel(file_path, sheet_name, usecols=None):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str)
        df = clean_column_names(df)
        if usecols:
            for col in usecols:
                if col not in df.columns: df[col] = np.nan
            df = df[[c for c in usecols if c in df.columns]]
        return df
    except Exception as e:
        print(f"Aviso: Aba '{sheet_name}' não encontrada ou erro na leitura: {e}")
        return pd.DataFrame()


def convert_code(df, col_name="Código Produto"):
    if col_name in df.columns:
        df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
        df = df.dropna(subset=[col_name])
        df[col_name] = df[col_name].astype(int)
    return df


def split_colon_column(df, column_name, new_col_1, new_col_2):
    if column_name in df.columns:
        df[column_name] = df[column_name].astype(str)
        df_split = df[column_name].str.split(':', n=1, expand=True)
        df[new_col_1] = df_split[0].str.strip()
        df[new_col_2] = df_split[1].str.strip() if df_split.shape[1] > 1 else np.nan
    return df


def get_last_6_months_range():
    today = datetime.date.today()
    end_date = today.replace(day=1) - datetime.timedelta(days=1)
    start_date = (end_date - relativedelta(months=5)).replace(day=1)
    return start_date, end_date


def load_all_data_dynamic(path_estoque, path_venda, path_entrada):
    print("Carregando dados das abas específicas...")
    data = {}
    load = lambda f, s, c: convert_code(safe_load_excel(f, s, usecols=c))

    # ESTOQUE
    data['trib'] = load(path_estoque, "PRODUTO&TRIB E P37",
                        ["Código Produto", "Produto : Tributação", "Preço Vda Unitário", "Custo Liq. Unitário"])
    data['comp'] = load(path_estoque, "PRODUTO&COMPRADOR E P37", ["Código Produto", "Produto : Comprador"])
    data['forn'] = load(path_estoque, "PRODUTO&FORN. E P37", ["Código Produto", "Produto : Fornecedor Principal"])
    data['loja'] = load(path_estoque, "PRODUTO&LOJA",
                        ["Código Produto", "Produto : Empresa", "Quantidade em Estoque", "Qtd. Pend. Ped.Compra"])
    data['emb'] = load(path_estoque, "EMBALAGENS", ["Código Produto", "Produto", "Embalagem"])
    data['lead'] = load(path_estoque, "LEADTIME",
                        ["Código Produto", "Produto : Fornecedor Principal", "Lead time", "Lead time CD",
                         "Tempo de Negociação", "Intervalo de compra", "Miudeza?", "Abastece?", "Ativo?"])

    # VENDAS
    abas = {'venda_09': "VENDA&DIA PV09", 'venda_13': "VENDA&DIA PV13", 'venda_30': "VENDA&DIA PV30",
            'venda_2em1': "VENDA&DIA 2EM1"}
    for k, v in abas.items():
        data[k] = load(path_venda, v, ["Código Produto", "Produto : Dia", "Venda Quantidade"])

    # ENTRADAS
    data['entrada'] = load(path_entrada, "PRODUTO&DTEMISSAO E P37",
                           ["Código Produto", "Produto : Data Emissão", "Quantidade", "Total do Produto"])

    print("Leitura das planilhas concluída.")
    return data


def preprocess_data(data):
    print("Pré-processando e corrigindo números...")
    if 'trib' in data and not data['trib'].empty: data['trib'] = split_colon_column(data['trib'],
                                                                                    "Produto : Tributação", "Produto",
                                                                                    "Tributação")
    if 'comp' in data and not data['comp'].empty: data['comp'] = split_colon_column(data['comp'], "Produto : Comprador",
                                                                                    "Produto", "Comprador")
    if 'forn' in data and not data['forn'].empty: data['forn'] = split_colon_column(data['forn'],
                                                                                    "Produto : Fornecedor Principal",
                                                                                    "Produto", "Fornecedor Principal")
    if 'loja' in data and not data['loja'].empty: data['loja'] = split_colon_column(data['loja'], "Produto : Empresa",
                                                                                    "Produto", "Empresa")
    if 'lead' in data and not data['lead'].empty: data['lead'] = split_colon_column(data['lead'],
                                                                                    "Produto : Fornecedor Principal",
                                                                                    "Produto",
                                                                                    "Fornecedor Principal (Lead)")

    numeric_cols_map = {'trib': ['Preço Vda Unitário', 'Custo Liq. Unitário'],
                        'loja': ['Quantidade em Estoque', 'Qtd. Pend. Ped.Compra'],
                        'lead': ['Lead time', 'Lead time CD', 'Tempo de Negociação', 'Intervalo de compra'],
                        'entrada': ['Quantidade', 'Total do Produto'], 'emb': ['Embalagem']}
    for key, cols in numeric_cols_map.items():
        if key in data and not data[key].empty:
            for col in cols:
                if col in data[key].columns: data[key][col] = data[key][col].apply(clean_number_br_strict)

    start_date, end_date = get_last_6_months_range()
    for key in ['venda_09', 'venda_13', 'venda_30', 'venda_2em1']:
        if key not in data or data[key].empty: continue
        df = data[key]
        if "Venda Quantidade" in df.columns: df["Venda Quantidade"] = df["Venda Quantidade"].apply(
            clean_number_br_strict)
        if "Produto : Dia" in df.columns:
            df = split_colon_column(df, "Produto : Dia", "Produto", "Dia_Str")
            df['Dia_Limpa'] = df['Dia_Str'].astype(str).str.extract(r'(\d{2}/\d{2}/\d{4})')
            df['Dia'] = pd.to_datetime(df['Dia_Limpa'], format='%d/%m/%Y', errors='coerce')
            df = df.dropna(subset=['Dia'])
            data[key] = df[(df['Dia'] >= pd.to_datetime(start_date)) & (df['Dia'] <= pd.to_datetime(end_date))].copy()

    if 'entrada' in data and not data['entrada'].empty:
        df = data['entrada']
        if "Produto : Data Emissão" in df.columns:
            df = split_colon_column(df, "Produto : Data Emissão", "Produto", "Data_Emissao_Str")
            df['Data_Emissao_Limpa'] = df['Data_Emissao_Str'].astype(str).str.extract(r'(\d{2}/\d{2}/\d{4})')
            df['Data Emissão'] = pd.to_datetime(df['Data_Emissao_Limpa'], format='%d/%m/%Y', errors='coerce')
            data['entrada'] = df.dropna(subset=['Data Emissão', 'Código Produto'])

    if 'lead' in data and not data['lead'].empty:
        for col in ['Miudeza?', 'Abastece?', 'Ativo?']:
            if col in data['lead'].columns:
                data['lead'][col] = data['lead'][col].astype(str).str.upper().str[0].replace(
                    {'S': 'S', 'N': 'N'}).fillna('N' if col != 'Ativo?' else 'S')
            else:
                data['lead'][col] = 'S' if col == 'Ativo?' else 'N'

    if 'loja' in data and not data['loja'].empty:
        data['loja_pivot'] = data['loja'].pivot_table(index='Código Produto', columns='Empresa',
                                                      values=['Quantidade em Estoque', 'Qtd. Pend. Ped.Compra'],
                                                      aggfunc='sum').fillna(0)
        data['loja_pivot'].columns = [f'{val.replace(" ", "_")}_{emp}' for val, emp in data['loja_pivot'].columns]
    else:
        data['loja_pivot'] = pd.DataFrame()

    print("Pré-processamento concluído.")
    return data


def calculate_sales_stats(df_venda, start_date, end_date):
    cols_meses = [f'Venda_{(start_date + relativedelta(months=i)).strftime("%Y-%m")}' for i in range(6)]
    cols_stats = ['Média venda/dia', 'Std Dev Venda', 'Total Venda 6m', 'Média venda/mês']
    if df_venda is None or df_venda.empty: return pd.DataFrame(columns=cols_stats + cols_meses)

    df_venda_dia = df_venda.groupby(['Código Produto', 'Dia'])['Venda Quantidade'].sum().reset_index()
    if df_venda_dia.empty: return pd.DataFrame(columns=cols_stats + cols_meses)

    idx = pd.MultiIndex.from_product([df_venda_dia['Código Produto'].unique(), pd.date_range(start_date, end_date)],
                                     names=['Código Produto', 'Dia'])
    df_full = df_venda_dia.set_index(['Código Produto', 'Dia']).reindex(idx, fill_value=0).reset_index()

    stats = df_full.groupby('Código Produto')['Venda Quantidade'].agg(['mean', 'std']).rename(
        columns={'mean': 'Média venda/dia', 'std': 'Std Dev Venda'}).fillna(0)

    df_venda['AnoMes'] = df_venda['Dia'].dt.to_period('M')
    mensal = df_venda.groupby(['Código Produto', 'AnoMes'])['Venda Quantidade'].sum().unstack(fill_value=0)
    mensal.columns = [f'Venda_{str(c)}' for c in mensal.columns]

    curr = start_date
    for i in range(6):
        cname = f'Venda_{curr.strftime("%Y-%m")}'
        if cname not in mensal.columns: mensal[cname] = 0
        curr += relativedelta(months=1)

    cols_ok = [c for c in cols_meses if c in mensal.columns]
    mensal['Total Venda 6m'] = mensal[cols_ok].sum(axis=1) if cols_ok else 0
    mensal['Média venda/mês'] = mensal['Total Venda 6m'] / 6

    return stats.join(mensal, how='outer').fillna(0)


def get_last_purchase_info(df_entrada):
    if df_entrada is None or df_entrada.empty: return pd.DataFrame(
        columns=['Data Últ Compra', 'Qntde últ compra', 'Valor de compra'])
    df = df_entrada.sort_values(by='Data Emissão', ascending=False).drop_duplicates(subset='Código Produto',
                                                                                    keep='first').copy()
    df['Valor de compra'] = 0.0
    mask = df['Quantidade'] > 0
    df.loc[mask, 'Valor de compra'] = df.loc[mask, 'Total do Produto'] / df.loc[mask, 'Quantidade']
    df = df.rename(columns={'Data Emissão': 'Data Últ Compra', 'Quantidade': 'Qntde últ compra'})
    return df.set_index('Código Produto')[['Data Últ Compra', 'Qntde últ compra', 'Valor de compra']]


def calculate_global_abc_pqr(df_master):
    sales_cols = [col for col in df_master.columns if col.startswith('Total Venda 6m_')]
    price_col = 'Preço Vda Unitário'
    if price_col not in df_master.columns: df_master[price_col] = 0

    df_master['Qtd Total Global'] = df_master[sales_cols].sum(axis=1)
    df_master['Faturamento Global'] = df_master[price_col] * df_master['Qtd Total Global']

    df_master = df_master.sort_values(by='Faturamento Global', ascending=False).reset_index(drop=True)
    df_master['Fat Acumulado Global'] = df_master['Faturamento Global'].cumsum()
    fat_total = df_master['Faturamento Global'].sum()
    df_master['Fat Pct Global'] = df_master['Fat Acumulado Global'] / fat_total if fat_total > 0 else 0
    df_master['Curva'] = 'C'
    df_master.loc[df_master['Fat Pct Global'] <= 0.7, 'Curva'] = 'A'
    df_master.loc[(df_master['Fat Pct Global'] > 0.7) & (df_master['Fat Pct Global'] <= 0.9), 'Curva'] = 'B'

    df_master = df_master.sort_values(by='Qtd Total Global', ascending=False).reset_index(drop=True)
    df_master['Qtd Acumulada Global'] = df_master['Qtd Total Global'].cumsum()
    qtd_total = df_master['Qtd Total Global'].sum()
    df_master['Qtd Pct Global'] = df_master['Qtd Acumulada Global'] / qtd_total if qtd_total > 0 else 0
    df_master['Popularidade'] = 'R'
    df_master.loc[df_master['Qtd Pct Global'] <= 0.7, 'Popularidade'] = 'P'
    df_master.loc[(df_master['Qtd Pct Global'] > 0.7) & (df_master['Qtd Pct Global'] <= 0.9), 'Popularidade'] = 'Q'

    return df_master


def build_master_product_table(data, start_date, end_date):
    print("Construindo tabela mestre...")
    if 'trib' not in data or data['trib'].empty: return pd.DataFrame()

    df = data['trib'].drop_duplicates(subset='Código Produto').set_index('Código Produto')

    def join_part(main, key, cols):
        if key in data and not data[key].empty:
            part = data[key].drop_duplicates(subset='Código Produto').set_index('Código Produto')
            valid = [c for c in cols if c in part.columns]
            return main.join(part[valid])
        return main

    df = join_part(df, 'comp', ['Comprador'])
    df = join_part(df, 'forn', ['Fornecedor Principal'])
    df = join_part(df, 'emb', ['Embalagem'])
    df = join_part(df, 'lead',
                   ['Lead time', 'Lead time CD', 'Tempo de Negociação', 'Intervalo de compra', 'Miudeza?', 'Abastece?',
                    'Ativo?', 'Fornecedor Principal (Lead)'])

    if 'loja_pivot' in data: df = df.join(data['loja_pivot'])
    df = df.join(get_last_purchase_info(data.get('entrada')))

    sales_dfs = {'PV09': data.get('venda_09'), 'PV13': data.get('venda_13'), 'PV30': data.get('venda_30'),
                 '2EM1': data.get('venda_2em1')}
    for store, df_venda in sales_dfs.items():
        if df_venda is not None:
            stats = calculate_sales_stats(df_venda, start_date, end_date)
            stats.columns = [f'{col}_{store}' for col in stats.columns]
            df = df.join(stats)

    df['Média venda/dia_Total'] = df[[c for c in df.columns if 'Média venda/dia_' in c]].fillna(0).sum(axis=1)
    df['Std Dev Venda_Total'] = np.sqrt(
        (df[[c for c in df.columns if 'Std Dev Venda_' in c]].fillna(0) ** 2).sum(axis=1))

    meses = [f'Venda_{(start_date + relativedelta(months=i)).strftime("%Y-%m")}' for i in range(6)]
    for mes in meses:
        df[f'{mes}_Total'] = df[[c for c in df.columns if c.startswith(mes) and c != f'{mes}_Total']].fillna(0).sum(
            axis=1)

    df['Total Venda 6m_Total'] = df[[f'{m}_Total' for m in meses]].sum(axis=1)
    df['Média venda/mês_Total'] = df['Total Venda 6m_Total'] / 6

    extras_est = [c for c in df.columns if
                  'Quantidade_em_Estoque_' in c and not any(l in c for l in ['PV09', 'PV13', 'PV30', 'PV37'])]
    extras_pend = [c for c in df.columns if
                   'Qtd._Pend._Ped.Compra_' in c and not any(l in c for l in ['PV09', 'PV13', 'PV30', 'PV37'])]

    if extras_est:
        if 'Quantidade_em_Estoque_2EM1' not in df.columns: df['Quantidade_em_Estoque_2EM1'] = 0.0
        df['Quantidade_em_Estoque_2EM1'] += df[extras_est].sum(axis=1)
    if extras_pend:
        if 'Qtd._Pend._Ped.Compra_2EM1' not in df.columns: df['Qtd._Pend._Ped.Compra_2EM1'] = 0.0
        df['Qtd._Pend._Ped.Compra_2EM1'] += df[extras_pend].sum(axis=1)

    rename_dict = {}
    for s in ['PV09', 'PV13', 'PV30', 'PV37', '2EM1']:
        if f'Quantidade_em_Estoque_{s}' in df.columns: rename_dict[f'Quantidade_em_Estoque_{s}'] = f'Estoque_{s}'
        if f'Qtd._Pend._Ped.Compra_{s}' in df.columns: rename_dict[f'Qtd._Pend._Ped.Compra_{s}'] = f'Pendente_{s}'
    df = df.rename(columns=rename_dict)

    df_temp = df.reset_index().copy()
    df_temp['Is_Colorante'] = df_temp['Produto'].str.contains('COLORANTE', case=False, na=False, regex=True)

    print("Calculando ABC Global...")
    df_all = calculate_global_abc_pqr(df_temp.copy()).set_index('Código Produto')

    df_no_color = df_temp[~df_temp['Is_Colorante']].copy()
    if not df_no_color.empty:
        df_filtered = calculate_global_abc_pqr(df_no_color).set_index('Código Produto')
        cols_map = {c: f'{c} (s/ Colorante)' for c in ['Curva', 'Popularidade', 'Qtd Total Global']}
        df_filtered = df_filtered.rename(columns=cols_map)
        df_final = df_all.join(df_filtered[cols_map.values()], how='left')
    else:
        df_final = df_all

    return df_final.fillna(0)


def pre_calculate_pv37_demand(df):
    cols_check = ['Estoque_PV37', 'Pendente_PV37', 'Média venda/dia_2EM1', 'Std Dev Venda_2EM1']
    for c in cols_check:
        if c not in df.columns: df[c] = 0.0

    lt_cols = ['Lead time', 'Lead time CD', 'Tempo de Negociação', 'Intervalo de compra']
    for c in lt_cols:
        if c not in df.columns: df[c] = 0.0

    df['L_Compra'] = df[lt_cols].sum(axis=1)
    ss = Z_SCORE * df['Std Dev Venda_2EM1'] * np.sqrt(df['L_Compra'].clip(lower=0))
    pp = (df['Média venda/dia_2EM1'] * df['L_Compra']) + ss
    total_demand = pp + (df['Média venda/dia_2EM1'] * 30)

    df['Stock_Available_Transfer'] = (df['Estoque_PV37'] - total_demand).clip(lower=0)
    return df


def calculate_suggestions(df, store, start_date, end_date):
    print(f"Calculando sugestões para {store}...")

    # Garante que 'Código Produto' está na coluna e não no index
    if 'Código Produto' not in df.columns and df.index.name == 'Código Produto':
        df = df.reset_index()

    # Nomes dos meses para colunas
    col_names_display = []
    current_month_dt = start_date
    meses_pt = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro',
                'Novembro', 'Dezembro']

    for i in range(6):
        col_name_friendly = meses_pt[current_month_dt.month - 1] if start_date else f"Mês {i + 1}"
        col_names_display.append(col_name_friendly)
        if start_date: current_month_dt += relativedelta(months=1)

    if df.empty:
        return pd.DataFrame()

    # Prepara métricas
    for suffix in ['_Total', '_2EM1', f'_{store}']:
        for metric in ['Média venda/dia', 'Std Dev Venda', 'Total Venda 6m', 'Média venda/mês']:
            col_name = f'{metric}{suffix}'
            if col_name not in df.columns: df[col_name] = 0.0

    # Lógica de vendas e estoque
    if store == 'PV37':
        mask_m = df['Miudeza?'] == 'S'
        df['mv_dia_calc'] = np.where(mask_m, df.get('Média venda/dia_2EM1', 0), df.get('Média venda/dia_Total', 0))
        df['sd_venda_calc'] = np.where(mask_m, df.get('Std Dev Venda_2EM1', 0), df.get('Std Dev Venda_Total', 0))
        df['L_calc'] = df[['Lead time', 'Tempo de Negociação', 'Intervalo de compra']].sum(axis=1)

        cols_est_global = [f'Estoque_{s}' for s in ['PV09', 'PV13', 'PV30', 'PV37', '2EM1'] if
                           f'Estoque_{s}' in df.columns]
        df['Estoque_Total_Global'] = df[cols_est_global].sum(axis=1)
        df['Current_Supply'] = np.where(mask_m, df.get('Estoque_PV37', 0) + df.get('Pendente_PV37', 0),
                                        df['Estoque_Total_Global'] + df.get('Pendente_PV37', 0))
    else:
        df['mv_dia_calc'] = df.get(f'Média venda/dia_{store}', 0)
        df['sd_venda_calc'] = df.get(f'Std Dev Venda_{store}', 0)
        df['L_calc'] = df[['Lead time', 'Lead time CD', 'Tempo de Negociação', 'Intervalo de compra']].sum(axis=1)
        df['Current_Supply'] = df.get(f'Estoque_{store}', 0) + df.get(f'Pendente_{store}', 0)

    # =========================================================================
    # REGRA DE PISO ADICIONADA AQUI
    # =========================================================================
    df['Demand_30'] = df['mv_dia_calc'] * 30 # Demanda padrão de 30 dias

    if 'Produto' in df.columns:
        df['is_piso'] = df['Produto'].str.upper().str.startswith('PISO', na=False)
        # Substitui o Lead Time por 7 dias para pisos
        df.loc[df['is_piso'], 'L_calc'] = 7
        # Substitui a demanda padrão de 30 dias pela cobertura de 14 dias para pisos
        df.loc[df['is_piso'], 'Demand_30'] = df.loc[df['is_piso'], 'mv_dia_calc'] * 14
    # =========================================================================

    # Cálculos estatísticos
    df['SS_calc'] = Z_SCORE * df['sd_venda_calc'] * np.sqrt(df['L_calc'].clip(lower=0))
    df['PP_calc'] = (df['mv_dia_calc'] * df['L_calc']) + df['SS_calc']
    needed_pp = (df['PP_calc'] - df['Current_Supply']).clip(lower=0)
    needed_pp30 = (df['PP_calc'] + df['Demand_30'] - df['Current_Supply']).clip(lower=0)

    sug_abast_pp30 = pd.Series(0.0, index=df.index)
    if store in ['PV09', 'PV13', 'PV30']:
        mask_abast = df['Abastece?'] == 'S'
        avail = df.get('Stock_Available_Transfer', 0)
        sug_abast_pp30 = np.where(mask_abast, np.minimum(needed_pp30, avail), 0)

    emb = df['Embalagem'].replace(0, 1).fillna(1)
    df['Sugestão de compra PP'] = np.ceil(needed_pp / emb) * emb
    df['Sugestão de compra PP+30'] = np.ceil((needed_pp30 - sug_abast_pp30) / emb) * emb
    df['Sugestão de abast PP'] = 0
    df['Sugestão de abast PP+30'] = np.ceil(sug_abast_pp30)

    # Formatação de Colunas para o Excel Final
    df['Média venda/dia'] = df['mv_dia_calc'].round(2)
    df['Média venda/mês'] = (df['mv_dia_calc'] * 30).round(2)
    df['Desvio Padrão (Cálculo)'] = df['sd_venda_calc'].round(2)
    df['Estoque'] = df.get('Estoque_Total_Global', 0) if store == 'PV37' else df.get(f'Estoque_{store}', 0)
    df['Qntde comprada'] = df.get(f'Pendente_{store}', 0)
    df['Dias est'] = np.where(df['mv_dia_calc'] > 0, df['Estoque'] / df['mv_dia_calc'], 999)
    df['Dias est + qntde comprada'] = np.where(df['mv_dia_calc'] > 0,
                                               (df['Estoque'] + df['Qntde comprada']) / df['mv_dia_calc'], 999)
    df['Dias de estoque PP'] = np.where(df['mv_dia_calc'] > 0,
                                        (df['Current_Supply'] + df['Sugestão de compra PP']) / df['mv_dia_calc'], 999)
    df['Dias de estoque PP+30'] = np.where(df['mv_dia_calc'] > 0,
                                           (df['Current_Supply'] + df['Sugestão de compra PP+30']) / df['mv_dia_calc'],
                                           999)
    df['Estoque PV37'] = df.get('Estoque_PV37', 0)
    df['Pendente PV37 (exclusivo para não-miudeza)'] = np.where(df['Miudeza?'] == 'N', df.get('Pendente_PV37', 0), 0)
    df['Fornecedor'] = df.get('Fornecedor Principal', '')
    df['Custo Líquido'] = df.get('Custo Liq. Unitário', 0)
    df['Preço de venda'] = df.get('Preço Vda Unitário', 0)

    # Cálculo de Margem
    factor = np.where(df['Tributação'].str.contains('22%', na=False), 0.6875, 0.9075)
    df['Margem no sistema'] = (((df['Preço de venda'] * factor) - df['Custo Líquido']) / df['Preço de venda'].replace(0,
                                                                                                                      np.nan)).fillna(
        0).map('{:.2%}'.format)

    # Histórico Mensal
    suffix = f'_{store}' if store != 'PV37' else '_Total'
    for i, nome_mes in enumerate(col_names_display):
        mes_ref = (start_date + relativedelta(months=i)).strftime("%Y-%m")
        df[nome_mes] = df.get(f'Venda_{mes_ref}{suffix}', 0)
    df['Total'] = df[col_names_display].sum(axis=1)

    final_order = ['Código Produto', 'Produto'] + col_names_display + [
        'Total', 'Média venda/mês', 'Média venda/dia', 'Desvio Padrão (Cálculo)',
        'Estoque', 'Qntde comprada', 'Dias est', 'Dias est + qntde comprada',
        'Sugestão de compra PP', 'Sugestão de compra PP+30', 'Sugestão de abast PP', 'Sugestão de abast PP+30',
        'Dias de estoque PP', 'Dias de estoque PP+30', 'Estoque PV37',
        'Pendente PV37 (exclusivo para não-miudeza)', 'Fornecedor', 'Valor de compra',
        'Custo Líquido', 'Preço de venda', 'Margem no sistema', 'Qntde últ compra', 'Curva', 'Popularidade'
    ]
    return df[[c for c in final_order if c in df.columns]]


# =============================================================================
# INTERFACE GRÁFICA (FRONTEND)
# =============================================================================

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Sugestão de Compras")
        self.geometry("1100x800")
        self.configure(fg_color=COLOR_BG)
        self.df_master_global = None
        self.start_date = None
        self.end_date = None
        self.file_paths = {}

        self.build_ui()

    def build_ui(self):
        self.head = ctk.CTkFrame(self, fg_color=COLOR_BG)
        self.head.pack(fill="x", padx=20, pady=10)
        try:
            img_path = resource_path("logo.png")
            img = ctk.CTkImage(Image.open(img_path), size=(150, 60))
            ctk.CTkLabel(self.head, text="", image=img).pack()
        except:
            ctk.CTkLabel(self.head, text="[LOGO]", font=("Arial", 20, "bold")).pack()

        self.main_frame = ctk.CTkFrame(self, fg_color=COLOR_BG)
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=10)
        self.show_file_selection()

    def show_file_selection(self):
        for w in self.main_frame.winfo_children(): w.destroy()
        ctk.CTkLabel(self.main_frame, text="SELEÇÃO DE ARQUIVOS ABC", font=("Arial", 18, "bold"),
                     text_color=COLOR_DARK).pack(pady=20)
        self.entry_est = self.add_file_input("1. Estoque:", "estoque")
        self.entry_ven = self.add_file_input("2. Venda:", "venda")
        self.entry_ent = self.add_file_input("3. Entradas:", "entrada")
        self.btn_load = ctk.CTkButton(self.main_frame, text="CARREGAR DADOS >>", height=50, width=300,
                                      fg_color=COLOR_PRIMARY, command=self.run_load)
        self.btn_load.pack(pady=40)
        self.lbl_log = ctk.CTkLabel(self.main_frame, text="Aguardando...", text_color="gray")
        self.lbl_log.pack()

    def add_file_input(self, txt, key):
        f = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        f.pack(fill="x", padx=100, pady=5)
        ctk.CTkLabel(f, text=txt, font=("Arial", 12, "bold")).pack(anchor="w")
        e = ctk.CTkEntry(f)
        e.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(f, text="...", width=40, command=lambda: self.browse(e, key)).pack(side="right", padx=5)
        return e

    def browse(self, entry, key):
        f = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if f: entry.delete(0, "end"); entry.insert(0, f); self.file_paths[key] = f

    def run_load(self):
        if len(self.file_paths) < 3: return messagebox.showwarning("Aviso", "Selecione os 3 arquivos.")
        self.btn_load.configure(state="disabled", text="PROCESSANDO...")
        threading.Thread(target=self.backend_load, daemon=True).start()

    def backend_load(self):
        try:
            print("Lendo arquivos...")
            data = load_all_data_dynamic(self.file_paths['estoque'], self.file_paths['venda'],
                                         self.file_paths['entrada'])
            data = preprocess_data(data)
            self.start_date, self.end_date = get_last_6_months_range()
            self.df_master_global = build_master_product_table(data, self.start_date, self.end_date)
            self.after(0, self.show_filters)
        except Exception:
            msg = traceback.format_exc()
            self.after(0, lambda: messagebox.showerror("Erro", msg))
            self.after(0, lambda: self.btn_load.configure(state="normal", text="CARREGAR DADOS >>"))

    def show_filters(self):
        # 1. Limpa a tela
        for w in self.main_frame.winfo_children(): w.destroy()

        # 2. Desenha o FOOTER e BOTÃO primeiro (Evita sumir se houver erro nas listas)
        foot = ctk.CTkFrame(self.main_frame, fg_color=COLOR_DARK, corner_radius=0)
        foot.pack(side="bottom", fill="x", pady=10)
        self.txt_console = ctk.CTkTextbox(foot, height=120, fg_color="#1a2b45", text_color="white")
        self.txt_console.pack(fill="x", padx=10, pady=10)

        # Acopla o redirecionador ao widget recém criado
        safe_redirector.set_widget(self.txt_console)

        self.btn_run = ctk.CTkButton(foot, text="GERAR RELATÓRIOS", height=50, font=("Arial", 14, "bold"),
                                     fg_color=COLOR_PRIMARY, command=self.run_reports)
        self.btn_run.pack(pady=10)

        # 3. Desenha as listas de filtros
        try:
            grid = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            grid.pack(expand=True, fill="both")
            grid.columnconfigure((0, 1, 2), weight=1, uniform="a")
            grid.rowconfigure(0, weight=1)

            # =================================================================
            # CORREÇÃO: Garante que as colunas existam para não dar KeyError
            # =================================================================
            if 'Comprador' not in self.df_master_global.columns:
                self.df_master_global['Comprador'] = 'Não Informado'
            if 'Fornecedor Principal' not in self.df_master_global.columns:
                self.df_master_global['Fornecedor Principal'] = 'Não Informado'

            comps = sorted(self.df_master_global['Comprador'].dropna().unique().astype(str))
            lojas = ['PV09', 'PV13', 'PV30', 'PV37']
            forns = sorted(self.df_master_global['Fornecedor Principal'].dropna().unique().astype(str))
            # =================================================================

            self.list_comp = self.create_scroll_list(grid, "1. COMPRADORES", comps, 0)
            self.list_loja = self.create_scroll_list(grid, "2. LOJAS", lojas, 1)
            self.list_forn = self.create_scroll_list(grid, "3. FORNECEDORES", forns, 2)

            print(f"✅ Base carregada: {len(self.df_master_global)} produtos.")
        except Exception as e:
            print(f"Erro ao montar filtros: {e}")
            traceback.print_exc()

    def create_scroll_list(self, parent, title, values, col):
        frame = ctk.CTkScrollableFrame(parent, label_text=title)
        frame.grid(row=0, column=col, sticky="nsew", padx=5)
        vars = []
        for v in values:
            var = ctk.StringVar(value="off")
            ctk.CTkCheckBox(frame, text=str(v)[:35], variable=var, onvalue=str(v), offvalue="off").pack(anchor="w")
            vars.append(var)
        return vars

    def get_selected(self, vars):
        return [v.get() for v in vars if v.get() != "off"]

    def run_reports(self):
        sel_comp = self.get_selected(self.list_comp)
        sel_loja = self.get_selected(self.list_loja)
        sel_forn = self.get_selected(self.list_forn)
        if not sel_loja: return messagebox.showwarning("Aviso", "Selecione a Loja")
        self.btn_run.configure(state="disabled", text="PROCESSANDO...")
        threading.Thread(target=self.backend_report, args=(sel_comp, sel_loja, sel_forn), daemon=True).start()

    def backend_report(self, comps, lojas, forns):
        try:
            print("\n--- INICIANDO PROCESSAMENTO ---")
            df = pre_calculate_pv37_demand(self.df_master_global.copy())
            if comps: df = df[df['Comprador'].isin(comps)]
            if forns: df = df[df['Fornecedor Principal'].isin(forns)]

            prio = ['PV09', 'PV13', 'PV30', 'PV37']
            for lj in [l for l in prio if l in lojas]:
                print(f"Processando {lj}...")
                df_lj = df[df['Ativo?'] == 'S'].copy()
                if lj != 'PV37': df_lj = df_lj[df_lj['Abastece?'] != 'N']
                final = calculate_suggestions(df_lj, lj, self.start_date, self.end_date)

                # Filtra apenas o que tem sugestão positiva
                mask = (final['Sugestão de compra PP'] > 0) | (final['Sugestão de compra PP+30'] > 0) | (
                            final.get('Sugestão de abast PP+30', 0) > 0)
                final = final[mask].copy()

                if not final.empty:
                    fname = f"Sugestao_{lj}_{datetime.datetime.now().strftime('%H%M%S')}.xlsx"
                    final.to_excel(fname, index=False)
                    print(f"✅ Salvo: {fname}")
                else:
                    print(f"⚠️ {lj}: Sem sugestões.")

            self.after(0, lambda: messagebox.showinfo("Fim", "Relatórios Gerados!"))
        except Exception:
            msg = traceback.format_exc()
            self.after(0, lambda: messagebox.showerror("Erro", msg))
        finally:
            self.after(0, lambda: self.btn_run.configure(state="normal", text="GERAR RELATÓRIOS"))


if __name__ == "__main__":
    app = App()
    app.mainloop()