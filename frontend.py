import streamlit as st
import requests
import pandas as pd
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="YouTube Niche Analyzer", page_icon="🚀", layout="wide")

# --- CSS "APPLE GLASS" ULTRA PERSONALIZADO ---
# Aqui é onde a mágica visual acontece. Estamos injetando CSS pesado para
# mudar a cara do Streamlit e criar o efeito de "Vidro".
st.markdown("""
    <style>
    /* 1. FUNDO GERAL (Gradiente Pastel Fluido) */
    [data-testid="stAppViewContainer"] {
        background-image: linear-gradient(to top right, #a8caba 0%, #5d4157 100%);
        background-attachment: fixed;
    }
    
    /* 2. PAINEL PRINCIPAL (O "Vidro") */
    [data-testid="stAppViewBlockContainer"] {
        background-color: rgba(255, 255, 255, 0.25); /* Branco transparente */
        backdrop-filter: blur(15px); /* O Desfoque do vidro */
        -webkit-backdrop-filter: blur(15px); /* Para Safari */
        border-radius: 25px;
        padding: 30px;
        margin-top: 30px;
        border: 1px solid rgba(255, 255, 255, 0.18); /* Borda sutil */
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15); /* Sombra suave */
    }
    
    /* 3. SIDEBAR (Vidro mais escuro) */
    [data-testid="stSidebar"] {
        background-color: rgba(0, 0, 0, 0.1) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    [data-testid="stSidebarUserContent"] {
        background-color: transparent !important;
    }

    /* 4. TIPOGRAFIA E CORES */
    h1, h2, h3, p, div, span, label {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        color: #f0f2f5 !important; /* Texto claro para fundo escuro */
    }
    h1 { font-weight: 800 !important; letter-spacing: -1px; }
    
    /* 5. BOTÕES (Estilo "Pílula" Apple) */
    .stButton button {
        background: linear-gradient(135deg, #6B73FF 0%, #000DFF 100%) !important;
        color: white !important;
        border-radius: 30px !important;
        border: none !important;
        padding: 12px 28px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    /* Botão secundário (Logout/Histórico) */
    [data-testid="stSidebar"] .stButton button {
        background: rgba(255,255,255,0.1) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
    }

    /* 6. CAMPOS DE TEXTO (Inputs redondos e transparentes) */
    .stTextInput input {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 20px !important;
        color: white !important;
        padding: 10px 15px !important;
    }
    .stTextInput input::placeholder { color: rgba(255,255,255,0.6) !important; }
    
    /* 7. MÉTRICAS E TABELAS */
    div[data-testid="stMetricValue"] { font-size: 32px; font-weight: 700; text-shadow: 0 2px 10px rgba(0,0,0,0.2); }
    [data-testid="stDataFrame"] { background-color: rgba(0,0,0,0.2); border-radius: 15px; padding: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- SISTEMA DE SESSÃO ---
if 'logado' not in st.session_state:
    st.session_state['logado'] = False
if 'usuario' not in st.session_state:
    st.session_state['usuario'] = ""

# --- FUNÇÃO DE LOGIN (Com visual novo) ---
def tela_de_login():
    # Usamos colunas vazias para centralizar o card de login
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("🔒 Acesso Restrito")
        st.write("Ambiente seguro. Identifique-se.")
        
        st.divider()
        usuario = st.text_input("Usuário", placeholder="Digite seu usuário")
        senha = st.text_input("Senha", type="password", placeholder="••••••")
        st.write("") # Espaço
        
        if st.button("Entrar no Sistema", type="primary", use_container_width=True):
            if usuario == "admin" and senha == "1234":
                st.session_state['logado'] = True
                st.session_state['usuario'] = usuario
                st.success("Conectado!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Acesso negado.")

# --- FUNÇÃO DO APLICATIVO PRINCIPAL ---
def app_principal():
    with st.sidebar:
        st.title("Niche 🚀")
        st.write(f"👤 **{st.session_state['usuario']}** (Premium)")
        if st.button("Sair"):
            st.session_state['logado'] = False
            st.rerun()
            
        st.divider()
        st.caption("Histórico Recente")
        if st.button("🔄 Atualizar"):
            try:
                resp_hist = requests.get("http://127.0.0.1:8000/historico")
                if resp_hist.status_code == 200:
                    historico = resp_hist.json()
                    for item in historico[:5]:
                        st.text(f"• {item['nicho'].title()}")
            except:
                st.sidebar.error("Erro de conexão")

    st.title("Painel de Inteligência")
    st.write("Descubra oportunidades inexploradas no YouTube com IA.")
    st.divider()
    
    c_input, c_btn = st.columns([3, 1])
    with c_input:
        nicho = st.text_input("Investigar Nicho:", placeholder="Ex: Marketing, Yoga, Finanças...", label_visibility="collapsed")
    with c_btn:
        botao = st.button("🔍 Analisar Agora", type="primary", use_container_width=True)

    if botao and nicho:
        with st.spinner(f"Processando dados de '{nicho}'..."):
            try:
                response = requests.get(f"http://127.0.0.1:8000/analise/{nicho}")
                if response.status_code == 200:
                    dados = response.json()
                    if dados:
                        df = pd.DataFrame(dados)
                        st.success("Análise concluída com sucesso.")
                        
                        st.subheader("KPIs do Mercado")
                        kpi1, kpi2, kpi3 = st.columns(3)
                        media_views = df['media_views_por_video'].mean() if not df.empty else 0
                        media_subs = df['inscritos'].mean() if not df.empty else 0
                        top_nome = df.iloc[0]['nome'] if not df.empty else "N/A"

                        kpi1.metric("Demand Média (Views)", f"{media_views:,.0f}")
                        kpi2.metric("Concorrência Média", f"{media_subs:,.0f}")
                        kpi3.metric("💎 Oportunidade Top 1", top_nome)
                        
                        st.subheader("Mapa de Calor de Oportunidade")
                        st.scatter_chart(df, x='inscritos', y='media_views_por_video', color='taxa_engajamento', size='total_videos', height=400)
                        
                        st.subheader("Ranking Detalhado")
                        tabela = df[['nome', 'taxa_engajamento', 'inscritos', 'media_views_por_video', 'link']]
                        st.dataframe(
                            tabela,
                            column_config={
                                "link": st.column_config.LinkColumn("Ver Canal"),
                                "taxa_engajamento": st.column_config.ProgressColumn("Score Oportunidade", format="%.1f%%", min_value=0, max_value=100),
                                "inscritos": st.column_config.NumberColumn("Inscritos"),
                                "media_views_por_video": st.column_config.NumberColumn("Views/Vídeo")
                            },
                            hide_index=True, use_container_width=True
                        )
                    else:
                        st.warning("Nenhum canal encontrado.")
                else:
                    st.error("Erro no servidor backend.")
            except Exception as e:
                st.error(f"Erro: {e}")

# --- CONTROLE DE FLUXO ---
if st.session_state['logado']:
    app_principal()
else:
    tela_de_login()