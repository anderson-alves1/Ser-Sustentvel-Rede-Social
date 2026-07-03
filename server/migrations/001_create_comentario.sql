CREATE TABLE IF NOT EXISTS comentarios (
    id_comentario INT PRIMARY KEY AUTO_INCREMENT,
    texto TEXT NOT NULL,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_usuario INT NOT NULL,
    id_postagem INT NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_postagem) REFERENCES postagem(id_postagem) ON DELETE CASCADE
);
