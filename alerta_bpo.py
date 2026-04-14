import requests
import os
from datetime import datetime, timedelta
import pytz
from flask import Flask

app = Flask(__name__)

# ===== CONFIG =====
METABASE_URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.json"
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")
FUSO = pytz.timezone('America/Sao_Paulo')

ARQUIVO_CACHE = "cache_ids.txt"

# ===== CACHE =====
def carregar_cache():
    if not os.path.exists(ARQUIVO_CACHE):
        return {}

    cache = {}
    with open(ARQUIVO_CACHE, "r") as f:
        for linha in f:
            try:
                id_, ts = linha.strip().split("|")
                cache[id_] = datetime.fromisoformat(ts)
            except:
                continue
    return cache

def salvar_cache(cache):
    with open(ARQUIVO_CACHE, "w") as f:
        for k, v in cache.items():
            f.write(f"{k}|{v.isoformat()}\n")

def limpar_cache(cache):
    agora = datetime.now(FUSO)
    limite = agora - timedelta(hours=2)
    return {k: v for k, v in cache.items() if v > limite}

# ===== ROUTE =====
@app.route('/')
def home():
    enviados = executar_bot()
    return f"OK | enviados: {enviados} | hora: {datetime.now(FUSO).strftime('%H:%M:%S')}"

# ===== BOT =====
def executar_bot():
    try:
        res = requests.get(METABASE_URL, timeout=30)
        res.raise_for_status()
        dados = res.json()

        # 🔥 ordenar do mais novo para o mais antigo
        dados = sorted(dados, key=lambda x: x.get('data_ajuste', ''), reverse=True)

        agora = datetime.now(FUSO)
        limite = agora - timedelta(minutes=15)

        cache = carregar_cache()
        cache = limpar_cache(cache)

        enviados = 0

        for linha in dados:
            data_str = linha.get('data_ajuste')
            pedido = linha.get('order_number')

            if not data_str or not pedido:
                continue

            try:
                # ✅ NÃO usa timezone (já vem em horário BR)
                data_obj = datetime.strptime(data_str[:19], "%Y-%m-%dT%H:%M:%S")
            except:
                continue

            if data_obj < limite:
                break

            id_unico = f"{pedido}_{data_str}"

            if id_unico in cache:
                continue

            enviar_slack(linha)

            cache[id_unico] = datetime.now(FUSO)
            enviados += 1

        salvar_cache(cache)

        print(f"Enviados nesta execução: {enviados}")
        return enviados

    except Exception as e:
        print("Erro no bot:", e)
        return 0

# ===== SLACK =====
def enviar_slack(item):
    try:
        status = str(item.get('status_alerta', 'OK')).upper()

        header = "*ATENÇÃO: AJUSTE CRÍTICO*" if "CRIT" in status else "*AJUSTE DE PEDIDO*"

        msg = {
            "text": (
                f"{header}\n"
                f"----------------------------------\n"
                f"*Pedido:* {item.get('order_number')}\n"
                f"*Produto:* {item.get('product')}\n"
                f"*Ajuste:* R$ {item.get('valor_ajuste')}\n"
                f"*Status:* {status}\n"
                f"*Responsável:* {item.get('analista')}\n"
                f"*Data:* {item.get('data_ajuste')}\n"
                f"----------------------------------"
            )
        }

        response = requests.post(SLACK_WEBHOOK, json=msg, timeout=10)

        if response.status_code != 200:
            print("Erro Slack:", response.status_code, response.text)

    except Exception as e:
        print("Erro ao enviar Slack:", e)

# ===== START =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
