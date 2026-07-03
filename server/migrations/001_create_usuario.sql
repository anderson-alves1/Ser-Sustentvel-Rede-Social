CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    data_nascimento DATE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    sobre_mim TEXT,
    avatar VARCHAR(255),
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
);
