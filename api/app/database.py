"""Conexão com o banco de dados.

Qual banco usar vem da variável de ambiente DATABASE_URL (configuração FORA do código):
  - sem a variável  -> SQLite (um arquivo local, bom para desenvolver e testar)
  - no Compose/K8s  -> PostgreSQL (ex.: postgresql+psycopg://usuario:senha@db:5432/pets)
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pets.db")

# check_same_thread só existe no SQLite; para os outros bancos não passamos nada
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# "engine" = a conexão com o banco. pool_pre_ping testa a conexão antes de usar
# (se o banco reiniciou, a API se reconecta sozinha em vez de dar erro)
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

# Fábrica de "sessões": cada requisição abre uma sessão, conversa com o banco e fecha
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """Classe-mãe de todas as tabelas."""


def get_db():
    """Abre uma sessão para a requisição e garante que ela será fechada no final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
