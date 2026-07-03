# Ser Sustentável API 🌿

Backend API para a rede social ecológica "Ser Sustentável" - uma plataforma para compartilhar e celebrar ações sustentáveis da comunidade.

## 📋 Visão Geral

A **Ser Sustentável API** é um servidor FastAPI que gerencia usuários, autenticação JWT, publicações ecológicas, comentários e interações em uma rede social focada em sustentabilidade. O projeto utiliza **SQLAlchemy ORM** com **MySQL** como banco de dados.

## 🚀 Funcionalidades

### Autenticação e Usuários
- ✅ Cadastro de usuários com validações de segurança
- ✅ Login com geração de tokens JWT
- ✅ Perfil de usuário com avatar e biografia
- ✅ Gerenciamento de sessões

### Feed Social
- ✅ Criar publicações com legenda e fotos
- ✅ Comentar em publicações
- ✅ Curtir publicações
- ✅ Listar feed com posts dos usuários

### Segurança
- ✅ Hash seguro de senhas (bcrypt)
- ✅ Autenticação por JWT
- ✅ CORS configurado para integração com frontend
- ✅ Validação de dados com Pydantic

## 🛠️ Stack Técnico

- **Framework**: FastAPI
- **Banco de Dados**: MySQL
- **ORM**: SQLAlchemy
- **Autenticação**: JWT (PyJWT)
- **Validação**: Pydantic
- **Hash de Senha**: Passlib com Bcrypt

## 📁 Estrutura do Projeto

```
server/
├── main.py                 # Aplicação FastAPI principal
├── database.py             # Configuração do banco de dados
├── models.py               # Modelos SQLAlchemy (ORM)
├── schemas.py              # Schemas de validação (Pydantic)
├── routes/
│   └── authRoutes.py       # Rotas de autenticação e feed
├── controllers/
│   └── authController.py   # Lógica de autenticação
├── migrations/             # Migrações do banco (se aplicável)
└── __pycache__/            # Cache Python
```

## 📊 Modelos de Dados

### Usuario
```python
- id_usuario (PK)
- nome
- email (único)
- data_nascimento
- senha_hash
- sobre_mim
- avatar
- data_criacao
```

### SessaoLogin
```python
- id_sessao (PK)
- id_usuario (FK)
- token_sessao
- data_hora_login
```

### Postagem
```python
- id_postagem (PK)
- legenda
- caminho_foto
- data_criacao
- id_usuario (FK - Autor)
```

### Comentario
```python
- id_comentario (PK)
- texto
- data_criacao
- id_usuario (FK - Autor)
- id_postagem (FK)
```

### Curtida
```python
- id_curtida (PK)
- id_usuario (FK)
- id_postagem (FK)
- data_curtida
```

## 🔧 Instalação

### Pré-requisitos
- Python 3.8+
- MySQL 5.7+ ou superior
- pip (gerenciador de pacotes Python)

### Passo a Passo

1. **Clone o repositório**
```bash
cd O-Sustent-vel-Rede-Social/server
```

2. **Crie um ambiente virtual**
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. **Instale as dependências**
```bash
pip install fastapi sqlalchemy mysql-connector-python pydantic pydantic[email] passlib[bcrypt] python-jose[cryptography] pyjwt
```

4. **Configure o banco de dados**

Edite o arquivo `database.py` e atualize a string de conexão:

```python
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://usuario:senha@localhost/ser_sustentavel"
```

Crie o banco de dados no MySQL:
```sql
CREATE DATABASE ser_sustentavel;
```

5. **Inicie o servidor**
```bash
uvicorn main:app --reload
```

O servidor estará rodando em `http://localhost:8000`

## 📚 Documentação da API

Após iniciar o servidor, acesse:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Rotas Disponíveis

### Autenticação
- `POST /auth/cadastro` - Cadastrar novo usuário
- `POST /auth/login` - Fazer login
- `POST /auth/logout` - Fazer logout

### Usuários
- `GET /auth/perfil` - Obter perfil do usuário logado
- `PUT /auth/perfil` - Atualizar perfil

### Publicações
- `POST /auth/postagens` - Criar nova publicação
- `GET /auth/feed` - Listar feed de publicações
- `GET /auth/postagens/{id}` - Obter detalhes de uma publicação

### Comentários
- `POST /auth/postagens/{id}/comentarios` - Adicionar comentário
- `GET /auth/postagens/{id}/comentarios` - Listar comentários

### Curtidas
- `POST /auth/postagens/{id}/curtir` - Curtir publicação
- `DELETE /auth/postagens/{id}/curtir` - Remover curtida

## 🔑 Variáveis de Ambiente

Para facilitar a configuração, crie um arquivo `.env`:

```env
DATABASE_URL=mysql+pymysql://usuario:senha@localhost/ser_sustentavel
SECRET_KEY=sua_chave_secreta_super_segura
ALGORITHM=HS256
```

## ⚙️ Configuração de CORS

Atualmente configurado para aceitar requisições de qualquer origem. **Em produção**, altere em `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://seu-frontend.com"],  # Especifique o domínio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🧪 Testando a API

### Exemplo de Cadastro
```bash
curl -X POST "http://localhost:8000/auth/cadastro" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "João Silva",
    "email": "joao@example.com",
    "data_nascimento": "2000-01-15",
    "senha": "senha123"
  }'
```

### Exemplo de Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "joao@example.com",
    "senha": "senha123"
  }'
```

## 📝 Validações Implementadas

- ✅ Idade mínima: 16 anos
- ✅ Senha mínima: 6 caracteres
- ✅ Email válido e único
- ✅ Cascata de deleção para manter integridade referencial

## 🐛 Troubleshooting

### Erro de conexão com MySQL
- Verifique se o MySQL está rodando
- Confirme as credenciais em `database.py`
- Certifique-se que o banco `ser_sustentavel` existe

### Erro 401 (Não autorizado)
- Verifique se o token JWT está correto
- Confirme se a sessão ainda está ativa
- Faça login novamente se necessário

### Erro CORS
- Atualize `allow_origins` em `main.py` com o domínio do frontend

## 🚀 Deploy

### Produção com Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

### Com Docker (Exemplo)
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📖 Convenções de Código

- **Nomes de tabelas**: UPPERCASE (ex: USUARIO, POSTAGEM)
- **Nomes de colunas**: snake_case com PREFIX (ex: ID_USUARIO, DATA_CRIACAO)
- **Modelos SQLAlchemy**: PascalCase (ex: Usuario, Postagem)
- **Schemas Pydantic**: PascalCase (ex: UsuarioCadastro, PostagemResposta)

## 🤝 Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👥 Autores

Projeto desenvolvido com ❤️ para a **Rede Social Ecológica Ser Sustentável**

## 📞 Suporte

Para dúvidas ou problemas, abra uma **Issue** no repositório ou entre em contato com o time de desenvolvimento.

---

**Vamos juntos construir um futuro mais sustentável!** 🌍💚
