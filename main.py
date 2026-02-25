from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

aplicativo.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://72.61.57.15:3000",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ⚠️ Ajuste se necessário (senha/host/porta)
DATABASE_URL = "postgresql://analisarpro:analisar123@banco:5432/analisarpro"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# =========================
# MODELS
# =========================
class TradeIn(BaseModel):
    ativo: str
    resultado: str  # "win" ou "loss" (ou "vitoria"/"derrota")
    valor: float

class SettingsIn(BaseModel):
    meta_dia: float
    stop_loss_dia: float

# =========================
# BOOTSTRAP TABLES
# =========================
def init_db():
    with engine.begin() as conn:
        # tabela trades
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY,
                ativo TEXT NOT NULL,
                resultado TEXT NOT NULL,
                valor NUMERIC(12,2) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
        """))

        # tabela trader_settings
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS trader_settings (
                id SERIAL PRIMARY KEY,
                meta_dia NUMERIC(12,2) NOT NULL DEFAULT 0,
                stop_loss_dia NUMERIC(12,2) NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
        """))

        # garante 1 linha de config
        conn.execute(text("""
            INSERT INTO trader_settings (meta_dia, stop_loss_dia)
            SELECT 100, 50
            WHERE NOT EXISTS (SELECT 1 FROM trader_settings);
        """))

init_db()

# =========================
# HELPERS
# =========================
def get_settings_row():
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT meta_dia, stop_loss_dia
            FROM trader_settings
            ORDER BY id DESC
            LIMIT 1
        """)).mappings().first()

    if not row:
        return {"meta_dia": 0.0, "stop_loss_dia": 0.0}
    return {"meta_dia": float(row["meta_dia"]), "stop_loss_dia": float(row["stop_loss_dia"])}

def calcular_dashboard():
    settings = get_settings_row()
    meta = settings["meta_dia"]
    stop = settings["stop_loss_dia"]

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT resultado, valor
            FROM trades
            WHERE DATE(created_at) = CURRENT_DATE
        """)).all()

    lucro = 0.0
    vitorias = 0
    perdas = 0

    for resultado, valor in rows:
        r = (resultado or "").strip().lower()
        v = float(valor)

        # aceita win/loss ou vitoria/derrota
        if r in ("win", "vitoria", "vitória", "gain", "g"):
            lucro += v
            vitorias += 1
        else:
            lucro -= v
            perdas += 1

    meta_batida = lucro >= meta if meta > 0 else False
    stop_batido = lucro <= -stop if stop > 0 else False

    return {
        "lucro_dia": lucro,
        "vitorias": vitorias,
        "perdas": perdas,
        "meta": meta,
        "stop_loss": stop,
        "meta_batida": meta_batida,
        "stop_batido": stop_batido
    }

# =========================
# ROUTES
# =========================
@app.get("/")
def root():
    return {"status": "API OK"}

@app.get("/db")
def db():
    try:
        with engine.connect() as conn:
            now = conn.execute(text("SELECT NOW()")).scalar()
        return {"status": "Banco conectado", "hora": str(now)}
    except SQLAlchemyError as e:
        return {"status": "Erro", "detalhe": str(e)}

@app.get("/trades")
def listar_trades():
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT id, ativo, resultado, valor, created_at
                FROM trades
                ORDER BY id DESC
                LIMIT 200
            """)).mappings().all()

        return {"total": len(rows), "items": [dict(r) for r in rows]}
    except SQLAlchemyError as e:
        return {"ok": False, "erro": str(e)}

@app.post("/trades")
def criar_trade(trade: TradeIn):
    # ✅ trava por meta/stop ANTES de inserir
    d = calcular_dashboard()

    if d["meta_batida"]:
        raise HTTPException(status_code=403, detail="META BATIDA: pare de operar hoje.")
    if d["stop_batido"]:
        raise HTTPException(status_code=403, detail="STOP LOSS BATIDO: pare de operar hoje.")

    try:
        sql = text("""
            INSERT INTO trades (ativo, resultado, valor)
            VALUES (:ativo, :resultado, :valor)
            RETURNING id, ativo, resultado, valor, created_at
        """)

        with engine.begin() as conn:
            row = conn.execute(sql, {
                "ativo": trade.ativo,
                "resultado": trade.resultado.strip().lower(),
                "valor": trade.valor
            }).mappings().first()

        return {"ok": True, "trade": dict(row)}
    except SQLAlchemyError as e:
        return {"ok": False, "erro": str(e)}

@app.get("/settings")
def get_settings():
    return get_settings_row()

@app.put("/settings")
def update_settings(payload: SettingsIn):
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE trader_settings
                SET meta_dia = :meta_dia,
                    stop_loss_dia = :stop_loss_dia
                WHERE id = (
                    SELECT id FROM trader_settings ORDER BY id DESC LIMIT 1
                )
            """), {"meta_dia": payload.meta_dia, "stop_loss_dia": payload.stop_loss_dia})

        return {"ok": True}
    except SQLAlchemyError as e:
        return {"ok": False, "erro": str(e)}

@app.get("/dashboard")
def dashboard():
    return calcular_dashboard()
    
