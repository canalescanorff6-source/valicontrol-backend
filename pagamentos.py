from fastapi import Request
from auth import ativar_usuario  # 🔥 IMPORTANTE
import mercadopago
import os

try:
    import mercadopago

    MP_TOKEN = os.getenv("MP_TOKEN")
    sdk = mercadopago.SDK(MP_TOKEN) if MP_TOKEN else None

except Exception as e:
    print("⚠️ MercadoPago erro:", e)
    sdk = None


def criar_pagamento(email):
    if not sdk:
        return {"erro": "Pagamento indisponível"}

    try:
        payment = sdk.payment().create({
            "transaction_amount": 10,
            "description": "Plano ValiControl",
            "payment_method_id": "pix",
            "payer": {"email": email}
        })

        response = payment.get("response", {})
        poi = response.get("point_of_interaction", {})
        transaction = poi.get("transaction_data", {})

        return {
            "qr": transaction.get("qr_code"),
            "qr_base64": transaction.get("qr_code_base64"),
            "payment_id": response.get("id"),
            "status": response.get("status")
        }

    except Exception as e:
        print("ERRO PIX:", e)
        return {"erro": "falha pagamento"}
