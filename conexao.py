from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Caminho da pasta principal do projeto
PASTA_PROJETO = Path(__file__).resolve().parent.parent

# Caminho do banco de dados SQLite
CAMINHO_BANCO = PASTA_PROJETO / "ti.db"

DATABASE_URL = f"sqlite:///{CAMINHO_BANCO.as_posix()}"

# Conexão com o banco
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

# Base dos modelos
Base = declarative_base()

# Sessões do banco de dados
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)
