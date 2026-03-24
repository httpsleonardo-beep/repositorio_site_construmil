"""
Módulo de autenticação para o Repositório de Scripts Construmil.
Utiliza streamlit-authenticator para gerenciar login/logout.
"""

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from pathlib import Path


def load_auth_config():
    """Carrega a configuração de autenticação do YAML."""
    config_path = Path(__file__).parent.parent / "config" / "auth_config.yaml"
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.load(file, Loader=SafeLoader)
    return config


def save_auth_config(config):
    """Salva a configuração de autenticação no YAML."""
    config_path = Path(__file__).parent.parent / "config" / "auth_config.yaml"
    with open(config_path, "w", encoding="utf-8") as file:
        yaml.dump(config, file, default_flow_style=False, allow_unicode=True)


def init_authenticator():
    """
    Inicializa e retorna o autenticador e a configuração.
    
    Returns:
        tuple: (authenticator, config)
    """
    config = load_auth_config()
    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )
    return authenticator, config


def render_login_page(authenticator):
    """
    Renderiza a página de login com design profissional.
    
    Args:
        authenticator: instância do stauth.Authenticate
        
    Returns:
        tuple: (name, authentication_status, username)
    """
    logo_path = Path(__file__).parent.parent / "assets" / "Logo.jpeg"
    
    # Layout centralizado
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # Logo
        st.markdown('<div class="login-header">', unsafe_allow_html=True)
        if logo_path.exists():
            st.image(str(logo_path), width=200)
        st.markdown("""
            <h1>Scripts Repository</h1>
            <p>Faça login para acessar o sistema</p>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Login form
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        try:
            authenticator.login(location="main")
        except Exception as e:
            st.error(f"Erro no login: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    return (
        st.session_state.get("name"),
        st.session_state.get("authentication_status"),
        st.session_state.get("username")
    )


def render_sidebar_user(authenticator, name, username):
    """
    Renderiza informações do usuário na sidebar.
    
    Args:
        authenticator: instância do stauth.Authenticate
        name: nome do usuário logado
        username: username do usuário logado
    """
    initial = name[0].upper() if name else "U"
    
    st.sidebar.markdown(f"""
        <div class="user-profile">
            <div class="user-avatar">{initial}</div>
            <div class="user-info">
                <div class="user-name">{name}</div>
                <div class="user-role">@{username}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    authenticator.logout("🚪 Sair", "sidebar")


def check_authentication():
    """
    Verifica o status de autenticação e redireciona se necessário.
    
    Returns:
        tuple: (authenticated: bool, authenticator, name, username)
    """
    authenticator, config = init_authenticator()

    # Se já autenticado (via cookie), retorna direto sem renderizar login
    if st.session_state.get("authentication_status") is True:
        return (
            True,
            authenticator,
            st.session_state.get("name"),
            st.session_state.get("username"),
        )

    # Renderiza a página de login apenas quando NÃO autenticado
    name, auth_status, username = render_login_page(authenticator)

    if auth_status is False:
        st.error("⚠️ Usuário ou senha incorretos.")
    elif auth_status is None:
        st.info("👆 Insira suas credenciais para acessar o sistema.")

    return auth_status is True, authenticator, name, username
