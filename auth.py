# backend/auth.py

from database import conectar
import hashlib
import uuid
from datetime import datetime, timedelta


def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def gerar_token():
    return str(uuid.uuid4())


def register_user(email, senha, device_id):
    conn = conectar()
    cursor = conn.cursor()

    # email já existe
    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        return {"erro": "Email já cadastrado"}

    # bloqueio por dispositivo
    cursor.execute("SELECT id FROM users WHERE device_id=%s", (device_id,))
    if cursor.fetchone():
        return {"erro": "Este dispositivo já possui conta"}

    agora = datetime.now()
    trial = agora + timedelta(days=15)

    cursor.execute("""
        INSERT INTO users (email, senha, criado_em, trial_expira_em, ativo, device_id)
        VALUES (%s, %s, %s, %s, 0, %s)
    """, (
        email,
        hash_senha(senha),
        agora,
        trial,
        device_id
    ))

    conn.commit()
    conn.close()

    return {"status": "ok"}


def login_user(email, senha):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT senha, trial_expira_em, ativo
        FROM users
        WHERE email=%s
    """, (email,))

    user = cursor.fetchone()

    if not user:
        return {"erro": "Usuário não encontrado"}

    senha_db, trial_expira, ativo = user

    if hash_senha(senha) != senha_db:
        return {"erro": "Senha inválida"}

    agora = datetime.now()

    if not trial_expira:
        trial_expira = agora

    # status
    if agora <= trial_expira:
        status = "trial"
    elif ativo == 1:
        status = "ativo"
    else:
        return {"status": "bloqueado"}

    token = gerar_token()

    cursor.execute(
        "UPDATE users SET token=%s WHERE email=%s",
        (token, email)
    )

    conn.commit()
    conn.close()

    return {
        "status": status,
        "token": token
    }


def ativar_usuario(email):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET ativo=1 WHERE email=%s",
        (email,)
    )

    conn.commit()
    conn.close()