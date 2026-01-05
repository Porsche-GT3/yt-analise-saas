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
    [data-testid="stAppViewBlockContainer"] {
        background-color: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    h1, h2, h3, p, span, div, label { color: #ffffff !important; font-family: 'Helvetica Neue', sans-serif; }
    
    /* Botões dentro do form */
    div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
        color: #000 !important;
        font-weight: bold !important;
        border: none;
        border-radius: 25px;
        width: 100%; /* Botão ocupa largura total */
    }
    
    .stTextInput input {
        background-color: rgba(0,0,0,0.3) !important;
        color: white !important;
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,0.2);
    }
    .gold-box {
        background-color: rgba(255, 215, 0, 0.15);
        border: 1px solid gold;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE BUSCA ---
def buscar_dados_youtube(nicho, api_key):
    if not api_key: return None, "Configure a API Key"
    
    url_search = "https://www.googleapis.com/youtube/v3/search"
    params_search = { "part": "snippet", "q": nicho, "type": "channel", "key": api_key, "maxResults": 20 }
    
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

            e_ouro = False
            motivo = ""
            if videos > 0 and videos <= 50 and inscritos >= 1000 and media > 3000:
                e_ouro = True
                motivo = "🚀 Oportunidade Validada!"

            resultado.append({
                "nome": snippet["title"],
                "inscritos": inscritos,
                "total_videos": videos,
                "media_views": round(media, 0),
                "score": round(engajamento, 1),
                "e_ouro": e_ouro,
                "motivo": motivo,
                "link": f"https://www.youtube.com/channel/{id_canal}"
            })
        return resultado, None
    except Exception as e:
        return None, str(e)

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state['logado'] = False

def tela_login():
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("🔒 Login SaaS")
        with st.form("login_form"):
            u = st.text_input("Usuário")
            s = st.text_input("Senha", type="password")
            btn_login = st.form_submit_button("Acessar Painel")
            
            if btn_login:
                if u == "admin" and s == "1234":
                    st.session_state['logado'] = True
                    st.rerun()
                else:
                    st.error("Acesso negado")

# --- APP PRINCIPAL ---
def app_principal():
    api_key_env = os.getenv("YOUTUBE_API_KEY")
    
    with st.sidebar:
        st.header("Menu")
        if st.button("Sair"):
            st.session_state['logado'] = False
            st.rerun()
    
    st.title("💎 Caçador de Canais de Ouro")
    st.write("Identifique canais novos que estão explodindo para modelar.")

    # --- AQUI ESTÁ A MUDANÇA: O FORMULÁRIO ---
    # Ao usar 'with st.form', o Enter funciona para enviar!
    with st.form(key="search_form"):
        # Se não tiver chave no ambiente, pede aqui dentro do form
        if not api_key_env:
            api_key_input = st.text_input("Cole sua API Key do YouTube:", type="password")
        else:
            api_key_input = api_key_env
        
        nicho = st.text_input("Digite o Nicho:", placeholder="Ex: Historia triste, Dark Web, Curiosidades...")
        
        # O botão agora é de "submit" (envio)
        enviar = st.form_submit_button("🔍 Analisar Mercado")

    # A lógica só roda se o botão de envio (ou Enter) for acionado
    if enviar:
        if not nicho:
            st.warning("Por favor, digite um nicho.")
        elif not api_key_input:
            st.warning("Precisamos da API Key para funcionar.")
        else:
            with st.spinner("Minerando 20 canais e procurando pepitas de ouro..."):
                dados, erro = buscar_dados_youtube(nicho, api_key_input)
                
                if erro:
                    st.error(f"Erro: {erro}")
                elif dados:
                    df = pd.DataFrame(dados)
                    df_ouro = df[df['e_ouro'] == True]
                    
                    st.divider()
                    if not df_ouro.empty:
                        st.success(f"🔥 ENCONTRAMOS {len(df_ouro)} CANAIS DE OURO!")
                        for index, row in df_ouro.iterrows():
                            st.markdown(f"""
                            <div class="gold-box">
                                <h3>🏆 {row['nome']}</h3>
                                <p>📹 <b>Vídeos:</b> {row['total_videos']} (Baixo esforço)</p>
                                <p>👥 <b>Inscritos:</b> {row['inscritos']}</p>
                                <p>👁️ <b>Média Views:</b> {row['media_views']:,.0f}</p>
                                <a href="{row['link']}" target="_blank">
                                    <button style="background:white; color:black; border:none; padding:8px 15px; border-radius:15px; cursor:pointer;">
                                        Ver Canal ↗
                                    </button>
                                </a>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.warning("Nenhum canal 'Mina de Ouro' (Vídeos < 50 e Views Altas) encontrado. Tente outro termo!")

                    st.divider()
                    st.subheader("📊 Tabela Geral")
                    st.dataframe(
                        df[['nome', 'total_videos', 'inscritos', 'media_views', 'link']],
                        column_config={
                            "link": st.column_config.LinkColumn("Link"),
                            "media_views": st.column_config.NumberColumn("Views Médias"),
                        },
                        use_container_width=True, hide_index=True
                    )

if st.session_state['logado']:
    app_principal()
else:
    tela_login()