"""
Repositório de Scripts — Construmil
Aplicação principal Streamlit.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import importlib
import time

# ---- Configuração da página (DEVE ser a primeira chamada Streamlit) ----
st.set_page_config(
    page_title="Scripts Repository — Construmil",
    page_icon="📂",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---- Imports internos ----
from modules.ui_components import (
    load_css,
    render_top_navbar,
    render_nav_user,
    render_page_title,
    render_metric_card,
    render_script_card,
    log_execution,
)
from modules.auth import (
    check_authentication,
)
from modules.script_loader import (
    get_all_scripts,
    get_script_by_id,
    discover_scripts,
)

# ---- CSS ----
load_css()


# =====================================================================
#  AUTENTICAÇÃO
# =====================================================================
authenticated, authenticator, user_name, user_username = check_authentication()

if not authenticated:
    st.stop()

# =====================================================================
#  TOP NAVIGATION (substitui a sidebar)
# =====================================================================

# Gerencia a página selecionada via session_state
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Scripts"

# Renderiza a barra de navegacao com HTML puro para o fundo
render_top_navbar()

# Ancora para puxar as colunas sobre a barra
st.markdown('<div class="nav-anchor"></div>', unsafe_allow_html=True)

# Navegacao funcional com Streamlit e layout de usuario
nav_col1, nav_col2, nav_space, nav_user, nav_logout = st.columns([1.5, 1.5, 4, 3, 1.2])

with nav_col1:
    if st.button("📂 Scripts", use_container_width=True,
                 type="primary" if st.session_state["current_page"] == "Scripts" else "secondary"):
        st.session_state["current_page"] = "Scripts"
        st.rerun()

with nav_col2:
    if st.button("📜 Histórico", use_container_width=True,
                 type="primary" if st.session_state["current_page"] == "Histórico" else "secondary"):
        st.session_state["current_page"] = "Histórico"
        st.rerun()

with nav_user:
    render_nav_user(user_name)

with nav_logout:
    authenticator.logout("Sair", "main")

selected = st.session_state["current_page"]


# =====================================================================
#  PÁGINA: SCRIPTS
# =====================================================================
def page_scripts():
    render_page_title("Repositório de Scripts", "📂")

    scripts = get_all_scripts()
    unregistered = discover_scripts()

    # Métricas rápidas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Scripts Disponíveis", len(scripts), "📂")
    with col2:
        render_metric_card("Categorias", len({s["category"] for s in scripts}), "🏷️")
    with col3:
        render_metric_card("Não Registrados", len(unregistered), "🆕")
    with col4:
        render_metric_card("Usuário Ativo", user_name, "👤")

    st.markdown("")

    if not scripts:
        st.info("Nenhum script registrado. Adicione scripts na pasta `scripts/` e "
                "registre-os no `script_loader.py`.")
        return

    # Selecionar script
    script_names = [f"{s['icon']} {s['name']}" for s in scripts]
    chosen_idx = st.selectbox(
        "Selecione um script para executar",
        range(len(scripts)),
        format_func=lambda i: script_names[i],
    )

    script_meta = scripts[chosen_idx]
    render_script_card(script_meta)

    # Rotas: external_link vs multi-stage vs single-stage
    if script_meta.get("type") == "external_link":
        _render_external_link(script_meta)
    elif script_meta.get("multi_stage"):
        _render_multi_stage_script(script_meta)
    else:
        _render_single_stage_script(script_meta)


# -----------------------------------------------------------------
#  LINK EXTERNO (ex: Profissional Nota Mil)
# -----------------------------------------------------------------
def _render_external_link(script_meta):
    tab_access, tab_doc = st.tabs([
        "🔗 Acesso",
        "📝 Documentação",
    ])

    with tab_access:
        st.markdown("### 🌐 Acesso Externo")
        st.markdown(
            f"Este item redireciona para uma plataforma externa. "
            f"Clique no botão abaixo para acessar."
        )
        st.markdown("")

        url = script_meta.get("url", "#")

        # Botão estilizado com link externo (abre em nova aba)
        st.markdown('<div class="execute-btn">', unsafe_allow_html=True)
        st.link_button(
            "🚀  Acessar Site — " + script_meta["name"],
            url=url,
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("")
        st.info(f"🔗 **URL:** {url}")

    with tab_doc:
        doc = script_meta.get("doc", "")
        if doc:
            st.markdown(doc)
        else:
            st.info("Documentação não disponível.")


# -----------------------------------------------------------------
#  SCRIPTS DE ETAPA ÚNICA (ex: Comparar Preços Amanco)
# -----------------------------------------------------------------
def _render_single_stage_script(script_meta):
    tab_exec, tab_result, tab_doc = st.tabs([
        "🚀 Execução",
        "📊 Resultados",
        "📝 Documentação",
    ])

    # ---- ABA EXECUÇÃO ----
    with tab_exec:
        st.markdown("### ⚙️ Parâmetros de Entrada")

        inputs = {}
        all_filled = True

        for inp in script_meta.get("inputs", []):
            inp_type = inp["type"]
            key = inp["key"]
            label = inp["label"]
            help_text = inp.get("help", "")

            if inp_type == "file_uploader":
                val = st.file_uploader(
                    label,
                    type=inp.get("file_types"),
                    help=help_text,
                    key=f"input_{script_meta['id']}_{key}",
                )
                inputs[key] = val
                if val is None:
                    all_filled = False

            elif inp_type == "text_input":
                val = st.text_input(label, help=help_text,
                                    key=f"input_{script_meta['id']}_{key}")
                inputs[key] = val
                if not val:
                    all_filled = False

            elif inp_type == "number_input":
                val = st.number_input(label, help=help_text,
                                      key=f"input_{script_meta['id']}_{key}")
                inputs[key] = val

            elif inp_type == "selectbox":
                options = inp.get("options", [])
                val = st.selectbox(label, options, help=help_text,
                                   key=f"input_{script_meta['id']}_{key}")
                inputs[key] = val

        st.markdown("")

        if not all_filled:
            st.warning("⚠️ Preencha todos os campos antes de executar.")

        # Botão executar
        st.markdown('<div class="execute-btn">', unsafe_allow_html=True)
        run_clicked = st.button(
            "▶️  Executar Script",
            disabled=not all_filled,
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        if run_clicked and all_filled:
            progress_bar = st.progress(0, text="Iniciando…")
            status_area = st.empty()

            try:
                # Importa o módulo do script dinamicamente
                module = importlib.import_module(script_meta["module"])

                progress_bar.progress(20, text="Módulo carregado…")
                time.sleep(0.3)

                with st.spinner("⏳ Processando — aguarde…"):
                    progress_bar.progress(40, text="Lendo arquivos…")
                    result = module.run(inputs)
                    progress_bar.progress(80, text="Finalizando…")
                    time.sleep(0.2)

                progress_bar.progress(100, text="Concluído!")
                time.sleep(0.3)
                progress_bar.empty()

                # Armazena o resultado na sessão
                st.session_state[f"result_{script_meta['id']}"] = result

                # Log
                log_execution(user_username, script_meta["name"], "sucesso")

                st.success("✅ Script executado com sucesso! Veja os resultados na aba **📊 Resultados**.")

                # Mostra logs do script
                if result.get("logs"):
                    with st.expander("📋 Log de Execução", expanded=False):
                        for log_line in result["logs"]:
                            st.text(log_line)

            except Exception as e:
                progress_bar.empty()
                log_execution(user_username, script_meta["name"], "erro", str(e))
                st.error(f"❌ Erro na execução: {e}")
                import traceback
                with st.expander("🔍 Detalhes do Erro"):
                    st.code(traceback.format_exc())

    # ---- ABA RESULTADOS ----
    with tab_result:
        result_key = f"result_{script_meta['id']}"

        if result_key not in st.session_state:
            st.info("🔎 Execute o script na aba **🚀 Execução** para ver os resultados aqui.")
        else:
            result = st.session_state[result_key]
            st.markdown("### 📊 Resultados da Comparação")

            # Sumário em cards
            summary = result.get("summary", {})
            if summary:
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1:
                    render_metric_card("Total de Produtos", summary.get("total", 0), "📦")
                with c2:
                    render_metric_card("Correspondências", summary.get("matches", 0), "✅")
                with c3:
                    render_metric_card("Sem Correspondência", summary.get("no_match", 0), "❌")
                with c4:
                    render_metric_card("Qtde Divergente", summary.get("qtde_divergente", 0), "📏")
                with c5:
                    render_metric_card("Preço Divergente", summary.get("preco_divergente", 0), "💰")

            st.markdown("")

            # DataFrame
            df_result = result.get("df_result")
            if df_result is not None and not df_result.empty:
                st.markdown("#### 📋 Tabela Comparativa")
                st.dataframe(df_result, use_container_width=True, height=400)

                # Gráficos
                st.markdown("#### 📈 Gráficos")

                col_g1, col_g2 = st.columns(2)

                with col_g1:
                    if "Diferença de Preço" in df_result.columns:
                        df_chart = df_result.dropna(subset=["Diferença de Preço"])
                        df_chart = df_chart[df_chart["Diferença de Preço"] != 0].copy()

                        if not df_chart.empty:
                            df_chart = df_chart.head(20)
                            product_label = df_chart.get("Produto", df_chart.get("Código Extraído", pd.Series(range(len(df_chart)))))

                            fig = go.Figure(go.Bar(
                                x=df_chart["Diferença de Preço"],
                                y=product_label.astype(str),
                                orientation="h",
                                marker_color=[
                                    "#ef4444" if v > 0 else "#10b981"
                                    for v in df_chart["Diferença de Preço"]
                                ],
                            ))
                            fig.update_layout(
                                title="Diferença de Preço (Top 20)",
                                xaxis_title="Diferença (R$)",
                                yaxis_title="Produto",
                                template="plotly_dark",
                                paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="rgba(0,0,0,0)",
                                height=500,
                                margin=dict(l=10, r=10, t=40, b=10),
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("Nenhuma divergência de preço encontrada.")

                with col_g2:
                    if "Diferença de Qtde" in df_result.columns:
                        df_chart2 = df_result.dropna(subset=["Diferença de Qtde"])
                        df_chart2 = df_chart2[df_chart2["Diferença de Qtde"] != 0].copy()

                        if not df_chart2.empty:
                            df_chart2 = df_chart2.head(20)
                            product_label2 = df_chart2.get("Produto", df_chart2.get("Código Extraído", pd.Series(range(len(df_chart2)))))

                            fig2 = go.Figure(go.Bar(
                                x=df_chart2["Diferença de Qtde"],
                                y=product_label2.astype(str),
                                orientation="h",
                                marker_color=[
                                    "#f59e0b" if v > 0 else "#8b5cf6"
                                    for v in df_chart2["Diferença de Qtde"]
                                ],
                            ))
                            fig2.update_layout(
                                title="Diferença de Quantidade (Top 20)",
                                xaxis_title="Diferença",
                                yaxis_title="Produto",
                                template="plotly_dark",
                                paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="rgba(0,0,0,0)",
                                height=500,
                                margin=dict(l=10, r=10, t=40, b=10),
                            )
                            st.plotly_chart(fig2, use_container_width=True)
                        else:
                            st.info("Nenhuma divergência de quantidade encontrada.")

                # Gráfico de pizza — status
                if summary:
                    st.markdown("#### 🍩 Visão Geral")
                    fig_pie = go.Figure(go.Pie(
                        labels=["Com Correspondência", "Sem Correspondência"],
                        values=[summary.get("matches", 0), summary.get("no_match", 0)],
                        hole=0.5,
                        marker_colors=["#10b981", "#ef4444"],
                        textinfo="label+percent",
                        textfont_size=13,
                    ))
                    fig_pie.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        height=350,
                        showlegend=False,
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)

                # Download
                st.markdown("#### ⬇️ Download")
                excel_bytes = result.get("excel_bytes")
                if excel_bytes:
                    st.download_button(
                        label="📥  Baixar Resultado (.xlsx)",
                        data=excel_bytes,
                        file_name=f"comparacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
            else:
                st.warning("A comparação não retornou dados.")

    # ---- ABA DOCUMENTAÇÃO ----
    with tab_doc:
        doc = script_meta.get("doc", "")
        if doc:
            st.markdown(doc)
        else:
            st.info("Documentação não disponível para este script.")


# -----------------------------------------------------------------
#  SCRIPTS MULTI-ETAPA (ex: Sugestão de Compras)
# -----------------------------------------------------------------
def _render_multi_stage_script(script_meta):
    sid = script_meta["id"]

    tab_exec, tab_result, tab_doc = st.tabs([
        "🚀 Execução",
        "📊 Resultados",
        "📝 Documentação",
    ])

    # ---- ABA EXECUÇÃO ----
    with tab_exec:
        # ============================================================
        # ETAPA 1 — Upload dos arquivos
        # ============================================================
        st.markdown("### 📂 Etapa 1 — Carregar Planilhas")

        inputs = {}
        all_filled = True

        for inp in script_meta.get("inputs", []):
            val = st.file_uploader(
                inp["label"],
                type=inp.get("file_types"),
                help=inp.get("help", ""),
                key=f"input_{sid}_{inp['key']}",
            )
            inputs[inp["key"]] = val
            if val is None:
                all_filled = False

        if not all_filled:
            st.warning("⚠️ Envie todos os arquivos para continuar.")

        # Botão CARREGAR DADOS
        st.markdown('<div class="execute-btn">', unsafe_allow_html=True)
        load_clicked = st.button(
            "📥  Carregar Dados",
            disabled=not all_filled,
            use_container_width=True,
            key=f"btn_load_{sid}",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        if load_clicked and all_filled:
            progress_bar = st.progress(0, text="Carregando planilhas…")
            try:
                module = importlib.import_module(script_meta["module"])
                progress_bar.progress(15, text="Módulo carregado…")

                with st.spinner("⏳ Processando dados — isso pode levar alguns minutos…"):
                    progress_bar.progress(30, text="Lendo planilhas…")
                    inputs["_stage"] = "load"
                    result = module.run(inputs)
                    progress_bar.progress(90, text="Finalizando…")

                progress_bar.progress(100, text="✅ Dados carregados!")
                time.sleep(0.3)
                progress_bar.empty()

                # Salva na sessão
                st.session_state[f"loaded_{sid}"] = result
                st.success(f"✅ Base carregada com sucesso: **{result['total_produtos']}** produtos encontrados!")

                if result.get("logs"):
                    with st.expander("📋 Log de Carregamento", expanded=False):
                        for log_line in result["logs"]:
                            st.text(log_line)

                st.rerun()

            except Exception as e:
                progress_bar.empty()
                st.error(f"❌ Erro ao carregar dados: {e}")
                import traceback
                with st.expander("🔍 Detalhes do Erro"):
                    st.code(traceback.format_exc())

        # ============================================================
        # ETAPA 2 — Filtros e Geração (só aparece se dados carregados)
        # ============================================================
        loaded_data = st.session_state.get(f"loaded_{sid}")

        if loaded_data and loaded_data.get("stage") == "loaded":
            st.markdown("---")
            st.markdown("### 🔧 Etapa 2 — Filtros e Geração de Relatórios")

            st.info(f"📦 **{loaded_data['total_produtos']}** produtos na base | "
                    f"Período: últimos 6 meses")

            col_lojas, col_comp, col_forn = st.columns(3)

            # Lojas (obrigatório)
            with col_lojas:
                st.markdown("**🏪 Lojas** *(obrigatório)*")
                lojas_disponiveis = ["PV09", "PV13", "PV30", "PV37"]
                sel_lojas = []
                for loja in lojas_disponiveis:
                    if st.checkbox(loja, key=f"loja_{sid}_{loja}"):
                        sel_lojas.append(loja)

            # Compradores (opcional)
            with col_comp:
                st.markdown("**👤 Compradores** *(opcional)*")
                compradores = loaded_data.get("compradores", [])
                sel_comps = st.multiselect(
                    "Filtrar por comprador",
                    options=compradores,
                    key=f"comps_{sid}",
                    label_visibility="collapsed",
                )

            # Fornecedores (opcional)
            with col_forn:
                st.markdown("**🏭 Fornecedores** *(opcional)*")
                fornecedores = loaded_data.get("fornecedores", [])
                sel_forns = st.multiselect(
                    "Filtrar por fornecedor",
                    options=fornecedores,
                    key=f"forns_{sid}",
                    label_visibility="collapsed",
                )

            st.markdown("")

            if not sel_lojas:
                st.warning("⚠️ Selecione pelo menos uma loja para gerar os relatórios.")

            # Botão GERAR RELATÓRIOS
            st.markdown('<div class="execute-btn">', unsafe_allow_html=True)
            gen_clicked = st.button(
                "📊  Gerar Relatórios",
                disabled=len(sel_lojas) == 0,
                use_container_width=True,
                key=f"btn_gen_{sid}",
            )
            st.markdown("</div>", unsafe_allow_html=True)

            if gen_clicked and sel_lojas:
                progress_bar = st.progress(0, text="Iniciando geração…")
                try:
                    module = importlib.import_module(script_meta["module"])
                    progress_bar.progress(10, text="Calculando sugestões…")

                    gen_inputs = {
                        "_stage": "generate",
                        "df_master": loaded_data["df_master"],
                        "start_date": loaded_data["start_date"],
                        "end_date": loaded_data["end_date"],
                        "lojas": sel_lojas,
                        "compradores": sel_comps,
                        "fornecedores": sel_forns,
                    }

                    with st.spinner("⏳ Gerando relatórios — aguarde…"):
                        progress_bar.progress(40, text="Processando lojas…")
                        result = module.run(gen_inputs)
                        progress_bar.progress(90, text="Finalizando…")

                    progress_bar.progress(100, text="✅ Relatórios prontos!")
                    time.sleep(0.3)
                    progress_bar.empty()

                    st.session_state[f"result_{sid}"] = result
                    log_execution(user_username, script_meta["name"], "sucesso",
                                  f"Lojas: {', '.join(sel_lojas)}")

                    st.success("✅ Relatórios gerados! Veja na aba **📊 Resultados**.")

                    if result.get("logs"):
                        with st.expander("📋 Log de Execução", expanded=False):
                            for log_line in result["logs"]:
                                st.text(log_line)

                except Exception as e:
                    progress_bar.empty()
                    log_execution(user_username, script_meta["name"], "erro", str(e))
                    st.error(f"❌ Erro na geração: {e}")
                    import traceback
                    with st.expander("🔍 Detalhes do Erro"):
                        st.code(traceback.format_exc())

    # ---- ABA RESULTADOS ----
    with tab_result:
        result_key = f"result_{sid}"

        if result_key not in st.session_state:
            st.info("🔎 Carregue os dados e gere os relatórios na aba **🚀 Execução**.")
        else:
            result = st.session_state[result_key]

            if result.get("stage") == "generated":
                st.markdown("### 📊 Relatórios de Sugestão de Compras")

                summary = result.get("summary", {})
                c1, c2, c3 = st.columns(3)
                with c1:
                    render_metric_card("Lojas Processadas", summary.get("lojas_processadas", 0), "🏪")
                with c2:
                    render_metric_card("Total de Sugestões", summary.get("total_sugestoes", 0), "🛒")
                with c3:
                    render_metric_card("Lojas com Resultado", summary.get("lojas_com_resultado", 0), "✅")

                st.markdown("")

                results_dict = result.get("results", {})
                excel_dict = result.get("excel_files", {})

                if not results_dict:
                    st.warning("Nenhuma sugestão foi gerada para os filtros selecionados.")
                else:
                    # Cria uma sub-aba para cada loja
                    loja_tabs = st.tabs([f"🏪 {lj}" for lj in results_dict.keys()])

                    for tab_lj, (loja, df_loja) in zip(loja_tabs, results_dict.items()):
                        with tab_lj:
                            st.markdown(f"#### Sugestão — {loja} ({len(df_loja)} itens)")

                            # Métricas por loja
                            lc1, lc2, lc3, lc4 = st.columns(4)
                            with lc1:
                                total_pp = df_loja["Sugestão de compra PP"].sum() if "Sugestão de compra PP" in df_loja.columns else 0
                                render_metric_card("Compra PP", f"{total_pp:,.0f}", "📦")
                            with lc2:
                                total_pp30 = df_loja["Sugestão de compra PP+30"].sum() if "Sugestão de compra PP+30" in df_loja.columns else 0
                                render_metric_card("Compra PP+30", f"{total_pp30:,.0f}", "📦")
                            with lc3:
                                total_abast = df_loja["Sugestão de abast PP+30"].sum() if "Sugestão de abast PP+30" in df_loja.columns else 0
                                render_metric_card("Abastecimento", f"{total_abast:,.0f}", "🔄")
                            with lc4:
                                render_metric_card("Itens", len(df_loja), "📋")

                            st.markdown("")

                            # Tabela
                            st.dataframe(df_loja, use_container_width=True, height=400)

                            # Download do Excel
                            if loja in excel_dict:
                                ts = result.get("timestamp", "export")
                                st.download_button(
                                    label=f"📥  Baixar Sugestão_{loja}.xlsx",
                                    data=excel_dict[loja],
                                    file_name=f"Sugestao_{loja}_{ts}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    use_container_width=True,
                                    key=f"dl_{sid}_{loja}",
                                )

    # ---- ABA DOCUMENTAÇÃO ----
    with tab_doc:
        doc = script_meta.get("doc", "")
        if doc:
            st.markdown(doc)
        else:
            st.info("Documentação não disponível para este script.")


# =====================================================================
#  PÁGINA: HISTÓRICO
# =====================================================================
def page_historico():
    render_page_title("Histórico de Execuções", "📜")
    st.markdown("")

    log_path = Path(__file__).parent / "logs" / "execution_log.csv"

    if not log_path.exists():
        st.info("Nenhum registro encontrado.")
        return

    try:
        df_log = pd.read_csv(log_path)
    except Exception:
        st.info("Nenhum registro encontrado.")
        return

    if df_log.empty:
        st.info("Nenhuma execução registrada ainda.")
        return

    # Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        render_metric_card("Total de Execuções", len(df_log), "🔢")
    with col2:
        successes = (df_log["status"] == "sucesso").sum() if "status" in df_log.columns else 0
        render_metric_card("Sucesso", int(successes), "✅")
    with col3:
        errors = (df_log["status"] == "erro").sum() if "status" in df_log.columns else 0
        render_metric_card("Erros", int(errors), "❌")

    st.markdown("")

    # Tabela
    st.dataframe(
        df_log.sort_index(ascending=False),
        use_container_width=True,
        height=400,
    )

    # Download do log
    st.download_button(
        label="📥  Baixar Log Completo (.csv)",
        data=df_log.to_csv(index=False).encode("utf-8"),
        file_name="execution_log.csv",
        mime="text/csv",
    )


# =====================================================================
#  ROTEADOR
# =====================================================================
if selected == "Scripts":
    page_scripts()
elif selected == "Histórico":
    page_historico()
