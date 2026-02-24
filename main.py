from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

app = FastAPI()

DATABASE_URL = "postgresql://analisepro:analise123@banco:5432/analisepro"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# 1) Cria tabela automaticamente quando a API subir
def criar_tabela():
    sql = """
    CREATE TABLE IF NOT EXISTS trades (
        id SERIAL PRIMARY KEY,
        ativo TEXT NOT NULL,
        resultado TEXT NOT NULL,
        valor NUMERIC(12,2) NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """
    with engine.begin() as conn:
        conn.execute(text(sql))

criar_tabela()

class TradeIn(BaseModel):
    ativo: str
    resultado: str  # "win" ou "loss"
    valor: float

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

@app.post("/trades")
def criar_trade(trade: TradeIn):
    try:
        sql = text("""
            INSERT INTO trades (ativo, resultado, valor)
            VALUES (:ativo, :resultado, :valor)
            RETURNING id, ativo, resultado, valor, created_at
        """)
        with engine.begin() as conn:
            row = conn.execute(sql, {
                "ativo": trade.ativo,
                "resultado": trade.resultado.lower(),
                "valor": trade.valor
            }).mappings().first()

        return {"ok": True, "trade": dict(row)}
    except SQLAlchemyError as e:
        return {"ok": False, "erro": str(e)}

@app.get("/trades")
def listar_trades():
    try:
        sql = text("""
            SELECT id, ativo, resultado, valor, created_at
            FROM trades
            ORDER BY id DESC
            LIMIT 200
        """)
        with engine.connect() as conn:
            rows = conn.execute(sql).mappings().all()

        return {"total": len(rows), "items": [dict(r) for r in rows]}
    except SQLAlchemyError as e:
        return {"ok": False, "erro": str(e)}
        # =============================
# SETTINGS (META E STOP)
# =============================

@app.get("/settings")
def get_settings():

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT meta_dia, stop_loss_dia
        FROM trader_settings
        ORDER BY id DESC
        LIMIT 1
    """)

    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return {"meta_dia":0,"stop_loss_dia":0}

    return {
        "meta_dia": float(row[0]),
        "stop_loss_dia": float(row[1])
    }



@app.put("/settings")
def update_settings(meta_dia: float, stop_loss_dia: float):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE trader_settings
        SET meta_dia=%s,
            stop_loss_dia=%s
        WHERE id = (
            SELECT id
            FROM trader_settings
            ORDER BY id DESC
            LIMIT 1
        )
    """,(meta_dia,stop_loss_dia))

    conn.commit()

    cur.close()
    conn.close()

    return {"ok":True}
