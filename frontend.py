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
st.set_page_config(page_title="Blueberry Finder AI v6.6", page_icon="🫐", layout="wide")

# --- CSS "BLUEBERRY UNICORN THEME" ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f3e7e9 0%, #e3eeff 100%, #e8dbfc 100%); background-attachment: fixed; }
    header[data-testid="stHeader"] { background: transparent; }
    h1, h2, h3 { font-family: 'Inter', sans-serif; color: #3d3563 !important; font-weight: 700; }
    p, label, span, div, caption { color: #544a85 !important; }
    .gold-card { background: rgba(255, 255, 255, 0.90); backdrop-filter: blur(15px); border: 2px solid #c4b5fd; border-radius: 25px; padding: 25px; box-shadow: 0 10px 30px rgba(139, 92, 246, 0.15); margin-bottom: 25px; transition: all 0.4s ease; }
    .gold-card:hover { transform: translateY(-8px); box-shadow: 0 20px 40px rgba(139, 92, 246, 0.25); border-color: #8b5cf6; }
    .gold-badge { background: linear-gradient(90deg, #a78bfa 0%, #f472b6 100%); color: white !important; padding: 6px 15px; border-radius: 20px; font-size: 12px; font-weight: 800; position: absolute; top: -12px; right: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] { background-color: rgba(255, 255, 255, 0.9) !important; border: 2px solid #ddd6fe !important; color: #3d3563 !important; border-radius: 18px !important; }
    div[data-testid="stFormSubmitButton"] button, div[data-testid="stButton"] button { background: linear-gradient(135deg, #8b5cf6 0%, #d946ef 100%); color: #ffffff !important; font-weight: 700 !important; border: none; padding: 14px 28px; border-radius: 50px; width: 100%; box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4); transition: all 0.3s ease; }
    div[data-testid="stFormSubmitButton"] button:hover, div[data-testid="stButton"] button:hover { transform: scale(1.05); background: linear-gradient(135deg, #7c3aed 0%, #c026d3 100%); }
    .visit-btn { display: block; width: 100%; text-align: center; padding: 12px; background: white; border: 2px solid #ddd6fe; color: #6b6399; border-radius: 15px; text-decoration: none; font-weight: 700; margin-top: 10px; transition:0.3s; }
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

# --- BUSCA HÍBRIDA POR CONTEÚDO (NÃO POR NOME DE CANAL) ---
@st.cache_data(ttl=21600, show_spinner=False)
def buscar_micro_nicho(palavra_chave, keys_str):
    keys = get_api_keys_list(keys_str)
    if not keys: return None, None, "Chave necessária"
    
    canais_unicornios = []
    canais_secundarios = []
    
    # PEGAR A DATA DE 3 MESES ATRÁS (Limita a busca a vídeos postados recentemente)
    data_limite = datetime.datetime.now() - timedelta(days=90)
    published_after = data_limite.isoformat("T") + "Z"
    
    canais_vistos = set()
    lote_canais = []
    next_page_token = None
    
    # FASE 1: ACHAR OS VÍDEOS QUE CONTÊM A PALAVRA-CHAVE (Engenharia Reversa)
    # Aumentei para 10 páginas (500 vídeos) para garantir que ache os 5 canais difíceis.
    for page in range(10): 
        params_busca = {
            "part": "snippet",
            "q": palavra_chave,
            "type": "video", # Procura no Título, Descrição e Tags do VÍDEO
            "maxResults": 50,
            "order": "relevance", 
            "publishedAfter": published_after # Só vídeos dos últimos 3 meses
        }
        if next_page_token:
            params_busca["pageToken"] = next_page_token
            
        dados_busca, erro = request_hydra("https://www.googleapis.com/youtube/v3/search", params_busca, keys)
        if erro or not dados_busca or "items" not in dados_busca: 
            break
            
        for item in dados_busca.get("items", []):
            try:
                cid = item["snippet"]["channelId"]
                if cid not in canais_vistos:
                    canais_vistos.add(cid)
                    lote_canais.append(cid)
            except: continue
            
        next_page_token = dados_busca.get("nextPageToken")
        if not next_page_token: 
            break

    # FASE 2: ANALISAR OS DONOS DOS VÍDEOS E APLICAR AS REGRAS ESTRITAS
    for i in range(0, len(lote_canais), 50):
        chunk = lote_canais[i:i+50]
        
        stats_dados, stats_erro = request_hydra("https://www.googleapis.com/youtube/v3/channels", {"part": "statistics,snippet", "id": ",".join(chunk)}, keys)
        if stats_erro or not stats_dados: 
            continue
            
        for canal in stats_dados.get("items", []):
            try:
                stats = canal.get("statistics", {})
                snippet = canal.get("snippet", {})
                
                subs = int(stats.get("subscriberCount", 0))
                views = int(stats.get("viewCount", 0))
                videos = int(stats.get("videoCount", 0))
                
                pub_str = snippet.get("publishedAt", "")
                if pub_str:
                    criacao_dt = datetime.datetime.strptime(pub_str, "%Y-%m-%dT%H:%M:%SZ")
                    dias_vida = (datetime.datetime.now() - criacao_dt).days
                else: 
                    dias_vida = 9999
                
                # SÓ CANAIS CRIADOS HÁ NO MÁXIMO 3 MESES (90 dias)
                if dias_vida <= 90:
                    media_views = views / videos if videos > 0 else 0
                    viral_score = media_views / subs if subs > 0 else 0
                    
                    canal_dict = {
                        "Canal": snippet.get("title", ""),
                        "Inscritos": subs,
                        "Vídeos": videos,
                        "Média Views": int(media_views),
                        "Viral Score": round(viral_score, 2),
                        "Idade (Dias)": dias_vida,
                        "Link": f"https://www.youtube.com/channel/{canal['id']}",
                        "id": canal['id']
                    }
                    
                    # AS 3 REGRAS DE OURO CRAVADAS
                    if subs >= 1000 and videos <= 70 and dias_vida <= 90:
                        canal_dict["Status"] = f"🎯 UNICÓRNIO"
                        if canal_dict not in canais_unicornios:
                            canais_unicornios.append(canal_dict)
                            
                    # RADAR DE APROXIMAÇÃO (Menos de 3 meses, mas falhou em subs ou videos)
                    else:
                        canal_dict["Status"] = f"🌱 RADAR"
                        if canal_dict not in canais_secundarios:
                            canais_secundarios.append(canal_dict)

            except Exception as e: 
                continue
                
        # OTIMIZAÇÃO: Para assim que achar os 5 Unicórnios Exigidos
        if len(canais_unicornios) >= 5 and len(canais_secundarios) >= 10:
            break

    # Ordenações
    canais_unicornios.sort(key=lambda x: x["Viral Score"], reverse=True)
    canais_secundarios.sort(key=lambda x: x["Inscritos"], reverse=True) # Aproximação por inscritos
    
    return canais_unicornios, canais_secundarios[:10], None 

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state['logado'] = False
def tela_login():
    c1,c2,c3=st.columns([1,1,1])
    with c2:
        st.markdown("<br><div style='background:rgba(255,255,255,0.9); padding:30px; border-radius:30px; text-align:center; border:2px solid #eaddff;'><h1 style='color:#5a4fcf;'>🫐</h1><h2 style='color:#3d3563;'>Blueberry Finder AI v6.6</h2><p>Strict Sniper (Max 70 Vídeos)</p></div><br>", unsafe_allow_html=True)
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
        st.markdown("📍 **Modo:** Strict Sniper (Conteúdo)")
        st.divider()
        st.info("**🎯 Regras Unicórnio:**\n\n✅ Min 1.000 Inscritos\n✅ Max 70 Vídeos\n✅ Max 3 Meses (90d)")
        st.info("**🌱 Regras Radar (Top 10):**\n\n✅ Max 3 Meses\n✅ Quase lá nas outras regras")
        st.divider()
        if st.button("Sair"): st.session_state['logado']=False; st.rerun()

    st.markdown("<h1 style='text-align: center; color: #5a4fcf;'>🫐 Sniper de Conteúdo Strict</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Ele busca <b>VÍDEOS</b> que contenham a palavra-chave e depois filtra os donos dos canais.</p>", unsafe_allow_html=True)

    with st.form("f_sniper"):
        
        c1, c2 = st.columns([3, 1])
        palavra_chave = c1.text_input("Nicho, Sub-nicho ou Micro-nicho:", placeholder="Ex: holy bible, food, rain sounds...")
        k = api_key_env if api_key_env else c2.text_input("API Keys (Hydra)", type="password")
        
        st.write("")
        b = st.form_submit_button("🌍 Iniciar Varredura de Conteúdo")
        
    if b and palavra_chave:
        
        with st.spinner(f"Analisando os vídeos que falam sobre '{palavra_chave}' no mundo todo..."):
            unicornios, secundarios, erro = buscar_micro_nicho(palavra_chave, k)
            
            if erro:
                st.error(erro)
            elif unicornios is not None:
                
                # ==========================================
                # BLOCO 1: UNICÓRNIOS PERFEITOS
                # ==========================================
                st.divider()
                st.markdown(f"<h2 style='color:#8b5cf6;'>🎯 Canais Unicórnios (≤ 3 Meses, ≥ 1k Subs, ≤ 70 Vídeos)</h2>", unsafe_allow_html=True)
                
                qtd_uni = len(unicornios)
                if qtd_uni >= 5:
                    st.success(f"Excelente! Encontramos os 5+ canais perfeitos que falam sobre '{palavra_chave}'!")
                elif qtd_uni > 0:
                    st.warning(f"Encontramos {qtd_uni} canais perfeitos. A meta era 5, o que indica que esse nicho exato tem poucos canais novos batendo os 1k de subs com menos de 70 vídeos.")
                else:
                    st.error(f"Nenhum canal no mundo atendeu 100% das regras para os vídeos de '{palavra_chave}'. Os criadores que existem são mais velhos ou já passaram dos 70 vídeos. Veja o Radar abaixo!")

                if qtd_uni > 0:
                    cols = st.columns(3)
                    for i, r in enumerate(unicornios): 
                        with cols[i%3]:
                            st.markdown(f"""
                            <div class='gold-card'>
                                <span class='gold-badge'>{r['Status']}</span>
                                <h4 style='text-overflow: ellipsis; white-space: nowrap; overflow: hidden;' title='{r['Canal']}'>{r['Canal']}</h4>
                                <p>⏳ {r['Idade (Dias)']} dias | 📹 {r['Vídeos']} vídeos | 👥 {r['Inscritos']:,}</p>
                                <small style='color:#d946ef'>🚀 Score: {r['Viral Score']}x</small>
                                <a href='{r['Link']}' target='_blank' class='visit-btn'>Acessar Canal ↗</a>
                            </div>""", unsafe_allow_html=True)
                            
                            with st.expander("Ver Vídeos Deste Canal"):
                                vs = buscar_top_videos(r['id'], k)
                                if vs:
                                    texto_vid = ""
                                    for v in vs:
                                        texto_vid += f"- {v['titulo']}\n"
                                    st.code(texto_vid, language='text')

                # ==========================================
                # BLOCO 2: RADAR DE APROXIMAÇÃO (TOP 10)
                # ==========================================
                st.divider()
                st.markdown(f"<h2 style='color:#6b6399;'>🔭 Radar de Aproximação (Criados há ≤ 3 meses)</h2>", unsafe_allow_html=True)
                st.markdown("Estes canais postaram sobre o tema recentemente. Eles têm menos de 3 meses de vida, mas não bateram os 1000 inscritos **OU** ultrapassaram o limite de 70 vídeos.")
                
                if len(secundarios) > 0:
                    df_sec = pd.DataFrame(secundarios)
                    st.dataframe(
                        df_sec[['Canal', 'Idade (Dias)', 'Vídeos', 'Inscritos', 'Média Views', 'Link']], 
                        column_config={
                            "Link": st.column_config.LinkColumn("Link", display_text="Ver no YouTube ↗"),
                        }, 
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.warning("Não encontramos canais recentes (< 3 meses) aproximados para essa busca global.")

if st.session_state['logado']: app_principal()
else: tela_login()
