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

# --- CSS "ZEN PASTEL" (A Mágica Visual) ---
st.markdown("""
    <style>
    /* 1. FUNDO GERAL (Gradiente Pastel Fluido) */
    .stApp {
        background: linear-gradient(120deg, #fdfbfb 0%, #ebedee 100%);
        /* Se preferir colorido suave: background: linear-gradient(to top, #accbee 0%, #e7f0fd 100%); */
        background-attachment: fixed;
    }

    /* 2. HEADER TRANSPARENTE */
    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* 3. TIPOGRAFIA (Legibilidade Máxima) */
    h1, h2, h3 {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #2c3e50 !important; /* Azul escuro profundo, não preto */
        font-weight: 700;
    }
    p, label, span, div {
        color: #4a5568 !important; /* Cinza médio confortável */
        font-size: 16px;
    }

    /* 4. CARDS (Efeito Vidro Branco) */
    .card-container {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.6);
        border-radius: 20px;
        padding: 25px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05); /* Sombra super suave */
        margin-bottom: 20px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .card-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
    }

    /* 5. DESTAQUE DOURADO (Suave e Elegante) */
    .gold-card {
        background: linear-gradient(135deg, #ffffff 0%, #fffbf0 100%);
        border: 2px solid #f6e6b4; /* Ouro pastel */
        border-radius: 20px;
        padding: 25px;
        box-shadow: 0 10px 25px rgba(212, 175, 55, 0.15);
        margin-bottom: 20px;
        position: relative;
        transition: transform 0.3s ease;
    }
    .gold-card:hover {
        transform: scale(1.02);
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
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }

    /* 6. INPUTS (Campos de texto modernos) */
    .stTextInput input {
        background-color: #ffffff !important;
        border: 2px solid #e2e8f0 !important;
        color: #2d3748 !important;
        border-radius: 15px !important;
        padding: 15px !important;
        font-size: 16px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    .stTextInput input:focus {
        border-color: #a0aec0 !important;
        box-shadow: 0 0 0 3px rgba(160, 174, 192, 0.2) !important;
    }

    /* 7. BOTÕES (Gradientes Pastéis) */
    div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); /* Roxo/Azul Moderno */
        /* Ou opção mais calma: background: linear-gradient(to right, #4facfe 0%, #00f2fe 100%); */
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 50px; /* Pílula completa */
        font-weight: 600;
        font-size: 16px;
        width: 100%;
        box-shadow: 0 4px 15px rgba(118, 75, 162, 0.3);
        transition: all 0.3s ease;
    }
    div[data-testid="stFormSubmitButton"] button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(118, 75, 162, 0.4);
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
            # Regra: < 60 videos, > 1k inscritos, > 2k views médias
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
        # Card de login branco e limpo
        st.markdown("""
        <div style="background:white; padding:30px; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,0.05); text-align:center;">
            <h2 style="color:#2c3e50; margin-bottom:10px;">Bem-vindo</h2>
            <p style="color:#718096;">Acesse sua ferramenta de inteligência.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            u = st.text_input("Usuário", placeholder="Digite seu usuário")
            s = st.text_input("Senha", type="password", placeholder="••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            btn = st.form_submit_button("✨ Entrar no Sistema")
            
            if btn:
                if u == "admin" and s == "1234":
                    st.session_state['logado'] = True
                    st.rerun()
                else:
                    st.error("Dados de acesso inválidos.")

# --- APP PRINCIPAL ---
def app_principal():
    api_key_env = os.getenv("YOUTUBE_API_KEY")
    
    with st.sidebar:
        st.title("Navegação")
        st.caption(f"Logado como: admin")
        if st.button("Sair do Sistema"):
            st.session_state['logado'] = False
            st.rerun()
    
    # Cabeçalho Zen
    st.markdown("<h1 style='text-align: center; color: #2d3748;'>✨ Gold Finder AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #718096; margin-bottom: 40px;'>Descubra oportunidades ocultas com clareza e precisão.</p>", unsafe_allow_html=True)

    # Área de Busca
    with st.container():
        with st.form(key="search_form"):
            c1, c2 = st.columns([3, 1])
            with c1:
                if not api_key_env:
                    api_key_input = st.text_input("Chave API", type="password")
                else:
                    api_key_input = api_key_env
                nicho = st.text_input("O que você quer descobrir hoje?", placeholder="Ex: Meditação, Yoga, Finanças Pessoais...")
            with c2:
                st.write("")
                st.write("")
                enviar = st.form_submit_button("🔍 Iniciar Busca")

    if enviar:
        if not nicho:
            st.warning("Por favor, digite um tema.")
        elif not api_key_input:
            st.warning("Chave de API necessária.")
        else:
            with st.spinner("Conectando ao universo de dados..."):
                dados, erro = buscar_dados_youtube(nicho, api_key_input)
                
                if erro:
                    st.error(f"Erro: {erro}")
                elif dados:
                    df = pd.DataFrame(dados)
                    df_ouro = df[df['e_ouro'] == True]
                    
                    st.divider()
                    
                    # RESULTADOS DOURADOS
                    if not df_ouro.empty:
                        st.markdown(f"<h3 style='color:#d4af37'>🏆 {len(df_ouro)} Oportunidades Encontradas</h3>", unsafe_allow_html=True)
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
                                        👁️ <strong>{row['media_views']:,.0f}</strong> views/vídeo
                                    </p>
                                    <a href="{row['link']}" target="_blank" style="text-decoration:none;">
                                        <button style="width:100%; background:#fcfcfc; border:1px solid #e2e8f0; color:#4a5568; padding:8px; border-radius:10px; cursor:pointer; font-weight:600; margin-top:5px; transition:0.3s;">
                                            Visitar Canal ↗
                                        </button>
                                    </a>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.info("Nenhuma oportunidade 'Gold' encontrada. Tente termos mais específicos.")

                    # RESULTADOS GERAIS
                    st.divider()
                    st.subheader("📊 Visão Geral do Mercado")
                    
                    # Card Branco para a tabela
                    st.markdown('<div class="card-container">', unsafe_allow_html=True)
                    st.dataframe(
                        df[['nome', 'inscritos', 'total_videos', 'media_views', 'link']],
                        column_config={
                            "nome": "Canal",
                            "inscritos": st.column_config.NumberColumn("Inscritos", format="%d"),
                            "total_videos": st.column_config.NumberColumn("Vídeos"),
                            "media_views": st.column_config.NumberColumn("Views Médias", format="%d"),
                            "link": st.column_config.LinkColumn("Link")
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state['logado']:
    app_principal()
else:
    tela_login()