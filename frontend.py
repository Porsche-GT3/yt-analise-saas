import streamlit as st
import pandas as pd
import requests
import os
import datetime
import smtplib
import bcrypt
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import timedelta
from dotenv import load_dotenv

# Carrega variáveis
load_dotenv()

# Banco de Dados
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Blueberry Finder AI", page_icon="🫐", layout="wide")

# --- BANCO DE DADOS & MODELS ---
DATABASE_URL = "sqlite:///./saas.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    senha_hash = Column(String)
    nome = Column(String)
    reset_token = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)

# --- FUNÇÕES AUXILIARES (HASH, EMAIL, YOUTUBE) ---
def criar_hash(senha):
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verificar_senha(senha, hash_armazenado):
    return bcrypt.checkpw(senha.encode('utf-8'), hash_armazenado.encode('utf-8'))

def enviar_email_recuperacao(email_destino, codigo):
    smtp_user = os.getenv("SMTP_EMAIL")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    
    if not smtp_user or not smtp_pass:
        return False, "Configure SMTP_EMAIL e SMTP_PASSWORD nas Secrets."

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = email_destino
    msg['Subject'] = "🫐 Seu Código - Blueberry AI"

    body = f"""
    <html>
      <body>
        <h2 style="color: #5a4fcf;">Recuperação de Senha</h2>
        <p>Seu código blueberry de acesso é:</p>
        <h1 style="background-color: #eaddff; padding: 10px; border-radius: 10px; color: #3d3563;">{codigo}</h1>
      </body>
    </html>
    """
    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True, "Enviado!"
    except Exception as e:
        return False, str(e)

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
            videos.append({ "titulo": item["snippet"]["title"], "data": item["snippet"]["publishedAt"][:10], "thumb": item["snippet"]["thumbnails"]["high"]["url"] })
        return videos
    except: return []

def buscar_dados_youtube(nicho, api_key):
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

