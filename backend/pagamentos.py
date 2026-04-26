import mercadopago

sdk = mercadopago.SDK("APP_USR-7644007864092484-042523-6627b8e270268c808eee183961e284e4-3361329264")

def criar_pix(email):
    payment_data = {
        "transaction_amount": 29.90,
        "description": "Plano ValiControl",
        "payment_method_id": "pix",
        "payer": {
            "email": email
        }
    }

    payment = sdk.payment().create(payment_data)

    return {
        "qr": payment["response"]["point_of_interaction"]["transaction_data"]["qr_code"],
        "id": payment["response"]["id"]
    }