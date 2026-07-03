CREATE TABLE IF NOT EXISTS postagens (
    id_postagem INT PRIMARY KEY AUTO_INCREMENT,
    legenda TEXT NOT NULL,
    caminho_foto VARCHAR(255) NOT NULL,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_usuario INT NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE
);
