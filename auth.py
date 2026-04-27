import hashlib
import uuid
from datetime import datetime, timedelta
from database import conectar


def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def gerar_token():
    return str(uuid.uuid4())


# =========================
# 🧾 REGISTER
# =========================
def register_user(email, senha, device_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        conn.close()
        return {"erro": "Email já existe"}

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


# =========================
# 🔐 LOGIN
# =========================
def login_user(email, senha, device_id):
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT senha, trial_expira_em, ativo, device_id
            FROM users WHERE email=%s
        """, (email,))

        user = cursor.fetchone()

        if not user:
            return {"erro": "Usuário não existe"}

        senha_db, trial_expira, ativo, device_db = user

        if hash_senha(senha) != senha_db:
            return {"erro": "Senha inválida"}

        # 🔒 trava dispositivo
        if device_db and device_db != device_id:
            return {"erro": "Conta usada em outro dispositivo"}

        # salva device primeira vez
        if not device_db:
            cursor.execute(
                "UPDATE users SET device_id=%s WHERE email=%s",
                (device_id, email)
            )

        agora = datetime.now()

        trial_restante = 0
        if trial_expira:
            trial_restante = (trial_expira - agora).days

        # ⛔ bloqueado
        if trial_restante <= 0 and ativo == 0:
            return {
                "status": "bloqueado",
                "trial_restante": 0
            }

        token = gerar_token()

        cursor.execute(
            "UPDATE users SET token=%s WHERE email=%s",
            (token, email)
        )

        conn.commit()

        return {
            "status": "ok",
            "token": token,
            "trial_restante": trial_restante,
            "ativo": ativo
        }

    except Exception as e:
        print("ERRO LOGIN:", e)
        return {"erro": "falha no login"}

    finally:
        conn.close()


# =========================
# 💳 ATIVAR USUÁRIO (PIX)
# =========================
def ativar_usuario(email):
    conn = conectar()
    cursor = conn.cursor()

    # ativa e adiciona +30 dias
    cursor.execute("""
        UPDATE users
        SET ativo = 1,
            trial_expira_em = NOW() + INTERVAL '30 days'
        WHERE email = %s
    """, (email,))

    conn.commit()
    conn.close()

    return True
