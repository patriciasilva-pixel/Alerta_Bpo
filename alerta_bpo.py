def enviar_slack(item):
    try:
        status = str(item.get('status_alerta', 'OK')).upper()

        titulo = "Ajuste de Pedido"
        if "CRIT" in status:
            titulo = "ALERTA CRÍTICO - Ajuste de Pedido"

        msg = {
            "text": (
                f"*{titulo}*\n"
                f"────────────────────────────\n"
                f"*Pedido:* `{item.get('order_number')}`\n"
                f"*Produto:* {item.get('product')}\n"
                f"*Valor do Ajuste:* R$ {item.get('valor_ajuste')}\n"
                f"*Status:* {status}\n"
                f"*Responsável:* {item.get('analista')}\n"
                f"*Data:* {item.get('data_ajuste')}\n"
            )
        }

        response = requests.post(SLACK_WEBHOOK, json=msg, timeout=10)

        if response.status_code != 200:
            print("Erro Slack:", response.status_code, response.text)

    except Exception as e:
        print("Erro ao enviar Slack:", e)
