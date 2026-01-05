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

# --- CSS "BLUEBERRY UNICORN THEME" (COM HOVER FX 3.0) 🦄🫐 ---
st.markdown("""
    <style>
    /* 1. FUNDO E GERAL */
    .stApp { background: linear-gradient(135deg, #f3e7e9 0%, #e3eeff 100%, #e8dbfc 100%); background-attachment: fixed; }
    header[data-testid="stHeader"] { background: transparent; }
    h1, h2, h3 { font-family: 'Inter', sans-serif; color: #3d3563 !important; font-weight: 700; }
    p, label, span, div, caption { color: #544a85 !important; }
    
    /* 2. CARDS (Vidro) */
    .gold-card { 
        background: rgba(255, 255, 255, 0.85); 
        backdrop-filter: blur(15px); 
        border: 2px solid #c4b5fd; 
        border-radius: 25px; 
        padding: 25px; 
        box-shadow: 0 10px 30px rgba(139, 92, 246, 0.15); 
        margin-bottom: 25px; 
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); /* Efeito elástico */
    }
    .gold-card:hover { 
        transform: translateY(-8px); 
        box-shadow: 0 20px 40px rgba(139, 92, 246, 0.25);
        border-color: #8b5cf6;
    }
    .gold-badge { 
        background: linear-gradient(90deg, #a78bfa 0%, #f472b6 100%); 
        color: white !important; padding: 6px 15px; border-radius: 20px; 
        font-size: 11px; font-weight: 800; position: absolute; top: -12px; right: 20px; 
        box-shadow: 0 4px 10px rgba(167, 139, 250, 0.4);
    }
    
    /* 3. INPUTS */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] { 
        background-color: rgba(255, 255, 255, 0.9) !important; 
        border: 2px solid #ddd6fe !important; 
        color: #3d3563 !important; 
        border-radius: 18px !important; 
        transition: all 0.3s ease;
    }
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus-within {
        border-color: #8b5cf6 !important;
        box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.2) !important;
        transform: scale(1.01);
    }

    /* 4. BOTÕES PRINCIPAIS (Buscar/Escanear) - SUPER RESPONSIVOS */
    div[data-testid="stFormSubmitButton"] button, div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #8b5cf6 0%, #d946ef 100%); 
        color: #ffffff !important; 
        font-weight: 700 !important; 
        border: none; 
        padding: 14px 28px; 
        border-radius: 50px; 
        width: 100%; 
        box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        cursor: pointer;
    }
    div[data-testid="stFormSubmitButton"] button:hover, div[data-testid="stButton"] button:hover {
        transform: scale(1.05) translateY(-2px); /* Cresce e Sobe */
        box-shadow: 0 15px 35px rgba(217, 70, 239, 0.6); /* Brilho Rosa */
        background: linear-gradient(135deg, #7c3aed 0%, #c026d3 100%);
    }
    div[data-testid="stFormSubmitButton"] button:active {
        transform: scale(0.95); /* Clica para dentro */
    }
    
    /* 5. BOTÃO VER CANAL (Estilo Link) */
    .visit-btn {
        display: block;
        width: 100%;
        text-align: center;
        padding: 12px;
        background: white;
        border: 2px solid #ddd6fe;
        color: #6b6399;
        border-radius: 15px;
        text-decoration: none;
        font-weight: 700;
        transition: all 0.3s ease;
        margin-top: 10px;
    }
    .visit-btn:hover {
        background: #8b5cf6;
        color: white !important;
        border-color: #8b5cf6;
        transform: translateY(-3px);
        box-shadow: 0 5px 15px rgba(139, 92, 246, 0.3);
    }

    /* 6. TAGS & VÍDEOS */
    .trend-tag { display: inline-block; background: #eaddff; color: #3d3563; padding: 5px 12px; border-radius: 15px; margin: 3px; font-size: 12px; font-weight: 600; transition:0.3s;}
    .trend-tag:hover { background: #d8b4fe; cursor: default; transform: scale(1.1); }
    
    .video-card {
        background:rgba(255,255,255,0.6); padding:15px; border-radius:15px; margin-bottom:15px; border:1px solid #eaddff; display:flex; gap:10px; transition: all 0.3s ease;
    }
    .video-card:hover {
        background: white;
        transform: scale(1.02);
        border-color: #d946ef;
        box-shadow: 0 5px 20px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- DICIONÁRIO MESTRE (50 CATEGORIAS + SUPERAÇÃO) ---
def get_nichos_dark():
    return {
        "🚀 GERAL (Top Trends)": None,
        "😭 Histórias de Superação & Drama Real": "sad story overcoming|immigrant story|vida de imigrante|rich vs poor humiliation|humiliated by billionaire|rags to riches documentary|crossing the border|latino struggle|volta por cima|revenge story|sacrificio de mãe|father sacrifice|historia emocionante|hard life motivation|poor to rich transformation|humilhada por ser pobre|historia de superação",
        "🔪 True Crime (Investigação)": "true crime documentary|investigação criminal|serial killer|cold cases|crimes não solucionados|forensic files|murder mystery|interrogation footage|casos criminais|desaparecimentos|missing persons|criminal psychology|crime scene|detective stories|policia investigação",
        "👻 Paranormal & Assustador": "ghost caught on camera|poltergeist video|scary stories|lendas urbanas|relatos sobrenaturais|haunted house|investigação paranormal|demon sighting|shadow people|terror real|skinwalker|creepy videos|medo real|espiritos filmados|paranormal activity",
        "👽 Ufologia & Alienígenas": "ufo sighting 2024|alien evidence|area 51 secrets|ovni avistamentos|extraterrestrial life|ancient aliens|abdução alienigena|nasa secrets|uap footage|contatos imediatos|alien autopsy|mars anomalies|secret space program|vida em outros planetas|universo misterioso",
        "📼 Lost Media & Dark Web": "lost media iceberg|internet mysteries|dark web stories|deep web videos|arg horror|found footage|videos perturbadores|misterios da internet|cicada 3301|backrooms explained|liminal spaces|analog horror|midia perdida|arquivos secretos|creepy pasta",
        "🕵️ Mistérios Históricos": "unsolved mysteries history|jack the ripper|dyatlov pass|misterios da humanidade|atlantis found|triangulo das bermudas|manuscrito voynich|historical secrets|segredos do vaticano|forbidden history|arqueologia misteriosa|ancient enigmas|civilizações perdidas|teorias da conspiração|segredos ocultos",
        "📜 História Antiga (Documentários)": "ancient civilizations|sumerians|babylon|ancient egypt documentary|roma antiga|grecia antiga|mesopotamia history|persian empire|alexander the great|julius caesar|historia antiga|pharaohs secrets|pyramids construction|ancient technology|berço da civilização",
        "⚔️ Guerras & Batalhas Épicas": "world war 2 documentary|segunda guerra mundial|batalhas historicas|military strategy|napoleonic wars|vietnam war footage|guerra fria|tank battles|sniper stories|special forces history|grandes generais|war history|combat footage history|armas secretas|historia militar",
        "👑 Biografias de Grandes Líderes": "biography documentary|napoleon bonaparte|genghis khan|winston churchill|greatest leaders|life of alexander|nikola tesla biography|albert einstein life|figuras historicas|imperadores romanos|kings and queens|royal family secrets|dictators history|historia de vida|grandes personalidades",
        "🏰 Idade Média & Castelos": "medieval history|middle ages documentary|knights and castles|crusades history|viking history|black plague|vida na idade media|tortura medieval|feudalismo|samurai history|castelos antigos|medieval warfare|sword fighting|historia medieval|dark ages",
        "🗿 Arqueologia Proibida": "forbidden archaeology|ooparts|ancient advanced technology|gobekli tepe|descobertas impossiveis|arqueologia proibida|artefatos antigos|ancient giants|underground cities|piramides antartida|ancient apocalypse|flood myth|pre-ice age civilization|civilização antes da historia|mistérios arqueologicos",
        "🙏 Histórias Bíblicas & Fé": "bible stories explained|book of enoch|angels and demons|historia biblica|apocalipse|genesis|old testament|life of jesus|profecias biblicas|nephilim|arca de noé|sodoma e gomorra|jerusalem history|milagres de jesus|biblical archaeology",
        "🧠 Estoicismo & Filosofia de Vida": "stoicism for beginners|marcus aurelius quotes|seneca philosophy|filosofia de vida|controle emocional|sabedoria antiga|taoism explained|confucius quotes|nietzsche philosophy|plato allegory of the cave|socrates wisdom|art of war sun tzu|discipline mindset|filosofia estoica|mentalidade forte",
        "🦁 Motivação Sigma & Disciplina": "sigma male grindset|motivational speech|david goggins motivation|discipline quotes|gym motivation|mentalidade de sucesso|homem de valor|maskulinity|financial freedom motivation|never give up|winner mindset|leis do poder|robert greene|jordan peterson clips|dark motivation",
        "🗣️ Psicologia Sombria & Manipulação": "dark psychology tricks|manipulation techniques|body language analysis|leis da natureza humana|psicologia reversa|linguagem corporal|como ler pessoas|machiavellianism|narcissism explained|detect lies|psicologia comportamental|influenciar pessoas|segredos da mente|persuasão|analise comportamental",
        "🧘 Meditação & Lei da Atração": "guided meditation|manifestation frequency|law of attraction success|ho'oponopono|abundancia financeira|reprogramação mental|solfeggio frequencies|dormir profundamente|limpeza energetica|chakras healing|spiritual awakening|opening third eye|frequencia 963hz|meditação guiada|poder da mente",
        "🚀 Espaço & Universo": "space documentary|james webb images|black hole sound|tamanho do universo|sistema solar|vida em marte|spacex launch|nasa discoveries|universe documentary|cosmic horror|time dilation|dark matter|nebulas|astronomia|curiosidades do espaço",
        "🤖 Inteligência Artificial (News)": "ai news today|chatgpt 5|midjourney v6|ai tools for business|inteligencia artificial|futuro da ia|robots boston dynamics|ai taking over|novidades ia|automação|nvidia ai|openai sora|artificial general intelligence|ai avatar|tecnologia futura",
        "🧬 Futuro da Humanidade & Evolução": "future of humanity|human evolution timeline|ano 3000|transhumanism|crispr technology|futuro da terra|evolution documentary|post human|timeline of the future|cyberpunk reality|biotecnologia|life in 100 years|futurismo|scifi technology|evolução humana",
        "💻 Programação & Tech Dark": "coding for beginners|hacker culture|cybersecurity tips|linux for hackers|python projects|programação web|tech news|gadgets reviews|pc gaming setup|hardware unboxing|tecnologia avançada|quantum computing|internet of things|dark tech|futuro dos computadores",
        "☢️ Desastres & Engenharia": "engineering disasters|bridge collapse|chernobyl documentary|nuclear explosion|mega structures|construções incriveis|falhas de engenharia|catastrofes naturais|predios mais altos|industrial accidents|oil rig disaster|plane crash investigation|engenharia extrema|como foi feito|grandes construções",
        "🌍 Geografia & Mapas Curiosos": "geography facts|interesting maps|why this country is poor|geopolitica|fronteiras estranhas|paises mais ricos|curiosidades geografia|mapas explicados|demographics|population growth|megacities|geography now|curiosidades paises|travel documentary|mundo curioso",
        "🤯 Fatos Alucinantes (Did You Know)": "amazing facts|things you didn't know|fatos aleatorios|curiosidades do mundo|voce sabia|fatos interessantes|mind blowing facts|science facts|fatos historicos|curiosidades rapidas|top 10 fatos|listas curiosas|strange facts|fatos bizarros|conhecimento geral",
        "🆚 Comparações (Probabilidade/Tamanho)": "probability comparison|size comparison 3d|comparison video|universe size comparison|richest companies comparison|comparação de tamanho|velocidade comparação|animais comparação|predios comparação|exercito comparação|população comparação|evolution comparison|wealth comparison|comparação visual|data visualization",
        "❓ Quiz & Testes de QI": "general knowledge quiz|guess the country|logo quiz|teste de inteligencia|adivinhe o som|riddles with answers|enigma|teste de qi|quiz de geografia|quiz de historia|movie quiz|emoji challenge|brain teasers|desafio mental|jogos de adivinhação",
        "💊 O Que Aconteceria Se... (What If)": "what if scenarios|what if earth stopped|e se o sol apagasse|what if dinosaurs survived|e se|cenarios hipoteticos|ciencia explicada|teoria do caos|efeito borboleta|what if history|e se a alemanha ganhasse|what if humans disappeared|future timeline|ciencia curiosa|experiencias mentais",
        "💰 Luxo & Vida de Bilionário": "billionaire lifestyle|mega mansions tour|superyachts|vida de luxo|carros de luxo|most expensive things|dubai lifestyle|monaco luxury|billionaire motivation|luxo extremo|mansões incriveis|private jet|relogios caros|estilo de vida rico|old money aesthetic",
        "📈 Histórias de Marcas & Magnates": "business documentary|company downfall|how they make money|historia das marcas|historia mcdonalds|apple history|elon musk story|jeff bezos|warren buffett|marketing strategies|fracassos de empresas|ascensão e queda|business lessons|biografia empreendedores|economia explicada",
        "🪙 Cripto & Mercado Financeiro": "crypto news|bitcoin prediction|investing for beginners|bolsa de valores|day trade|analise grafica|ethereum|altcoins|criptomoedas|financial crisis|economia mundial|dolar hoje|investimentos|educação financeira|dividendos",
        "💸 Renda Extra & Marketing Digital": "passive income ideas|make money online|dropshipping results|marketing digital|afiliados|chatgpt money|youtube automation|print on demand|renda extra|trabalhar em casa|freelancer tips|side hustles|dinheiro online|ecommerce|vendas online",
        "🌧️ ASMR & Sons de Chuva": "rain sounds for sleep|thunderstorm black screen|heavy rain|white noise|sons de chuva|barulho de chuva|sleep music|sons da natureza|ocean waves|fireplace sound|relaxing sounds|insomnia relief|deep sleep|sons para dormir|ambiente relaxante",
        "✨ Frequências & Música Lofi": "lofi hip hop study|432hz healing|binaural beats|focus music|musica para estudar|relaxing jazz|musica ambiente|frequency healing|stress relief music|musica calma|piano relaxante|ambient music|study beats|musica para trabalhar|soundscape",
        "🥒 Saúde Natural & Corpo": "natural remedies|benefits of ginger|foods that kill diabetes|curas naturais|dicas de saude|perder peso rapido|exercicios em casa|home workout|intermittent fasting|jejum intermitente|alimentos saudaveis|longevidade|biohacking|rotina saudavel|corpo humano",
        "🌲 Sobrevivência & Bushcraft": "bushcraft shelter|solo camping rain|survival skills|acampamento solo|construção na floresta|off grid living|primitive technology|sobrevivencialismo|camping in rain|cooking in forest|vida na natureza|cabana na floresta|camping asmr|natureza selvagem|wild camping",
        "🔨 Satisfatório & Restauração": "oddly satisfying video|restoration rusty|carpet cleaning|pressure washing|videos satisfatorios|asmr cleaning|restauracao de relogios|knife restoration|shredding machine|hydraulic press|satisfying slime|kinetic sand|soap cutting|limpeza pesada|art restoration"
    }

# --- FUNÇÕES (MANTIDAS) ---
def buscar_radar_dark(pais_code, query_especifica, api_key):
    if not api_key: return None, "API Key necessária"
    data_inicio = datetime.datetime.now() - timedelta(days=30)
    published_after = data_inicio.isoformat("T") + "Z"
    if query_especifica is None:
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = { "part": "snippet,statistics", "chart": "mostPopular", "regionCode": pais_code, "maxResults": 50, "key": api_key }
    else:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = { "part": "snippet", "q": query_especifica, "type": "video", "order": "viewCount", "publishedAfter": published_after, "regionCode": pais_code, "maxResults": 50, "key": api_key }
    try:
        resp = requests.get(url, params=params)
        dados = resp.json()
        if "items" not in dados: return [], "Nenhum dado encontrado"
        if query_especifica is not None:
            ids = ",".join([i["id"]["videoId"] for i in dados["items"]])
            stats_resp = requests.get("https://www.googleapis.com/youtube/v3/videos", params={"part":"statistics,snippet", "id": ids, "key": api_key})
            dados_items = stats_resp.json().get("items", [])
        else: dados_items = dados["items"]
        todos_tags = []
        videos_analisados = []
        for item in dados_items:
            stats = item["statistics"]
            snippet = item["snippet"]
            tags = snippet.get("tags", [])
            if tags: todos_tags.extend([t.lower() for t in tags])
            videos_analisados.append({ "titulo": snippet["title"], "canal": snippet["channelTitle"], "views": int(stats.get("viewCount", 0)), "thumb": snippet["thumbnails"]["high"]["url"], "link": f"https://www.youtube.com/watch?v={item['id']}" })
        videos_analisados.sort(key=lambda x: x['views'], reverse=True)
        return {"videos": videos_analisados, "top_assuntos": Counter(todos_tags).most_common(15)}, None
    except Exception as e: return None, str(e)

def buscar_top_videos(channel_id, api_key):
    data = datetime.datetime.now() - timedelta(days=45)
    params = { "key": api_key, "channelId": channel_id, "part": "snippet", "order": "viewCount", "publishedAfter": data.isoformat("T")+"Z", "type": "video", "maxResults": 5 }
    try:
        r = requests.get("https://www.googleapis.com/youtube/v3/search", params=params)
        return [{"titulo": i["snippet"]["title"], "data": i["snippet"]["publishedAt"][:10], "thumb": i["snippet"]["thumbnails"]["high"]["url"]} for i in r.json().get("items", [])]
    except: return []

def buscar_dados_youtube(nicho, api_key):
    if not api_key: return None, "Chave necessária"
    try:
        r = requests.get("https://www.googleapis.com/youtube/v3/search", params={"part":"snippet", "q":nicho, "type":"channel", "key":api_key, "maxResults":20})
        d = r.json()
        if "items" not in d: return [], None
        ids = ",".join([i["id"]["channelId"] for i in d["items"]])
        s_r = requests.get("https://www.googleapis.com/youtube/v3/channels", params={"part":"statistics", "id":ids, "key":api_key})
        s_map = {i["id"]: i["statistics"] for i in s_r.json().get("items", [])}
        res = []
        for i in d["items"]:
            cid = i["id"]["channelId"]
            s = s_map.get(cid, {})
            v, sub, vid = int(s.get("viewCount",0)), int(s.get("subscriberCount",0)), int(s.get("videoCount",0))
            media = v/vid if vid > 0 else 0
            gold = True if (0 < vid <= 60 and sub >= 1000 and media > 2000) else False
            res.append({"nome":i["snippet"]["title"], "inscritos":sub, "total_videos":vid, "media_views":media, "e_ouro":gold, "link":f"https://www.youtube.com/channel/{cid}", "id":cid})
        return res, None
    except Exception as e: return None, str(e)

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state['logado'] = False
def tela_login():
    c1,c2,c3=st.columns([1,1,1])
    with c2:
        st.markdown("<br><div style='background:rgba(255,255,255,0.9); padding:30px; border-radius:30px; text-align:center; border:2px solid #eaddff;'><h1 style='color:#5a4fcf;'>🫐</h1><h2 style='color:#3d3563;'>Blueberry Finder AI</h2><p>Login Admin</p></div><br>", unsafe_allow_html=True)
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
        modo = st.radio("Navegação:", ["🔍 Busca por Nicho", "🌍 Radar Global (Dark)"])
        st.divider()
        if st.button("Sair"): st.session_state['logado']=False; st.rerun()

    st.markdown("<h1 style='text-align: center; color: #5a4fcf;'>🫐 Blueberry Finder AI</h1>", unsafe_allow_html=True)

    # MODO 1: BUSCA
    if modo == "🔍 Busca por Nicho":
        st.markdown("<p style='text-align:center;'>Encontre canais específicos.</p>", unsafe_allow_html=True)
        with st.form("f1"):
            c1,c2=st.columns([3,1])
            k = api_key_env if api_key_env else c1.text_input("API Key", type="password")
            n = c1.text_input("Nicho", placeholder="Ex: Yoga...")
            c2.write(""); c2.write("")
            b = c2.form_submit_button("🔍 Buscar")
        if b and n:
            with st.spinner("Minerando..."):
                d, e = buscar_dados_youtube(n, k)
                if d:
                    df = pd.DataFrame(d)
                    ouro = df[df['e_ouro']==True]
                    st.divider()
                    if not ouro.empty:
                        st.success(f"Encontramos {len(ouro)} Canais Gold!")
                        cols = st.columns(3)
                        for i, r in ouro.reset_index().iterrows():
                            with cols[i%3]:
                                st.markdown(f"""
                                <div class='gold-card'>
                                    <span class='gold-badge'>GOLD</span>
                                    <h4>{r['nome']}</h4>
                                    <p>📹 {r['total_videos']} | 👥 {r['inscritos']}</p>
                                    <a href='{r['link']}' target='_blank' class='visit-btn'>Ver Canal ↗</a>
                                </div>""", unsafe_allow_html=True)
                                with st.expander("Ver Virais"):
                                    vs = buscar_top_videos(r['id'], k)
                                    if vs:
                                        p = "Crie titulos baseados nestes:\n"
                                        for v in vs:
                                            st.markdown(f"**{v['titulo']}**<br><small>{v['data']}</small><hr>", unsafe_allow_html=True)
                                            p+=f"- {v['titulo']}\n"
                                        st.code(p, language='text')
                    st.divider()
                    st.dataframe(df[['nome','inscritos','total_videos','media_views','link']], column_config={"link": st.column_config.LinkColumn("Link", display_text="Ver ↗")}, use_container_width=True)

    # MODO 2: RADAR
    elif modo == "🌍 Radar Global (Dark)":
        st.markdown("<p style='text-align:center;'>Espione os nichos mais lucrativos do mundo <b>AGORA</b> (Últimos 30 dias).</p>", unsafe_allow_html=True)
        paises = {
            "🇺🇸 Estados Unidos": "US",
            "🇬🇧 Reino Unido": "GB", # Tier 1
            "🇨🇦 Canadá": "CA",      # Tier 1
            "🇦🇺 Austrália": "AU",   # Tier 1
            "🇸🇪 Suécia": "SE", "🇳🇴 Noruega": "NO", "🇩🇰 Dinamarca": "DK", "🇫🇮 Finlândia": "FI", "🇮🇸 Islândia": "IS", # Escandinavia
            "🇩🇪 Alemanha": "DE", "🇫🇷 França": "FR", "🇪🇸 Espanha": "ES",
            "🇧🇷 Brasil": "BR", "🇵🇹 Portugal": "PT",
            "🇯🇵 Japão": "JP", "🇰🇷 Coreia do Sul": "KR", "🇷🇺 Rússia": "RU", "🇮🇳 Índia": "IN"
        }
        filtros_dict = get_nichos_dark()
        
        c1, c2, c3 = st.columns([1, 1, 1])
        pais = c1.selectbox("1. Escolha o País:", list(paises.keys()))
        categoria_nome = c2.selectbox("2. Escolha o Nicho Dark:", list(filtros_dict.keys()))
        c3.write(""); c3.write("")
        key_r = api_key_env if api_key_env else st.text_input("API Key", type="password")
        
        if c3.button("📡 Escanear Nicho", type="primary"):
            query = filtros_dict[categoria_nome]
            with st.spinner(f"Varrendo YouTube {paises[pais]} atrás de '{categoria_nome}'..."):
                res, erro = buscar_radar_dark(paises[pais], query, key_r)
                if res:
                    videos = res["videos"]
                    tags = res["top_assuntos"]
                    st.divider()
                    st.subheader(f"🔥 Tags em Alta: {categoria_nome}")
                    html_tags = "".join([f"<span class='trend-tag'>#{t[0].upper()} ({t[1]})</span>" for t in tags if len(t[0])>3])
                    st.markdown(f"<div style='background:white; padding:20px; border-radius:15px; border:1px solid #c4b5fd;'>{html_tags}</div>", unsafe_allow_html=True)
                    st.divider()
                    st.subheader(f"📹 Top 50 Vídeos Recentes ({len(videos)})")
                    c_v1, c_v2 = st.columns(2)
                    for i, v in enumerate(videos):
                        with (c_v1 if i%2==0 else c_v2):
                             st.markdown(f"""
                                <div class="video-card">
                                    <img src="{v['thumb']}" style="width:120px; height:90px; object-fit:cover; border-radius:10px;">
                                    <div>
                                        <h5 style="margin:0; font-size:14px; color:#3d3563;">{v['titulo'][:60]}...</h5>
                                        <p style="font-size:11px; margin:5px 0; color:#6b6399;">📺 {v['canal']}</p>
                                        <p style="font-size:12px; font-weight:bold; color:#d946ef;">👁️ {v['views']:,} views</p>
                                        <a href="{v['link']}" target="_blank" style="font-size:11px; color:#8b5cf6; font-weight:700;">Assistir ↗</a>
                                    </div>
                                </div>""", unsafe_allow_html=True)
                elif erro: st.error(erro)

if st.session_state['logado']: app_principal()
else: tela_login()
