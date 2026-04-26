import sqlite3
import hashlib
import uuid
from datetime import datetime, timedelta

DB = "backend.db"


# =========================
# 🔌 CONEXÃO
# =========================
def conectar():
    return sqlite3.connect(DB)


# =========================
# 🏗 CRIAR TABELA
# =========================
def criar_tabela():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            senha TEXT,
            token TEXT,
            criado_em TEXT,
            trial_expira_em TEXT,
            ativo INTEGER DEFAULT 0,
            device_id TEXT
        )
    """)

    conn.commit()
    conn.close()


# =========================
# 🔐 HASH SENHA
# =========================
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


# =========================
# 📱 GERAR DEVICE ID
# =========================
def gerar_device():
    return str(uuid.uuid4())


# =========================
# 🔑 GERAR TOKEN
# =========================
def gerar_token(email):
    token = str(uuid.uuid4())

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET token = ?
        WHERE email = ?
    """, (token, email))

    conn.commit()
    conn.close()

    return token


# =========================
# 👤 REGISTRAR
# =========================
def register_user(email, senha):
    conn = conectar()
    cursor = conn.cursor()

    # já existe?
    cursor.execute("SELECT id FROM users WHERE email=?", (email,))
    if cursor.fetchone():
        conn.close()
        return {"erro": "Usuário já existe"}

    hoje = datetime.now()
    trial = hoje + timedelta(days=7)

    device = gerar_device()

    try:
        cursor.execute("""
            INSERT INTO users (
                email, senha, criado_em, trial_expira_em, ativo, device_id
            )
            VALUES (?, ?, ?, ?, 0, ?)
        """, (
            email,
            hash_senha(senha),
            hoje.isoformat(),
            trial.isoformat(),
            device
        ))

        conn.commit()
        return {"status": "ok"}

    except Exception as e:
        return {"erro": str(e)}

    finally:
        conn.close()


# =========================
# 🔑 LOGIN
# =========================
def login_user(email, senha):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT senha, trial_expira_em, ativo
        FROM users
        WHERE email=?
    """, (email,))

    user = cursor.fetchone()

    if not user:
        conn.close()
        return {"erro": "Usuário não existe"}

    senha_db, trial_expira, ativo = user

    # valida senha
    if hash_senha(senha) != senha_db:
        conn.close()
        return {"erro": "Senha inválida"}

    agora = datetime.now()
    trial_expira = datetime.fromisoformat(trial_expira)

    # 🔥 status
    if agora <= trial_expira:
        status = "trial"
    elif ativo == 1:
        status = "ativo"
    else:
        conn.close()
        return {"status": "bloqueado"}

    # 🔑 gera token
    token = gerar_token(email)

    conn.close()

    return {
        "status": status,
        "token": token
    }


# =========================
# 💳 ATIVAR PLANO
# =========================
def ativar_usuario(email):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET ativo = 1
        WHERE email = ?
    """, (email,))

    conn.commit()
    conn.close()