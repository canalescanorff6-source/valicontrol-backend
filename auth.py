import hashlib
import uuid
from datetime import datetime, timedelta
from database import conectar


# =========================
# 🔐 UTIL
# =========================
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def gerar_token():
    return str(uuid.uuid4())


def log(email, acao):
    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO logs (email, acao) VALUES (%s, %s)",
            (email, acao)
        )

        conn.commit()
        conn.close()
    except Exception as e:
        print("ERRO LOG:", e)


# =========================
# 📝 REGISTER
# =========================
def register_user(email, senha, device_id):
    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            return {"erro": "Email já existe"}

        agora = datetime.now()
        trial = agora + timedelta(days=15)

        cursor.execute("""
            INSERT INTO users (email, senha, criado_em, trial_expira_em, ativo, device_id)
            VALUES (%s, %s, %s, %s, 0, %s)
        """, (email, hash_senha(senha), agora, trial, device_id))

        conn.commit()
        return {"status": "ok"}

    except Exception as e:
        print("ERRO REGISTER:", e)
        return {"erro": "erro ao registrar"}

    finally:
        conn.close()


# =========================
# 🔑 LOGIN
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

        # senha
        if hash_senha(senha) != senha_db:
            return {"erro": "Senha inválida"}

        # dispositivo
        if device_db and device_db != device_id:
            return {"erro": "Conta já usada em outro dispositivo"}

        # salva device
        if not device_db:
            cursor.execute(
                "UPDATE users SET device_id=%s WHERE email=%s",
                (device_id, email)
            )

        agora = datetime.now()

        # 🔥 PROTEÇÃO CONTRA NULL
        if trial_expira:
            dias = max(0, (trial_expira - agora).days)
        else:
            dias = 0

        if dias <= 0 and ativo == 0:
            return {"status": "bloqueado", "trial_restante": 0}

        # token
        token = gerar_token()

        cursor.execute(
            "UPDATE users SET token=%s WHERE email=%s",
            (token, email)
        )

        conn.commit()

        log(email, "login")

        return {
            "status": "ok",
            "token": token,
            "trial_restante": dias,
            "ativo": ativo
        }

    except Exception as e:
        print("ERRO LOGIN:", e)
        return {"erro": "falha no login"}

    finally:
        conn.close()


# =========================
# 💳 ATIVAR USUÁRIO
# =========================
def ativar_usuario(email):
    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users
            SET ativo = 1,
                plano = 'pago',
                trial_expira_em = NOW() + INTERVAL '30 days'
            WHERE email = %s
        """, (email,))

        conn.commit()

        log(email, "pagamento_aprovado")

        return True

    except Exception as e:
        print("ERRO ATIVAR:", e)
        return False

    finally:
        conn.close()
