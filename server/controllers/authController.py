import os
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
import models
import schemas

# Lendo a chave de forma segura. Se não configurada no Railway, usa o padrão.
SECRET_KEY = os.getenv("SECRET_KEY", "chave_secreta_super_segura_do_ser_sustentavel")
ALGORITHM = "HS256"
TOKEN_EXPIRATION_HOURS = 24

password_hash = PasswordHash((BcryptHasher(),))

class AuthController:

    @staticmethod
    def hash_senha(senha: str) -> str:
        """Transforma a senha em texto limpo em um hash seguro usando Bcrypt."""
        return password_hash.hash(senha)

    @staticmethod
    def verificar_senha(senha_limpa: str, senha_hash: str) -> bool:
        """Verifica se a senha digitada no login bate com o hash salvo no banco."""
        return password_hash.verify(senha_limpa, senha_hash)

    @staticmethod
    def cadastrar_usuario(dados: schemas.UsuarioCadastro, db: Session):
        """Verifica se o e-mail já existe e salva o novo usuário no MySQL com senha criptografada."""
        usuario_existente = db.query(models.Usuario).filter(models.Usuario.email == dados.email).first()
        if usuario_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este e-mail já está cadastrado no Ser Sustentável."
            )
        
        senha_criptografada = AuthController.hash_senha(dados.senha)
        
        novo_usuario = models.Usuario(
            nome=dados.nome,
            email=dados.email,
            data_nascimento=dados.data_nascimento,
            senha_hash=senha_criptografada
        )
        
        try:
            db.add(novo_usuario)
            db.commit()
            db.refresh(novo_usuario)
            return novo_usuario
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro interno ao salvar no banco de dados: {str(e)}"
            )

    @staticmethod
    def login_usuario(dados: schemas.UsuarioLogin, db: Session):
        """Valida as credenciais e gera um Token JWT criptografado real e legítimo."""
        usuario = db.query(models.Usuario).filter(models.Usuario.email == dados.email).first()
        
        if not usuario or not AuthController.verificar_senha(dados.senha, usuario.senha_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha incorretos."
            )
        
        # CORREÇÃO: datetime.now(timezone.utc) substitui o descontinuado utcnow()
        payload = {
            "sub": usuario.email,
            "id_usuario": usuario.id_usuario,
            "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRATION_HOURS)
        }
        token_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        try:
            nova_sessao = models.SessaoLogin(
                id_usuario=usuario.id_usuario,
                token_sessao=token_jwt
            )
            db.add(nova_sessao)
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao registrar a sessão de login no banco de dados."
            )

        return {
            "mensagem": "Login bem-sucedido!",
            "token_sessao": token_jwt,
            "usuario": {
                "id_usuario": usuario.id_usuario,
                "nome": usuario.nome,
                "email": usuario.email,
                "data_criacao": usuario.data_criacao.isoformat() if usuario.data_criacao else None,
                "sobre_mim": usuario.sobre_mim,
                "avatar": usuario.avatar
            }
        }