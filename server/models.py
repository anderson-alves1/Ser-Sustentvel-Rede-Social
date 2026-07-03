from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# 1. MODELO DE USUÁRIO
class Usuario(Base):
    __tablename__ = "USUARIO"

    id_usuario = Column(Integer, primary_key=True, autoincrement=True, name="ID_USUARIO")
    nome = Column(String(100), name="NOME")
    email = Column(String(100), unique=True, name="EMAIL")
    data_nascimento = Column(DateTime, name="DATA_NASCIMENTO")
    senha_hash = Column(String(255), name="SENHA_HASH")
    sobre_mim = Column(Text, name="SOBRE_MIM")
    avatar = Column(String(255), name="AVATAR")
    data_criacao = Column(DateTime, default=datetime.utcnow, name="DATA_CRIACAO")

    # Relacionamentos (Se o usuário for deletado, limpa em cascata suas interações)
    sessoes = relationship("SessaoLogin", back_populates="usuario", cascade="all, delete")
    postagens = relationship("Postagem", back_populates="autor", cascade="all, delete")
    comentarios = relationship("Comentario", back_populates="autor", cascade="all, delete")
    curtidas = relationship("Curtida", back_populates="autor", cascade="all, delete")


# 2. MODELO DE SESSÃO DE LOGIN
class SessaoLogin(Base):
    __tablename__ = "SESSAO_LOGIN"

    id_sessao = Column(Integer, primary_key=True, autoincrement=True, name="ID_SESSAO")
    id_usuario = Column(Integer, ForeignKey("USUARIO.ID_USUARIO", ondelete="CASCADE"), name="ID_USUARIO")
    # Alterado para Text para suportar os tokens JWT da Sprint 4 sem estourar o limite de caracteres
    token_sessao = Column(Text, name="TOKEN_SESSAO")
    data_hora_login = Column(DateTime, default=datetime.utcnow, name="DATA_HORA_LOGIN")

    # Relacionamento de volta para o usuário
    usuario = relationship("Usuario", back_populates="sessoes")


# 3. MODELO DE POSTAGEM (Novo para a Sprint 4)
class Postagem(Base):
    __tablename__ = "POSTAGEM"

    id_postagem = Column(Integer, primary_key=True, autoincrement=True, name="ID_POSTAGEM")
    # Mudado de TITULO para LEGENDA com formato Text para permitir "textões" sobre as ações ecológicas
    legenda = Column(Text, name="LEGENDA")
    caminho_foto = Column(String(255), name="CAMINHO_FOTO")
    data_criacao = Column(DateTime, default=datetime.utcnow, name="DATA_CRIACAO")
    id_usuario = Column(Integer, ForeignKey("USUARIO.ID_USUARIO", ondelete="CASCADE"), name="ID_USUARIO")

    # Relacionamentos amarrados
    autor = relationship("Usuario", back_populates="postagens")
    comentarios = relationship("Comentario", back_populates="postagem", cascade="all, delete")
    curtidas = relationship("Curtida", back_populates="postagem", cascade="all, delete")


# 4. MODELO DE COMENTÁRIO (Novo para a Sprint 4)
class Comentario(Base):
    __tablename__ = "COMENTARIO"

    id_comentario = Column(Integer, primary_key=True, autoincrement=True, name="ID_COMENTARIO")
    texto = Column(Text, name="TEXTO")
    data_criacao = Column(DateTime, default=datetime.utcnow, name="DATA_CRIACAO")
    id_usuario = Column(Integer, ForeignKey("USUARIO.ID_USUARIO", ondelete="CASCADE"), name="ID_USUARIO")
    id_postagem = Column(Integer, ForeignKey("POSTAGEM.ID_POSTAGEM", ondelete="CASCADE"), name="ID_POSTAGEM")

    # Relacionamentos de volta
    autor = relationship("Usuario", back_populates="comentarios")
    postagem = relationship("Postagem", back_populates="comentarios")


# 5. MODELO DE CURTIDA (Novo para a Sprint 4)
class Curtida(Base):
    __tablename__ = "CURTIDA"

    id_curtida = Column(Integer, primary_key=True, autoincrement=True, name="ID_CURTIDA")
    id_usuario = Column(Integer, ForeignKey("USUARIO.ID_USUARIO", ondelete="CASCADE"), name="ID_USUARIO")
    id_postagem = Column(Integer, ForeignKey("POSTAGEM.ID_POSTAGEM", ondelete="CASCADE"), name="ID_POSTAGEM")
    data_curtida = Column(DateTime, default=datetime.utcnow, name="DATA_CURTIDA")

    # Relacionamentos de volta
    autor = relationship("Usuario", back_populates="curtidas")
    postagem = relationship("Postagem", back_populates="curtidas")
