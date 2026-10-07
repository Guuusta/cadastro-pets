"""Conexão com o banco de dados.

Qual banco usar vem de variáveis de ambiente (configuração FORA do código):
  - DB_HOST definido -> PostgreSQL, montado a partir de DB_HOST, DB_PORT, DB_NAME, DB_USER e DB_PASSWORD
  - DATABASE_URL     -> usa o endereço pronto (ex.: nos testes)
  - nenhum dos dois  -> SQLite (um arquivo local, bom para desenvolver)
"""
import os

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


def montar_url_do_banco() -> str | URL:
    """Decide qual banco usar.

    Por que receber usuário/senha SEPARADOS em vez de um endereço pronto?
    Porque a senha pode ter caracteres especiais (@ : / #) que "quebram" o endereço
    postgresql://usuario:senha@host. O URL.create trata esses caracteres sozinho.
    """
    if os.getenv("DB_HOST"):
        return URL.create(
            "postgresql+psycopg",
            username=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            host=os.environ["DB_HOST"],
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.environ["DB_NAME"],
        )
    return os.getenv("DATABASE_URL", "sqlite:///./pets.db")


DATABASE_URL = montar_url_do_banco()

# check_same_thread só existe no SQLite; para os outros bancos não passamos nada
connect_args = {"check_same_thread": False} if str(DATABASE_URL).startswith("sqlite") else {}

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
