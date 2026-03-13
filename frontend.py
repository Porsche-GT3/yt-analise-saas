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
st.set_page_config(page_title="Blueberry Finder AI v8.0", page_icon="🫐", layout="wide")

# --- CSS "BLUEBERRY UNICORN THEME" ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f3e7e9 0%, #e3eeff 100%, #e8dbfc 100%); background-attachment: fixed; }
    header[data-testid="stHeader"] { background: transparent; }
    h1, h2, h3 { font-family: 'Inter', sans-serif; color: #3d3563 !important; font-weight: 700; }
    p, label, span, div, caption { color: #544a85 !important; }
    .gold-card { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(15px); border: 2px solid #c4b5fd; border-radius: 25px; padding: 25px; box-shadow: 0 10px 30px rgba(139, 92, 246, 0.15); margin-bottom: 25px; transition: all 0.4s ease; position: relative;}
    .gold-card:hover { transform: translateY(-8px); box-shadow: 0 20px 40px rgba(139, 92, 246, 0.25); border-color: #8b5cf6; }
    .gold-badge { background: linear-gradient(90deg, #a78bfa 0%, #f472b6 100%); color: white !important; padding: 6px 15px; border-radius: 20px; font-size: 11px; font-weight: 800; position: absolute; top: -12px; right: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    .stTextInput input { background-color: rgba(255, 255, 255, 0.9) !important; border: 2px solid #ddd6fe !important; color: #3d3563 !important; border-radius: 18px !important; }
    div[data-testid="stFormSubmitButton"] button { background: linear-gradient(135deg, #8b5cf6 0%, #d946ef 100%); color: #ffffff !important; font-weight: 700 !important; border: none; padding: 14px 28px; border-radius: 50px; width: 100%; box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4); transition: all 0.3s ease; }
    div[data-testid="stFormSubmitButton"] button:hover { transform: scale(1.05); background: linear-gradient(135deg, #7c3aed 0%, #c026d3 100%); }
    .visit-btn { display: block; width: 100%; text-align: center; padding: 12px; background: white; border: 2px solid #ddd6fe; color: #6b6399; border-radius: 15px; text-decoration: none; font-weight: 700; margin-top: 15px; transition:0.3s; }
    .visit-btn:hover { background: #8b5cf6; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# --- PROTOCOLO HYDRA ---
def get_api_keys_list(input_keys):
    if not input_keys: return []
    return [k.strip() for k in input_keys.split(',') if k.strip()]

def request_hydra(url, params, keys_list):
    for i, key in enumerate(keys_list):
        params['key'] = key
        try:
            resp = requests.get(url, params=params)
            if resp.status_code == 200:
                return resp.json(), None
            if resp.status_code in [403, 429]:
                print(f"Chave {i+1} esgotada. Trocando...")
                continue
            return None, f"Erro API (Chave {i+1}): {resp.text}"
        except Exception as e:
            continue
    return None, "💀 Todas as chaves falharam (Cota Total Excedida)."

def buscar_top_videos(channel_id, keys_str):
    keys = get_api_keys_list(keys_str)
    if not keys: return []
    try:
        data = datetime.datetime.now() - timedelta(days=90)
        params = { "channelId": channel_id, "part": "snippet", "order": "viewCount", "publishedAfter": data.isoformat("T")+"Z", "type": "video", "maxResults": 3 }
        d, e = request_hydra("https://www.googleapis.com/youtube/v3/search", params, keys)
        if not d: return []
        return [{"titulo": i["snippet"]["title"], "data": i["snippet"]["publishedAt"][:10]} for i in d.get("items", [])]
    except: return []

# --- BUSCA ABERTA (REDE DUPLA SEM TRAVA DE IDADE DA CONTA) ---
@st.cache_data(ttl=21600, show_spinner=False)
def buscar_gems_universal(palavra_chave, keys_str):
    keys = get_api_keys_list(keys_str)
    if not keys: return None, None, "Chave necessária"
    
    gems_encontradas = []
    radar_quase_la = []
    
    canais_vistos = set()
    lote_canais = []
    
    # REDE 1: BUSCA DIRETA POR CANAIS
    next_page = None
    for _ in range(4): # Até 200 canais com a palavra-chave
        params = {"part": "snippet", "q": palavra_chave, "type": "channel", "maxResults": 50, "order": "relevance"}
        if next_page: params["pageToken"] = next_page
        d_canais, e = request_hydra("https://www.googleapis.com/youtube/v3/search", params, keys)
        if e or not d_canais: break
        for item in d_canais.get("items", []):
            cid = item["snippet"]["channelId"]
            if cid not in canais_vistos:
                canais_vistos.add(cid)
                lote_canais.append(cid)
        next_page = d_canais.get("nextPageToken")
        if not next_page: break

    # REDE 2: BUSCA POR VÍDEOS RECENTES (Últimos 3 meses)
    data_limite = datetime.datetime.now() - timedelta(days=90)
    pub_after = data_limite.isoformat("T") + "Z"
    next_page = None
    for _ in range(6): # Até 300 vídeos bombando agora
        params = {"part": "snippet", "q": palavra_chave, "type": "video", "maxResults": 50, "order": "relevance", "publishedAfter": pub_after}
        if next_page: params["pageToken"] = next_page
        d_videos, e = request_hydra("https://www.googleapis.com/youtube/v3/search", params, keys)
        if e or not d_videos: break
        for item in d_videos.get("items", []):
            cid = item["snippet"]["channelId"]
            if cid not in canais_vistos:
                canais_vistos.add(cid)
                lote_canais.append(cid)
        next_page = d_videos.get("nextPageToken")
        if not next_page: break

    # FASE 3: A PENEIRA (Apenas volume de vídeos e subs importam agora)
    for i in range(0, len(lote_canais), 50):
        chunk = lote_canais[i:i+50]
        stats_dados, stats_erro = request_hydra("https://www.googleapis.com/youtube/v3/channels", {"part": "statistics,snippet", "id": ",".join(chunk)}, keys)
        if stats_erro or not stats_dados: continue
            
        for canal in stats_dados.get("items", []):
            try:
                stats = canal.get("statistics", {})
                snippet = canal.get("snippet", {})
                
                subs = int(stats.get("subscriberCount", 0))
                views = int(stats.get("viewCount", 0))
                videos = int(stats.get("videoCount", 0))
                
                # Ignora canais vazios
                if videos == 0: continue
                
                media_views = views / videos
                viral_score = media_views / subs if subs > 0 else 0
                
                canal_dict = {
                    "Canal": snippet.get("title", ""),
                    "Inscritos": subs,
                    "Vídeos": videos,
                    "Média Views": int(media_views),
                    "Viral Score": round(viral_score, 2),
                    "Link": f"https://www.youtube.com/channel/{canal['id']}",
                    "id": canal['id']
                }

                # --- AS REGRAS MESTRAS DO USUÁRIO ---
                
                # Se o canal tem no MÁXIMO 70 vídeos totais...
                if videos <= 70:
                    
                    # 💎 GEMS: Bateu 1000 inscritos
                    if subs >= 1000:
                        gems_encontradas.append(canal_dict)
                        
                    # 🌱 RADAR: Menos de 1000 inscritos
                    else:
                        radar_quase_la.append(canal_dict)

            except Exception as e: 
                continue

    # Ordenações
    gems_encontradas.sort(key=lambda x: x["Viral Score"], reverse=True)
    radar_quase_la.sort(key=lambda x: x["Inscritos"], reverse=True) 
    
    return gems_encontradas, radar_quase_la[:10], None 

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state['logado'] = False
def tela_login():
    c1,c2,c3=st.columns([1,1,1])
    with c2:
        st.markdown("<br><div style='background:rgba(255,255,255,0.9); padding:30px; border-radius:30px; text-align:center; border:2px solid #eaddff;'><h1 style='color:#5a4fcf;'>🫐</h1><h2 style='color:#3d3563;'>Blueberry Finder AI v8.0</h2><p>GEMS Edition</p></div><br>", unsafe_allow_html=True)
        with st.form("l"):
            u=st.text_input("User"); p=st.text_input("Pass", type="password")
            if st.form_submit_button("🚀 Entrar"):
                if u=="admin" and p=="1234": st.session_state['logado']=True; st.rerun()
                else: st.error("Erro.")

# --- APP ---
def app_principal():
    api_key_env = os.getenv("YOUTUBE_API_KEY")
    
    with st.sidebar:
        st.markdown("### Menu 🫐")
        st.markdown("📍 **Modo:** Universal GEMS")
        st.divider()
        st.info("**💎 Regra Ouro:**\n\n✅ Min 1.000 Inscritos\n✅ Max 70 Vídeos Totais")
        st.info("**🌱 Radar (Top 10):**\n\n✅ Max 70 Vídeos\n✅ Menos de 1k Subs")
        st.divider()
        if st.button("Sair"): st.session_state['logado']=False; st.rerun()

    st.markdown("<h1 style='text-align: center; color: #5a4fcf;'>🫐 Motor GEMS Definitivo</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Procura <b>canais reais</b> que subiram através de uma palavra-chave com até 70 vídeos.</p>", unsafe_allow_html=True)

    with st.form("f_sniper"):
        c1, c2 = st.columns([3, 1])
        palavra_chave = c1.text_input("Palavra-chave (Qualquer idioma):", placeholder="Ex: bible hidden, reddit, cook...")
        k = api_key_env if api_key_env else c2.text_input("API Keys (Hydra)", type="password")
        
        st.write("")
        b = st.form_submit_button("🌍 Buscar GEMS")
        
    if b and palavra_chave:
        
        with st.spinner(f"Minerando o YouTube atrás de '{palavra_chave}'..."):
            gems, radar, erro = buscar_gems_universal(palavra_chave, k)
            
            if erro:
                st.error(erro)
            else:
                
                # ==========================================
                # BLOCO 1: AS GEMS ENCONTRADAS
                # ==========================================
                st.divider()
                st.markdown(f"<h2 style='color:#8b5cf6;'>💎 Canais GEM (≤ 70 vídeos, ≥ 1.000 Subs)</h2>", unsafe_allow_html=True)
                
                qtd_gems = len(gems)
                if qtd_gems >= 5:
                    st.success(f"Missão Cumprida! Encontramos {qtd_gems} canais GEMS que batem as regras para '{palavra_chave}'!")
                elif qtd_gems > 0:
                    st.warning(f"Encontramos {qtd_gems} canais GEMS. Se forem menos de 5, o nicho ainda tem espaço para crescer!")
                else:
                    st.error(f"Nenhum canal com até 70 vídeos e mais de 1k inscritos encontrado para essa busca. Veja o Radar abaixo!")

                if qtd_gems > 0:
                    cols = st.columns(3)
                    for i, r in enumerate(gems[:15]): # Mostra até os top 15 se achar muito
                        with cols[i%3]:
                            st.markdown(f"""
                            <div class='gold-card'>
                                <span class='gold-badge'>💎 GEM {r['Viral Score']}</span>
                                <h4 style='text-overflow: ellipsis; white-space: nowrap; overflow: hidden;' title='{r['Canal']}'>{r['Canal']}</h4>
                                <p>📹 <b>{r['Vídeos']} vídeos</b> | 👥 <b>{r['Inscritos']:,}</b></p>
                                <a href='{r['Link']}' target='_blank' class='visit-btn'>Acessar Canal ↗</a>
                            </div>""", unsafe_allow_html=True)
                            
                            with st.expander("Ver Últimos Vídeos"):
                                vs = buscar_top_videos(r['id'], k)
                                if vs:
                                    texto_vid = ""
                                    for v in vs:
                                        texto_vid += f"- {v['titulo']}\n"
                                    st.code(texto_vid, language='text')

                # ==========================================
                # BLOCO 2: RADAR (< 1.000 Subs)
                # ==========================================
                st.divider()
                st.markdown(f"<h2 style='color:#6b6399;'>🔭 Radar de Crescimento (≤ 70 vídeos & < 1.000 Subs)</h2>", unsafe_allow_html=True)
                
                if len(radar) > 0:
                    df_rad = pd.DataFrame(radar)
                    st.dataframe(
                        df_rad[['Canal', 'Vídeos', 'Inscritos', 'Média Views', 'Link']], 
                        column_config={"Link": st.column_config.LinkColumn("Link", display_text="Ver no YouTube ↗")}, 
                        use_container_width=True, hide_index=True
                    )
                else:
                    st.info("Nenhum canal novato encontrado com essas métricas.")

if st.session_state['logado']: app_principal()
else: tela_login()
