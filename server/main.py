from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importa a conexão do banco para garantir que as tabelas sejam reconhecidas
from database import engine
import models

# --- GARANTIA DE PERSISTÊNCIA (Crucial para a Sprint 4) ---
# Esta linha lê todos os modelos do seu 'models.py' (Usuario, SessaoLogin, Postagem, Comentario, Curtida)
# e cria as tabelas automaticamente no seu MySQL local caso elas ainda não existam.
models.Base.metadata.create_all(bind=engine)


# Aponta para o arquivo real 'authRoutes.py' que está na raiz do seu projeto
from routes.authRoutes import router as auth_router

# Cria a aplicação FastAPI com metadados do teu projeto ecológico
app = FastAPI(
    title="Ser Sustentável API 🌿",
    description="API para a rede social ecológica Ser Sustentável, gerenciando usuários, publicações e interações.",
    version="1.0.0"
)

# --- CONFIGURAÇÃO DE CORS (Atualizado para a Sprint 4) ---
# Permite que Front-end (que estará rodando via Live Server ou localmente)
# consiga fazer requisições para este Back-end sem ser bloqueado por segurança pelo navegador.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, substitui pelo link oficial do teu site
    allow_credentials=True,
    allow_methods=["*"],  # Permite GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # Libera cabeçalhos de autenticação (como os tokens JWT)
)

# --- INCLUSÃO DAS ROTAS ---
# Vincula as rotas de autenticação e interações do feed ao servidor principal
app.include_router(auth_router)

# Rota inicial padrão apenas para testar se o servidor está online
@app.get("/", tags=["Raiz"])
def verificar_servidor():
    return {
        "status": "online",
        "mensagem": "Servidor da rede social Ser Sustentável está rodando perfeitamente e integrado!"
    }
