from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configuração da linha de conexão com o seu MySQL local
# IMPORTANTE: Altere 'root' e 'suasenha' para o seu usuário e senha reais do MySQL
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:gggg@localhost/ser_sustentavel"

# 1. Cria o motor que conecta o Python ao servidor MySQL
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 2. Cria a fábrica de sessões (será usada para abrir e fechar consultas ao banco)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Cria a classe base que o arquivo 'models.py' vai usar para mapear as tabelas
Base = declarative_base()

# 4. Função utilitária (Dependency Injection) para abrir e fechar o banco a cada requisição
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()