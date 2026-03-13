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
st.set_page_config(page_title="Blueberry Finder AI v7.0", page_icon="🫐", layout="wide")

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

# --- BUSCA DUPLA X-RAY ---
@st.cache_data(ttl=21600, show_spinner=False)
def buscar_xray_universal(palavra_chave, keys_str):
    keys = get_api_keys_list(keys_str)
    if not keys: return None, None, None, "Chave necessária"
    
    unicornios_puros = []
    renascidos = []
    radar_quase_la = []
    
    canais_vistos = set()
    lote_canais = []
    
    # REDE 1: BUSCA DIRETA POR CANAIS (Acha quem tem a palavra no nome)
    next_page = None
    for _ in range(4): # 200 resultados
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

    # REDE 2: BUSCA POR VÍDEOS (Acha canais com nomes nada a ver, mas que postaram vídeos sobre o tema nos últimos 90 dias)
    data_limite = datetime.datetime.now() - timedelta(days=90)
    pub_after = data_limite.isoformat("T") + "Z"
    next_page = None
    for _ in range(6): # 300 resultados
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

    # FASE 3: RAIO-X DOS CANAIS
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
                
                pub_str = snippet.get("publishedAt", "")
                if pub_str:
                    criacao_dt = datetime.datetime.strptime(pub_str, "%Y-%m-%dT%H:%M:%SZ")
                    dias_vida = (datetime.datetime.now() - criacao_dt).days
                else: 
                    dias_vida = 9999
                
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

                # --- AS REGRAS ESTRITAS (BIFURCADAS) ---
                
                # Regra Comum: Tem que ter NO MÁXIMO 70 VÍDEOS!
                if videos <= 70:
                    
                    # 1. UNICÓRNIOS PUROS (1k+ subs, <= 90 dias)
                    if subs >= 1000 and dias_vida <= 90:
                        canal_dict["Status"] = f"🎯 UNICÓRNIO PURO"
                        unicornios_puros.append(canal_dict)
                        
                    # 2. RENASCIDOS / FALSOS NOVATOS (1k+ subs, > 90 dias) -> Bible Hidden entra aqui!
                    elif subs >= 1000 and dias_vida > 90:
                        canal_dict["Status"] = f"🔥 CONTA ANTIGA"
                        renascidos.append(canal_dict)
                        
                    # 3. RADAR (Menos de 1k subs, mas é novato <= 90 dias)
                    elif subs < 1000 and dias_vida <= 90:
                        canal_dict["Status"] = f"🌱 RADAR (< 1k subs)"
                        radar_quase_la.append(canal_dict)

            except Exception as e: 
                continue

    # Ordenações
    unicornios_puros.sort(key=lambda x: x["Viral Score"], reverse=True)
    renascidos.sort(key=lambda x: x["Viral Score"], reverse=True)
    radar_quase_la.sort(key=lambda x: x["Inscritos"], reverse=True) 
    
    return unicornios_puros, renascidos[:15], radar_quase_la[:10], None 

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state['logado'] = False
def tela_login():
    c1,c2,c3=st.columns([1,1,1])
    with c2:
        st.markdown("<br><div style='background:rgba(255,255,255,0.9); padding:30px; border-radius:30px; text-align:center; border:2px solid #eaddff;'><h1 style='color:#5a4fcf;'>🫐</h1><h2 style='color:#3d3563;'>Blueberry Finder AI v7.0</h2><p>X-Ray Edition (Busca Universal)</p></div><br>", unsafe_allow_html=True)
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
        st.markdown("📍 **Modo:** Raio-X Universal")
        st.divider()
        st.info("**🎯 Regra Ouro:**\n\n✅ Min 1.000 Inscritos\n✅ Max 70 Vídeos\n✅ Max 3 Meses")
        st.info("**🔥 Regra Renascidos:**\n\n✅ Max 70 Vídeos\n✅ Contas velhas reaproveitadas")
        st.divider()
        if st.button("Sair"): st.session_state['logado']=False; st.rerun()

    st.markdown("<h1 style='text-align: center; color: #5a4fcf;'>🫐 Busca Universal (Raio-X)</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Pesquise sua palavra-chave. O algoritmo filtrará os canais por regras estritas e revelará os 'falsos novatos'.</p>", unsafe_allow_html=True)

    with st.form("f_sniper"):
        c1, c2 = st.columns([3, 1])
        palavra_chave = c1.text_input("Palavra-chave (Qualquer idioma):", placeholder="Ex: holy bible, reddit, motivation...")
        k = api_key_env if api_key_env else c2.text_input("API Keys (Hydra)", type="password")
        
        st.write("")
        b = st.form_submit_button("🌍 Ativar Scanner Raio-X")
        
    if b and palavra_chave:
        
        with st.spinner(f"Varrendo a base de dados do YouTube para '{palavra_chave}'..."):
            unicornios, renascidos, radar, erro = buscar_xray_universal(palavra_chave, k)
            
            if erro:
                st.error(erro)
            else:
                
                # ==========================================
                # BLOCO 1: UNICÓRNIOS PUROS
                # ==========================================
                st.divider()
                st.markdown(f"<h2 style='color:#8b5cf6;'>🎯 Canais Unicórnios (100% REGRA: ≤ 3 meses, ≤ 70 vídeos, ≥ 1k Subs)</h2>", unsafe_allow_html=True)
                
                if len(unicornios) > 0:
                    st.success(f"Encontramos {len(unicornios)} canais que bateram todas as suas regras estritas de forma pura!")
                    cols = st.columns(3)
                    for i, r in enumerate(unicornios): 
                        with cols[i%3]:
                            st.markdown(f"""
                            <div class='gold-card'>
                                <span class='gold-badge'>{r['Status']}</span>
                                <h4 style='text-overflow: ellipsis; white-space: nowrap; overflow: hidden;' title='{r['Canal']}'>{r['Canal']}</h4>
                                <p>⏳ {r['Idade (Dias)']} dias | 📹 <b>{r['Vídeos']} vídeos</b> | 👥 <b>{r['Inscritos']:,}</b></p>
                                <small style='color:#d946ef; font-weight:bold;'>🚀 Score: {r['Viral Score']}x</small>
                                <a href='{r['Link']}' target='_blank' class='visit-btn'>Acessar Canal ↗</a>
                            </div>""", unsafe_allow_html=True)
                else:
                    st.error(f"Nenhum canal puro (< 3 meses) atendeu à sua regra. Isso significa que não há novatos recentes no topo. Veja os 'Falsos Novatos' abaixo!")

                # ==========================================
                # BLOCO 2: FALSOS NOVATOS (Renascidos) - BIBLE HIDDEN APARECE AQUI
                # ==========================================
                st.divider()
                st.markdown(f"<h2 style='color:#f97316;'>🔥 Falsos Novatos (Contas Antigas c/ ≤ 70 Vídeos)</h2>", unsafe_allow_html=True)
                st.markdown("Estes canais têm os inscritos e o baixo volume de vídeos que você quer (**≤ 70 vídeos**), mas a API acusa que a conta é mais velha que 3 meses. Geralmente são contas compradas/reaproveitadas que explodiram agora.")
                
                if len(renascidos) > 0:
                    df_ren = pd.DataFrame(renascidos)
                    st.dataframe(
                        df_ren[['Canal', 'Vídeos', 'Inscritos', 'Média Views', 'Idade (Dias)', 'Link']], 
                        column_config={"Link": st.column_config.LinkColumn("Link", display_text="Ver no YouTube ↗")}, 
                        use_container_width=True, hide_index=True
                    )
                else:
                    st.info("Nenhum canal renascido encontrado.")

                # ==========================================
                # BLOCO 3: RADAR (< 1.000 Subs)
                # ==========================================
                st.divider()
                st.markdown(f"<h2 style='color:#6b6399;'>🔭 Radar de Crescimento (≤ 3 meses & ≤ 70 vídeos)</h2>", unsafe_allow_html=True)
                st.markdown("Estes canais são novos e têm poucos vídeos, mas ainda estão na luta para bater 1.000 inscritos.")
                
                if len(radar) > 0:
                    df_rad = pd.DataFrame(radar)
                    st.dataframe(
                        df_rad[['Canal', 'Idade (Dias)', 'Vídeos', 'Inscritos', 'Média Views', 'Link']], 
                        column_config={"Link": st.column_config.LinkColumn("Link", display_text="Ver no YouTube ↗")}, 
                        use_container_width=True, hide_index=True
                    )
                else:
                    st.info("Nenhum canal bebê encontrado com essas métricas.")

if st.session_state['logado']: app_principal()
else: tela_login()
