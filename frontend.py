import streamlit as st
import pandas as pd
import requests
import os
import datetime
from collections import Counter
from dotenv import load_dotenv

# Carrega variáveis
load_dotenv()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Blueberry Finder AI v6.2", page_icon="🫐", layout="wide")

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
    .silver-card { background: rgba(255, 255, 255, 0.6); padding: 15px; border-radius: 15px; margin-bottom: 10px; border: 1px solid #ddd6fe; }
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
        data = datetime.datetime.now() - datetime.timedelta(days=90)
        params = { "channelId": channel_id, "part": "snippet", "order": "viewCount", "publishedAfter": data.isoformat("T")+"Z", "type": "video", "maxResults": 3 }
        d, e = request_hydra("https://www.googleapis.com/youtube/v3/search", params, keys)
        if not d: return []
        return [{"titulo": i["snippet"]["title"], "data": i["snippet"]["publishedAt"][:10]} for i in d.get("items", [])]
    except: return []

# --- BUSCA SNIPER E BIFURCAÇÃO ---
@st.cache_data(ttl=21600, show_spinner=False)
def buscar_micro_nicho(palavra_chave, pais_code, keys_str):
    keys = get_api_keys_list(keys_str)
    if not keys: return None, None, "Chave necessária"
    
    canais_unicornios = []
    canais_secundarios = []
    next_page_token = None
    vistos = set() # Evita duplicatas da API
    
    # Aumentado para 8 páginas para garantir que encontre quantidade suficiente
    max_pages = 8 
    
    for page in range(max_pages):
        params_busca = {
            "part": "snippet",
            "q": palavra_chave,
            "type": "channel",
            "regionCode": pais_code,
            "maxResults": 50,
            "order": "relevance"
        }
        if next_page_token:
            params_busca["pageToken"] = next_page_token
            
        dados_busca, erro = request_hydra("https://www.googleapis.com/youtube/v3/search", params_busca, keys)
        if erro or not dados_busca or "items" not in dados_busca: 
            break
            
        ids_canais = [i["id"]["channelId"] for i in dados_busca.get("items", []) if "channelId" in i["id"] and i["id"]["channelId"] not in vistos]
        if not ids_canais: 
            break
            
        for cid in ids_canais: vistos.add(cid)
            
        stats_dados, stats_erro = request_hydra("https://www.googleapis.com/youtube/v3/channels", {"part": "statistics,snippet", "id": ",".join(ids_canais)}, keys)
        if stats_erro or not stats_dados: 
            break
            
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
                
                # REGRA MESTRE: Todos devem ter no máximo 3 meses (90 dias)
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
                    
                    # BIFURCAÇÃO: Unicórnio (Regra Restrita) vs Secundário (Aproximação)
                    if subs >= 1000 and videos <= 70:
                        canal_dict["Status"] = f"🎯 UNICÓRNIO"
                        canais_unicornios.append(canal_dict)
                    else:
                        canal_dict["Status"] = f"🌱 EM CRESCIMENTO"
                        canais_secundarios.append(canal_dict)

            except Exception as e: 
                continue
        
        # Para a busca se já temos 5 Unicórnios E pelo menos 10 Secundários
        if len(canais_unicornios) >= 5 and len(canais_secundarios) >= 10:
            break
            
        next_page_token = dados_busca.get("nextPageToken")
        if not next_page_token: 
            break

    # Ordenações
    canais_unicornios.sort(key=lambda x: x["Viral Score"], reverse=True)
    # Secundários ordenados por inscritos para mostrar quem está "quase lá"
    canais_secundarios.sort(key=lambda x: x["Inscritos"], reverse=True) 
    
    return canais_unicornios, canais_secundarios[:10], None # Retorna Unicórnios e Top 10 Secundários

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state['logado'] = False
def tela_login():
    c1,c2,c3=st.columns([1,1,1])
    with c2:
        st.markdown("<br><div style='background:rgba(255,255,255,0.9); padding:30px; border-radius:30px; text-align:center; border:2px solid #eaddff;'><h1 style='color:#5a4fcf;'>🫐</h1><h2 style='color:#3d3563;'>Blueberry Finder AI v6.2</h2><p>Sniper & Radar Edition</p></div><br>", unsafe_allow_html=True)
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
        st.markdown("📍 **Modo:** Sniper + Radar")
        st.divider()
        st.info("**🎯 Regras Unicórnio:**\n\n✅ Min 1.000 Inscritos\n✅ Max 70 Vídeos\n✅ Max 3 Meses")
        st.info("**🌱 Regras Radar (Top 10):**\n\n✅ Max 3 Meses\n✅ Não bateu 1k ou passou de 70 vídeos")
        st.divider()
        if st.button("Sair"): st.session_state['logado']=False; st.rerun()

    st.markdown("<h1 style='text-align: center; color: #5a4fcf;'>🫐 Busca Sniper Universal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Pesquise <b>qualquer palavra-chave</b> para achar Unicórnios e Monitorar Concorrentes Recentes.</p>", unsafe_allow_html=True)

    with st.form("f_sniper"):
        paises = { "🌎 Qualquer (Global)": "", "🇺🇸 Estados Unidos (EN)": "US", "🇬🇧 Reino Unido (EN)": "GB", "🇧🇷 Brasil (PT)": "BR", "🇪🇸 Espanha (ES)": "ES", "🇫🇷 França (FR)": "FR", "🇩🇪 Alemanha (DE)": "DE" }
        
        c1, c2, c3 = st.columns([2, 1, 1])
        palavra_chave = c1.text_input("Palavra-chave ou Sub-nicho:", placeholder="Ex: [food], [story], [bible]...")
        pais_selecionado = c2.selectbox("Idioma / País:", list(paises.keys()))
        k = api_key_env if api_key_env else c3.text_input("API Keys (Hydra)", type="password")
        
        b = st.form_submit_button("🎯 Escanear Nicho Completo")
        
    if b and palavra_chave:
        codigo_pais = paises[pais_selecionado]
        
        with st.spinner(f"Varrendo páginas do YouTube em busca de '{palavra_chave}'..."):
            unicornios, secundarios, erro = buscar_micro_nicho(palavra_chave, codigo_pais, k)
            
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
                    st.success(f"Encontramos {qtd_uni} canais perfeitos para '{palavra_chave}'!")
                elif qtd_uni > 0:
                    st.warning(f"Encontramos {qtd_uni} canais perfeitos. A meta era 5, o nicho pode estar inexplorado!")
                else:
                    st.error("Nenhum canal atendeu 100% das regras rígidas. Mas veja os aproximados abaixo!")

                if qtd_uni > 0:
                    cols = st.columns(3)
                    for i, r in enumerate(unicornios[:6]): 
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
                st.markdown("Estes canais são **muito novos**, mas ainda não bateram 1k de inscritos ou postaram mais de 70 vídeos. Fique de olho neles!")
                
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
                    st.info("Não encontramos canais recentes (< 3 meses) aproximados neste nicho.")

if st.session_state['logado']: app_principal()
else: tela_login()
