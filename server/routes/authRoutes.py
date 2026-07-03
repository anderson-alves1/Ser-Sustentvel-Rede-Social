from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import models
from database import get_db
from schemas import UsuarioCadastro, UsuarioLogin, NovaPostagem, NovoComentario
from controllers.authController import AuthController, SECRET_KEY, ALGORITHM  # Importa do Controller centralizado
import jwt

router = APIRouter(prefix="/auth", tags=["Autenticação e Rede Social"])


# --- FUNÇÃO AUXILIAR: PROTEÇÃO DE ROTAS (DEPENDÊNCIA) ---
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


# --- ROTA DE CADASTRO ---
@router.post("/cadastro", status_code=status.HTTP_201_CREATED)
def cadastrar_usuario(usuario: UsuarioCadastro, db: Session = Depends(get_db)):
    # Delega a lógica de validação e persistência para o Controller
    novo_usuario = AuthController.cadastrar_usuario(usuario, db)
    return {"mensagem": "Usuário ecológico cadastrado com sucesso!", "id_usuario": novo_usuario.id_usuario}


# --- ROTA DE LOGIN ---
@router.post("/login")
def logar_usuario(usuario: UsuarioLogin, db: Session = Depends(get_db)):
    # Delega a autenticação e geração de sessão JWT para o Controller
    return AuthController.login_usuario(usuario, db)


# --- ROTA DE LOGOUT ---
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao encerrar a sessão no banco de dados.")


# --- ROTA DO FEED DO DASHBOARD ---
@router.get("/feed")
def listar_feed(db: Session = Depends(get_db)):
    try:
        postagens = db.query(models.Postagem).order_by(models.Postagem.data_criacao.desc()).all()
        lista_feed = []
        for post in postagens:
            lista_feed.append({
                "id_postagem": post.id_postagem,
                "legenda": post.legenda,
                "caminho_foto": post.caminho_foto,
                "data_criacao": post.data_criacao.strftime("%d/%m/%Y %H:%M") if post.data_criacao else None,
                "autor": post.autor.nome if post.autor else "Usuário Anônimo", 
                "total_curtidas": len(post.curtidas), 
                "comentarios": [
                    {
                        "id_comentario": c.id_comentario,
                        "autor": c.autor.nome if c.autor else "Anônimo",
                        "texto": c.texto,
                        "data": c.data_criacao.strftime("%d/%m/%Y %H:%M") if c.data_criacao else None
                    } for c in post.comentarios
                ]
            })
        return lista_feed
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao carregar o feed do banco de dados.")


# --- ROTA PARA CRIAR POSTAGEM ---
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
        db.commit()
        return {"mensagem": "Ação sustentável publicada com sucesso!"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao criar publicação.")


# --- ROTA PARA DELETAR POSTAGEM ---
@router.delete("/postar/{id_postagem}")
def deletar_postagem(id_postagem: int, token: str, db: Session = Depends(get_db)):
    usuario_atual = obter_usuario_logado(token, db)
    
    post = db.query(models.Postagem).filter(models.Postagem.id_postagem == id_postagem).first()
    
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Postagem não encontrada.")
        
    if post.id_usuario != usuario_atual.id_usuario:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado. Você só pode excluir suas próprias publicações.")

    try:
        db.delete(post)
        db.commit()
        return {"mensagem": "Publicação excluída com sucesso!"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao excluir a publicação.")


# --- ROTA DE ECO-CURTIDAS (CURTIR/DESCUTIR) ---
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
            db.commit()
            return {"mensagem": "Postagem curtida com sucesso!"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar curtida.")


# --- ROTA PARA CRIAR COMENTÁRIOS ---
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
        db.commit()
        return {"mensagem": "Comentário publicado com sucesso!"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao salvar comentário no banco de dados.")


# --- ROTA DE PERFIL (MÉTRICAS DO DASHBOARD) ---
@router.get("/perfil")
def buscar_perfil_usuario(token: str, db: Session = Depends(get_db)):
    usuario_atual = obter_usuario_logado(token, db)
    
    total_posts = len(usuario_atual.postagens)
    total_curtidas_recebidas = sum(len(post.curtidas) for post in usuario_atual.postagens)
    
    return {
        "nome": usuario_atual.nome,
        "email": usuario_atual.email,
        "data_cadastro": usuario_atual.data_criacao.strftime("%d/%m/%Y") if usuario_atual.data_criacao else None,
        "metricas": {
            "acoes_compartilhadas": total_posts,
            "eco_curtidas_recebidas": total_curtidas_recebidas
        }
    }