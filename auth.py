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
    conn = None
    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO logs (email, acao) VALUES (%s, %s)",
            (email, acao)
        )

        conn.commit()

    except Exception as e:
        print("ERRO LOG:", e)

    finally:
        if conn:
            conn.close()


# =========================
# 🧠 CALCULAR DIAS
# =========================
def calcular_dias_restantes(data):
    if not data:
        return 0

    agora = datetime.now()

    hoje = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    expira = data.replace(hour=0, minute=0, second=0, microsecond=0)

    dias = (expira - hoje).days

    return max(0, dias)


# =========================
# 📝 REGISTER
# =========================
def register_user(email, senha, device_id):
    conn = None
    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            return {"erro": "Email já existe"}

        cursor.execute("SELECT id FROM users WHERE device_id=%s", (device_id,))
        if cursor.fetchone():
            return {"erro": "Já existe uma conta neste dispositivo"}

        agora = datetime.now()
        trial = agora + timedelta(days=15)

        cursor.execute("""
            INSERT INTO users (email, senha, criado_em, trial_expira_em, ativo, device_id, is_admin)
            VALUES (%s, %s, %s, %s, 0, %s, FALSE)
        """, (email, hash_senha(senha), agora, trial, device_id))

        conn.commit()

        log(email, "registro")

        return {"status": "ok"}

    except Exception as e:
        print("ERRO REGISTER:", e)
        return {"erro": str(e)}  # 🔥 MOSTRA ERRO REAL

    finally:
        if conn:
            conn.close()


# =========================
# 🔑 LOGIN
# =========================
def login_user(email, senha, device_id):
    conn = None
    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT senha, trial_expira_em, ativo, device_id, is_admin
            FROM users WHERE email=%s
        """, (email,))

        user = cursor.fetchone()

        if not user:
            return {"erro": "Usuário não existe"}

        senha_db, trial_expira, ativo, device_db, is_admin = user

        if hash_senha(senha) != senha_db:
            return {"erro": "Senha inválida"}

        if device_db and device_db != device_id:
            return {"erro": "Conta vinculada a outro dispositivo"}

        if not device_db:
            cursor.execute(
                "UPDATE users SET device_id=%s WHERE email=%s",
                (device_id, email)
            )

        dias = calcular_dias_restantes(trial_expira)

        if dias <= 0 and ativo == 0:
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

        log(email, "login")

        return {
            "status": "ok",
            "token": token,
            "trial_restante": dias,
            "ativo": ativo,
            "is_admin": is_admin
        }

    except Exception as e:
        print("ERRO LOGIN:", e)
        return {"erro": str(e)}  # 🔥 MOSTRA ERRO REAL

    finally:
        if conn:
            conn.close()


# =========================
# 💳 ATIVAR USUÁRIO
# =========================
def ativar_usuario(email):
    conn = None
    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT ativo FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if not user:
            return False

        ativo = user[0]

        if ativo == 1:
            print("⚠️ Usuário já ativo")
            return True

        nova_data = datetime.now() + timedelta(days=30)

        cursor.execute("""
            UPDATE users
            SET ativo = 1,
                plano = 'pago',
                trial_expira_em = %s
            WHERE email = %s
        """, (nova_data, email))

        conn.commit()

        log(email, "pagamento_aprovado")

        return True

    except Exception as e:
        print("ERRO ATIVAR:", e)
        return False

    finally:
        if conn:
            conn.close()
