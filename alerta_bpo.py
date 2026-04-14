import requests
import os
from datetime import datetime, timedelta
import pytz
from flask import Flask

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
METABASE_URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.json"
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")
FUSO = pytz.timezone('America/Sao_Paulo')

@app.route('/')
def home():
    enviados = executar_bot()
    return f"Status: OK | Enviados: {enviados} | Hora Br: {datetime.now(FUSO).strftime('%H:%M:%S')}", 200

def executar_bot():
    try:
        res = requests.get(METABASE_URL, timeout=30)
        res.raise_for_status()
        dados = res.json()

        # 🔥 Ordena do mais novo pro mais antigo
        dados = sorted(dados, key=lambda x: x.get('data_ajuste', ''), reverse=True)

        contagem = 0
        agora_br = datetime.now(FUSO)

        # 🔥 Janela segura (15 minutos)
        limite_br = agora_br - timedelta(minutes=15)

        ids_processados = set()

        for linha in dados:
            data_str = linha.get('data_ajuste')
            pedido_id = linha.get('order_number')

            if not data_str or not pedido_id:
                continue

            try:
                # ✅ NÃO usa timezone aqui (já está em BR)
                data_obj_br = datetime.strptime(data_str[:19], "%Y-%m-%dT%H:%M:%S")
            except Exception as e:
                print(f"Erro ao converter data: {e}")
                continue

            # 🔥 Filtro de tempo
            if data_obj_br > limite_br:

                # ✅ ID único (evita duplicidade)
                id_unico = f"{pedido_id}_{data_str}"

                if id_unico not in ids_processados:
                    enviar_slack(linha)
                    ids_processados.add(id_unico)
                    contagem += 1

            else:
                # 🚀 Para o loop (já ordenado)
                break

        print(f"Total enviados: {contagem}")
        return contagem

    except Exception as e:
        print(f"Erro no bot: {e}")
        return 0

def enviar_slack(item):
    try:
        status = str(item.get('status_alerta', 'OK')).upper()

        header = "*ATENÇÃO: MONITORAMENTO DE AJUSTE CRÍTICO*" if 'CRIT' in status else "*RELATÓRIO DE AJUSTE DE PEDIDO*"

        msg = {
            "text": (
                f"{header}\n"
                f"--------------------------------------------------\n"
                f"*Status:* {status}\n"
                f"*Pedido:* `{item.get('order_number')}`\n"
                f"*Produto:* {item.get('product')}\n"
                f"*Preço Original:* R$ {item.get('preco_original')}\n"
                f"*Valor Ajuste:* R$ {item.get('valor_ajuste')}\n"
                f"*Responsável:* {item.get('analista')}\n"
                f"*Data:* {item.get('data_ajuste')}\n"
                f"--------------------------------------------------"
            )
        }

        response = requests.post(SLACK_WEBHOOK, json=msg, timeout=10)

        if response.status_code != 200:
            print(f"Erro Slack: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Erro ao enviar Slack: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
