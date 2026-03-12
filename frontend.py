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
st.set_page_config(page_title="Blueberry Finder AI v6.4", page_icon="🫐", layout="wide")

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
                print(f"Chave {i+1} esgotada. Trocando para a próxima...")
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

# --- BUSCA SNIPER COM ENGENHARIA REVERSA (O SEGREDO) ---
@st.cache_data(ttl=21600, show_spinner=False)
def buscar_micro_nicho(palavra_chave, keys_str):
    keys = get_api_keys_list(keys_str)
    if not keys: return None, None, "Chave necessária"
    
    canais_unicornios = []
    canais_secundarios = []
    
    # 1. PEGAR A DATA DE 3 MESES ATRÁS (90 dias)
    data_limite = datetime.datetime.now() - timedelta(days=90)
    published_after = data_limite.isoformat("T") + "Z"
    
    canais_vistos = set()
    lote_canais = []
    next_page_token = None
    
    # FASE 1: VARREDURA DE VÍDEOS (Engenharia Reversa)
    # Buscamos até 300 VÍDEOS (não canais) que estejam bombando sobre o tema, postados recentemente.
    for page in range(6): 
        params_busca = {
            "part": "snippet",
            "q": palavra_chave,
            "type": "video",       # PROCURAR VÍDEO (Pega o conteúdo real)
            "maxResults": 50,
            "order": "viewCount",  # Ordenado por Views (Para achar quem está viralizando)
            "publishedAfter": published_after # Força a achar só vídeos recentes
        }
        if next_page_token:
            params_busca["pageToken"] = next_page_token
            
        dados_busca, erro = request_hydra("https://www.googleapis.com/youtube/v3/search", params_busca, keys)
        if erro or not dados_busca or "items" not in dados_busca: 
            break
            
        # Extrai os donos dos vídeos (Canais)
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

    # FASE 2: ANÁLISE DOS CANAIS (Raio-X)
    # A API só permite analisar 50 canais por vez. Quebramos nossa lista em lotes de 50.
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
                
                # REGRA MESTRE ABSOLUTA: Todos devem ter no máximo 3 meses (90 dias)
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
                    
                    # BIFURCAÇÃO: 
                    # Unicórnio (>= 1k subs E <= 70 vídeos)
                    if subs >= 1000 and videos <= 70:
                        canal_dict["Status"] = f"🎯 UNICÓRNIO"
                        if canal_dict not in canais_unicornios:
                            canais_unicornios.append(canal_dict)
                    # Secundário / Radar de Crescimento
                    else:
                        canal_dict["Status"] = f"🌱 EM CRESCIMENTO"
                        if canal_dict not in canais_secundarios:
                            canais_secundarios.append(canal_dict)

            except Exception as e: 
                continue
        
        # Otimização: Se já achou muito, pode parar
        if len(canais_unicornios) >= 15 and len(canais_secundarios) >= 30:
            break

    # Ordenações
    canais_unicornios.sort(key=lambda x: x["Viral Score"], reverse=True)
    canais_secundarios.sort(key=lambda x: x["Inscritos"], reverse=True) 
    
    return canais_unicornios, canais_secundarios[:10], None 

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state['logado'] = False
def tela_login():
    c1,c2,c3=st.columns([1,1,1])
    with c2:
        st.markdown("<br><div style='background:rgba(255,255,255,0.9); padding:30px; border-radius:30px; text-align:center; border:2px solid #eaddff;'><h1 style='color:#5a4fcf;'>🫐</h1><h2 style='color:#3d3563;'>Blueberry Finder AI v6.4</h2><p>Reverse Engineering Engine</p></div><br>", unsafe_allow_html=True)
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
        st.markdown("📍 **Modo:** Engenharia Reversa (Global)")
        st.divider()
        st.info("**🎯 Regras Unicórnio:**\n\n✅ Min 1.000 Inscritos\n✅ Max 70 Vídeos\n✅ Max 3 Meses")
        st.info("**🌱 Regras Radar (Top 10):**\n\n✅ Max 3 Meses\n✅ Quase lá (Subindo de Inscritos)")
        st.divider()
        if st.button("Sair"): st.session_state['logado']=False; st.rerun()

    st.markdown("<h1 style='text-align: center; color: #5a4fcf;'>🫐 Motor de Busca Apurado</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Procura <b>vídeos virais</b> primeiro, depois encontra os donos (Canais) e aplica as regras.</p>", unsafe_allow_html=True)

    with st.form("f_sniper"):
        
        c1, c2 = st.columns([3, 1])
        palavra_chave = c1.text_input("Nicho, Sub-nicho ou Micro-nicho:", placeholder="Ex: holy bible, food, dark history...")
        k = api_key_env if api_key_env else c2.text_input("API Keys (Hydra)", type="password")
        
        st.write("")
        b = st.form_submit_button("🌍 Iniciar Engenharia Reversa")
        
    if b and palavra_chave:
        
        with st.spinner(f"Extraindo dados dos vídeos virais sobre '{palavra_chave}' no mundo..."):
            unicornios, secundarios, erro = buscar_micro_nicho(palavra_chave, k)
            
            if erro:
                st.error(erro)
            elif unicornios is not None:
                
                # ==========================================
                # BLOCO 1: UNICÓRNIOS PERFEITOS
                # ==========================================
                st.divider()
                st.markdown(f"<h2 style='color:#8b5cf6;'>🎯 Canais Unicórnios (Atendem TODAS as Regras)</h2>", unsafe_allow_html=True)
                
                qtd_uni = len(unicornios)
                if qtd_uni >= 5:
                    st.success(f"Excelente! Encontramos {qtd_uni} canais globais perfeitos para '{palavra_chave}'!")
                elif qtd_uni > 0:
                    st.warning(f"Encontramos {qtd_uni} canais globais perfeitos. A meta era 5, o nicho pode estar inexplorado!")
                else:
                    st.error("Nenhum canal no mundo atendeu 100% das regras rígidas para esse termo. Mas veja o Radar de crescimento abaixo!")

                if qtd_uni > 0:
                    cols = st.columns(3)
                    for i, r in enumerate(unicornios[:9]): 
                        with cols[i%3]:
                            st.markdown(f"""
                            <div class='gold-card'>
                                <span class='gold-badge'>{r['Status']}</span>
                                <h4 style='text-overflow: ellipsis; white-space: nowrap; overflow: hidden;' title='{r['Canal']}'>{r['Canal']}</h4>
                                <p>⏳ {r['Idade (Dias)']} dias | 📹 {r['Vídeos']} vídeos | 👥 {r['Inscritos']:,}</p>
                                <small style='color:#d946ef'>🚀 Score: {r['Viral Score']}x</small>
                                <a href='{r['Link']}' target='_blank' class='visit-btn'>Acessar Canal ↗</a>
                            </div>""", unsafe_allow_html=True)
                            
                            with st.expander("Ver Vídeos de Sucesso"):
                                vs = buscar_top_videos(r['id'], k)
                                if vs:
                                    texto_vid = ""
                                    for v in vs:
                                        texto_vid += f"- {v['titulo']}\n"
                                    st.code(texto_vid, language='text')

                # ==========================================
                # BLOCO 2: RADAR DE APROXIMAÇÃO (SECUNDÁRIOS)
                # ==========================================
                st.divider()
                st.markdown(f"<h2 style='color:#6b6399;'>🔭 Radar: Top 10 Canais de Aproximação (Criados há ≤ 3 meses)</h2>", unsafe_allow_html=True)
                st.markdown("Estes canais postaram vídeos virais recentemente e estão em fase de teste. Fique de olho neles!")
                
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
                    st.info("Não encontramos canais recentes (< 3 meses) aproximados para essa busca global.")

if st.session_state['logado']: app_principal()
else: tela_login()
