CREATE TABLE IF NOT EXISTS sessao_logins (
    id_sessao INT PRIMARY KEY AUTO_INCREMENT,
    id_usuario INT NOT NULL,
    token_sessao TEXT NOT NULL,
    data_hora_login DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE
);
