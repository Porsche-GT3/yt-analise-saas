import streamlit as st
import pandas as pd
import requests
import os
import datetime
import re
from datetime import timedelta
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Blueberry Finder AI v8.7", page_icon="🫐", layout="wide")

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
                continue 
            return None, f"Erro API (Código {resp.status_code}): {resp.text}"
        except Exception as e:
            continue
    return None, "💀 COTA EXCEDIDA OU CHAVE INVÁLIDA: Todas as chaves falharam."

def buscar_top_videos(channel_id, keys_str):
    keys = get_api_keys_list(keys_str)
    if not keys: return []
    try:
        data = datetime.datetime.now() - timedelta(days=105)
        params = { "channelId": channel_id, "part": "snippet", "order": "viewCount", "publishedAfter": data.isoformat("T")+"Z", "type": "video", "maxResults": 3 }
        d, e = request_hydra("https://www.googleapis.com/youtube/v3/search", params, keys)
        if not d: return []
        return [{"titulo": i["snippet"]["title"], "data": i["snippet"]["publishedAt"][:10]} for i in d.get("items", [])]
    except: return []

# --- UTILITÁRIOS DE DURAÇÃO ---
def duration_to_seconds(duration_str):
    """Converte duração ISO 8601 (ex: PT1M30S) em segundos."""
    match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if not match: return 0
    h = int(match.group(1) or 0)
    m = int(match.group(2) or 0)
    s = int(match.group(3) or 0)
    return h * 3600 + m * 60 + s

# --- RAIO-X DE PLAYLIST (Idade + Formato Longo) ---
def verificar_canal_valido(uploads_id, keys_list, data_limite):
    """
    Retorna True APENAS se:
    1. TODOS os vídeos forem mais recentes que data_limite (3.5 meses)
    2. Existir PELO MENOS UM vídeo longo (> 65 segundos, excluindo canais só de Shorts)
    """
    next_page = None
    video_ids = []
    
    # 1. Coletar IDs de vídeos e verificar se há vídeos velhos
    for _ in range(2): # Verifica até 100 vídeos
        params = {"part": "snippet", "playlistId": uploads_id, "maxResults": 50}
        if next_page: params["pageToken"] = next_page
        
        data, err = request_hydra("https://www.googleapis.com/youtube/v3/playlistItems", params, keys_list)
        if err or not data: break
            
        items = data.get("items", [])
        for item in items:
            pub_str = item.get("snippet", {}).get("publishedAt", "")
            vid_id = item.get("snippet", {}).get("resourceId", {}).get("videoId")
            
            if pub_str:
                try:
                    pub_date = datetime.datetime.strptime(pub_str, "%Y-%m-%dT%H:%M:%SZ")
                    # REJEIÇÃO 1: Vídeo postado há mais de 3.5 meses
                    if pub_date < data_limite:
                        return False 
                except: pass
                
            if vid_id: video_ids.append(vid_id)
                    
        next_page = data.get("nextPageToken")
        if not next_page: break

    # 2. Verificar se existe Pelo Menos Um vídeo LONGO (> 65s)
    tem_video_longo = False
    
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i+50]
        params = {"part": "contentDetails", "id": ",".join(chunk)}
        data, err = request_hydra("https://www.googleapis.com/youtube/v3/videos", params, keys_list)
        if err or not data: continue
        
        for item in data.get("items", []):
            dur_str = item.get("contentDetails", {}).get("duration", "")
            segundos = duration_to_seconds(dur_str)
            if segundos > 65: # Mais de 65 segundos garante que NÃO é um Short
                tem_video_longo = True
                break
        if tem_video_longo: break

    # REJEIÇÃO 2: Só tem Shorts (tem_video_longo = False)
    return tem_video_longo

