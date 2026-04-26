from fastapi import FastAPI, Request
from auth import login_user, register_user, ativar_usuario
from database import init_db
from pydantic import BaseModel
from pagamentos import criar_pix

import mercadopago
import os

app = FastAPI()

# =========================
# 🔑 MERCADO PAGO
# =========================
MP_TOKEN = os.getenv("MP_TOKEN")

if not MP_TOKEN:
    raise Exception("❌ MP_TOKEN não configurado no Render")

sdk = mercadopago.SDK("APP_USR-7644007864092484-042523-6627b8e270268c808eee183961e284e4-3361329264")


# =========================
# 📦 MODELS
# =========================
class UserAuth(BaseModel):
    email: str
    senha: str
    device_id: str | None = None


class EmailRequest(BaseModel):
    email: str


# =========================
# 🚀 STARTUP
# =========================
@app.on_event("startup")
def startup():
    init_db()
    print("🚀 Backend iniciado com sucesso")
    print("🔑 TOKEN MP:", MP_TOKEN[:10], "...")  # debug seguro


# =========================
# 🔑 LOGIN
# =========================
@app.post("/login")
def login(data: UserAuth):
    return login_user(data.email, data.senha)


# =========================
# 👤 REGISTER
# =========================
@app.post("/register")
def register(data: UserAuth):
    return register_user(
        data.email,
        data.senha,
        data.device_id
    )


# =========================
# 💳 GERAR PIX REAL
# =========================
@app.post("/pagar")
def pagar(data: EmailRequest):
    try:
        print("🔥 GERANDO PIX PARA:", data.email)

        result = criar_pix(data.email)

        print("📦 RESPOSTA PIX:", result)

        return result

    except Exception as e:
        print("💥 ERRO NO ENDPOINT /pagar:", e)
        return {"erro": "Falha interna ao gerar pagamento"}


# =========================
# 🔥 WEBHOOK MERCADO PAGO
# =========================
@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        print("🔥 WEBHOOK RECEBIDO:", data)

        if "data" not in data or "id" not in data["data"]:
            print("⚠️ Webhook ignorado")
            return {"ok": True}

        payment_id = data["data"]["id"]

        print("🔎 BUSCANDO PAGAMENTO:", payment_id)

        payment = sdk.payment().get(payment_id)
        response = payment.get("response", {})

        if not response:
            print("❌ Erro ao buscar pagamento")
            return {"ok": False}

        status = response.get("status")
        email = response.get("payer", {}).get("email")

        print("📊 STATUS:", status)
        print("📧 EMAIL:", email)

        if status == "approved" and email:
            print("✅ PAGAMENTO APROVADO — ATIVANDO USUÁRIO")
            ativar_usuario(email)

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