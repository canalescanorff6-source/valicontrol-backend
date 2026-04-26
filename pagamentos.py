from fastapi import Request
from auth import ativar_usuario  # 🔥 IMPORTANTE
import mercadopago
import os

MP_TOKEN = os.getenv("MP_TOKEN")

if not MP_TOKEN:
    print("❌ MP_TOKEN NÃO CONFIGURADO")

sdk = mercadopago.SDK(MP_TOKEN)


@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        print("🔥 WEBHOOK RECEBIDO:", data)

        # ignora eventos que não são pagamento
        if data.get("type") != "payment":
            return {"ok": True}

        payment_id = data.get("data", {}).get("id")

        if not payment_id:
            print("⚠️ payment_id não encontrado")
            return {"ok": True}

        print("🔎 BUSCANDO PAGAMENTO:", payment_id)

        payment = sdk.payment().get(payment_id)
        response = payment.get("response", {})

        if not response:
            print("❌ erro ao buscar pagamento")
            return {"ok": False}

        status = response.get("status")
        email = response.get("payer", {}).get("email")

        print("📊 STATUS:", status)
        print("📧 EMAIL:", email)

        if status == "approved" and email:
            print("✅ PAGAMENTO APROVADO → ATIVANDO")
            ativar_usuario(email)

        return {"ok": True}

    except Exception as e:
        print("💥 ERRO WEBHOOK:", e)
        return {"ok": False}