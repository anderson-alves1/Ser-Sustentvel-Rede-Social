import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine
import models
from routes.authRoutes import router as auth_router

os.makedirs("uploads", exist_ok=True)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Ser Sustentável API 🌿",
    description="API para a rede social ecológica Ser Sustentável, gerenciando usuários, publicações e interações.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth_router)

@app.get("/", tags=["Raiz"])
def verificar_servidor():
    return {
        "status": "online",
        "mensagem": "Servidor da rede social Ser Sustentável está rodando perfeitamente e integrado!"
    }