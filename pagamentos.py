from fastapi import Request
from auth import ativar_usuario  # 🔥 IMPORTANTE
import mercadopago
import os

sdk = mercadopago.SDK(os.getenv("MP_TOKEN"))

def criar_pix(email):
    try:
        payment_data = {
            "transaction_amount": 29.90,
            "description": "Plano ValiControl",
            "payment_method_id": "pix",
            "payer": {
                "email": email
            }
        }

        payment = sdk.payment().create(payment_data)
        response = payment.get("response", {})

        if not response:
            return {"erro": "Erro ao criar pagamento"}

        return {
            "qr": response["point_of_interaction"]["transaction_data"]["qr_code"],
            "qr_base64": response["point_of_interaction"]["transaction_data"]["qr_code_base64"],
            "payment_id": response["id"],
            "status": response["status"]
        }

    except Exception as e:
        print("💥 ERRO PIX:", e)
        return {"erro": str(e)}