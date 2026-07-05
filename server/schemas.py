from pydantic import BaseModel, EmailStr, field_validator
from datetime import date, datetime
from typing import Optional, List

# --- 1. SCHEMAS DE USUÁRIO ---

class UsuarioCadastro(BaseModel):
    nome: str
    email: EmailStr
    data_nascimento: date
    senha: str

    @field_validator('senha')
    def validar_senha(cls, v):
        if len(v) < 6:
            raise ValueError('A senha deve conter pelo menos 6 caracteres.')
        return v

    @field_validator('data_nascimento')
    def validar_idade(cls, v):
        hoje = date.today()
        idade = hoje.year - v.year - ((hoje.month, hoje.day) < (v.month, v.day))
        if idade < 16:
            raise ValueError('O usuário deve ter pelo menos 16 anos para se cadastrar.')
        return v

class UsuarioLogin(BaseModel):
    email: EmailStr
    senha: str

class UsuarioMinimo(BaseModel):
    id_usuario: int
    nome: str
    avatar: Optional[str] = None

    class Config:
        from_attributes = True

class UsuarioResposta(BaseModel):
    id_usuario: int
    nome: str
    email: EmailStr
    sobre_mim: Optional[str] = None
    avatar: Optional[str] = None
    data_criacao: datetime
    pontos: Optional[int] = 0

    class Config:
        from_attributes = True

# Schema para alterar configurações de conta
class AlterarConfiguracoes(BaseModel):
    senha_atual: str
    novo_email: Optional[EmailStr] = None
    nova_senha: Optional[str] = None

    @field_validator('nova_senha')
    def validar_nova_senha(cls, v):
        if v is not None and len(v) < 6:
            raise ValueError('A nova senha deve conter pelo menos 6 caracteres.')
        return v


# --- 2. SCHEMAS DE TOKEN ---

class Token(BaseModel):
    token_sessao: str
    mensagem: str
    usuario: UsuarioResposta

class TokenData(BaseModel):
    email: Optional[str] = None


# --- 3. SCHEMAS DE COMENTÁRIO (postagem) ---

class NovoComentario(BaseModel):
    texto: str

class ComentarioResposta(BaseModel):
    id_comentario: int
    texto: str
    data_criacao: datetime
    autor: UsuarioMinimo
    total_curtidas: Optional[int] = 0
    eu_curto: Optional[bool] = False

    class Config:
        from_attributes = True


# --- 4. SCHEMAS DE POSTAGEM ---

class NovaPostagem(BaseModel):
    legenda: str
    caminho_foto: str

class PostagemResposta(BaseModel):
    id_postagem: int
    legenda: str
    caminho_foto: str
    data_criacao: datetime
    autor: UsuarioMinimo
    total_curtidas: int
    comentarios: List[ComentarioResposta] = []

    class Config:
        from_attributes = True


# --- 5. SCHEMAS DO FÓRUM ---

class NovoTopico(BaseModel):
    titulo: str
    conteudo: str

class NovoComentarioForum(BaseModel):
    texto: str

class ComentarioForumResposta(BaseModel):
    id_comentario_forum: int
    texto: str
    data_criacao: datetime
    autor: UsuarioMinimo
    total_curtidas: Optional[int] = 0
    eu_curto: Optional[bool] = False

    class Config:
        from_attributes = True

class TopicoForumResposta(BaseModel):
    id_topico: int
    titulo: str
    conteudo: str
    data_criacao: datetime
    autor: UsuarioMinimo
    total_comentarios: Optional[int] = 0

    class Config:
        from_attributes = True


# --- 6. SCHEMA DE PESQUISA ---

class ResultadoPesquisa(BaseModel):
    tipo: str  # "usuario" ou "publicacao" ou "topico"
    id: int
    titulo: str
    subtitulo: Optional[str] = None