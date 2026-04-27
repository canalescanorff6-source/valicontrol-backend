from fastapi import FastAPI, Request
from auth import login_user, register_user, ativar_usuario
from database import init_db, conectar
from pydantic import BaseModel
from pagamentos import criar_pix

import mercadopago
import os

app = FastAPI()

# =========================
# 🔑 MERCADO PAGO (SEGURO)
# =========================
MP_TOKEN = os.getenv("MP_TOKEN")

if not MP_TOKEN:
    raise Exception("❌ MP_TOKEN não configurado no Render")

sdk = mercadopago.SDK(MP_TOKEN)  # 🔥 CORRETO


# =========================
# 📦 MODELS
# =========================
class UserAuth(BaseModel):
    email: str
    senha: str
    device_id: str | None = None


class EmailRequest(BaseModel):
    email: str


class Produto(BaseModel):
    codigo: str
    nome: str
    validade: str
    quantidade: int
    email: str


# =========================
# 🚀 STARTUP
# =========================
@app.on_event("startup")
def startup():
    init_db()
    print("🚀 Backend iniciado com sucesso")


# =========================
# 🔑 LOGIN
# =========================
@app.post("/login")
def login(data: UserAuth):
    try:
        return login_user(data.email, data.senha)
    except Exception as e:
        print("💥 ERRO LOGIN:", e)
        return {"status": "erro", "msg": "Falha no login"}


# =========================
# 👤 REGISTER
# =========================
@app.post("/register")
def register(data: UserAuth):
    try:
        return register_user(
            data.email,
            data.senha,
            data.device_id
        )
    except Exception as e:
        print("💥 ERRO REGISTER:", e)
        return {"status": "erro", "msg": "Falha no cadastro"}


# =========================
# 💳 GERAR PIX
# =========================
@app.post("/pagar")
def pagar(data: EmailRequest):
    try:
        return criar_pix(data.email)
    except Exception as e:
        print("💥 ERRO PAGAMENTO:", e)
        return {"erro": "Falha ao gerar pagamento"}


# =========================
# 📦 PRODUTOS
# =========================
@app.get("/produtos")
def listar_produtos(email: str):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, codigo, nome, validade, quantidade
        FROM produtos
        WHERE user_email = %s
    """, (email,))

    dados = cursor.fetchall()

    conn.close()

    return dados


# =========================
# 🔥 WEBHOOK MERCADO PAGO
# =========================
@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        print("🔥 WEBHOOK:", data)

        payment_id = data.get("data", {}).get("id")
        if not payment_id:
            return {"ok": True}

        payment = sdk.payment().get(payment_id)
        response = payment.get("response", {})

        status = response.get("status")
        email = response.get("payer", {}).get("email")

        if status == "approved" and email:
            ativar_usuario(email)
            print("✅ Usuário ativado:", email)

        return {"ok": True}

    except Exception as e:
        print("💥 ERRO WEBHOOK:", e)
        return {"ok": False}


# =========================
# 🧪 TESTE
# =========================
@app.get("/")
def home():
    return {"status": "API ONLINE 🚀"}