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
    pontos = Column(Integer, default=0, name="PONTOS")

    # Relacionamentos (Se o usuário for deletado, limpa em cascata suas interações)
    sessoes = relationship("SessaoLogin", back_populates="usuario", cascade="all, delete")
    postagens = relationship("Postagem", back_populates="autor", cascade="all, delete")
    comentarios = relationship("Comentario", back_populates="autor", cascade="all, delete")
    curtidas = relationship("Curtida", back_populates="autor", cascade="all, delete")
    topicos_forum = relationship("TopicoForum", back_populates="autor", cascade="all, delete")
    comentarios_forum = relationship("ComentarioForum", back_populates="autor", cascade="all, delete")
    curtidas_comentario = relationship("CurtidaComentario", back_populates="autor", cascade="all, delete")
    curtidas_comentario_forum = relationship("CurtidaComentarioForum", back_populates="autor", cascade="all, delete")


# 2. MODELO DE SESSÃO DE LOGIN
class SessaoLogin(Base):
    __tablename__ = "SESSAO_LOGIN"

    id_sessao = Column(Integer, primary_key=True, autoincrement=True, name="ID_SESSAO")
    id_usuario = Column(Integer, ForeignKey("USUARIO.ID_USUARIO", ondelete="CASCADE"), name="ID_USUARIO")
    token_sessao = Column(Text, name="TOKEN_SESSAO")
    data_hora_login = Column(DateTime, default=datetime.utcnow, name="DATA_HORA_LOGIN")

    usuario = relationship("Usuario", back_populates="sessoes")


# 3. MODELO DE POSTAGEM
class Postagem(Base):
    __tablename__ = "POSTAGEM"

    id_postagem = Column(Integer, primary_key=True, autoincrement=True, name="ID_POSTAGEM")
    legenda = Column(Text, name="LEGENDA")
    caminho_foto = Column(String(255), name="CAMINHO_FOTO")
    data_criacao = Column(DateTime, default=datetime.utcnow, name="DATA_CRIACAO")
    id_usuario = Column(Integer, ForeignKey("USUARIO.ID_USUARIO", ondelete="CASCADE"), name="ID_USUARIO")

    autor = relationship("Usuario", back_populates="postagens")
    comentarios = relationship("Comentario", back_populates="postagem", cascade="all, delete")
    curtidas = relationship("Curtida", back_populates="postagem", cascade="all, delete")


# 4. MODELO DE COMENTÁRIO
class Comentario(Base):
    __tablename__ = "COMENTARIO"

    id_comentario = Column(Integer, primary_key=True, autoincrement=True, name="ID_COMENTARIO")
    texto = Column(Text, name="TEXTO")
    data_criacao = Column(DateTime, default=datetime.utcnow, name="DATA_CRIACAO")
    id_usuario = Column(Integer, ForeignKey("USUARIO.ID_USUARIO", ondelete="CASCADE"), name="ID_USUARIO")
    id_postagem = Column(Integer, ForeignKey("POSTAGEM.ID_POSTAGEM", ondelete="CASCADE"), name="ID_POSTAGEM")

    autor = relationship("Usuario", back_populates="comentarios")
    postagem = relationship("Postagem", back_populates="comentarios")
    curtidas = relationship("CurtidaComentario", back_populates="comentario", cascade="all, delete")


# 5. MODELO DE CURTIDA (em postagem)
class Curtida(Base):
    __tablename__ = "CURTIDA"

    id_curtida = Column(Integer, primary_key=True, autoincrement=True, name="ID_CURTIDA")
    id_usuario = Column(Integer, ForeignKey("USUARIO.ID_USUARIO", ondelete="CASCADE"), name="ID_USUARIO")
    id_postagem = Column(Integer, ForeignKey("POSTAGEM.ID_POSTAGEM", ondelete="CASCADE"), name="ID_POSTAGEM")
    data_curtida = Column(DateTime, default=datetime.utcnow, name="DATA_CURTIDA")

    autor = relationship("Usuario", back_populates="curtidas")
    postagem = relationship("Postagem", back_populates="curtidas")


# 6. CURTIDA EM COMENTÁRIO DE POSTAGEM
class CurtidaComentario(Base):
    __tablename__ = "CURTIDA_COMENTARIO"

    id_curtida_comentario = Column(Integer, primary_key=True, autoincrement=True, name="ID_CURTIDA_COMENTARIO")
    id_usuario = Column(Integer, ForeignKey("USUARIO.ID_USUARIO", ondelete="CASCADE"), name="ID_USUARIO")
    id_comentario = Column(Integer, ForeignKey("COMENTARIO.ID_COMENTARIO", ondelete="CASCADE"), name="ID_COMENTARIO")
    data_curtida = Column(DateTime, default=datetime.utcnow, name="DATA_CURTIDA")

    autor = relationship("Usuario", back_populates="curtidas_comentario")
    comentario = relationship("Comentario", back_populates="curtidas")


# 7. MODELO DE TÓPICO DO FÓRUM
class TopicoForum(Base):
    __tablename__ = "TOPICO_FORUM"

    id_topico = Column(Integer, primary_key=True, autoincrement=True, name="ID_TOPICO")
    titulo = Column(String(200), name="TITULO")
    conteudo = Column(Text, name="CONTEUDO")
    data_criacao = Column(DateTime, default=datetime.utcnow, name="DATA_CRIACAO")
    id_usuario = Column(Integer, ForeignKey("USUARIO.ID_USUARIO", ondelete="CASCADE"), name="ID_USUARIO")

    autor = relationship("Usuario", back_populates="topicos_forum")
    comentarios = relationship("ComentarioForum", back_populates="topico", cascade="all, delete")


# 8. MODELO DE COMENTÁRIO DO FÓRUM
class ComentarioForum(Base):
    __tablename__ = "COMENTARIO_FORUM"

    id_comentario_forum = Column(Integer, primary_key=True, autoincrement=True, name="ID_COMENTARIO_FORUM")
    texto = Column(Text, name="TEXTO")
    data_criacao = Column(DateTime, default=datetime.utcnow, name="DATA_CRIACAO")
    id_usuario = Column(Integer, ForeignKey("USUARIO.ID_USUARIO", ondelete="CASCADE"), name="ID_USUARIO")
    id_topico = Column(Integer, ForeignKey("TOPICO_FORUM.ID_TOPICO", ondelete="CASCADE"), name="ID_TOPICO")

    autor = relationship("Usuario", back_populates="comentarios_forum")
    topico = relationship("TopicoForum", back_populates="comentarios")
    curtidas = relationship("CurtidaComentarioForum", back_populates="comentario_forum", cascade="all, delete")


# 9. CURTIDA EM COMENTÁRIO DO FÓRUM
class CurtidaComentarioForum(Base):
    __tablename__ = "CURTIDA_COMENTARIO_FORUM"

    id_curtida = Column(Integer, primary_key=True, autoincrement=True, name="ID_CURTIDA")
    id_usuario = Column(Integer, ForeignKey("USUARIO.ID_USUARIO", ondelete="CASCADE"), name="ID_USUARIO")
    id_comentario_forum = Column(Integer, ForeignKey("COMENTARIO_FORUM.ID_COMENTARIO_FORUM", ondelete="CASCADE"), name="ID_COMENTARIO_FORUM")
    data_curtida = Column(DateTime, default=datetime.utcnow, name="DATA_CURTIDA")

    autor = relationship("Usuario", back_populates="curtidas_comentario_forum")
    comentario_forum = relationship("ComentarioForum", back_populates="curtidas")
