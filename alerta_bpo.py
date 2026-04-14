import requests
import os
from datetime import datetime, timedelta
import pytz
from flask import Flask

app = Flask(__name__)

# CONFIG
METABASE_URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.json"
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")
FUSO = pytz.timezone('America/Sao_Paulo')

ARQUIVO_CACHE = "/app/cache_ids.txt"

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
        dados = res.json()

        # Ordena do mais novo para o mais antigo
        dados = sorted(dados, key=lambda x: x.get('data_ajuste', ''), reverse=True)

        agora = datetime.now(FUSO)
        limite = agora - timedelta(minutes=60) # Janela de 15 min para segurança

        cache = carregar_cache()
        cache = limpar_cache(cache)

        enviados = 0

        for linha in dados:
            data_str = linha.get('data_ajuste')
            pedido = linha.get('order_number')

            if not data_str or not pedido:
                continue

            try:
                data_crua = datetime.strptime(data_str[:19], "%Y-%m-%dT%H:%M:%S")
                data_obj = FUSO.localize(data_crua)
            except:
                continue

            if data_obj < limite:
                break

            # 🔥 SOLUÇÃO PARA DUPLICADOS:
            # Usamos apenas o número do pedido como ID. 
            # Se o pedido já foi enviado nas últimas 2h, ele não repete.
            id_unico = str(pedido)

            if id_unico in cache:
                continue

            enviar_slack(linha)

            cache[id_unico] = agora
            enviados += 1

        salvar_cache(cache)
        return enviados

    except Exception as e:
        print("Erro:", e)
        return 0

# ===== SLACK =====
def enviar_slack(item):
    status = str(item.get('status_alerta', 'OK')).upper()

    mensagem = (
        "*📊 Ajuste de Pedido*\n"
        "──────────────────────────────\n"
        f"*Pedido:* `{item.get('order_number')}`\n"
        f"*Produto:* {item.get('product')}\n"
        f"*Valor Ajuste:* R$ {item.get('valor_ajuste')}\n"
        f"*Status:* {status}\n"
        f"*Responsável:* {item.get('analista')}\n"
        f"*Data:* {item.get('data_ajuste')}\n"
        "──────────────────────────────"
    )

    requests.post(SLACK_WEBHOOK, json={"text": mensagem})

# ===== START =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
