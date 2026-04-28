from fastapi import FastAPI, Header, Request
from pydantic import BaseModel
from datetime import datetime
from database import conectar, init_db
from auth import login_user, register_user, ativar_usuario
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

    cursor.execute("SELECT email FROM users WHERE token=%s", (token,))
    user = cursor.fetchone()

    conn.close()
    return user[0] if user else None


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
# 🔔 WEBHOOK
# =========================
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

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
    except:
        # fallback caso coluna não exista ainda
        cursor.execute("""
            SELECT id, codigo, nome, validade, quantidade, '' as tipo_qtd
            FROM produtos WHERE user_email=%s
        """, (email,))

    dados = cursor.fetchall()
    conn.close()

    return dados


# =========================
# ➕ ADICIONAR (CORRIGIDO)
# =========================
@app.post("/produtos")
def adicionar(data: Produto, token: str = Header(None)):
    try:
        email = get_email(token)

        if not email:
            return {"erro": "não autorizado"}

        # 🔥 valida data (evita erro 500)
        try:
            datetime.strptime(data.validade, "%Y-%m-%d")
        except:
            return {"erro": "data inválida, use yyyy-MM-dd"}

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
        except Exception as db_error:
            print("ERRO DB:", db_error)
            return {"erro": "erro banco (provavelmente falta coluna tipo_qtd)"}

        conn.commit()
        conn.close()

        return {"ok": True}

    except Exception as e:
        print("ERRO INSERT:", e)
        return {"erro": "erro ao salvar produto"}


# =========================
# ❌ EXCLUIR
# =========================
@app.delete("/produtos/{id}")
def excluir(id: int, token: str = Header(None)):
    email = get_email(token)

    if not email:
        return {"erro": "não autorizado"}

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM produtos WHERE id=%s AND user_email=%s
    """, (id, email))

    conn.commit()
    conn.close()

    return {"ok": True}


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

    cursor.execute("SELECT COUNT(*) FROM produtos WHERE user_email=%s", (email,))
    total = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT COUNT(*) FROM produtos 
        WHERE user_email=%s AND validade < CURRENT_DATE
    """, (email,))
    vencidos = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT COUNT(*) FROM produtos 
        WHERE user_email=%s 
        AND validade BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
    """, (email,))
    proximos = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT trial_expira_em, ativo FROM users WHERE email=%s
    """, (email,))
    user = cursor.fetchone()

    trial_restante = 0
    ativo = 0

    if user:
        trial_expira, ativo = user
        if trial_expira:
            trial_restante = max(0, (trial_expira - datetime.now()).days)

    conn.close()

    return {
        "total": total,
        "vencidos": vencidos,
        "proximos": proximos,
        "trial_restante": trial_restante,
        "limite": 50,
        "plano": "PRO" if ativo else "TRIAL"
    }


@app.get("/")
def home():
    return {"status": "API ONLINE"}
