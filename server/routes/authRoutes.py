from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
import models
from database import get_db
from schemas import (
    UsuarioCadastro, UsuarioLogin, NovaPostagem, NovoComentario,
    NovoTopico, NovoComentarioForum, AlterarConfiguracoes
)
from controllers.authController import AuthController, SECRET_KEY, ALGORITHM
import jwt
import shutil
import uuid
import os

router = APIRouter(prefix="/auth", tags=["Autenticação e Rede Social"])

# ─────────────────────────────────────────────
# HELPER: valida token e retorna usuario logado
# ─────────────────────────────────────────────
def obter_usuario_logado(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado ou inválido.")

    sessao_ativa = db.query(models.SessaoLogin).filter(models.SessaoLogin.token_sessao == token).first()
    if not sessao_ativa:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão encerrada. Faça login novamente.")

    usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == sessao_ativa.id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado.")
    return usuario

# ─────────────────────────────────────────────
# UPLOAD DE ARQUIVO
# ─────────────────────────────────────────────
@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_arquivo(file: UploadFile = File(...)):
    try:
        extensao = file.filename.split(".")[-1]
        nome_unico = f"{uuid.uuid4().hex}.{extensao}"
        caminho_salvamento = os.path.join("uploads", nome_unico)
        with open(caminho_salvamento, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"url": f"/{caminho_salvamento}"}
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar o upload do arquivo.")

# ─────────────────────────────────────────────
# AUTENTICAÇÃO
# ─────────────────────────────────────────────
@router.post("/cadastro", status_code=status.HTTP_201_CREATED)
def cadastrar_usuario(usuario: UsuarioCadastro, db: Session = Depends(get_db)):
    novo_usuario = AuthController.cadastrar_usuario(usuario, db)
    return {"mensagem": "Usuário ecológico cadastrado com sucesso!", "id_usuario": novo_usuario.id_usuario}

@router.post("/login")
def logar_usuario(usuario: UsuarioLogin, db: Session = Depends(get_db)):
    return AuthController.login_usuario(usuario, db)

@router.post("/logout")
def deslogar_usuario(token: str, db: Session = Depends(get_db)):
    sessao = db.query(models.SessaoLogin).filter(models.SessaoLogin.token_sessao == token).first()
    if not sessao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessão não encontrada ou já expirada.")
    try:
        db.delete(sessao)
        db.commit()
        return {"mensagem": "Logout realizado com sucesso. Sessão encerrada!"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao encerrar a sessão.")

# ─────────────────────────────────────────────
# CONFIGURAÇÕES DE CONTA (e-mail / senha)
# ─────────────────────────────────────────────
@router.put("/configuracoes")
def alterar_configuracoes(dados: AlterarConfiguracoes, token: str, db: Session = Depends(get_db)):
    usuario_atual = obter_usuario_logado(token, db)

    # Autentica com a senha atual antes de qualquer alteração
    if not AuthController.verificar_senha(dados.senha_atual, usuario_atual.senha_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Senha atual incorreta.")

    if not dados.novo_email and not dados.nova_senha:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe o novo e-mail ou a nova senha.")

    try:
        if dados.novo_email and dados.novo_email != usuario_atual.email:
            email_em_uso = db.query(models.Usuario).filter(models.Usuario.email == dados.novo_email).first()
            if email_em_uso:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este e-mail já está em uso.")
            usuario_atual.email = dados.novo_email

        if dados.nova_senha:
            usuario_atual.senha_hash = AuthController.hash_senha(dados.nova_senha)

        db.commit()
        db.refresh(usuario_atual)
        return {
            "mensagem": "Configurações atualizadas com sucesso!",
            "usuario": {
                "id_usuario": usuario_atual.id_usuario,
                "nome": usuario_atual.nome,
                "email": usuario_atual.email,
                "sobre_mim": usuario_atual.sobre_mim,
                "avatar": usuario_atual.avatar,
                "data_criacao": usuario_atual.data_criacao.isoformat() if usuario_atual.data_criacao else None,
                "pontos": usuario_atual.pontos or 0
            }
        }
    except HTTPException:
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao salvar as configurações.")

# ─────────────────────────────────────────────
# FEED / POSTAGENS
# ─────────────────────────────────────────────
@router.get("/feed")
def listar_feed(token: str = None, db: Session = Depends(get_db)):
    try:
        # Identifica usuário logado para saber curtidas
        usuario_logado_id = None
        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                email = payload.get("sub")
                sessao = db.query(models.SessaoLogin).filter(models.SessaoLogin.token_sessao == token).first()
                if sessao:
                    usuario_logado_id = sessao.id_usuario
            except Exception:
                pass

        postagens = db.query(models.Postagem).order_by(models.Postagem.data_criacao.desc()).all()
        lista_feed = []
        for post in postagens:
            comentarios_serializados = []
            for c in post.comentarios:
                # verifica se usuário logado curtiu este comentário
                eu_curto_com = False
                if usuario_logado_id:
                    eu_curto_com = db.query(models.CurtidaComentario).filter(
                        models.CurtidaComentario.id_usuario == usuario_logado_id,
                        models.CurtidaComentario.id_comentario == c.id_comentario
                    ).first() is not None
                comentarios_serializados.append({
                    "id_comentario": c.id_comentario,
                    "autor": c.autor.nome if c.autor else "Anônimo",
                    "id_autor": c.id_usuario,
                    "texto": c.texto,
                    "data": c.data_criacao.strftime("%d/%m/%Y %H:%M") if c.data_criacao else None,
                    "total_curtidas": len(c.curtidas),
                    "eu_curto": eu_curto_com
                })

            lista_feed.append({
                "id_postagem": post.id_postagem,
                "legenda": post.legenda,
                "caminho_foto": post.caminho_foto,
                "data_criacao": post.data_criacao.strftime("%d/%m/%Y %H:%M") if post.data_criacao else None,
                "autor": post.autor.nome if post.autor else "Usuário Anônimo",
                "id_autor": post.id_usuario,
                "total_curtidas": len(post.curtidas),
                "comentarios": comentarios_serializados
            })
        return lista_feed
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao carregar o feed.")

@router.post("/postar", status_code=status.HTTP_201_CREATED)
def criar_postagem(postagem: NovaPostagem, token: str, db: Session = Depends(get_db)):
    usuario_atual = obter_usuario_logado(token, db)
    try:
        novo_post = models.Postagem(
            legenda=postagem.legenda,
            caminho_foto=postagem.caminho_foto,
            id_usuario=usuario_atual.id_usuario
        )
        db.add(novo_post)
        # +5 pontos por publicar
        usuario_atual.pontos = (usuario_atual.pontos or 0) + 5
        db.commit()
        return {"mensagem": "Ação sustentável publicada com sucesso!"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao criar publicação.")

@router.delete("/postar/{id_postagem}")
def deletar_postagem(id_postagem: int, token: str, db: Session = Depends(get_db)):
    usuario_atual = obter_usuario_logado(token, db)
    post = db.query(models.Postagem).filter(models.Postagem.id_postagem == id_postagem).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Postagem não encontrada.")
    if post.id_usuario != usuario_atual.id_usuario:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")
    try:
        db.delete(post)
        db.commit()
        return {"mensagem": "Publicação excluída com sucesso!"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao excluir a publicação.")

# ─────────────────────────────────────────────
# CURTIDAS EM POSTAGENS
# ─────────────────────────────────────────────
@router.post("/curtir/{id_postagem}")
def curtir_postagem(id_postagem: int, token: str, db: Session = Depends(get_db)):
    usuario_atual = obter_usuario_logado(token, db)
    post = db.query(models.Postagem).filter(models.Postagem.id_postagem == id_postagem).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Postagem não encontrada.")
    curtida_existente = db.query(models.Curtida).filter(
        models.Curtida.id_usuario == usuario_atual.id_usuario,
        models.Curtida.id_postagem == id_postagem
    ).first()
    try:
        if curtida_existente:
            db.delete(curtida_existente)
            db.commit()
            return {"mensagem": "Curtida removida!"}
        else:
            nova_curtida = models.Curtida(id_usuario=usuario_atual.id_usuario, id_postagem=id_postagem)
            db.add(nova_curtida)
            # +2 pontos ao autor da postagem por receber curtida
            if post.autor:
                post.autor.pontos = (post.autor.pontos or 0) + 2
            db.commit()
            return {"mensagem": "Postagem curtida com sucesso!"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar curtida.")

# ─────────────────────────────────────────────
# COMENTÁRIOS EM POSTAGENS
# ─────────────────────────────────────────────
@router.post("/comentar/{id_postagem}", status_code=status.HTTP_201_CREATED)
def criar_comentario(id_postagem: int, comentario: NovoComentario, token: str, db: Session = Depends(get_db)):
    usuario_atual = obter_usuario_logado(token, db)
    post = db.query(models.Postagem).filter(models.Postagem.id_postagem == id_postagem).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Postagem não encontrada.")
    try:
        novo_comentario = models.Comentario(
            texto=comentario.texto,
            id_usuario=usuario_atual.id_usuario,
            id_postagem=id_postagem
        )
        db.add(novo_comentario)
        # +3 pontos por comentar
        usuario_atual.pontos = (usuario_atual.pontos or 0) + 3
        db.commit()
        return {"mensagem": "Comentário publicado com sucesso!"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao salvar comentário.")

@router.delete("/comentario/{id_comentario}")
def deletar_comentario(id_comentario: int, token: str, db: Session = Depends(get_db)):
    usuario_atual = obter_usuario_logado(token, db)
    comentario = db.query(models.Comentario).filter(models.Comentario.id_comentario == id_comentario).first()
    if not comentario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentário não encontrado.")
    if comentario.id_usuario != usuario_atual.id_usuario:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")
    try:
        db.delete(comentario)
        db.commit()
        return {"mensagem": "Comentário excluído com sucesso!"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao excluir comentário.")

@router.post("/curtir-comentario/{id_comentario}")
def curtir_comentario(id_comentario: int, token: str, db: Session = Depends(get_db)):
    usuario_atual = obter_usuario_logado(token, db)
    comentario = db.query(models.Comentario).filter(models.Comentario.id_comentario == id_comentario).first()
    if not comentario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentário não encontrado.")
    curtida_existente = db.query(models.CurtidaComentario).filter(
        models.CurtidaComentario.id_usuario == usuario_atual.id_usuario,
        models.CurtidaComentario.id_comentario == id_comentario
    ).first()
    try:
        if curtida_existente:
            db.delete(curtida_existente)
            db.commit()
            return {"mensagem": "Curtida removida do comentário!"}
        else:
            nova_curtida = models.CurtidaComentario(id_usuario=usuario_atual.id_usuario, id_comentario=id_comentario)
            db.add(nova_curtida)
            db.commit()
            return {"mensagem": "Comentário curtido!"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar curtida no comentário.")

# ─────────────────────────────────────────────
# PERFIL
# ─────────────────────────────────────────────
@router.get("/perfil")
def buscar_perfil_usuario(token: str, db: Session = Depends(get_db)):
    usuario_atual = obter_usuario_logado(token, db)
    total_posts = len(usuario_atual.postagens)
    total_curtidas_recebidas = sum(len(post.curtidas) for post in usuario_atual.postagens)
    return {
        "nome": usuario_atual.nome,
        "email": usuario_atual.email,
        "data_cadastro": usuario_atual.data_criacao.strftime("%d/%m/%Y") if usuario_atual.data_criacao else None,
        "pontos": usuario_atual.pontos or 0,
        "metricas": {
            "acoes_compartilhadas": total_posts,
            "eco_curtidas_recebidas": total_curtidas_recebidas
        }
    }

@router.put("/perfil")
def atualizar_perfil(token: str, sobre_mim: str = None, avatar: str = None, db: Session = Depends(get_db)):
    usuario_atual = obter_usuario_logado(token, db)
    try:
        if sobre_mim is not None:
            usuario_atual.sobre_mim = sobre_mim
        if avatar is not None:
            usuario_atual.avatar = avatar
        db.commit()
        db.refresh(usuario_atual)
        return {
            "mensagem": "Perfil atualizado com sucesso!",
            "usuario": {
                "id_usuario": usuario_atual.id_usuario,
                "nome": usuario_atual.nome,
                "email": usuario_atual.email,
                "sobre_mim": usuario_atual.sobre_mim,
                "avatar": usuario_atual.avatar,
                "data_criacao": usuario_atual.data_criacao.isoformat() if usuario_atual.data_criacao else None,
                "pontos": usuario_atual.pontos or 0
            }
        }
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao atualizar o perfil.")

# ─────────────────────────────────────────────
# RANKING DE PONTOS
# ─────────────────────────────────────────────
@router.get("/ranking")
def obter_ranking(db: Session = Depends(get_db)):
    try:
        usuarios = db.query(models.Usuario).order_by(
            (models.Usuario.pontos).desc()
        ).limit(20).all()
        return [
            {
                "posicao": i + 1,
                "id_usuario": u.id_usuario,
                "nome": u.nome,
                "avatar": u.avatar,
                "pontos": u.pontos or 0
            }
            for i, u in enumerate(usuarios)
        ]
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao obter ranking.")

# ─────────────────────────────────────────────
# FÓRUM - TÓPICOS
# ─────────────────────────────────────────────
@router.get("/forum")
def listar_topicos(db: Session = Depends(get_db)):
    try:
        topicos = db.query(models.TopicoForum).order_by(models.TopicoForum.data_criacao.desc()).all()
        return [
            {
                "id_topico": t.id_topico,
                "titulo": t.titulo,
                "conteudo": t.conteudo,
                "autor": t.autor.nome if t.autor else "Anônimo",
                "id_autor": t.id_usuario,
                "data_criacao": t.data_criacao.strftime("%d/%m/%Y %H:%M") if t.data_criacao else None,
                "total_comentarios": len(t.comentarios)
            }
            for t in topicos
        ]
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao listar tópicos do fórum.")

@router.post("/forum", status_code=status.HTTP_201_CREATED)
def criar_topico(topico: NovoTopico, token: str, db: Session = Depends(get_db)):
    usuario_atual = obter_usuario_logado(token, db)
    try:
        novo_topico = models.TopicoForum(
            titulo=topico.titulo,
            conteudo=topico.conteudo,
            id_usuario=usuario_atual.id_usuario
        )
        db.add(novo_topico)
        # +5 pontos por abrir tópico
        usuario_atual.pontos = (usuario_atual.pontos or 0) + 5
        db.commit()
        return {"mensagem": "Tópico criado com sucesso!"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao criar tópico.")

@router.delete("/forum/{id_topico}")
def deletar_topico(id_topico: int, token: str, db: Session = Depends(get_db)):
    usuario_atual = obter_usuario_logado(token, db)
    topico = db.query(models.TopicoForum).filter(models.TopicoForum.id_topico == id_topico).first()
    if not topico:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tópico não encontrado.")
    if topico.id_usuario != usuario_atual.id_usuario:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")
    try:
        db.delete(topico)
        db.commit()
        return {"mensagem": "Tópico excluído com sucesso!"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao excluir tópico.")

# ─────────────────────────────────────────────
# FÓRUM - COMENTÁRIOS
# ─────────────────────────────────────────────
@router.get("/forum/{id_topico}/comentarios")
def listar_comentarios_forum(id_topico: int, token: str = None, db: Session = Depends(get_db)):
    topico = db.query(models.TopicoForum).filter(models.TopicoForum.id_topico == id_topico).first()
    if not topico:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tópico não encontrado.")

    usuario_logado_id = None
    if token:
        try:
            sessao = db.query(models.SessaoLogin).filter(models.SessaoLogin.token_sessao == token).first()
            if sessao:
                usuario_logado_id = sessao.id_usuario
        except Exception:
            pass

    comentarios = db.query(models.ComentarioForum).filter(
        models.ComentarioForum.id_topico == id_topico
    ).order_by(models.ComentarioForum.data_criacao.asc()).all()

    resultado = []
    for c in comentarios:
        eu_curto = False
        if usuario_logado_id:
            eu_curto = db.query(models.CurtidaComentarioForum).filter(
                models.CurtidaComentarioForum.id_usuario == usuario_logado_id,
                models.CurtidaComentarioForum.id_comentario_forum == c.id_comentario_forum
            ).first() is not None
        resultado.append({
            "id_comentario_forum": c.id_comentario_forum,
            "autor": c.autor.nome if c.autor else "Anônimo",
            "id_autor": c.id_usuario,
            "texto": c.texto,
            "data": c.data_criacao.strftime("%d/%m/%Y %H:%M") if c.data_criacao else None,
            "total_curtidas": len(c.curtidas),
            "eu_curto": eu_curto
        })

    return {
        "id_topico": topico.id_topico,
        "titulo": topico.titulo,
        "conteudo": topico.conteudo,
        "autor": topico.autor.nome if topico.autor else "Anônimo",
        "id_autor": topico.id_usuario,
        "data_criacao": topico.data_criacao.strftime("%d/%m/%Y %H:%M") if topico.data_criacao else None,
        "comentarios": resultado
    }

@router.post("/forum/{id_topico}/comentarios", status_code=status.HTTP_201_CREATED)
def comentar_no_topico(id_topico: int, comentario: NovoComentarioForum, token: str, db: Session = Depends(get_db)):
    usuario_atual = obter_usuario_logado(token, db)
    topico = db.query(models.TopicoForum).filter(models.TopicoForum.id_topico == id_topico).first()
    if not topico:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tópico não encontrado.")
    try:
        novo_com = models.ComentarioForum(
            texto=comentario.texto,
            id_usuario=usuario_atual.id_usuario,
            id_topico=id_topico
        )
        db.add(novo_com)
        usuario_atual.pontos = (usuario_atual.pontos or 0) + 3
        db.commit()
        return {"mensagem": "Comentário publicado no fórum!"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao comentar no tópico.")

@router.delete("/forum/comentario/{id_comentario_forum}")
def deletar_comentario_forum(id_comentario_forum: int, token: str, db: Session = Depends(get_db)):
    usuario_atual = obter_usuario_logado(token, db)
    comentario = db.query(models.ComentarioForum).filter(
        models.ComentarioForum.id_comentario_forum == id_comentario_forum
    ).first()
    if not comentario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentário não encontrado.")
    if comentario.id_usuario != usuario_atual.id_usuario:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")
    try:
        db.delete(comentario)
        db.commit()
        return {"mensagem": "Comentário excluído!"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao excluir comentário do fórum.")

@router.post("/forum/curtir-comentario/{id_comentario_forum}")
def curtir_comentario_forum(id_comentario_forum: int, token: str, db: Session = Depends(get_db)):
    usuario_atual = obter_usuario_logado(token, db)
    comentario = db.query(models.ComentarioForum).filter(
        models.ComentarioForum.id_comentario_forum == id_comentario_forum
    ).first()
    if not comentario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentário não encontrado.")
    curtida_existente = db.query(models.CurtidaComentarioForum).filter(
        models.CurtidaComentarioForum.id_usuario == usuario_atual.id_usuario,
        models.CurtidaComentarioForum.id_comentario_forum == id_comentario_forum
    ).first()
    try:
        if curtida_existente:
            db.delete(curtida_existente)
            db.commit()
            return {"mensagem": "Curtida removida!"}
        else:
            nova_curtida = models.CurtidaComentarioForum(
                id_usuario=usuario_atual.id_usuario,
                id_comentario_forum=id_comentario_forum
            )
            db.add(nova_curtida)
            db.commit()
            return {"mensagem": "Comentário curtido!"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao curtir comentário do fórum.")

# ─────────────────────────────────────────────
# PESQUISA
# ─────────────────────────────────────────────
@router.get("/pesquisar")
def pesquisar(q: str, db: Session = Depends(get_db)):
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Digite pelo menos 2 caracteres para pesquisar.")
    termo = f"%{q.strip()}%"
    resultados = []

    # Pesquisa usuários pelo NOME
    usuarios = db.query(models.Usuario).filter(models.Usuario.nome.ilike(termo)).limit(10).all()
    for u in usuarios:
        resultados.append({
            "tipo": "usuario",
            "id": u.id_usuario,
            "titulo": u.nome,
            "subtitulo": u.sobre_mim or "",
            "avatar": u.avatar
        })

    # Pesquisa publicações pelo CONTEUDO (legenda)
    publicacoes = db.query(models.Postagem).filter(models.Postagem.legenda.ilike(termo)).limit(10).all()
    for p in publicacoes:
        resultados.append({
            "tipo": "publicacao",
            "id": p.id_postagem,
            "titulo": p.legenda[:80] + ("..." if len(p.legenda or "") > 80 else ""),
            "subtitulo": f"Por {p.autor.nome if p.autor else 'Anônimo'} em {p.data_criacao.strftime('%d/%m/%Y') if p.data_criacao else ''}",
            "avatar": None
        })

    # Pesquisa tópicos do fórum
    topicos = db.query(models.TopicoForum).filter(
        or_(models.TopicoForum.titulo.ilike(termo), models.TopicoForum.conteudo.ilike(termo))
    ).limit(10).all()
    for t in topicos:
        resultados.append({
            "tipo": "topico_forum",
            "id": t.id_topico,
            "titulo": t.titulo,
            "subtitulo": f"Por {t.autor.nome if t.autor else 'Anônimo'} — {t.conteudo[:60]}...",
            "avatar": None
        })

    return resultados