# --- BUSCA UNIVERSAL ---
def buscar_gems_universal(palavra_chave, keys_str, status_box):
    keys = get_api_keys_list(keys_str)
    if not keys: return None, None, "Chave necessária"
    
    gems_encontradas = []
    radar_quase_la = []
    canais_vistos = set()
    lote_canais = []
    
    # REDE 1
    status_box.write("📡 Rede 1: Pesquisando canais por relevância de nome...")
    next_page = None
    for _ in range(3): 
        params = {"part": "snippet", "q": palavra_chave, "type": "channel", "maxResults": 50, "order": "relevance"}
        if next_page: params["pageToken"] = next_page
        d_canais, e = request_hydra("https://www.googleapis.com/youtube/v3/search", params, keys)
        if e: return None, None, e
        if not d_canais: break
        for item in d_canais.get("items", []):
            cid = item["snippet"]["channelId"]
            if cid not in canais_vistos:
                canais_vistos.add(cid)
                lote_canais.append(cid)
        next_page = d_canais.get("nextPageToken")
        if not next_page: break

    # REDES 2 E 3
    dias_limite = 105
    data_limite_3_5_meses = datetime.datetime.now() - timedelta(days=dias_limite)
    pub_after = data_limite_3_5_meses.isoformat("T") + "Z"
    
    status_box.write("📡 Rede 2 e 3: Rastreado vídeos publicados nos últimos 3.5 meses...")
    
    next_page = None
    for _ in range(3): 
        params = {"part": "snippet", "q": palavra_chave, "type": "video", "maxResults": 50, "order": "relevance", "publishedAfter": pub_after}
        if next_page: params["pageToken"] = next_page
        d_videos, e = request_hydra("https://www.googleapis.com/youtube/v3/search", params, keys)
        if e: return None, None, e
        if not d_videos: break
        for item in d_videos.get("items", []):
            cid = item["snippet"]["channelId"]
            if cid not in canais_vistos:
                canais_vistos.add(cid)
                lote_canais.append(cid)
        next_page = d_videos.get("nextPageToken")
        if not next_page: break
        
    next_page = None
    for _ in range(4): 
        params = {"part": "snippet", "q": palavra_chave, "type": "video", "maxResults": 50, "order": "viewCount", "publishedAfter": pub_after}
        if next_page: params["pageToken"] = next_page
        d_videos, e = request_hydra("https://www.googleapis.com/youtube/v3/search", params, keys)
        if e: return None, None, e
        if not d_videos: break
        for item in d_videos.get("items", []):
            cid = item["snippet"]["channelId"]
            if cid not in canais_vistos:
                canais_vistos.add(cid)
                lote_canais.append(cid)
        next_page = d_videos.get("nextPageToken")
        if not next_page: break

    # FASE 4: O GRANDE FILTRO
    status_box.write(f"⚙️ Analisando dados, datas e formato longo de {len(lote_canais)} canais únicos...")
    
    for i in range(0, len(lote_canais), 50):
        chunk = lote_canais[i:i+50]
        stats_dados, stats_erro = request_hydra("https://www.googleapis.com/youtube/v3/channels", {"part": "statistics,snippet,contentDetails", "id": ",".join(chunk)}, keys)
        if stats_erro: return None, None, stats_erro
        if not stats_dados: continue
            
        for canal in stats_dados.get("items", []):
            try:
                stats = canal.get("statistics", {})
                snippet = canal.get("snippet", {})
                
                subs = int(stats.get("subscriberCount", 0))
                views = int(stats.get("viewCount", 0))
                videos = int(stats.get("videoCount", 0))
                
                if videos == 0 or videos > 100: continue
                
                uploads_id = canal.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
                if uploads_id:
                    # Roda o filtro duplo: Idade Max + Vídeos Longos
                    canal_eh_valido = verificar_canal_valido(uploads_id, keys, data_limite_3_5_meses)
                    if not canal_eh_valido: continue 
                else:
                    continue
                
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

                if subs >= 1000: gems_encontradas.append(canal_dict)
                else: radar_quase_la.append(canal_dict)
                    
            except Exception as e: 
                continue

    status_box.write(f"🎯 Escaneamento finalizado! GEMS perfeitas encontradas: {len(gems_encontradas)}")

    gems_encontradas.sort(key=lambda x: x["Viral Score"], reverse=True)
    radar_quase_la.sort(key=lambda x: x["Inscritos"], reverse=True) 
    
    return gems_encontradas, radar_quase_la[:15], None 

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state['logado'] = False
def tela_login():
    c1,c2,c3=st.columns([1,1,1])
    with c2:
        st.markdown("<br><div style='background:rgba(255,255,255,0.9); padding:30px; border-radius:30px; text-align:center; border:2px solid #eaddff;'><h1 style='color:#5a4fcf;'>🫐</h1><h2 style='color:#3d3563;'>Blueberry Finder AI v8.7</h2><p>Niche Validator (Long-Form Edition)</p></div><br>", unsafe_allow_html=True)
        with st.form("l"):
            u=st.text_input("Utilizador"); p=st.text_input("Palavra-passe", type="password")
            if st.form_submit_button("🚀 Iniciar Sessão"):
                if u=="admin" and p=="1234": st.session_state['logado']=True; st.rerun()
                else: st.error("Erro de autenticação.")

