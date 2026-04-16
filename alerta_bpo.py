import requests
import os
from datetime import datetime, timedelta
import pytz
from flask import Flask

app = Flask(__name__)

# CONFIGURAÇÕES
METABASE_URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.json"
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")
FUSO = pytz.timezone('America/Sao_Paulo')
ARQUIVO_CACHE = "/app/cache_ids.txt"

# ===== GESTÃO DE CACHE (Para evitar duplicados) =====
def carregar_cache():
    if not os.path.exists(ARQUIVO_CACHE):
        return {}
    cache = {}
    if os.path.exists(ARQUIVO_CACHE):
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

# ===== ROTA DO FLASK =====
@app.route('/')
def home():
    enviados = executar_bot()
    return f"OK | enviados: {enviados} | hora: {datetime.now(FUSO).strftime('%H:%M:%S')}"

# ===== LÓGICA DO ROBÔ =====
def executar_bot():
    try:
        res = requests.get(METABASE_URL, timeout=30)
        dados = res.json()

        # Ordena do mais antigo para o mais novo
        dados = sorted(dados, key=lambda x: x.get('data_ajuste', ''))

        agora = datetime.now(FUSO)
        limite = agora - timedelta(minutes=60)

        cache = carregar_cache()
        cache = limpar_cache(cache)

        enviados = 0

        for linha in dados:
            data_str = linha.get('data_ajuste')
            pedido = linha.get('order_number')
            valor_ajuste = linha.get('valor_ajuste')
            status_alerta = linha.get('status_alerta', 'OK')

            if not data_str or not pedido:
                continue

            try:
                data_crua = datetime.strptime(data_str[:19], "%Y-%m-%dT%H:%M:%S")
                data_obj = FUSO.localize(data_crua)
            except:
                continue

            if data_obj < limite:
                continue

            id_unico = f"{pedido}_{valor_ajuste}_{status_alerta}"

            if id_unico in cache:
                continue

            enviar_slack(linha)

            cache[id_unico] = agora
            enviados += 1

        salvar_cache(cache)
        return enviados

    except Exception as e:
        print("Erro no bot:", e)
        return 0

# ===== ENVIO PARA O SLACK =====
def enviar_slack(item):
    status = str(item.get('status_alerta', 'OK')).upper()
    
    # Preço Original
    v_original = item.get('preco_original', '0.0')
    
    # Tratamento do Valor de Ajuste com o traço --
    try:
        v_ajuste_num = float(item.get('valor_ajuste', 0))
    except:
        v_ajuste_num = 0

    if v_ajuste_num > 0:
        texto_ajuste = f"R$ {v_ajuste_num}"
    else:
        # Aqui o ajuste solicitado: apenas o traço
        texto_ajuste = "--"

    # Montagem da Mensagem
    mensagem = (
        "*📊 Ajuste de Pedido*\n"
        "──────────────────────────────\n"
        f"*Pedido:* `{item.get('order_number')}`\n"
        f"*Produto:* {item.get('product')}\n"
        f"*Preço Original:* R$ {v_original}\n"
        f"*Valor Ajuste:* {texto_ajuste}\n"
        f"*Status:* {status}\n"
        f"*Responsável:* {item.get('analista')}\n"
        f"*Data:* {item.get('data_ajuste')}\n"
        "──────────────────────────────"
    )

    payload = {"text": mensagem}
    
    if status == 'CRÍTICO':
        payload = {
            "text": f"🚨 *ALERTA CRÍTICO: {item.get('order_number')}*",
            "attachments": [
                {
                    "color": "#FF0000",
                    "text": mensagem
                }
            ]
        }

    requests.post(SLACK_WEBHOOK, json=payload)

# ===== INICIALIZAÇÃO =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
