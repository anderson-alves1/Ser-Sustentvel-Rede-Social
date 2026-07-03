from pydantic import BaseModel, EmailStr, field_validator
from datetime import date, datetime
from typing import Optional, List

# --- 1. SCHEMAS DE USUÁRIO ---

# Dados que o Front-end precisa enviar para cadastrar um usuário
class UsuarioCadastro(BaseModel):
    nome: str
    email: EmailStr
    data_nascimento: date
    senha: str

    # Regras de Negócio  (Validações estritas via Pydantic)
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

# Dados que o Front-end envia para fazer Login
class UsuarioLogin(BaseModel):
    email: EmailStr
    senha: str

# Dados básicos do usuário para exibir como Autor de posts/comentários
class UsuarioMinimo(BaseModel):
    id_usuario: int
    nome: str
    avatar: Optional[str] = None  # <-- NOVO: Permite exibir a foto do usuário no feed e nos comentários

    class Config:
        from_attributes = True

# Dados que a API vai devolver no Perfil (Proteção de dados: Sem senha!)
class UsuarioResposta(BaseModel):
    id_usuario: int
    nome: str
    email: EmailStr
    sobre_mim: Optional[str] = None  # <-- NOVO: Retorna a biografia do usuário
    avatar: Optional[str] = None     # <-- NOVO: Retorna a foto de perfil do usuário
    data_criacao: datetime

    class Config:
        from_attributes = True


# --- 2. SCHEMAS DE TOKEN (Autenticação JWT ) ---

# Estrutura do Token devolvido após o Login bem-sucedido
class Token(BaseModel):
    token_sessao: str  # Casando com o nome que o seu front/banco esperam
    mensagem: str
    usuario: UsuarioResposta # <-- ALTERADO: Agora usa UsuarioResposta para devolver todos os dados

class TokenData(BaseModel):
    email: Optional[str] = None


# --- 3. SCHEMAS DE COMENTÁRIO ---

# Dados recebidos ao criar um comentário
class NovoComentario(BaseModel):
    texto: str

# Dados que a API retorna ao listar comentários no Feed
class ComentarioResposta(BaseModel):
    id_comentario: int
    texto: str
    data_criacao: datetime
    autor: UsuarioMinimo

    class Config:
        from_attributes = True


# --- 4. SCHEMAS DE POSTAGEM ---

# Dados recebidos ao criar uma nova publicação ecológicas
class NovaPostagem(BaseModel):
    legenda: str       # Atualizado de 'titulo' para 'legenda' conforme o MySQL e Models
    caminho_foto: str

# Estrutura completa de retorno do Card do Feed
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