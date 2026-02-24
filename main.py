from fastapi import FastAPI
from sqlalchemy import create_engine, text
import os

app = FastAPI()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://analisepro:analise123@banco:5432/analisepro"
)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

@app.get("/")
def root():
    return {"status": "API OK"}

@app.get("/db")
def db():
    with engine.connect() as conn:
        now = conn.execute(text("SELECT NOW()")).scalar()
    return {"status": "Banco conectado", "hora": str(now)}
