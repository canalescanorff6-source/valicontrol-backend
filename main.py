from fastapi import FastAPI, Header, Request
from pydantic import BaseModel
from datetime import datetime
from database import conectar, init_db
from auth import login_user, register_user, ativar_usuario, calcular_dias_restantes
from pagamentos import criar_pagamento, sdk

app = FastAPI()

# =========================
# 📦 MODELS
# =========================
class UserAuth(BaseModel):
    email: str
    senha: str
    device_id: str


class Produto(BaseModel):
    codigo: str
    nome: str
    validade: str
    quantidade: int
    tipo_qtd: str


# =========================
# 🚀 START
# =========================
@app.on_event("startup")
def startup():
    init_db()
    print("🚀 API ONLINE")


# =========================
# 🔐 TOKEN
# =========================
def get_email(token):
    if not token:
        return None

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT email FROM users WHERE token=%s", (token,))
        user = cursor.fetchone()
        return user[0] if user else None
    finally:
        conn.close()


# =========================
# 🔐 LOGIN / REGISTER
# =========================
@app.post("/login")
def login(data: UserAuth):
    return login_user(data.email, data.senha, data.device_id)


@app.post("/register")
def register(data: UserAuth):
    return register_user(data.email, data.senha, data.device_id)


# =========================
# 💳 PAGAMENTO
# =========================
@app.post("/pagamento")
def pagamento(data: UserAuth):
    return criar_pagamento(data.email)


# =========================
# 🔔 WEBHOOK (CORRIGIDO)
# =========================
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    if not sdk:
        return {"ok": False}

    try:
        if data.get("type") == "payment":
            payment_id = data["data"]["id"]

            payment = sdk.payment().get(payment_id)
            res = payment.get("response", {})

            status = res.get("status")
            email = res.get("external_reference")

            if status == "approved" and email:
                ativar_usuario(email)

    except Exception as e:
        print("ERRO WEBHOOK:", e)

    return {"ok": True}


# =========================
# 📦 LISTAR
# =========================
@app.get("/produtos")
def listar(token: str = Header(None)):
    email = get_email(token)

    if not email:
        return {"erro": "token inválido"}

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, codigo, nome, validade, quantidade, tipo_qtd
            FROM produtos WHERE user_email=%s
        """, (email,))
        return cursor.fetchall()
    finally:
        conn.close()


# =========================
# ➕ ADICIONAR
# =========================
@app.post("/produtos")
def adicionar(data: Produto, token: str = Header(None)):
    email = get_email(token)

    if not email:
        return {"erro": "não autorizado"}

    try:
        datetime.strptime(data.validade, "%Y-%m-%d")
    except:
        return {"erro": "data inválida"}

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO produtos 
            (codigo, nome, validade, quantidade, tipo_qtd, user_email)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data.codigo,
            data.nome,
            data.validade,
            data.quantidade,
            data.tipo_qtd,
            email
        ))

        conn.commit()
        return {"ok": True}

    except Exception as e:
        print("ERRO INSERT:", e)
        return {"erro": "erro ao salvar produto"}

    finally:
        conn.close()


# =========================
# ❌ EXCLUIR (MELHORADO)
# =========================
@app.delete("/produtos/{id}")
def excluir(id: int, token: str = Header(None)):
    email = get_email(token)

    if not email:
        return {"erro": "não autorizado"}

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            DELETE FROM produtos WHERE id=%s AND user_email=%s
        """, (id, email))

        if cursor.rowcount == 0:
            return {"erro": "produto não encontrado"}

        conn.commit()
        return {"ok": True}

    finally:
        conn.close()


# =========================
# ✏️ ATUALIZAR (CORRIGIDO)
# =========================
@app.put("/produtos/{id}")
def atualizar_produto(id: int, data: Produto, token: str = Header(None)):
    email = get_email(token)

    if not email:
        return {"erro": "não autorizado"}

    try:
        datetime.strptime(data.validade, "%Y-%m-%d")
    except:
        return {"erro": "data inválida"}

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE produtos
            SET codigo=%s,
                nome=%s,
                validade=%s,
                quantidade=%s,
                tipo_qtd=%s
            WHERE id=%s AND user_email=%s
        """, (
            data.codigo,
            data.nome,
            data.validade,
            data.quantidade,
            data.tipo_qtd,
            id,
            email
        ))

        if cursor.rowcount == 0:
            return {"erro": "produto não encontrado"}

        conn.commit()
        return {"ok": True}

    except Exception as e:
        print("ERRO UPDATE:", e)
        return {"erro": "erro ao atualizar produto"}

    finally:
        conn.close()


# =========================
# 📊 STATS
# =========================
@app.get("/stats")
def stats(token: str = Header(None)):
    email = get_email(token)

    if not email:
        return {"erro": "não autorizado"}

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COUNT(*) FROM produtos WHERE user_email=%s
        """, (email,))
        total = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT trial_expira_em, ativo FROM users WHERE email=%s
        """, (email,))
        user = cursor.fetchone()

        trial_restante = 0
        ativo = 0

        if user:
            trial_expira_em, ativo = user
            trial_restante = calcular_dias_restantes(trial_expira_em)

        limite = 100 if ativo else 50

        return {
            "total": total,
            "trial_restante": trial_restante,
            "limite": limite,
            "plano": "PRO" if ativo else "TRIAL"
        }

    finally:
        conn.close()


@app.get("/")
def home():
    return {"status": "API ONLINE"}
