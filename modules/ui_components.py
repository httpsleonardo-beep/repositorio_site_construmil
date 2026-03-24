"""
UI Components — Componentes reutilizáveis da interface.
"""

import streamlit as st
from pathlib import Path
from datetime import datetime
import base64


def load_css():
    """Carrega o CSS customizado."""
    css_path = Path(__file__).parent.parent / "assets" / "style.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def _get_logo_base64():
    """Retorna a logo em base64 para embutir no HTML."""
    logo_path = Path(__file__).parent.parent / "assets" / "Logo.jpeg"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


def render_top_navbar():
    """
    Renderiza a barra de navegação principal (fundo azul, logo e título).
    """
    logo_b64 = _get_logo_base64()
    logo_html = f'<img src="data:image/jpeg;base64,{logo_b64}" alt="Logo">' if logo_b64 else ""

    st.markdown(f"""
        <div class="top-navbar">
            <div class="nav-logo">{logo_html}</div>
            <div class="nav-brand">Construmil — Repositório de Scripts</div>
        </div>
    """, unsafe_allow_html=True)

def render_nav_user(user_name):
    """Renderiza a exibição de usuário de forma alinhada para a coluna do painel de navegação."""
    initial = user_name[0].upper() if user_name else "U"
    
    st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: flex-end; gap: 8px; color: white; height: 40px; margin-top: 4px;">
            <div style="width: 32px; height: 32px; border-radius: 50%; background: rgba(255, 255, 255, 0.2); display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem;">{initial}</div>
            <span style="font-size: 0.9rem; font-weight: 500;">{user_name}</span>
        </div>
    """, unsafe_allow_html=True)


def render_page_title(title, icon="📂"):
    """Renderiza um título de página com a linha accent."""
    st.markdown(f"""
        <div class="page-title">
            <h1>{icon} {title}</h1>
        </div>
    """, unsafe_allow_html=True)


def render_metric_card(title, value, icon="📊", delta=None):
    """
    Renderiza um card de métrica.
    """
    delta_html = ""
    if delta is not None:
        color = "var(--success)" if delta >= 0 else "var(--danger)"
        sign = "+" if delta >= 0 else ""
        delta_html = f'<p style="color:{color};font-size:0.8rem;margin:0">{sign}{delta}</p>'

    is_text = isinstance(value, str) and not str(value).isdigit()
    font_size = "1rem" if is_text else "1.75rem"

    st.markdown(f"""
        <div class="metric-card animate-fade-in">
            <p style="color:var(--text-secondary);font-size:0.8rem;margin:0 0 6px 0;font-weight:500">{icon} {title}</p>
            <p style="color:var(--text-primary);font-size:{font_size};font-weight:700;margin:0">{value}</p>
            {delta_html}
        </div>
    """, unsafe_allow_html=True)


def render_script_card(script_meta):
    """Renderiza um card de script."""
    icon = script_meta.get("icon", "📄")
    name = script_meta.get("name", "Script")
    desc = script_meta.get("description", "")
    cat = script_meta.get("category", "Outros")

    st.markdown(f"""
        <div class="script-card animate-fade-in">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
                <span style="font-size:1.5rem">{icon}</span>
                <div>
                    <p style="color:var(--text-primary);font-weight:600;font-size:1rem;margin:0">{name}</p>
                    <p style="color:var(--primary);font-size:0.75rem;margin:0;font-weight:500">📁 {cat}</p>
                </div>
            </div>
            <p style="color:var(--text-secondary);font-size:0.85rem;margin:0;line-height:1.5">{desc}</p>
        </div>
    """, unsafe_allow_html=True)


def log_execution(username, script_name, status, details=""):
    """Registra uma execução no log CSV."""
    import csv

    log_path = Path(__file__).parent.parent / "logs" / "execution_log.csv"
    now = datetime.now()

    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            username,
            script_name,
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M:%S"),
            status,
            details,
        ])
