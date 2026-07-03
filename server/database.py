import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Se estiver no Railway, ele usa a URL segura da nuvem.
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+pymysql://root@localhost/ser_sustentavel"
)

# 2. Adaptação para o SQLAlchemy funcionar perfeitamente em produção
if SQLALCHEMY_DATABASE_URL.startswith("mysql://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

# 3. Cria o motor de conexão
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 4. Configura as sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 5. Classe base para as tabelas
Base = declarative_base()

# 6. Função utilitária para abrir e fechar conexões
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()