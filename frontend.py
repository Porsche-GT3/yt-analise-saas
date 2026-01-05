import streamlit as st
import pandas as pd
import requests
import os
import datetime
from datetime import timedelta
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
    h1, h2, h3 { font-family: 'Inter', sans-serif; color: #2c3e50 !important; font-weight: 700; }
    p, label, span, div { color: #4a5568 !important; }

    /* 3. CARDS */
    .gold-card {
        background: linear-gradient(135deg, #ffffff 0%, #fffbf0 100%);
        border: 2px solid #f6e6b4;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 10px 25px rgba(212, 175, 55, 0.15);
        margin-bottom: 20px;
        position: relative;
    }
    .gold-badge {
        background: linear-gradient(90deg, #fce38a 0%, #f38181 100%);
        color: white; padding: 5px 15px; border-radius: 15px;
        font-size: 10px; font-weight: bold; position: absolute; top: -10px; right: 15px;
    }

    /* 4. BOTÕES */
    div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; border: none; padding: 12px 24px; border-radius: 50px;
        width: 100%; box-shadow: 0 4px 15px rgba(118, 75, 162, 0.3);
    }
    
    /* 5. ÁREA DE VÍDEOS VIRAIS (Dentro do Expander) */
    .viral-box {
        background-color: #f8fafc;
        border-left: 3px solid #667eea;
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 0 10px 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- NOVA FUNÇÃO: BUSCAR TOP VÍDEOS RECENTES ---
def buscar_top_videos(channel_id, api_key):
    # 1. Define a data limite (45 dias atrás) no formato que o YouTube exige (RFC 3339)
    data_limite = datetime.datetime.now() - timedelta(days=45)
    published_after = data_limite.isoformat("T") + "Z" # Ex: 2023-11-20T00:00:00Z
    
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": api_key,
        "channelId": channel_id,
        "part": "snippet",
        "order": "viewCount", # Ordena pelos mais vistos
        "publishedAfter": published_after, # Só os novos
        "type": "video",
        "maxResults": 5
    }
    
    try:
        resp = requests.get(url, params=params)
        dados = resp.json()
        if "items" not in dados: return []
        
        videos = []
        for item in dados["items"]:
            videos.append({
                "titulo": item["snippet"]["title"],
                "data": item["snippet"]["publishedAt"][:10], # Pega só a data YYYY-MM-DD
                "thumb": item["snippet"]["thumbnails"]["high"]["url"],
                "video_id": item["id"]["videoId"]
            })
        return videos
    except:
        return []

# --- LÓGICA DE BUSCA DE CANAIS ---
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
            
            e_ouro = False
            # Regra mantida: < 60 videos, > 1k inscritos, > 2k views
            if videos > 0 and videos <= 60 and inscritos >= 1000 and media > 2000:
                e_ouro = True

            resultado.append({
                "id": id_canal, # Importante para buscar os vídeos depois
                "nome": snippet["title"],
                "inscritos": inscritos,
                "total_videos": videos,
                "media_views": round(media, 0),
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
            <h2 style="color:#2c3e50; margin-bottom:10px;">Login</h2>
        </div>""", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Usuário")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                if u == "admin" and s == "1234":
                    st.session_state['logado'] = True
                    st.rerun()
                else:
                    st.error("Erro.")

# --- APP PRINCIPAL ---
def app_principal():
    api_key_env = os.getenv("YOUTUBE_API_KEY")
    
    with st.sidebar:
        st.title("Menu")
        if st.button("Sair"):
            st.session_state['logado'] = False
            st.rerun()
    
    st.markdown("<h1 style='text-align: center; color: #2d3748;'>✨ Gold Finder AI</h1>", unsafe_allow_html=True)

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

    if enviar and nicho and api_key_input:
        with st.spinner("Minerando Canais e Analisando Vídeos..."):
            dados, erro = buscar_dados_youtube(nicho, api_key_input)
            
            if erro:
                st.error(f"Erro: {erro}")
            elif dados:
                df = pd.DataFrame(dados)
                df_ouro = df[df['e_ouro'] == True]
                
                st.divider()
                
                # Botão CSV Global
                csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig')
                st.download_button("📥 Baixar Relatório (Excel)", csv, f"relatorio.csv", "text/csv")

                if not df_ouro.empty:
                    st.success(f"🔥 {len(df_ouro)} Minas de Ouro Encontradas!")
                    
                    # Layout em Grid
                    cols = st.columns(3)
                    for index, row in df_ouro.reset_index().iterrows():
                        with cols[index % 3]:
                            with st.container():
                                st.markdown(f"""
                                <div class="gold-card">
                                    <div class="gold-badge">GOLD</div>
                                    <h4 style="margin:0; color:#2d3748;">{row['nome']}</h4>
                                    <p style="font-size:13px; margin-bottom:5px;">
                                        📹 {row['total_videos']} vids | 👥 {row['inscritos']} subs
                                    </p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # --- AQUI ESTÁ A MÁGICA: O RAIO-X DO VÍDEO ---
                                with st.expander("🕵️ Ver Top 5 Virais (45 dias)"):
                                    # Busca os vídeos SÓ quando expande (ou se quisermos carregar antes, aqui carrega na hora)
                                    # Para performance, vamos buscar agora:
                                    videos_top = buscar_top_videos(row['id'], api_key_input)
                                    
                                    if videos_top:
                                        prompt_gpt = "Atue como especialista em YouTube. Analise estes títulos virais e crie 5 variações para o meu nicho mantendo a estrutura psicológica:\n\n"
                                        
                                        for v in videos_top:
                                            st.markdown(f"""
                                            <div class="viral-box">
                                                <img src="{v['thumb']}" style="width:100%; border-radius:8px; margin-bottom:5px;">
                                                <p style="font-weight:bold; font-size:12px; color:#2d3748; line-height:1.2;">{v['titulo']}</p>
                                                <p style="font-size:10px; color:#718096;">📅 {v['data']}</p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                            prompt_gpt += f"- {v['titulo']}\n"
                                        
                                        st.divider()
                                        st.caption("🤖 Prompt para Modelagem:")
                                        st.code(prompt_gpt, language="text")
                                    else:
                                        st.warning("Nenhum vídeo bombou nos últimos 45 dias.")
                                        
                                # Botão de ver canal
                                st.markdown(f"""<a href="{row['link']}" target="_blank"><button style="width:100%; border:1px solid #ddd; background:white; border-radius:5px; cursor:pointer;">Ir para YouTube ↗</button></a>""", unsafe_allow_html=True)

                else:
                    st.info("Nenhuma oportunidade Gold encontrada.")

                st.divider()
                st.subheader("Tabela Geral")
                st.dataframe(df[['nome', 'inscritos', 'media_views']], use_container_width=True, hide_index=True)

if st.session_state['logado']:
    app_principal()
else:
    tela_login()
