import streamlit as st
import pandas as pd
import requests
import os
import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="YouTube Gold Finder", page_icon="💎", layout="wide")

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

# --- CSS "APPLE GLASS" ULTRA PREMIUM ---
st.markdown("""
    <style>
    /* Fundo Gradiente */
    [data-testid="stAppViewContainer"] {
        background-image: linear-gradient(to top right, #0F2027 0%, #203A43 50%, #2C5364 100%);
        background-attachment: fixed;
    }
    
    /* Blocos de Vidro */
    [data-testid="stAppViewBlockContainer"] {
        background-color: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }
    
    /* Tipografia e Cores */
    h1, h2, h3, p, span, div, label { color: #ffffff !important; font-family: 'Helvetica Neue', sans-serif; }
    
    /* Botões */
    .stButton button {
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
        color: #000 !important;
        font-weight: bold !important;
        border: none;
        border-radius: 25px;
        transition: transform 0.2s;
    }
    .stButton button:hover { transform: scale(1.05); }

    /* Inputs */
    .stTextInput input {
        background-color: rgba(0,0,0,0.3) !important;
        color: white !important;
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    /* Destaque para o "Ouro" */
    .gold-box {
        background-color: rgba(255, 215, 0, 0.15);
        border: 1px solid gold;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE BUSCA (ATUALIZADA) ---
def buscar_dados_youtube(nicho, api_key):
    if not api_key: return None, "Configure a API Key nas Secrets"

    # 1. AUMENTAMOS PARA 20 CANAIS
    url_search = "https://www.googleapis.com/youtube/v3/search"
    params_search = {
        "part": "snippet", "q": nicho, "type": "channel", 
        "key": api_key, "maxResults": 20 
    }
    
    try:
        resp = requests.get(url_search, params=params_search)
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

            # CRITÉRIO DE OURO: Validamos aqui se compensa modelar
            # Regra: < 50 videos E > 1000 inscritos E média > 3000 views
            e_ouro = False
            motivo = ""
            if videos > 0 and videos <= 50 and inscritos >= 1000 and media > 3000:
                e_ouro = True
                motivo = "🚀 Poucos vídeos, Muitas views!"

            resultado.append({
                "nome": snippet["title"],
                "inscritos": inscritos,
                "total_videos": videos,
                "media_views": round(media, 0),
                "score": round(engajamento, 1),
                "e_ouro": e_ouro, # Nova flag
                "motivo": motivo,
                "link": f"https://www.youtube.com/channel/{id_canal}"
            })
            
        return resultado, None
    except Exception as e:
        return None, str(e)

# --- SISTEMA DE LOGIN ---
if 'logado' not in st.session_state: st.session_state['logado'] = False

def tela_login():
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("🔒 Login SaaS")
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.button("Acessar Painel", use_container_width=True):
            if u == "admin" and s == "1234":
                st.session_state['logado'] = True
                st.rerun()
            else:
                st.error("Acesso negado")

# --- APP PRINCIPAL ---
def app_principal():
    api_key = os.getenv("YOUTUBE_API_KEY") # Tenta pegar local
    
    with st.sidebar:
        st.header("Menu")
        if st.button("Sair"):
            st.session_state['logado'] = False
            st.rerun()
    
    st.title("💎 Caçador de Canais de Ouro")
    st.write("Identifique canais novos que estão explodindo para modelar.")
    
    # Campo de API KEY se não estiver no .env (para facilitar teste na nuvem)
    if not api_key:
        api_key = st.text_input("Cole sua API Key do YouTube aqui (Temporário):", type="password")

    nicho = st.text_input("Digite o Nicho:", placeholder="Ex: Investimentos, ASMR, Cortes Podcast...")
    
    if st.button("🔎 Analisar Mercado", type="primary") and nicho and api_key:
        with st.spinner("Minerando 20 canais e procurando pepitas de ouro..."):
            dados, erro = buscar_dados_youtube(nicho, api_key)
            
            if erro:
                st.error(f"Erro: {erro}")
            elif dados:
                df = pd.DataFrame(dados)
                
                # --- SESSÃO 1: AS PEPITAS DE OURO (FILTRO QUE VOCÊ PEDIU) ---
                # Filtra apenas os que marcamos como "e_ouro" = True
                df_ouro = df[df['e_ouro'] == True]
                
                st.divider()
                if not df_ouro.empty:
                    st.success(f"🔥 ENCONTRAMOS {len(df_ouro)} CANAIS PERFEITOS PARA MODELAR!")
                    st.markdown("Estes canais têm **menos de 50 vídeos**, **mais de 1.000 inscritos** e **alta visualização**.")
                    
                    for index, row in df_ouro.iterrows():
                        with st.container():
                            st.markdown(f"""
                            <div class="gold-box">
                                <h3>🏆 {row['nome']}</h3>
                                <p>📹 <b>Vídeos:</b> {row['total_videos']} (Muito Baixo!)</p>
                                <p>👥 <b>Inscritos:</b> {row['inscritos']}</p>
                                <p>👁️ <b>Média Views:</b> {row['media_views']:,.0f}</p>
                                <a href="{row['link']}" target="_blank" style="text-decoration:none;">
                                    <button style="background:white; color:black; border:none; padding:10px; border-radius:10px; cursor:pointer;">
                                        Ver Canal no YouTube ↗
                                    </button>
                                </a>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Nenhum canal 'Mina de Ouro' encontrado neste nicho com as regras (Vídeos < 50 e Inscritos > 1k). Tente outro nicho!")

                # --- SESSÃO 2: TABELA GERAL (TOP 20) ---
                st.divider()
                st.subheader(f"📊 Análise Geral (Top {len(df)} Canais)")
                st.dataframe(
                    df[['nome', 'total_videos', 'inscritos', 'media_views', 'link']],
                    column_config={
                        "link": st.column_config.LinkColumn("Link"),
                        "media_views": st.column_config.NumberColumn("Média Views"),
                        "total_videos": st.column_config.NumberColumn("Total Vídeos"),
                    },
                    use_container_width=True, hide_index=True
                )

if st.session_state['logado']:
    app_principal()
else:
    tela_login()