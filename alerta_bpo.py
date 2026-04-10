import requests
import os
from datetime import datetime

# --- CONFIGURAÇÕES ---
# Adicionei o .json no final do seu link para o robô conseguir ler os dados
METABASE_PUBLIC_URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.json" 
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK")
CSV_FILE = 'enviados.csv'

def carregar_enviados():
    """Lê o arquivo de histórico"""
    if not os.path.exists(CSV_FILE):
        return []
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        return [linha.strip() for linha in f.readlines()]

def registrar_envio(pedido_id):
    """Salva o ID e a Data para não repetir"""
    hoje = datetime.now().strftime('%d/%m/%Y')
    entrada = f"{pedido_id}_{hoje}"
    with open(CSV_FILE, mode='a', encoding='utf-8') as f:
        f.write(f"\n{entrada}")

def main():
    print("🚀 Iniciando verificação de novos ajustes...")
    enviados = carregar_enviados()
    
    try:
        # Busca os dados no Metabase
        response = requests.get(METABASE_PUBLIC_URL)
        response.raise_for_status()
        dados = response.json()
        print(f"📊 Metabase retornou {len(dados)} registros.")
    except Exception as e:
        print(f"❌ Erro ao acessar Metabase: {e}")
        return

    for row in dados:
        # Mapeamento exato das colunas do seu SQL
        pedido_id = str(row.get('order_number'))
        status_regra = str(row.get('status_alerta', 'OK')).upper()
        hoje = datetime.now().strftime('%d/%m/%Y')
        
        if not pedido_id or pedido_id == 'None':
            continue

        # Verifica se o Pedido + Data de Hoje já estão no CSV
        identificador = f"{pedido_id}_{hoje}"
        
        if identificador not in enviados:
            # --- DEFINIÇÃO DO VISUAL ---
            if 'CRÍTICO' in status_regra or 'CRITICO' in status_regra:
                titulo = "🚨 *ALERTA CRÍTICO: AJUSTE ALTO DETECTADO* 🚨"
                cor_emoji = "🔴"
            else:
                titulo = "✅ *ALERTA: AJUSTE IDENTIFICADO* ✅"
                cor_emoji = "🟢"

            # Montagem da Mensagem para o Slack
            msg_slack = {
                "text": (
                    f"{titulo}\n\n"
                    f"{cor_emoji} *Status:* {status_regra}\n"
                    f"📦 *Pedido:* `{pedido_id}`\n"
                    f"🛒 *Produto:* {row.get('product', 'N/A')}\n"
                    f"👤 *Analista:* {row.get('analista', 'N/A')}\n"
                    f"📊 *Ajuste:* `{row.get('perc_ajuste', 0)}%` (R$ {row.get('valor_ajuste', 0)})\n"
                    f"🕒 *Data:* {row.get('data_ajuste', 'N/A')}\n"
                    f"__________________________________________"
                )
            }
            
            # Envio para o Slack
            res = requests.post(SLACK_WEBHOOK_URL, json=msg_slack)
            
            if res.status_code == 200:
                registrar_envio(pedido_id)
                print(f"✅ Alerta enviado para o pedido: {pedido_id}")
            else:
                print(f"❌ Erro ao enviar para o Slack: {res.status_code}")
        else:
            print(f"⏭️ Pedido {pedido_id} já enviado hoje. Pulando...")

if __name__ == "__main__":
    main()
