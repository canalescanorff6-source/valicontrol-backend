from fastapi import Request
import mercadopago
import os

sdk = mercadopago.SDK(os.getenv("MP_TOKEN"))

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        print("WEBHOOK:", data)

        if data.get("type") != "payment":
            return {"ok": True}

        payment_id = data["data"]["id"]

        payment = sdk.payment().get(payment_id)
        response = payment.get("response", {})

        if not response:
            print("Erro ao buscar pagamento")
            return {"ok": False}

        status = response.get("status")

        print("STATUS PAGAMENTO:", status)

        if status == "approved":
            email = response["payer"]["email"]

            print("ATIVANDO USUÁRIO:", email)
            ativar_usuario(email)

        return {"ok": True}

    except Exception as e:
        print("ERRO WEBHOOK:", e)
        return {"ok": False}