# --- APLICAÇÃO PRINCIPAL ---
def app_principal():
    api_key_env = os.getenv("YOUTUBE_API_KEY")
    
    with st.sidebar:
        st.markdown("### Menu 🫐")
        st.markdown("📍 **Modo:** Validador Absoluto")
        st.divider()
        st.info("**🎯 Regras de Validação:**\n\n✅ Exige 4 a 5 Canais Mínimo\n✅ Mín. 1.000 Subs por Canal\n✅ Máx. 100 Vídeos\n✅ TODOS os vídeos c/ ≤ 3.5 meses\n✅ Contém vídeos Longos (> 1 min)")
        st.divider()
        if st.button("Terminar Sessão"): st.session_state['logado']=False; st.rerun()

    st.markdown("<h1 style='text-align: center; color: #5a4fcf;'>🫐 Validador de Tendências</h1>", unsafe_allow_html=True)

    with st.form("f_sniper"):
        c1, c2 = st.columns([3, 1])
        palavra_chave = c1.text_input("Palavra-chave (Curta ou Longa):", placeholder="Ex: 'bible hidden', 'reddit stories'...")
        k = api_key_env if api_key_env else c2.text_input("Chave API (Pode usar múltiplas)", type="password")
        
        st.write("")
        b = st.form_submit_button("🌍 Validar Subnicho (Filtro Anti-Shorts)")
        
    if b and palavra_chave:
        
        with st.status(f"A validar a tendência '{palavra_chave}' (Verificando as regras rígidas e excluindo canais apenas de Shorts)...", expanded=True) as status_box:
            gems, radar, erro = buscar_gems_universal(palavra_chave, k, status_box)
            
            if erro:
                status_box.update(label="Falha na Busca!", state="error", expanded=True)
                st.error(f"🚨 ERRO CRÍTICO NA API:\n{erro}")
            else:
                status_box.update(label="Busca Concluída com Sucesso!", state="complete", expanded=False)
                
                # --- A LÓGICA DE VALIDAÇÃO ESTA AQUI ---
                st.divider()
                st.markdown(f"<h2 style='color:#8b5cf6;'>💎 Canais GEM Encontrados (Vídeos Longos, ≤ 100 vídeos em 3.5 meses, ≥ 1k Subs)</h2>", unsafe_allow_html=True)
                
                qtd_gems = len(gems)
                
                # REGRA MESTRE APLICADA NA INTERFACE: Exige de 4 a 5 canais
                if qtd_gems >= 4:
                    st.success(f"🔥 NICHO VALIDADO! Atingimos a meta com {qtd_gems} canais GEMS idênticos para '{palavra_chave}'. Todos com vídeos longos, mercado seguro para entrar!")
                elif qtd_gems > 0:
                    st.warning(f"⚠️ NICHO INCOMPLETO! Encontrámos apenas {qtd_gems} canal(is) GEM que passam em TODAS as regras (inclusive ter vídeos longos). A sua meta exige 4 a 5 canais concorrentes.")
                else:
                    st.error(f"❌ NICHO REJEITADO. Nenhum canal atendeu a todas as regras perfeitas (1k subs, < 100 vídeos, < 3.5 meses E com vídeos longos).")

                if qtd_gems > 0:
                    cols = st.columns(3)
                    for i, r in enumerate(gems[:18]): 
                        with cols[i%3]:
                            st.markdown(f"""
                            <div class='gold-card'>
                                <span class='gold-badge'>💎 GEM {r['Viral Score']}</span>
                                <h4 style='text-overflow: ellipsis; white-space: nowrap; overflow: hidden;' title='{r['Canal']}'>{r['Canal']}</h4>
                                <p>📹 <b>{r['Vídeos']} vídeos</b> | 👥 <b>{r['Inscritos']:,}</b></p>
                                <a href='{r['Link']}' target='_blank' class='visit-btn'>Aceder ao Canal ↗</a>
                            </div>""", unsafe_allow_html=True)

                # RADAR
                st.divider()
                st.markdown(f"<h2 style='color:#6b6399;'>🔭 Radar de Crescimento (< 1.000 Subs)</h2>", unsafe_allow_html=True)
                if len(radar) > 0:
                    df_rad = pd.DataFrame(radar)
                    st.dataframe(df_rad[['Canal', 'Vídeos', 'Inscritos', 'Link']], column_config={"Link": st.column_config.LinkColumn("Link")}, use_container_width=True, hide_index=True)

if st.session_state['logado']: app_principal()
else: tela_login()
