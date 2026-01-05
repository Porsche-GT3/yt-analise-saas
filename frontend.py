import streamlit as st
import pandas as pd
import requests
import os
import datetime
from datetime import timedelta
from collections import Counter
from dotenv import load_dotenv

# Carrega variáveis
load_dotenv()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Blueberry Finder AI", page_icon="🫐", layout="wide")

# --- CSS "BLUEBERRY UNICORN THEME" 🦄🫐 ---
st.markdown("""
    <style>
    /* 1. FUNDO GERAL */
    .stApp {
        background: linear-gradient(135deg, #f3e7e9 0%, #e3eeff 100%, #e8dbfc 100%);
        background-attachment: fixed;
    }
    header[data-testid="stHeader"] { background: transparent; }

    /* 2. TIPOGRAFIA */
    h1, h2, h3 { font-family: 'Inter', sans-serif; color: #3d3563 !important; font-weight: 700; }
    p, label, span, div, caption { color: #544a85 !important; }

    /* 3. CARDS */
    .gold-card {
        background: rgba(255, 255, 255, 0.80); backdrop-filter: blur(15px);
        border: 2px solid #c4b5fd; border-radius: 25px; padding: 25px;
        box-shadow: 0 10px 30px rgba(139, 92, 246, 0.15); margin-bottom: 25px;
        transition: transform 0.3s ease;
    }
    .gold-card:hover { transform: translateY(-5px); }

    .gold-badge {
        background: linear-gradient(90deg, #a78bfa 0%, #f472b6 100%);
        color: white !important; padding: 6px 15px; border-radius: 20px;
        font-size: 11px; font-weight: 800; position: absolute; top: -12px; right: 20px;
    }
    
    /* 4. INPUTS E BOTÕES */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(255, 255, 255, 0.9) !important;
        border: 2px solid #ddd6fe !important; color: #3d3563 !important;
        border-radius: 18px !important;
    }
    div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #8b5cf6 0%, #d946ef 100%);
        color: #ffffff !important; font-weight: 700 !important; border: none;
        padding: 14px 28px; border-radius: 50px; width: 100%;
        box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4);
    }
    
    /* 5. TOPICOS EM ALTA (Radar) */
    .trend-tag {
        display: inline-block; background: #eaddff; color: #3d3563;
        padding: 5px 12px; border-radius: 15px; margin: 3px; font-size: 12px; font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE BUSCA E RADAR ---

def buscar_tendencias_globais(pais_code, api_key):
    """Busca os vídeos em alta (Trending) de um país e extrai os nichos."""
    if not api_key: return None, "API Key necessária"
    
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": pais_code,
        "maxResults": 50, # Analisa os top 50 do país
        "key": api_key
    }
    
    try:
        resp = requests.get(url, params=params)
        dados = resp.json()
        if "items" not in dados: return [], "Nenhum dado encontrado"

        # Análise Inteligente de Nichos
        todos_tags = []
        videos_analisados = []
        
        for item in dados["items"]:
            stats = item["statistics"]
            snippet = item["snippet"]
            tags = snippet.get("tags", [])
            
            # Adiciona tags à lista geral para contagem
            if tags:
                todos_tags.extend([t.lower() for t in tags])
            
            videos_analisados.append({
                "titulo": snippet["title"],
                "canal": snippet["channelTitle"],
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "tags": tags[:5] if tags else ["Geral"], # Pega as 5 primeiras tags
                "thumb": snippet["thumbnails"]["high"]["url"],
                "link": f"https://www.youtube.com/watch?v={item['id']}"
            })

        # Conta as palavras-chave mais repetidas (Isso define o Nicho em Alta)
        contagem = Counter(todos_tags)
        top_nichos = contagem.most_common(15) # Top 15 assuntos do momento
        
        return {"videos": videos_analisados, "top_assuntos": top_nichos}, None

    except Exception as e:
        return None, str(e)

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
    # (Função de busca normal mantida igual)
    if not api_key: return None, "Chave de API necessária"
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {"part": "snippet", "q": nicho, "type": "channel", "key": api_key, "maxResults": 20}
        resp = requests.get(url, params=params)
        dados = resp.json()
        if "items" not in dados: return [], None
        
        ids = ",".join([i["id"]["channelId"] for i in dados["items"]])
        stats_resp = requests.get("https://www.googleapis.com/youtube/v3/channels", params={"part":"statistics", "id": ids, "key": api_key})
        stats_map = {i["id"]: i["statistics"] for i in stats_resp.json().get("items", [])}
        
        resultado = []
        for item in dados["items"]:
            cid = item["id"]["channelId"]
            stats = stats_map.get(cid, {})
            videos = int(stats.get("videoCount", 0))
            inscritos = int(stats.get("subscriberCount", 0))
            views = int(stats.get("viewCount", 0))
            media = views/videos if videos > 0 else 0
            e_ouro = True if (0 < videos <= 60 and inscritos >= 1000 and media > 2000) else False
            resultado.append({"nome": item["snippet"]["title"], "inscritos": inscritos, "total_videos": videos, "media_views": media, "e_ouro": e_ouro, "link": f"https://www.youtube.com/channel/{cid}", "id": cid})
        return resultado, None
    except Exception as e: return None, str(e)

# --- TELA DE LOGIN ---
if 'logado' not in st.session_state: st.session_state['logado'] = False

def tela_login():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
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
                else: st.error("Senha incorreta.")

# --- APP PRINCIPAL ---
def app_principal():
    api_key_env = os.getenv("YOUTUBE_API_KEY")
    
    with st.sidebar:
        st.markdown("<h3 style='color:#3d3563;'>Menu 🫐</h3>", unsafe_allow_html=True)
        # Seletor de Modo
        modo = st.radio("Navegação:", ["🔍 Busca por Nicho", "🌍 Radar Global"])
        st.divider()
        if st.button("Sair da Conta"):
            st.session_state['logado'] = False
            st.rerun()
    
    st.markdown("<h1 style='text-align: center; color: #5a4fcf; margin-bottom: 10px;'>🫐 Blueberry Finder AI</h1>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # MODO 1: BUSCA POR NICHO (O que já existia)
    # ---------------------------------------------------------
    if modo == "🔍 Busca por Nicho":
        st.markdown("<p style='text-align: center; color: #6b6399;'>Sua inteligência artificial para encontrar minas de ouro.</p>", unsafe_allow_html=True)
        
        with st.form(key="search_form"):
            c1, c2 = st.columns([3, 1])
            with c1:
                key_input = api_key_env if api_key_env else st.text_input("Chave API", type="password")
                nicho = st.text_input("Qual nicho vamos explorar?", placeholder="Ex: Confeitaria, ASMR...")
            with c2:
                st.write(""); st.write("")
                enviar = st.form_submit_button("🔍 Buscar")

        if enviar and nicho:
            with st.spinner("✨ Minerando dados..."):
                dados, erro = buscar_dados_youtube(nicho, key_input)
                if erro: st.error(erro)
                elif dados:
                    df = pd.DataFrame(dados)
                    df_ouro = df[df['e_ouro'] == True]
                    st.divider()
                    
                    # Cards Dourados
                    if not df_ouro.empty:
                        st.success(f"🎉 Encontramos {len(df_ouro)} Canais Blueberry!")
                        cols = st.columns(3)
                        for i, row in df_ouro.reset_index().iterrows():
                            with cols[i % 3]:
                                with st.container():
                                    st.markdown(f"""
                                    <div class="gold-card">
                                        <div class="gold-badge">BLUEBERRY GOLD</div>
                                        <h4 style="margin:0; color:#3d3563;">{row['nome']}</h4>
                                        <p style="font-size:14px; margin-bottom:15px;">📹 <b>{row['total_videos']}</b> vids | 👥 <b>{row['inscritos']}</b> subs</p>
                                    </div>""", unsafe_allow_html=True)
                                    with st.expander("🕵️ Ver Virais (45 dias)"):
                                        vids = buscar_top_videos(row['id'], key_input)
                                        if vids:
                                            prompt = "Analise estes títulos e crie variações:\n"
                                            for v in vids:
                                                st.markdown(f"**{v['titulo']}**<br><span style='font-size:10px'>{v['data']}</span><hr style='margin:5px 0'>", unsafe_allow_html=True)
                                                prompt += f"- {v['titulo']}\n"
                                            st.code(prompt, language="text")
                                        else: st.warning("Sem virais recentes.")
                                    st.markdown(f"<a href='{row['link']}' target='_blank'>Ver Canal ↗</a>", unsafe_allow_html=True)
                    else: st.info("Sem canais Gold hoje.")

                    # Tabela
                    st.divider()
                    st.markdown("### 📊 Tabela Geral")
                    st.dataframe(df[['nome', 'inscritos', 'total_videos', 'media_views', 'link']], column_config={"link": st.column_config.LinkColumn("Link", display_text="Ver ↗")}, use_container_width=True)

    # ---------------------------------------------------------
    # MODO 2: RADAR GLOBAL (O NOVO!) 🌍
    # ---------------------------------------------------------
    elif modo == "🌍 Radar Global":
        st.markdown("<p style='text-align: center; color: #6b6399;'>Veja o que o mundo está assistindo <b>AGORA</b>.</p>", unsafe_allow_html=True)
        
        # Mapeamento de Países
        paises = {
            "🇺🇸 Estados Unidos": "US",
            "🇧🇷 Brasil": "BR",
            "🇵🇹 Portugal": "PT",
            "🇬🇧 Reino Unido": "GB",
            "🇫🇷 França": "FR",
            "🇩🇪 Alemanha": "DE",
            "🇪🇸 Espanha": "ES",
            "🇲🇽 México": "MX",
            "🇨🇦 Canadá": "CA",
            "🇯🇵 Japão": "JP",
            "🇰🇷 Coreia do Sul": "KR",
            "🇮🇳 Índia": "IN",
            "🇦🇺 Austrália": "AU",
            "🇷🇺 Rússia": "RU"
        }
        
        col_sel, col_btn = st.columns([3, 1])
        with col_sel:
            pais_selecionado = st.selectbox("Escolha o País para Espionar:", list(paises.keys()))
        with col_btn:
            st.write(""); st.write("") # Espaço
            key_input_radar = api_key_env if api_key_env else st.text_input("API Key Radar", type="password")
            
        if st.button("📡 Escanear Tendências", type="primary"):
            codigo_pais = paises[pais_selecionado]
            with st.spinner(f"Interceptando sinal do YouTube {codigo_pais}..."):
                resultado, erro = buscar_tendencias_globais(codigo_pais, key_input_radar)
                
                if erro:
                    st.error(erro)
                elif resultado:
                    videos = resultado["videos"]
                    top_assuntos = resultado["top_assuntos"]
                    
                    # 1. VISÃO GERAL DOS NICHOS (Tags mais frequentes)
                    st.divider()
                    st.subheader(f"🔥 Nichos/Assuntos em Alta em: {pais_selecionado}")
                    
                    # Mostra os top assuntos como etiquetas coloridas
                    html_tags = ""
                    for assunto, count in top_assuntos:
                        # Filtra palavras inúteis muito curtas ou genéricas demais se quiser
                        if len(assunto) > 2:
                            html_tags += f"<span class='trend-tag'>#{assunto.upper()} ({count})</span>"
                    
                    st.markdown(f"<div style='background:white; padding:20px; border-radius:15px; border:1px solid #c4b5fd;'>{html_tags}</div>", unsafe_allow_html=True)
                    st.caption("*(O número indica quantos vídeos no Top 50 estão usando essa palavra-chave agora)*")

                    # 2. LISTA DETALHADA DOS VÍDEOS EM ALTA
                    st.divider()
                    st.subheader(f"📹 Top Vídeos Virais ({len(videos)})")
                    
                    # Exibe em grid de 2 colunas
                    col_v1, col_v2 = st.columns(2)
                    for i, vid in enumerate(videos):
                        col_atual = col_v1 if i % 2 == 0 else col_v2
                        with col_atual:
                            with st.container():
                                st.markdown(f"""
                                <div style="background:rgba(255,255,255,0.6); padding:15px; border-radius:15px; margin-bottom:15px; border:1px solid #eaddff; display:flex; gap:10px;">
                                    <img src="{vid['thumb']}" style="width:120px; height:90px; object-fit:cover; border-radius:10px;">
                                    <div>
                                        <h5 style="margin:0; font-size:14px; color:#3d3563;">{vid['titulo'][:50]}...</h5>
                                        <p style="font-size:12px; margin:5px 0; color:#6b6399;">📺 {vid['canal']}</p>
                                        <p style="font-size:12px; font-weight:bold; color:#d946ef;">👁️ {vid['views']:,} views</p>
                                        <a href="{vid['link']}" target="_blank" style="font-size:11px; text-decoration:none; color:#8b5cf6;">Assistir no YouTube ↗</a>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

if st.session_state['logado']:
    app_principal()
else:
    tela_login()
