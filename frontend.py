import streamlit as st
import pandas as pd
import requests
import os
import datetime
from dotenv import load_dotenv

# Carrega variáveis
load_dotenv()

# Banco de Dados
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gold Finder AI", page_icon="✨", layout="wide")

# --- BANCO DE DADOS ---
DATABASE_URL = "sqlite:///./saas.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Historico(Base):
    __tablename__ = "historico_pesquisas"
    id = Column(Integer, primary_key=True, index=True)
    nicho = Column(String, index=True)
    data_pesquisa = Column(DateTime, default=datetime.datetime.now)

Base.metadata.create_all(bind=engine)

# --- CSS "ZEN PASTEL" ---
st.markdown("""
    <style>
    /* 1. FUNDO GERAL */
    .stApp {
        background: linear-gradient(120deg, #fdfbfb 0%, #ebedee 100%);
        background-attachment: fixed;
    }
    header[data-testid="stHeader"] { background: transparent; }

    /* 2. TIPOGRAFIA */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        color: #2c3e50 !important;
        font-weight: 700;
    }
    p, label, span, div { color: #4a5568 !important; }

    /* 3. CARDS */
    .card-container {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.6);
        border-radius: 20px;
        padding: 25px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    .gold-card {
        background: linear-gradient(135deg, #ffffff 0%, #fffbf0 100%);
        border: 2px solid #f6e6b4;
        border-radius: 20px;
        padding: 25px;
        box-shadow: 0 10px 25px rgba(212, 175, 55, 0.15);
        margin-bottom: 20px;
        position: relative;
    }
    .gold-badge {
        background: linear-gradient(90deg, #fce38a 0%, #f38181 100%);
        color: white;
        padding: 5px 15px;
        border-radius: 15px;
        font-size: 12px;
        font-weight: bold;
        position: absolute;
        top: -12px;
        right: 20px;
    }

    /* 4. INPUTS E BOTÕES */
    .stTextInput input {
        background-color: #ffffff !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 15px !important;
        padding: 15px !important;
    }
    div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 50px;
        width: 100%;
        box-shadow: 0 4px 15px rgba(118, 75, 162, 0.3);
    }
    /* Estilo Especial para o Botão de Download */
    div[data-testid="stDownloadButton"] button {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        color: #2d3748;
        border: 1px solid #e2e8f0;
        border-radius: 15px;
        padding: 10px 20px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE BUSCA ---
def buscar_dados_youtube(nicho, api_key):
    if not api_key: return None, "Chave de API necessária"
    
    url_search = "https://www.googleapis.com/youtube/v3/search"
    params_search = { "part": "snippet", "q": nicho, "type": "channel", "key": api_key, "maxResults": 20 }
    
    try:
        resp = requests.get(url_search, params=params_search)
        if resp.status_code != 200: return None, f"Erro API: {resp.status_code}"
        
        dados_search = resp.json()
        if "items" not in dados_search: return [], None

        lista_ids = [item["id"]["channelId"] for item in dados_search["items"]]
        ids_concatenados = ",".join(lista_ids)

        url_stats = "https://www.googleapis.com/youtube/v3/channels"
        params_stats = {"part": "statistics", "id": ids_concatenados, "key": api_key}
        resp_stats = requests.get(url_stats, params=params_stats)
        dados_stats = resp_stats.json()

        mapa_stats = {}
        if "items" in dados_stats:
            for item in dados_stats["items"]:
                mapa_stats[item["id"]] = item["statistics"]

        resultado = []
        for item in dados_search["items"]:
            id_canal = item["id"]["channelId"]
            snippet = item["snippet"]
            stats = mapa_stats.get(id_canal, {})
            
            inscritos = int(stats.get("subscriberCount", 0))
            views = int(stats.get("viewCount", 0))
            videos = int(stats.get("videoCount", 0))
            media = views / videos if videos > 0 else 0
            engajamento = (media / inscritos * 100) if inscritos > 0 else 0

            e_ouro = False
            if videos > 0 and videos <= 60 and inscritos >= 1000 and media > 2000:
                e_ouro = True

            resultado.append({
                "nome": snippet["title"],
                "inscritos": inscritos,
                "total_videos": videos,
                "media_views": round(media, 0),
                "score": round(engajamento, 1),
                "e_ouro": e_ouro,
                "link": f"https://www.youtube.com/channel/{id_canal}"
            })
        return resultado, None
    except Exception as e:
        return None, str(e)

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state['logado'] = False

def tela_login():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:white; padding:30px; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,0.05); text-align:center;">
            <h2 style="color:#2c3e50; margin-bottom:10px;">Bem-vindo</h2>
            <p style="color:#718096;">Acesse sua ferramenta de inteligência.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            u = st.text_input("Usuário")
            s = st.text_input("Senha", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("✨ Entrar no Sistema"):
                if u == "admin" and s == "1234":
                    st.session_state['logado'] = True
                    st.rerun()
                else:
                    st.error("Dados inválidos.")

# --- APP PRINCIPAL ---
def app_principal():
    api_key_env = os.getenv("YOUTUBE_API_KEY")
    
    with st.sidebar:
        st.title("Menu")
        if st.button("Sair"):
            st.session_state['logado'] = False
            st.rerun()
    
    st.markdown("<h1 style='text-align: center; color: #2d3748;'>✨ Gold Finder AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #718096; margin-bottom: 30px;'>Descubra oportunidades ocultas.</p>", unsafe_allow_html=True)

    with st.container():
        with st.form(key="search_form"):
            c1, c2 = st.columns([3, 1])
            with c1:
                if not api_key_env:
                    api_key_input = st.text_input("Chave API", type="password")
                else:
                    api_key_input = api_key_env
                nicho = st.text_input("Pesquisar Nicho:", placeholder="Ex: Meditação, Yoga...")
            with c2:
                st.write("")
                st.write("")
                enviar = st.form_submit_button("🔍 Buscar")

    if enviar:
        if not nicho:
            st.warning("Digite um nicho.")
        elif not api_key_input:
            st.warning("Chave necessária.")
        else:
            with st.spinner("Analisando dados..."):
                dados, erro = buscar_dados_youtube(nicho, api_key_input)
                
                if erro:
                    st.error(f"Erro: {erro}")
                elif dados:
                    df = pd.DataFrame(dados)
                    df_ouro = df[df['e_ouro'] == True]
                    
                    # --- AQUI ESTÁ A MÁGICA DO DOWNLOAD ---
                    st.divider()
                    col_res, col_btn = st.columns([3, 1])
                    
                    with col_res:
                         # Mostra quantos achou
                        if not df_ouro.empty:
                            st.success(f"Encontramos {len(df_ouro)} oportunidades GOLD!")
                        else:
                            st.info(f"Encontramos {len(df)} canais no total.")
                            
                    with col_btn:
                        # CORREÇÃO PARA EXCEL BRASILEIRO:
                        # sep=';' -> Separa as colunas corretamente
                        # encoding='utf-8-sig' -> Faz os acentos (ã, é, ç) aparecerem certos
                        csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig')
                        
                        # O Botão de Download
                        st.download_button(
                            label="📥 Baixar Relatório (Excel)",
                            data=csv,
                            file_name=f"relatorio_{nicho.replace(' ', '_')}.csv",
                            mime="text/csv"
                        )
                    # ---------------------------------------

                    if not df_ouro.empty:
                        cols = st.columns(3)
                        for index, row in df_ouro.reset_index().iterrows():
                            with cols[index % 3]:
                                st.markdown(f"""
                                <div class="gold-card">
                                    <div class="gold-badge">GOLD</div>
                                    <h3 style="color:#2d3748; margin:0;">{row['nome']}</h3>
                                    <p style="margin-top:10px; font-size:14px;">
                                        📹 <strong>{row['total_videos']}</strong> vídeos<br>
                                        👥 <strong>{row['inscritos']}</strong> inscritos<br>
                                        👁️ <strong>{row['media_views']:,.0f}</strong> views
                                    </p>
                                    <a href="{row['link']}" target="_blank">
                                        <button style="width:100%; border:1px solid #e2e8f0; background:white; padding:8px; border-radius:10px; cursor:pointer;">Ver Canal ↗</button>
                                    </a>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    st.subheader("Tabela Completa")
                    st.dataframe(
                        df[['nome', 'inscritos', 'total_videos', 'media_views']], 
                        use_container_width=True, 
                        hide_index=True
                    )

if st.session_state['logado']:
    app_principal()
else:
    tela_login()
