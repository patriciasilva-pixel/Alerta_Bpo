import requests
import os
import csv
from datetime import datetime

# --- CONFIGURAÇÕES ---
# Certifique-se de que esta URL é o link público JSON do novo SQL
METABASE_PUBLIC_URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.csv" 
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK")
CSV_FILE = 'enviados.csv'

def carregar_enviados():
    if not os.path.exists(CSV_FILE):
        return []
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        return [linha.strip() for linha in f.readlines()]

def registrar_envio(pedido_id):
    # Formato exato do seu CSV: ID_DATA HORA
    agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    entrada = f"{pedido_id}_{agora}"
    with open(CSV_FILE, mode='a', encoding='utf-8') as f:
        # Garante que comece em uma linha nova
        f.write(f"\n{entrada}")

def ja_enviado_hoje(pedido_id, lista_enviados):
    hoje = datetime.now().strftime('%d/%m/%Y')
    for item in lista_enviados:
        # Verifica se o ID do pedido aparece na mesma linha que a data de hoje
        if str(pedido_id) in item and hoje in item:
            return True
    return False

def main():
    enviados = carregar_enviados()
    
    try:
        response = requests.get(METABASE_PUBLIC_URL)
        response.raise_for_status()
        dados = response.json()
    except Exception as e:
        print(f"Erro ao acessar Metabase: {e}")
        return

    for row in dados:
        # Mapeamento conforme as novas colunas do SQL
        pedido_id = str(row.get('order_number'))
        status_regra = str(row.get('status_alerta', 'OK')).upper()
        
        if not pedido_id or pedido_id == 'None':
            continue

        if not ja_enviado_hoje(pedido_id, enviados):
            # --- FORMATAÇÃO VISUAL BONITA ---
            if status_regra == 'CRÍTICO' or status_regra == 'CRITICO':
                emoji_titulo = "🚨 *ALERTA CRÍTICO: AJUSTE ALTO* 🚨"
                cor_emoji = "🔴"
            else:
                emoji_titulo = "✅ *ALERTA: AJUSTE IDENTIFICADO* ✅"
                cor_emoji = "🟢"

            # Formata a data para ficar legível (vem do Metabase como ISO string)
            data_raw = row.get('data_ajuste', 'N/A')
            try:
                # Tenta converter a data caso venha em formato esquisito
                data_formatada = data_raw.split('.')[0].replace('T', ' ')
            except:
                data_formatada = data_raw

            msg_slack = {
                "text": (
                    f"{emoji_titulo}\n\n"
                    f"{cor_emoji} *Status:* {status_regra}\n"
                    f"📦 *Pedido:* `{pedido_id}`\n"
                    f"🛒 *Produto:* {row.get('product', 'N/A')}\n"
                    f"👤 *Analista:* {row.get('analista', 'N/A')}\n"
                    f"📧 *Email:* {row.get('email', 'N/A')}\n"
                    f"📊 *Ajuste:* `{row.get('perc_ajuste', 0)}%` (R$ {row.get('valor_ajuste', 0)})\n"
                    f"🕒 *Data:* {data_formatada}\n"
                    f"__________________________________________"
                )
            }
            
            res = requests.post(SLACK_WEBHOOK_URL, json=msg_slack)
            
            if res.status_code == 200:
                registrar_envio(pedido_id)
                print(f"✅ Sucesso: Pedido {pedido_id}")
            else:
                print(f"❌ Erro Slack ({res.status_code}): {res.text}")
        else:
            print(f"⏭️ Pedido {pedido_id} já enviado hoje.")

if __name__ == "__main__":
    main()
