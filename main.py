# backend/main.py

from fastapi import FastAPI, Request
from pydantic import BaseModel
from database import init_db, conectar
from auth import login_user, register_user, ativar_usuario
from pagamentos import criar_pix
import mercadopago
import os

app = FastAPI()

sdk = mercadopago.SDK(os.getenv("MP_TOKEN"))

# =========================
# MODELS
# =========================

class UserAuth(BaseModel):
    email: str
    senha: str
    device_id: str | None = None


class Produto(BaseModel):
    codigo: str
    nome: str
    validade: str
    quantidade: int
    email: str


class EmailRequest(BaseModel):
    email: str


# =========================
# STARTUP
# =========================

@app.on_event("startup")
def startup():
    init_db()


# =========================
# LOGIN
# =========================

@app.post("/login")
def login(data: UserAuth):
    return login_user(data.email, data.senha)


# =========================
# REGISTER
# =========================

@app.post("/register")
def register(data: UserAuth):
    return register_user(data.email, data.senha, data.device_id)


# =========================
# PAGAMENTO
# =========================

@app.post("/pagar")
def pagar(data: EmailRequest):
    return criar_pix(data.email)


# =========================
# PRODUTOS
# =========================

@app.post("/produtos")
def adicionar_produto(p: Produto):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO produtos (codigo, nome, validade, quantidade, user_email)
        VALUES (%s, %s, %s, %s, %s)
    """, (p.codigo, p.nome, p.validade, p.quantidade, p.email))

    conn.commit()
    conn.close()

    return {"status": "ok"}


@app.get("/produtos")
def listar_produtos(email: str):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, codigo, nome, validade, quantidade
        FROM produtos
        WHERE user_email=%s
    """, (email,))

    dados = cursor.fetchall()
    conn.close()

    return dados


@app.put("/produtos/{id}")
def atualizar_produto(id: int, p: Produto):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE produtos
        SET codigo=%s, nome=%s, validade=%s, quantidade=%s
        WHERE id=%s
    """, (p.codigo, p.nome, p.validade, p.quantidade, id))

    conn.commit()
    conn.close()

    return {"status": "ok"}


@app.delete("/produtos/{id}")
def excluir_produto(id: int):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM produtos WHERE id=%s", (id,))
    conn.commit()
    conn.close()

    return {"status": "ok"}


# =========================
# WEBHOOK
# =========================

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    payment_id = data.get("data", {}).get("id")

    if not payment_id:
        return {"ok": True}

    payment = sdk.payment().get(payment_id)
    response = payment.get("response", {})

    if response.get("status") == "approved":
        email = response.get("payer", {}).get("email")
        if email:
            ativar_usuario(email)

    return {"ok": True}


@app.get("/")
def home():
    return {"status": "API ONLINE"}