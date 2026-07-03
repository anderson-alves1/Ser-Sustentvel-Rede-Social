import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Busca a variável de ambiente do Railway
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# 2. Se a variável existir, garante que ela use o driver correto (mysql+pymysql)
if SQLALCHEMY_DATABASE_URL:
    if SQLALCHEMY_DATABASE_URL.startswith("mysql://"):
        # Transforma mysql:// em mysql+pymysql:// para o SQLAlchemy aceitar na nuvem
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)
else:
    # 3. Caso rode localmente na sua máquina (sem a variável), usa o banco local
    # IMPORTANTE: Se o seu MySQL local tiver senha, mude de 'root' para 'root:suasenha'
    SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root@localhost/ser_sustentavel"

# 4. Cria o motor de conexão com a URL já corrigida
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 5. Configura as sessões do banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 6. Classe base para a criação dos modelos/tabelas
Base = declarative_base()

# 7. Função utilitária (Dependency Injection) para abrir e fechar a sessão das rotas
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()