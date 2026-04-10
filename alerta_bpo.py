import requests
import os
from datetime import datetime

# --- CONFIGURAÇÕES ---
# ⚠️ COLE AQUI O LINK QUE TERMINA EM .json
METABASE_PUBLIC_URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708" 
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK")
CSV_FILE = 'enviados.csv'

def carregar_enviados():
    if not os.path.exists(CSV_FILE): return []
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        return [linha.strip() for linha in f.readlines()]

def registrar_envio(pedido_id):
    agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    with open(CSV_FILE, mode='a', encoding='utf-8') as f:
        f.write(f"\n{pedido_id}_{agora}")

def main():
    enviados = carregar_enviados()
    print("Iniciando busca no Metabase...")
    
    try:
        res = requests.get(METABASE_PUBLIC_URL)
        dados = res.json()
        print(f"Dados recebidos: {len(dados)} linhas encontradas.")
    except Exception as e:
        print(f"Erro ao acessar link: {e}")
        return

    for row in dados:
        # Pega qualquer ID que encontrar
        pedido_id = row.get('order_number') or row.get('id_pedido') or row.get('ORDER_NUMBER')
        
        if not pedido_id:
            print("Linha sem ID encontrada no JSON.")
            continue

        # Verifica apenas se já foi enviado hoje (comparando com o CSV vazio)
        hoje = datetime.now().strftime('%d/%m/%Y')
        ja_foi = any(str(pedido_id) in registro and hoje in registro for registro in enviados)

        if not ja_foi:
            msg = {
                "text": (
                    f"🚀 *TESTE DE ENVIO*\n"
                    f"*Pedido:* {pedido_id}\n"
                    f"*Produto:* {row.get('product', 'N/A')}\n"
                    f"*Analista:* {row.get('email', row.get('modified_by', 'N/A'))}\n"
                    f"---"
                )
            }
            requests.post(SLACK_WEBHOOK_URL, json=msg)
            registrar_envio(pedido_id)
            print(f"Pedido {pedido_id} enviado para o Slack!")
        else:
            print(f"Pedido {pedido_id} já está no histórico de hoje.")

if __name__ == "__main__":
    main()
