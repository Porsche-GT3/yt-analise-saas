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
st.set_page_config(page_title="Blueberry Finder AI v4.1", page_icon="🫐", layout="wide")

# --- CSS "BLUEBERRY UNICORN THEME" ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f3e7e9 0%, #e3eeff 100%, #e8dbfc 100%); background-attachment: fixed; }
    header[data-testid="stHeader"] { background: transparent; }
    h1, h2, h3 { font-family: 'Inter', sans-serif; color: #3d3563 !important; font-weight: 700; }
    p, label, span, div, caption { color: #544a85 !important; }
    .gold-card { background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(15px); border: 2px solid #c4b5fd; border-radius: 25px; padding: 25px; box-shadow: 0 10px 30px rgba(139, 92, 246, 0.15); margin-bottom: 25px; transition: all 0.4s ease; }
    .gold-card:hover { transform: translateY(-8px); box-shadow: 0 20px 40px rgba(139, 92, 246, 0.25); border-color: #8b5cf6; }
    .gold-badge { background: linear-gradient(90deg, #a78bfa 0%, #f472b6 100%); color: white !important; padding: 6px 15px; border-radius: 20px; font-size: 11px; font-weight: 800; position: absolute; top: -12px; right: 20px; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] { background-color: rgba(255, 255, 255, 0.9) !important; border: 2px solid #ddd6fe !important; color: #3d3563 !important; border-radius: 18px !important; }
    div[data-testid="stFormSubmitButton"] button, div[data-testid="stButton"] button { background: linear-gradient(135deg, #8b5cf6 0%, #d946ef 100%); color: #ffffff !important; font-weight: 700 !important; border: none; padding: 14px 28px; border-radius: 50px; width: 100%; box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4); transition: all 0.3s ease; }
    div[data-testid="stFormSubmitButton"] button:hover, div[data-testid="stButton"] button:hover { transform: scale(1.05); background: linear-gradient(135deg, #7c3aed 0%, #c026d3 100%); }
    .trend-tag { display: inline-block; background: #eaddff; color: #3d3563; padding: 5px 12px; border-radius: 15px; margin: 3px; font-size: 12px; font-weight: 600; }
    .video-card { background:rgba(255,255,255,0.6); padding:15px; border-radius:15px; margin-bottom:15px; border:1px solid #eaddff; display:flex; gap:10px; transition: all 0.3s ease; }
    .video-card:hover { background: white; transform: scale(1.02); border-color: #d946ef; }
    .visit-btn { display: block; width: 100%; text-align: center; padding: 12px; background: white; border: 2px solid #ddd6fe; color: #6b6399; border-radius: 15px; text-decoration: none; font-weight: 700; margin-top: 10px; transition:0.3s; }
    .visit-btn:hover { background: #8b5cf6; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# --- DICIONÁRIO MESTRE ---
def get_nichos_dark():
    return {
        🚀 GERAL (Top Trends)"": None,"
        "🦖 Pré-História & Megafauna": "prehistoric animals|dinosaurs documentary|megafauna|ice age beasts|animais pré-históricos|monstros marinhos|bizarre animals|criaturas abissais|titanoboa|saber tooth tiger|animais extintos|paleontologia|jurassic world real|vida antes dos humanos",
        "🦑 Monstros Marinhos & Abissais": "deep sea creatures|mariana trench mystery|monsters of the deep|animais do fundo do mar|lula colossal|megalodon sightings|bloop sound|thalassophobia|ocean mysteries|biologia marinha bizarra|deepest part of ocean|animais abissais|sea monsters|estranhas criaturas",
        "🧬 Biologia & Evolução Bizarra": "evolutionary biology|weirdest animals|animais mais estranhos|human evolution documentary|microscopic world|vida microscopica|tardigrade|cell biology|dna secrets|parasitas bizarros|animal mutations|nature is metal|evolution mistakes|biologia explicada",
        "🦁 Batalhas Animais & Predadores": "predator vs prey|animal attacks|wildlife documentary|leia vs hiena|cobra gigante|animal battles|natureza selvagem|crocodilo ataque|eagle hunting|orca hunting|apex predators|mundo animal|documentario animais|vida selvagem",
        "🏺 Mesopotâmia & Sumérios": "mesopotamia history|sumerians|anunnaki|ancient babylon|berço da civilização|fertile crescent|gilgamesh epic|origem da escrita|civilização sumeria|ziggurat|history of iraq ancient|cradle of civilization|antiga mesopotamia|codex hammurabi|assírios",
        "🔥 Idade da Pedra & Homens das Cavernas": "stone age documentary|paleolithic life|neolithic revolution|homens das cavernas|humanos primitivos|descoberta do fogo|cave paintings|ice age humans|hunter gatherer lifestyle|ferramentas de pedra|evolução humana|vida na pre historia|tribos antigas|ancestrais humanos",
        "🏰 Idade Média & Tempos Sombrios": "medieval history|middle ages documentary|black plague|tortura medieval|vida na idade media|crusades|cavaleiros medievais|feudalismo|castelos medievais|dark ages history|viking raids|templars history|historia medieval|peste negra|inquisicao",
        "😭 Histórias de Superação & Drama": "sad story overcoming|immigrant story|vida de imigrante|rich vs poor humiliation|humiliated by billionaire|rags to riches|crossing the border|latino struggle|volta por cima|sacrificio de mãe|father sacrifice|historia emocionante|hard life motivation|poor to rich|historia de superação",
        "🔪 True Crime (Investigação)": "true crime documentary|investigação criminal|serial killer|cold cases|crimes não solucionados|forensic files|murder mystery|interrogation footage|casos criminais|desaparecimentos|missing persons|criminal psychology|crime scene|detective stories",
        "👻 Paranormal & Assustador": "ghost caught on camera|poltergeist video|scary stories|lendas urbanas|relatos sobrenaturais|haunted house|investigação paranormal|demon sighting|shadow people|terror real|skinwalker|creepy videos|medo real|espiritos filmados|paranormal activity",
        "👽 Ufologia & Alienígenas": "ufo sighting 2024|alien evidence|area 51 secrets|ovni avistamentos|extraterrestrial life|ancient aliens|abdução alienigena|nasa secrets|uap footage|contatos imediatos|alien autopsy|mars anomalies|secret space program|vida em outros planetas",
        "📼 Lost Media & Dark Web": "lost media iceberg|internet mysteries|dark web stories|deep web videos|arg horror|found footage|videos perturbadores|misterios da internet|cicada 3301|backrooms explained|liminal spaces|analog horror|midia perdida|arquivos secretos|creepy pasta",
        "🕵️ Mistérios Históricos": "unsolved mysteries history|jack the ripper|dyatlov pass|misterios da humanidade|atlantis found|triangulo das bermudas|manuscrito voynich|historical secrets|segredos do vaticano|forbidden history|arqueologia misteriosa|ancient enigmas|civilizações perdidas|teorias da conspiração|segredos ocultos",
        "🎮 Gaming Dark & Lore": "gaming lore|video game mysteries|scary easter eggs|lost video games|fnaf lore|dark souls story|silent hill history|iceberg gaming|creepypasta games|banned video games|historia dos jogos|misterios dos games|jogos perdidos|segredos dos jogos",
        "⚽ Esportes (Lado Sombrio)": "sports tragedies|dark side of sports|athletes who lost everything|biggest sports scandals|f1 history|boxing legends|football rivalries|worst injuries in sports|corruption in sports|untold stories sports|tragedias no esporte|escandalos esportivos|historia do futebol",
        "🎬 Cinema & Significados Ocultos": "movie ending explained|hidden details in movies|dark disney theories|cinema psychology|film analysis|matrix philosophy|joker analysis|fight club meaning|mensagens subliminares|teorias da conspiracao filmes|final explicado|analise de filmes|segredos do cinema",
        "📚 Resumos de Livros & Big Ideas": "book summaries|visual book review|48 laws of power|rich dad poor dad|psychology books|self improvement books|business book summary|greatest books of all time|wisdom bread style|escaping ordinary style|philosophy books|financial education|resumo de livros",
        "🍔 História da Comida & Marcas": "food history|origin of brands|dark history of coca cola|mcdonalds secrets|forbidden foods|most expensive food|history of sugar|fast food secrets|kfc history|historia das marcas|origem dos alimentos|comidas proibidas|segredos fast food",
        "📜 História Antiga (Geral)": "ancient civilizations|ancient egypt documentary|roma antiga|grecia antiga|persian empire|alexander the great|julius caesar|historia antiga|pharaohs secrets|pyramids construction|ancient technology|imperio romano|esparta|historia do mundo",
        "⚔️ Guerras & Batalhas": "world war 2 documentary|segunda guerra mundial|batalhas historicas|military strategy|napoleonic wars|vietnam war footage|guerra fria|tank battles|sniper stories|special forces history|grandes generais|war history|combat footage history|armas secretas|historia militar",
        "👑 Biografias de Grandes Líderes": "biography documentary|napoleon bonaparte|genghis khan|winston churchill|greatest leaders|life of alexander|nikola tesla biography|albert einstein life|figuras historicas|imperadores romanos|kings and queens|royal family secrets|dictators history|historia de vida",
        "🙏 Histórias Bíblicas & Fé": "bible stories explained|book of enoch|angels and demons|historia biblica|apocalipse|genesis|old testament|life of jesus|profecias biblicas|nephilim|arca de noé|sodoma e gomorra|jerusalem history|milagres de jesus|biblical archaeology",
        "🧠 Estoicismo & Filosofia": "stoicism for beginners|marcus aurelius quotes|seneca philosophy|filosofia de vida|controle emocional|sabedoria antiga|taoism explained|confucius quotes|nietzsche philosophy|plato allegory of the cave|socrates wisdom|art of war sun tzu|discipline mindset|filosofia estoica",
        "🚀 Espaço & Universo": "space documentary|james webb images|black hole sound|tamanho do universo|sistema solar|vida em marte|spacex launch|nasa discoveries|universe documentary|cosmic horror|time dilation|dark matter|nebulas|astronomia|curiosidades do espaço",
        "🤖 Inteligência Artificial": "ai news today|chatgpt 5|midjourney v6|ai tools for business|inteligencia artificial|futuro da ia|robots boston dynamics|ai taking over|novidades ia|automação|nvidia ai|openai sora|artificial general intelligence|ai avatar|tecnologia futura",
        "🤯 Fatos Alucinantes (Curiosidades)": "amazing facts|things you didn't know|fatos aleatorios|curiosidades do mundo|voce sabia|fatos interessantes|mind blowing facts|science facts|fatos historicos|curiosidades rapidas|top 10 fatos|listas curiosas|strange facts|fatos bizarros|conhecimento geral",
        "💊 O Que Aconteceria Se...": "what if scenarios|what if earth stopped|e se o sol apagasse|what if dinosaurs survived|e se|cenarios hipoteticos|ciencia explicada|teoria do caos|efeito borboleta|what if history|e se a alemanha ganhasse|what if humans disappeared|future timeline|ciencia curiosa|experiencias mentais",
        "💰 Luxo & Vida de Bilionário": "billionaire lifestyle|mega mansions tour|superyachts|vida de luxo|carros de luxo|most expensive things|dubai lifestyle|monaco luxury|billionaire motivation|luxo extremo|mansões incriveis|private jet|relogios caros|estilo de vida rico|old money aesthetic",
        "📈 Histórias de Marcas & Magnates": "business documentary|company downfall|how they make money|historia das marcas|historia mcdonalds|apple history|elon musk story|jeff bezos|warren buffett|marketing strategies|fracassos de empresas|ascensão e queda|business lessons|biografia empreendedores",
        "🪙 Cripto & Mercado Financeiro": "crypto news|bitcoin prediction|investing for beginners|bolsa de valores|day trade|analise grafica|ethereum|altcoins|criptomoedas|financial crisis|economia mundial|dolar hoje|investimentos|educação financeira|dividendos",
        "💸 Renda Extra & Marketing Digital": "passive income ideas|make money online|dropshipping results|marketing digital|afiliados|chatgpt money|youtube automation|print on demand|renda extra|trabalhar em casa|freelancer tips|side hustles|dinheiro online|ecommerce",
        "🌧️ ASMR & Sons de Chuva": "rain sounds for sleep|thunderstorm black screen|heavy rain|white noise|sons de chuva|barulho de chuva|sleep music|sons da natureza|ocean waves|fireplace sound|relaxing sounds|insomnia relief|deep sleep|sons para dormir|ambiente relaxante",
        "✨ Frequências & Música Lofi": "lofi hip hop study|432hz healing|binaural beats|focus music|musica para estudar|relaxing jazz|musica ambiente|frequency healing|stress relief music|musica calma|piano relaxante|ambient music|study beats|musica para trabalhar|soundscape",
        "🥒 Saúde Natural & Corpo": "natural remedies|benefits of ginger|foods that kill diabetes|curas naturais|dicas de saude|perder peso rapido|exercicios em casa|home workout|intermittent fasting|jejum intermitente|alimentos saudaveis|longevidade|biohacking|rotina saudavel|corpo humano",
        "🌲 Sobrevivência & Bushcraft": "bushcraft shelter|solo camping rain|survival skills|acampamento solo|construção na floresta|off grid living|primitive technology|sobrevivencialismo|camping in rain|cooking in forest|vida na natureza|cabana na floresta|camping asmr|natureza selvagem|wild camping",
        "🔨 Satisfatório & Restauração": "oddly satisfying video|restoration rusty|carpet cleaning|pressure washing|videos satisfatorios|asmr cleaning|restauracao de relogios|knife restoration|shredding machine|hydraulic press|satisfying slime|kinetic sand|soap cutting|limpeza pesada|art restoration"
    }

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

# --- FUNÇÃO DE BUSCA VIRAIS ---
def buscar_radar_dark(pais_code, query_especifica, keys_str):
    keys = get_api_keys_list(keys_str)
    if not keys: return None, "Chave necessária"
    
    data_inicio = datetime.datetime.now() - timedelta(days=30)
    published_after = data_inicio.isoformat("T") + "Z"
    
    params = {"part": "snippet,statistics", "regionCode": pais_code, "maxResults": 50}
    
    if query_especifica is None:
        url = "https://www.googleapis.com/youtube/v3/videos"
        params["chart"] = "mostPopular"
    else:
        url = "https://www.googleapis.com/youtube/v3/search"
        params["q"] = query_especifica
        params["type"] = "video"
        params["order"] = "viewCount"
        params["publishedAfter"] = published_after

    dados, erro = request_hydra(url, params, keys)
    if erro: return [], erro
    if "items" not in dados: return [], "Nenhum dado."
    
    dados_items = dados["items"]
    
    if query_especifica is not None:
        ids_list = [i["id"]["videoId"] for i in dados_items if isinstance(i["id"], dict) and "videoId" in i["id"]]
        if ids_list:
            stats_dados, stats_erro = request_hydra("https://www.googleapis.com/youtube/v3/videos", {"part":"statistics,snippet", "id": ",".join(ids_list)}, keys)
            if stats_dados: dados_items = stats_dados.get("items", [])
    
    todos_tags = []
    videos_analisados = []
    
    for item in dados_items:
        try:
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})
            tags = snippet.get("tags", [])
            if tags: todos_tags.extend([t.lower() for t in tags])
            
            vid_id = item.get("id")
            if isinstance(vid_id, dict): vid_id = vid_id.get("videoId", "")
            
            videos_analisados.append({ 
                "titulo": snippet.get("title", ""), 
                "canal": snippet.get("channelTitle", ""), 
                "views": int(stats.get("viewCount", 0)), 
                "thumb": snippet.get("thumbnails", {}).get("high", {}).get("url", ""), 
                "link": f"https://www.youtube.com/watch?v={vid_id}" 
            })
        except: continue
        
    videos_analisados.sort(key=lambda x: x['views'], reverse=True)
    return {"videos": videos_analisados, "top_assuntos": Counter(todos_tags).most_common(15)}, None

# --- TOP CANAIS (FILTRO DE JOIAS: <= 40 VÍDEOS) ---
def buscar_top_canais_nicho(pais_code, query_especifica, keys_str):
    keys = get_api_keys_list(keys_str)
    if not keys: return []
    
    q = query_especifica if query_especifica else ""
    canais_encontrados = []
    next_page_token = None
    
    for _ in range(2): 
        # BUSCA DE CANAIS
        url = "https://www.googleapis.com/youtube/v3/search"
        params = { "part": "snippet", "q": q, "type": "channel", "regionCode": pais_code, "maxResults": 50 }
        if next_page_token: params["pageToken"] = next_page_token
        
        data, erro = request_hydra(url, params, keys)
        if erro or not data or "items" not in data: break
        
        ids = [i["id"]["channelId"] for i in data["items"] if "channelId" in i["id"]]
        if not ids: break
        
        # DETALHES DOS CANAIS
        stats_data, s_erro = request_hydra("https://www.googleapis.com/youtube/v3/channels", {"part": "statistics,snippet", "id": ",".join(ids)}, keys)
        if s_erro or not stats_data: break
        
        for c in stats_data.get("items", []):
            try:
                stats = c.get("statistics", {})
                snippet = c.get("snippet", {})
                
                subs = int(stats.get("subscriberCount", 0))
                views = int(stats.get("viewCount", 0))
                videos = int(stats.get("videoCount", 0)) # Contagem de vídeos
                
                # --- FILTRO SNIPER (JOIAS) ---
                # Apenas canais com entre 5 e 40 vídeos
                if 5 <= videos <= 40:
                    
                    # Cálculo de Viralização (Growth)
                    media_views = views / videos if videos > 0 else 0
                    viral_score = media_views / subs if subs > 0 else 0
                    
                    canais_encontrados.append({
                        "Canal": snippet.get("title", ""),
                        "Inscritos": subs,
                        "Vídeos": videos,
                        "Média Views/Vídeo": int(media_views),
                        "Viral Score": round(viral_score, 2),
                        "Link": f"https://www.youtube.com/channel/{c['id']}"
                    })
            except: continue
        
        next_page_token = data.get("nextPageToken")
        if not next_page_token: break
    
    # ORDENA POR POTENCIAL DE VIRALIZAÇÃO
    canais_encontrados.sort(key=lambda x: x["Viral Score"], reverse=True)
    return canais_encontrados

# --- MODO 1: BUSCA POR NICHO (MANTIDO E MELHORADO) ---
def buscar_top_videos(channel_id, keys_str):
    keys = get_api_keys_list(keys_str)
    if not keys: return []
    try:
        data = datetime.datetime.now() - timedelta(days=45)
        params = { "channelId": channel_id, "part": "snippet", "order": "viewCount", "publishedAfter": data.isoformat("T")+"Z", "type": "video", "maxResults": 5 }
        d, e = request_hydra("https://www.googleapis.com/youtube/v3/search", params, keys)
        if not d: return []
        return [{"titulo": i["snippet"]["title"], "data": i["snippet"]["publishedAt"][:10], "thumb": i["snippet"]["thumbnails"]["high"]["url"]} for i in d.get("items", [])]
    except: return []

def buscar_dados_youtube(nicho, keys_str):
    keys = get_api_keys_list(keys_str)
    if not keys: return None, "Chave necessária"
    
    d, erro = request_hydra("https://www.googleapis.com/youtube/v3/search", {"part":"snippet", "q":nicho, "type":"channel", "maxResults":50}, keys)
    if erro or not d: return [], None
    
    ids = [i["id"]["channelId"] for i in d.get("items", []) if "channelId" in i["id"]]
    if not ids: return [], None
    
    s_r, erro_s = request_hydra("https://www.googleapis.com/youtube/v3/channels", {"part":"statistics", "id": ",".join(ids)}, keys)
    if not s_r: return [], None
    
    s_map = {i["id"]: i.get("statistics", {}) for i in s_r.get("items", [])}
    res = []
    
    for i in d["items"]:
        try:
            cid = i["id"]["channelId"]
            s = s_map.get(cid, {})
            v = int(s.get("viewCount",0))
            sub = int(s.get("subscriberCount",0))
            vid = int(s.get("videoCount",0)) # Contagem de vídeos
            
            media = v/vid if vid > 0 else 0
            
            # FILTRO SNIPER AQUI TAMBÉM (Modo Busca Direta)
            # Aceitamos canais um pouco maiores aqui (até 60) para dar mais opções, 
            # mas focamos nos < 40 para ser GOLD.
            if vid > 0: score = media / sub if sub > 0 else 0
            else: score = 0
            
            # GOLD = Poucos vídeos (<=40) + Crescimento Alto
            gold = True if (score > 0.5 and vid <= 40) else False
            
            # Só adiciona se tiver menos de 100 vídeos (filtro amplo)
            # Mas o destaque GOLD vai para os < 40
            if vid <= 100:
                res.append({
                    "nome": i["snippet"]["title"], 
                    "inscritos": sub, 
                    "total_videos": vid, 
                    "media_views": int(media),
                    "viral_score": round(score, 2),
                    "e_ouro": gold, 
                    "link": f"https://www.youtube.com/channel/{cid}", 
                    "id": cid
                })
        except: continue
        
    res.sort(key=lambda x: x['viral_score'], reverse=True)
    return res, None

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state['logado'] = False
def tela_login():
    c1,c2,c3=st.columns([1,1,1])
    with c2:
        st.markdown("<br><div style='background:rgba(255,255,255,0.9); padding:30px; border-radius:30px; text-align:center; border:2px solid #eaddff;'><h1 style='color:#5a4fcf;'>🫐</h1><h2 style='color:#3d3563;'>Blueberry Finder AI v4.1</h2><p>Gems Edition (Max 40 Vídeos)</p></div><br>", unsafe_allow_html=True)
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
        modo = st.radio("Navegação:", ["🔍 Busca por Nicho (Growth)", "🌍 Radar Global (Dark)"])
        st.divider()
        if st.button("Sair"): st.session_state['logado']=False; st.rerun()

    st.markdown("<h1 style='text-align: center; color: #5a4fcf;'>🫐 Blueberry Finder AI v4.1</h1>", unsafe_allow_html=True)

    # MODO 1: BUSCA POR NICHO (GROWTH)
    if modo == "🔍 Busca por Nicho (Growth)":
        st.markdown("<p style='text-align:center;'>Encontre <b>Joias Raras</b> (Canais com menos de 40 vídeos explodindo).</p>", unsafe_allow_html=True)
        with st.form("f1"):
            c1,c2=st.columns([3,1])
            k = api_key_env if api_key_env else c1.text_input("API Keys (Hydra)", type="password")
            n = c1.text_input("Nicho", placeholder="Ex: Yoga...")
            c2.write(""); c2.write("")
            b = c2.form_submit_button("🔍 Buscar Gems")
        
        if b and n:
            with st.spinner("Minerando canais recentes..."):
                d, e = buscar_dados_youtube(n, k)
                if d:
                    df = pd.DataFrame(d)
                    ouro = df[df['e_ouro']==True]
                    st.divider()
                    if not ouro.empty:
                        st.success(f"Encontramos {len(ouro)} Canais GOLD (Menos de 40 vídeos + Viral)!")
                        cols = st.columns(3)
                        for i, r in ouro.reset_index().iterrows():
                            with cols[i%3]:
                                st.markdown(f"""
                                <div class='gold-card'>
                                    <span class='gold-badge'>💎 GEM {r['viral_score']}</span>
                                    <h4>{r['nome']}</h4>
                                    <p>📹 {r['total_videos']} vídeos | 👥 {r['inscritos']}</p>
                                    <small style='color:#d946ef'>Média: {r['media_views']} views/vídeo</small>
                                    <a href='{r['link']}' target='_blank' class='visit-btn'>Ver Canal ↗</a>
                                </div>""", unsafe_allow_html=True)
                                with st.expander("Ver Virais"):
                                    vs = buscar_top_videos(r['id'], k)
                                    if vs:
                                        p = "Roteiros baseados nestes:\n"
                                        for v in vs:
                                            st.markdown(f"**{v['titulo']}**<br><small>{v['data']}</small><hr>", unsafe_allow_html=True)
                                            p+=f"- {v['titulo']}\n"
                                        st.code(p, language='text')
                    st.divider()
                    st.markdown("### 📊 Ranking de Novas Promessas (Max 100 vídeos)")
                    st.dataframe(
                        df[['nome','total_videos','inscritos','media_views','viral_score','link']], 
                        column_config={
                            "link": st.column_config.LinkColumn("Link", display_text="Ver ↗"),
                            "viral_score": st.column_config.ProgressColumn("Potencial Viral", min_value=0, max_value=5, format="%.2f")
                        }, 
                        use_container_width=True
                    )

    # MODO 2: RADAR GLOBAL
    elif modo == "🌍 Radar Global (Dark)":
        st.markdown("<p style='text-align:center;'>Espione os nichos mais lucrativos do mundo <b>AGORA</b> (Últimos 30 dias).</p>", unsafe_allow_html=True)
        paises = { "🇺🇸 Estados Unidos": "US", "🇧🇷 Brasil": "BR", "🇲🇽 México": "MX", "🇬🇧 Reino Unido": "GB", "🇩🇪 Alemanha": "DE", "🇪🇸 Espanha": "ES", "🇫🇷 França": "FR", "🇷🇺 Rússia": "RU", "🇮🇳 Índia": "IN" }
        filtros_dict = get_nichos_dark()
        c1, c2, c3 = st.columns([1, 1, 1])
        pais = c1.selectbox("1. País:", list(paises.keys()))
        categoria_nome = c2.selectbox("2. Nicho:", list(filtros_dict.keys()))
        c3.write(""); c3.write("")
        key_r = api_key_env if api_key_env else st.text_input("API Keys", type="password")
        
        if c3.button("📡 Escanear Nicho & Canais", type="primary"):
            query = filtros_dict[categoria_nome]
            with st.spinner(f"Hydra Varrendo YouTube {paises[pais]}..."):
                res, erro = buscar_radar_dark(paises[pais], query, key_r)
                top_canais = buscar_top_canais_nicho(paises[pais], query, key_r)
                
                if res:
                    videos = res["videos"]
                    st.divider()
                    st.subheader(f"📹 Top Vídeos Recentes")
                    c_v1, c_v2 = st.columns(2)
                    for i, v in enumerate(videos):
                        with (c_v1 if i%2==0 else c_v2):
                             st.markdown(f"<div class='video-card'><img src='{v['thumb']}' style='width:120px;height:90px;object-fit:cover;border-radius:10px;'><div><h5 style='margin:0;font-size:14px;color:#3d3563;'>{v['titulo'][:60]}...</h5><p style='font-size:11px;margin:5px 0;color:#6b6399;'>📺 {v['canal']}</p><p style='font-size:12px;font-weight:bold;color:#d946ef;'>👁️ {v['views']:,} views</p><a href='{v['link']}' target='_blank' style='font-size:11px;color:#8b5cf6;font-weight:700;'>Assistir ↗</a></div></div>", unsafe_allow_html=True)
                    
                    st.divider()
                    st.markdown(f"<h3 style='color:#3d3563'>🏆 Top Canais 'Hidden Gems' (Max 40 Vídeos)</h3>", unsafe_allow_html=True)
                    if top_canais:
                        df_canais = pd.DataFrame(top_canais)
                        st.dataframe(df_canais, column_config={"Link": st.column_config.LinkColumn("Link", display_text="Acessar ↗"), "Viral Score": st.column_config.ProgressColumn("Crescimento", min_value=0, max_value=5)}, use_container_width=True, hide_index=True)
                    else: st.warning("Nenhum canal com menos de 40 vídeos encontrado no topo deste nicho/país.")
                elif erro: st.error(erro)

if st.session_state['logado']: app_principal()
else: tela_login()