# --- CSS BLUEBERRY ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f3e7e9 0%, #e3eeff 100%, #e8dbfc 100%); background-attachment: fixed; }
    header[data-testid="stHeader"] { background: transparent; }
    h1, h2, h3 { font-family: 'Inter', sans-serif; color: #3d3563 !important; font-weight: 700; }
    p, label, span, div, caption { color: #544a85 !important; }
    .stTextInput input { background-color: rgba(255, 255, 255, 0.9) !important; border: 2px solid #ddd6fe !important; color: #3d3563 !important; border-radius: 18px !important; padding: 15px !important; }
    div[data-testid="stFormSubmitButton"] button { background: linear-gradient(135deg, #8b5cf6 0%, #d946ef 100%); color: #ffffff !important; font-weight: 700 !important; border: none; padding: 14px 28px; border-radius: 50px; width: 100%; }
    .gold-card { background: rgba(255, 255, 255, 0.80); backdrop-filter: blur(15px); border: 2px solid #c4b5fd; border-radius: 25px; padding: 25px; margin-bottom: 25px; }
    .gold-badge { background: linear-gradient(90deg, #a78bfa 0%, #f472b6 100%); color: white !important; padding: 6px 15px; border-radius: 20px; font-size: 11px; font-weight: 800; float: right;}
    .viral-box { background-color: rgba(255,255,255,0.8); border-left: 4px solid #8b5cf6; padding: 12px; margin-bottom: 12px; border-radius: 0 15px 15px 0; }
    </style>
""", unsafe_allow_html=True)

# --- TELA LOGIN ---
if 'logado' not in st.session_state: st.session_state['logado'] = False
if 'usuario_nome' not in st.session_state: st.session_state['usuario_nome'] = ""

def tela_auth():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><div style='background:rgba(255,255,255,0.9); padding:30px; border-radius:30px; text-align:center; border: 2px solid #eaddff;'><h1 style='font-size: 3em; margin:0;'>🫐</h1><h2 style='color:#3d3563; margin:0;'>Blueberry Channel</h2></div>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["Entrar", "Criar Conta", "Recuperar"])
        
        with tab1: # LOGIN
            with st.form("login"):
                email = st.text_input("E-mail")
                senha = st.text_input("Senha", type="password")
                if st.form_submit_button("🚀 Entrar"):
                    db = SessionLocal()
                    user = db.query(Usuario).filter(Usuario.email == email).first()
                    db.close()
                    if (email == "admin" and senha == "1234") or (user and verificar_senha(senha, user.senha_hash)):
                        st.session_state['logado'] = True
                        st.session_state['usuario_nome'] = user.nome if user else "Admin"
                        st.rerun()
                    else: st.error("Dados incorretos.")
        
        with tab2: # CADASTRO
            with st.form("cadastro"):
                nome = st.text_input("Nome")
                email = st.text_input("E-mail")
                senha = st.text_input("Senha", type="password")
                if st.form_submit_button("✨ Cadastrar"):
                    db = SessionLocal()
                    if db.query(Usuario).filter(Usuario.email == email).first(): st.error("Email já existe.")
                    else:
                        db.add(Usuario(email=email, senha_hash=criar_hash(senha), nome=nome))
                        db.commit()
                        st.success("Criado! Faça login.")
                    db.close()

        with tab3: # RECUPERAR
            email_rec = st.text_input("E-mail da conta")
            if st.button("Enviar Código"):
                db = SessionLocal()
                user = db.query(Usuario).filter(Usuario.email == email_rec).first()
                if user:
                    code = ''.join(random.choices(string.digits, k=6))
                    user.reset_token = code
                    db.commit()
                    ok, msg = enviar_email_recuperacao(email_rec, code)
                    if ok: st.success("Código enviado!")
                    else: st.error(msg)
                else: st.error("Email não achado.")
                db.close()
            
            with st.form("reset"):
                code = st.text_input("Código")
                new_pass = st.text_input("Nova Senha", type="password")
                if st.form_submit_button("Mudar Senha"):
                    db = SessionLocal()
                    user = db.query(Usuario).filter(Usuario.email == email_rec).first()
                    if user and user.reset_token == code:
                        user.senha_hash = criar_hash(new_pass)
                        user.reset_token = None
                        db.commit()
                        st.success("Senha alterada!")
                    else: st.error("Erro.")
                    db.close()

# --- APP PRINCIPAL ---
def app_principal():
    api_key_env = os.getenv("YOUTUBE_API_KEY")
    with st.sidebar:
        st.markdown(f"### Olá, {st.session_state['usuario_nome']} 🫐")
        if st.button("Sair"):
            st.session_state['logado'] = False
            st.rerun()

    st.markdown("<h1 style='text-align: center; color: #5a4fcf; font-size: 3em;'>🫐 Blueberry Finder AI</h1>", unsafe_allow_html=True)
    
    with st.form("search"):
        c1, c2 = st.columns([3, 1])
        key = api_key_env if api_key_env else c1.text_input("API Key", type="password")
        nicho = c1.text_input("Nicho", placeholder="Ex: ASMR...")
        c2.write(""); c2.write("")
        submit = c2.form_submit_button("🔍 Buscar")

    if submit and nicho:
        dados, erro = buscar_dados_youtube(nicho, key)
        if erro: st.error(erro)
        elif dados:
            df = pd.DataFrame(dados)
            df_ouro = df[df['e_ouro'] == True]
            
            # --- ÁREA DE DOWNLOAD E RESULTADOS ---
            st.divider()
            csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig')
            st.download_button("📥 Baixar Relatório (Excel)", csv, "relatorio_blueberry.csv", "text/csv")
            
            # 1. CANAIS GOLD (CARDS)
            if not df_ouro.empty:
                st.success(f"🦄 Encontramos {len(df_ouro)} canais Blueberry Gold!")
                cols = st.columns(3)
                for i, row in df_ouro.reset_index().iterrows():
                    with cols[i % 3]:
                        with st.container():
                            st.markdown(f"""
                            <div class='gold-card'>
                                <span class='gold-badge'>GOLD</span>
                                <h4>{row['nome']}</h4>
                                <p>📹 {row['total_videos']} | 👥 {row['inscritos']}</p>
                            </div>""", unsafe_allow_html=True)
                            
                            with st.expander("🕵️ Ver Virais (45 dias)"):
                                vids = buscar_top_videos(row['id'], key)
                                if vids:
                                    prompt = "Analise estes títulos e crie 5 variações:\n"
                                    for v in vids:
                                        st.markdown(f"<div class='viral-box'><p><b>{v['titulo']}</b><br><small>{v['data']}</small></p></div>", unsafe_allow_html=True)
                                        prompt += f"- {v['titulo']}\n"
                                    st.code(prompt, language='text')
                                else: st.warning("Sem virais recentes.")
                            st.markdown(f"<a href='{row['link']}' target='_blank'>Ver Canal ↗</a>", unsafe_allow_html=True)
            else:
                st.info("Nenhum canal Gold encontrado, mas veja a lista completa abaixo!")

            # 2. TABELA GERAL (VOLTOU!)
            st.divider()
            st.subheader("📊 Análise Geral do Mercado (Top 20)")
            st.dataframe(
                df[['nome', 'inscritos', 'total_videos', 'media_views']],
                column_config={
                    "nome": "Nome do Canal",
                    "inscritos": st.column_config.NumberColumn("Inscritos", format="%d"),
                    "total_videos": st.column_config.NumberColumn("Vídeos"),
                    "media_views": st.column_config.NumberColumn("Média Views", format="%d"),
                },
                use_container_width=True,
                hide_index=True
            )

if st.session_state['logado']:
    app_principal()
else:
    tela_auth()
