import os
import requests
import datetime
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

# --- BANCO DE DADOS ---
DATABASE_URL = "sqlite:///./saas.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Historico(Base):
    __tablename__ = "historico_pesquisas"
    id = Column(Integer, primary_key=True, index=True)
    nicho = Column(String, index=True)
    data_pesquisa = Column(DateTime, default=datetime.datetime.now)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- APP ---
app = FastAPI(title="YouTube Niche Analyzer", version="0.8.0")

class Canal(BaseModel):
    id_canal: str
    nome: str
    descricao: Optional[str] = ""
    inscritos: int
    total_views: int
    total_videos: int
    media_views_por_video: float
    taxa_engajamento: float  # <--- NOVO CAMPO DE INTELIGÊNCIA
    link: str

class ItemHistorico(BaseModel):
    nicho: str
    data_pesquisa: datetime.datetime

# --- ROTAS ---
@app.get("/")
def home():
    return {"status": "online"}

@app.get("/historico", response_model=List[ItemHistorico])
def ver_historico(db: Session = Depends(get_db)):
    return db.query(Historico).order_by(Historico.data_pesquisa.desc()).all()

@app.get("/analise/{nicho}", response_model=List[Canal])
def analisar_nicho(nicho: str, db: Session = Depends(get_db)):
    # Salva no histórico
    nova_pesquisa = Historico(nicho=nicho)
    db.add(nova_pesquisa)
    db.commit()
    
    # 1. Busca
    url_search = "https://www.googleapis.com/youtube/v3/search"
    params_search = {
        "part": "snippet", "q": nicho, "type": "channel", "key": API_KEY, "maxResults": 10
    }
    resp_search = requests.get(url_search, params=params_search)
    dados_search = resp_search.json()

    if "items" not in dados_search:
        return []

    lista_ids = [item["id"]["channelId"] for item in dados_search["items"]]
    ids_concatenados = ",".join(lista_ids)

    # 2. Estatísticas
    url_stats = "https://www.googleapis.com/youtube/v3/channels"
    params_stats = {"part": "statistics", "id": ids_concatenados, "key": API_KEY}
    resp_stats = requests.get(url_stats, params=params_stats)
    dados_stats = resp_stats.json()

    mapa_stats = {}
    if "items" in dados_stats:
        for item in dados_stats["items"]:
            mapa_stats[item["id"]] = item["statistics"]

    resultado_final = []
    for item in dados_search["items"]:
        id_atual = item["id"]["channelId"]
        snippet = item["snippet"]
        stats = mapa_stats.get(id_atual, {})
        
        inscritos = int(stats.get("subscriberCount", 0))
        views = int(stats.get("viewCount", 0))
        videos = int(stats.get("videoCount", 0))

        # Cálculos de Métricas
        if videos > 0:
            media = views / videos
        else:
            media = 0.0

        # CÁLCULO DO SCORE (Engajamento)
        # Quantas views o canal tem para cada 1 inscrito?
        # Ex: 1.0 = Cada inscrito assiste 1 video. 
        # Ex: 5.0 = O canal fura a bolha (MUITO BOM).
        if inscritos > 0:
            engajamento = (media / inscritos) * 100 
        else:
            engajamento = 0.0

        novo_canal = Canal(
            id_canal=id_atual,
            nome=snippet["title"],
            descricao=snippet["description"],
            inscritos=inscritos,
            total_views=views,
            total_videos=videos,
            media_views_por_video=round(media, 2),
            taxa_engajamento=round(engajamento, 2), # <--- Dado calculado
            link=f"https://www.youtube.com/channel/{id_atual}"
        )
        resultado_final.append(novo_canal)

    # Ordena pelo Score de Engajamento (As melhores oportunidades primeiro)
    resultado_final.sort(key=lambda x: x.taxa_engajamento, reverse=True)
    return resultado_final