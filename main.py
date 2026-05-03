from fastapi import FastAPI, Header, Request
from pydantic import BaseModel
from datetime import datetime
from database import conectar, init_db
from auth import login_user, register_user, ativar_usuario, calcular_dias_restantes
from pagamentos import criar_pagamento

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
def register(data: UserAuth, request: Request):
    ip = request.client.host
    return register_user(data.email, data.senha, data.device_id, ip)


# =========================
# 💳 PAGAMENTO
# =========================
@app.post("/pagamento")
def pagamento(data: UserAuth):
    return criar_pagamento(data.email)


@app.get("/pagar")
def pagar(email: str = None, token: str = Header(None)):
    if token:
        email = get_email(token)

    if not email:
        return {"erro": "não autorizado"}

    data = criar_pagamento(email)

    if "erro" in data:
        return data

    return {
        "status": "ok",
        "qr": data.get("qr"),
        "qr_base64": data.get("qr_base64"),
        "payment_id": data.get("payment_id")
    }


# =========================
# 🔔 WEBHOOK
# =========================
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    try:
        evento = data.get("event")

        if evento in ["PAYMENT_RECEIVED", "PAYMENT_CONFIRMED"]:
            payment = data.get("payment", {})

            email = payment.get("externalReference")
            status = payment.get("status")

            if status in ["RECEIVED", "CONFIRMED"] and email:
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
# ➕ ADICIONAR (COM BLOQUEIO)
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
        # total atual
        cursor.execute("""
            SELECT COUNT(*) FROM produtos WHERE user_email=%s
        """, (email,))
        total = cursor.fetchone()[0]

        # status usuário
        cursor.execute("""
            SELECT ativo FROM users WHERE email=%s
        """, (email,))
        ativo = cursor.fetchone()[0]

        # limite
        limite = 999999 if ativo else 50

        # bloqueio
        if total >= limite:
            return {
                "erro": "limite atingido",
                "limite": limite,
                "total": total
            }

        # inserir
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
# ❌ EXCLUIR
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
# ✏️ ATUALIZAR
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
# 📊 STATS (COM USO + BLOQUEIO)
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

        limite = 999999 if ativo else 50

        uso = int((total / limite) * 100) if limite > 0 else 0
        bloqueado = total >= limite

        return {
            "total": total,
            "trial_restante": trial_restante,
            "limite": limite,
            "uso": uso,
            "bloqueado": bloqueado,
            "plano": "PRO" if ativo else "TRIAL"
        }

    finally:
        conn.close()


# =========================
# 🏠 HOME
# =========================
@app.get("/")
def home():
    return {"status": "API ONLINE"}


# =========================
# 🔄 UPDATE (AUTO UPDATE APP)
# =========================
@app.get("/version")
def version():
    return {
        "version": "1.0.1",
        "url": "link"
    }
