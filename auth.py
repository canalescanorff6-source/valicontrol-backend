from database import conectar
import hashlib, uuid
from datetime import datetime, timedelta


def hash_senha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def gerar_token():
    return str(uuid.uuid4())


def register_user(email, senha, device_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        return {"erro": "Email já existe"}

    agora = datetime.now()
    trial = agora + timedelta(days=15)

    cursor.execute("""
        INSERT INTO users (email, senha, criado_em, trial_expira_em, ativo, device_id)
        VALUES (%s,%s,%s,%s,0,%s)
    """, (email, hash_senha(senha), agora, trial, device_id))

    conn.commit()
    conn.close()

    return {"status": "ok"}


def login_user(email, senha, device_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT senha, device_id, trial_expira_em, ativo, expira_em
        FROM users WHERE email=%s
    """, (email,))

    user = cursor.fetchone()

    if not user:
        return {"erro": "Usuário não existe"}

    senha_db, dev, trial, ativo, expira = user

    if hash_senha(senha) != senha_db:
        return {"erro": "Senha inválida"}

    if dev and dev != device_id:
        return {"erro": "Conta usada em outro dispositivo"}

    if not dev:
        cursor.execute("UPDATE users SET device_id=%s WHERE email=%s",
                       (device_id, email))

    agora = datetime.now()

    if trial and agora <= trial:
        status = "trial"
    elif ativo == 1 and expira and agora <= expira:
        status = "ativo"
    else:
        return {"status": "bloqueado"}

    token = gerar_token()

    cursor.execute("UPDATE users SET token=%s WHERE email=%s", (token, email))

    conn.commit()
    conn.close()

    return {"status": status, "token": token}


def ativar_usuario(email):
    conn = conectar()
    cursor = conn.cursor()

    expira = datetime.now() + timedelta(days=30)

    cursor.execute("""
        UPDATE users SET ativo=1, expira_em=%s WHERE email=%s
    """, (expira, email))

    conn.commit()
    conn.close()