import streamlit as st
import pandas as pd
import requests
import os
import datetime
from datetime import timedelta
from dotenv import load_dotenv

# Carrega variáveis
load_dotenv()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Blueberry Finder AI", page_icon="🫐", layout="wide")

# --- CSS "BLUEBERRY UNICORN THEME" 🦄🫐 ---
st.markdown("""
    <style>
    /* 1. FUNDO GERAL (Gradiente Lilás/Azul Suave) */
    .stApp {
        background: linear-gradient(135deg, #f3e7e9 0%, #e3eeff 100%, #e8dbfc 100%);
        background-attachment: fixed;
    }
    header[data-testid="stHeader"] { background: transparent; }

    /* 2. TIPOGRAFIA (Tons de Roxo Profundo) */
    h1, h2, h3 {
        font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
        color: #3d3563 !important; /* Roxo Blueberry Escuro */
        font-weight: 700;
    }
    p, label, span, div, caption {
        color: #544a85 !important; /* Roxo médio para textos */
    }
    .stCaption { color: #7a71a8 !important; }

    /* 3. CARDS (Vidro com Borda Lilás) */
    .gold-card {
        background: rgba(255, 255, 255, 0.80);
        backdrop-filter: blur(15px);
        border: 2px solid #c4b5fd; /* Borda Lilás */
        border-radius: 25px; /* Mais arredondado */
        padding: 25px;
        box-shadow: 0 10px 30px rgba(139, 92, 246, 0.15); /* Sombra roxa suave */
        margin-bottom: 25px;
        position: relative;
        transition: transform 0.3s ease;
    }
    .gold-card:hover { transform: translateY(-5px); }

    .gold-badge {
        background: linear-gradient(90deg, #a78bfa 0%, #f472b6 100%); /* Gradiente Roxo/Rosa */
        color: white !important; padding: 6px 15px; border-radius: 20px;
        font-size: 11px; font-weight: 800; position: absolute; top: -12px; right: 20px;
        box-shadow: 0 5px 15px rgba(167, 139, 250, 0.4);
    }

    /* 4. INPUTS (Campos de texto) */
    .stTextInput input {
        background-color: rgba(255, 255, 255, 0.9) !important;
        border: 2px solid #ddd6fe !important; /* Borda lilás clara */
        color: #3d3563 !important;
        border-radius: 18px !important;
        padding: 15px !important;
        box-shadow: 0 5px 15px rgba(0,0,0,0.02);
    }
    .stTextInput input:focus {
        border-color: #8b5cf6 !important; /* Roxo mais forte ao clicar */
        box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.2) !important;
    }

    /* 5. BOTÕES PRINCIPAIS (Buscar/Login) */
    div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #8b5cf6 0%, #d946ef 100%); /* Gradiente Roxo/Pink vibrante */
        color: #ffffff !important; /* TEXTO BRANCO FORÇADO */
        font-weight: 700 !important;
        border: none; padding: 14px 28px; border-radius: 50px;
        width: 100%; box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4);
        transition: all 0.3s ease;
        font-size: 16px;
    }
    div[data-testid="stFormSubmitButton"] button:hover {
        transform: scale(1.02);
        box-shadow: 0 12px 30px rgba(139, 92, 246, 0.6);
    }

    /* 6. EXPANDER (Área dos vídeos virais) */
    .viral-box {
        background-color: rgba(255,255,255,0.8);
        border-left: 4px solid #8b5cf6;
        padding: 12px; margin-bottom: 12px; border-radius: 0 15px 15px 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE BUSCA (Lógica Pura) ---
def buscar_top_videos(channel_id, api_key):
    data_limite = datetime.datetime.now() - timedelta(days=45)
    published_after = data_limite.isoformat("T") + "Z"
    url = "https://www.googleapis.com/youtube/v3/search"
    params = { "key": api_key, "channelId": channel_id, "part": "snippet", "order": "viewCount", "publishedAfter": published_after, "type": "video", "maxResults": 5 }
    try:
        resp = requests.get(url, params=params)
        dados = resp.json()
        if "items" not in dados: return []
        videos = []
        for item in dados["items"]:
            videos.append({ "titulo": item["snippet"]["title"], "data": item["snippet"]["publishedAt"][:10], "thumb": item["snippet"]["thumbnails"]["high"]["url"], "video_id": item["id"]["videoId"] })
        return videos
    except: return []

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
            for item in dados_stats["items"]: mapa_stats[item["id"]] = item["statistics"]
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
            if videos > 0 and videos <= 60 and inscritos >= 1000 and media > 2000: e_ouro = True
            resultado.append({ "id": id_canal, "nome": snippet["title"], "inscritos": inscritos, "total_videos": videos, "media_views": round(media, 0), "e_ouro": e_ouro, "link": f"https://www.youtube.com/channel/{id_canal}" })
        return resultado, None
    except Exception as e: return None, str(e)

# --- TELA DE LOGIN VISUAL ---
if 'logado' not in st.session_state: st.session_state['logado'] = False

def tela_login():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Card de login visual
        st.markdown("""
        <div style="background:rgba(255,255,255,0.9); backdrop-filter:blur(10px); padding:40px; border-radius:30px; box-shadow:0 20px 40px rgba(139, 92, 246, 0.2); text-align:center; border: 2px solid #eaddff;">
            <h1 style="color:#5a4fcf; margin-bottom:10px; font-size: 2.5em;">🫐</h1>
            <h2 style="color:#3d3563; margin-bottom:5px; font-weight: 800;">Blueberry Channel</h2>
            <p style="color:#6b6399; font-size: 15px;">Bem-vindo ao sistema blueberry de captação.</p>
        </div>
        <br>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            u = st.text_input("Usuário (admin)", placeholder="admin")
            s = st.text_input("Senha (1234)", type="password", placeholder="1234")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("🚀 Acessar Sistema"):
                if u == "admin" and s == "1234":
                    st.session_state['logado'] = True
                    st.rerun()
                else:
                    st.error("Senha incorreta (use admin / 1234)")

# --- APP PRINCIPAL ---
def app_principal():
    api_key_env = os.getenv("YOUTUBE_API_KEY")
    
    with st.sidebar:
        st.markdown("<h3 style='color:#3d3563;'>Menu 🫐</h3>", unsafe_allow_html=True)
        if st.button("Sair da Conta"):
            st.session_state['logado'] = False
            st.rerun()
    
    # --- CABEÇALHO ---
    st.markdown("<h1 style='text-align: center; color: #5a4fcf; font-size: 3.5em; margin-bottom: 10px;text-shadow: 2px 2px 4px rgba(139, 92, 246, 0.3);'>🫐 Blueberry Finder AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6b6399; font-size: 18px; margin-bottom: 40px;'>Sua inteligência artificial para encontrar minas de ouro.</p>", unsafe_allow_html=True)

    with st.container():
        with st.form(key="search_form"):
            c1, c2 = st.columns([3, 1])
            with c1:
                if not api_key_env:
                    api_key_input = st.text_input("Chave API", type="password")
                else:
                    api_key_input = api_key_env
                nicho = st.text_input("Qual nicho vamos explorar?", placeholder="Ex: Confeitaria, ASMR, Curiosidades...")
            with c2:
                st.write("")
                st.write("")
                enviar = st.form_submit_button("🔍 Buscar")

    if enviar and nicho and api_key_input:
        with st.spinner("✨ A mágica está acontecendo..."):
            dados, erro = buscar_dados_youtube(nicho, api_key_input)
            
            if erro:
                st.error(f"Erro: {erro}")
            elif dados:
                df = pd.DataFrame(dados)
                df_ouro = df[df['e_ouro'] == True]
                
                st.divider()
                csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig')
                st.download_button("🦄 Baixar Relatório Completo (Excel)", csv, f"relatorio_blueberry.csv", "text/csv")

                # 1. CARDS DOURADOS
                if not df_ouro.empty:
                    st.success(f"🎉 Sucesso! Encontramos {len(df_ouro)} Canais Blueberry!")
                    cols = st.columns(3)
                    for index, row in df_ouro.reset_index().iterrows():
                        with cols[index % 3]:
                            with st.container():
                                st.markdown(f"""
                                <div class="gold-card">
                                    <div class="gold-badge">BLUEBERRY GOLD</div>
                                    <h4 style="margin:0; color:#3d3563; font-size:1.2em;">{row['nome']}</h4>
                                    <p style="font-size:14px; margin-bottom:15px; color:#6b6399 !important;">
                                        📹 <b>{row['total_videos']}</b> vídeos | 👥 <b>{row['inscritos']}</b> subs
                                    </p>
                                </div>
                                """, unsafe_allow_html=True)
                                with st.expander("🕵️ Ver Virais Recentes (45 dias)"):
                                    videos_top = buscar_top_videos(row['id'], api_key_input)
                                    if videos_top:
                                        prompt_gpt = "Analise estes títulos e crie 5 variações:\n"
                                        for v in videos_top:
                                            st.markdown(f"""
                                            <div class="viral-box">
                                                <img src="{v['thumb']}" style="width:100%; border-radius:12px; margin-bottom:8px;">
                                                <p style="font-weight:700; font-size:13px; color:#3d3563; line-height:1.3;">{v['titulo']}</p>
                                                <p style="font-size:11px; color:#8b5cf6;">📅 {v['data']}</p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                            prompt_gpt += f"- {v['titulo']}\n"
                                        st.caption("🤖 Prompt ChatGPT:")
                                        st.code(prompt_gpt, language="text")
                                    else:
                                        st.warning("Sem virais recentes.")
                                st.markdown(f"""<a href="{row['link']}" target="_blank"><button style="width:100%; border:2px solid #ddd6fe; background:white; color:#6b6399; border-radius:12px; padding:10px; cursor:pointer; font-weight:600; transition:0.3s;">Visitar Canal ↗</button></a>""", unsafe_allow_html=True)
                else:
                    st.info("Nenhum canal 'Blueberry Gold' encontrado hoje.")
                
                # 2. TABELA GERAL (AGORA COM LINKS!)
                st.divider()
                st.markdown("<h3 style='color:#3d3563;'>📊 Tabela Geral do Nicho</h3>", unsafe_allow_html=True)
                st.dataframe(
                    # Adicionei 'link' aqui na lista de colunas
                    df[['nome', 'inscritos', 'total_videos', 'media_views', 'link']],
                    column_config={
                        "nome": "Canal",
                        "inscritos": st.column_config.NumberColumn("Inscritos", format="%d"),
                        "total_videos": st.column_config.NumberColumn("Vídeos"),
                        "media_views": st.column_config.NumberColumn("Média Views", format="%d"),
                        # Adicionei a configuração da nova coluna de Link
                        "link": st.column_config.LinkColumn("Acessar Canal", display_text="Ver Canal ↗")
                    },
                    use_container_width=True,
                    hide_index=True
                )

if st.session_state['logado']:
    app_principal()
else:
    tela_login()
