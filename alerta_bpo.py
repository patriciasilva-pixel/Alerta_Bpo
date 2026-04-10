import requests
import os
from datetime import datetime

# --- CONFIGURAÇÕES ---
METABASE_PUBLIC_URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.json" 
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK")
CSV_FILE = 'enviados.csv'

def carregar_enviados():
    if not os.path.exists(CSV_FILE):
        return set()
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        # Carrega tudo em um set para busca instantânea
        return set(linha.strip() for linha in f.readlines() if linha.strip())

def registrar_envio(id_unico):
    with open(CSV_FILE, mode='a', encoding='utf-8') as f:
        f.write(f"{id_unico}\n")

def formatar_valor(valor, sufixo=""):
    try:
        # Se for zero, nulo ou string "0", retorna traço
        if valor is None or str(valor).strip() in ["", "0", "0.0", "0.00", "0.0%"]:
            return "-"
        
        num = float(valor)
        if num == 0:
            return "-"
            
        # Formatação profissional de moeda (Padrão BR)
        if sufixo == "R$ ":
            return f"R$ {num:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        return f"{num}{sufixo}"
    except:
        return "-"

def main():
    print("Iniciando verificação de ajustes...")
    enviados = carregar_enviados()
    
    try:
        response = requests.get(METABASE_PUBLIC_URL)
        response.raise_for_status()
        dados = response.json()
    except Exception as e:
        print(f"Erro ao acessar Metabase: {e}")
        return

    for row in dados:
        pedido_id = str(row.get('order_number'))
        data_raw = str(row.get('data_ajuste', ''))
        
        if not pedido_id or pedido_id == 'None':
            continue

        # --- CHAVE DE SEGURANÇA CONTRA DUPLICADOS ---
        # Criamos uma chave com o Pedido + Data + Hora (até os segundos)
        # Isso impede que o mesmo ajuste seja enviado duas vezes
        id_unico = f"{pedido_id}_{data_raw.split('.')[0]}"

        if id_unico not in enviados:
            status_regra = str(row.get('status_alerta', 'OK')).upper()
            
            # Tratamento da Data para exibição
            try:
                dt_obj = datetime.strptime(data_raw.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                data_exibicao = dt_obj.strftime('%d/%m/%Y %H:%M')
            except:
                data_exibicao = data_raw.replace('T', ' ').split('.')[0]

            # Cabeçalho baseado no status
            if 'CRÍTICO' in status_regra or 'CRITICO' in status_regra:
                header = "*ALERTA DE AJUSTE CRÍTICO*"
                status_txt = "CRÍTICO"
            else:
                header = "*NOTIFICAÇÃO DE AJUSTE DE PEDIDO*"
                status_txt = "OK"

            msg_slack = {
                "text": (
                    f"{header}\n"
                    f"──────────────────────────────\n"
                    f"*Status:* {status_txt}\n"
                    f"*ID do Pedido:* {pedido_id}\n"
                    f"*Produto:* {row.get('product', 'N/A')}\n"
                    f"*Analista Responsável:* {row.get('analista', 'N/A')}\n"
                    f"*Percentual de Ajuste:* {formatar_valor(row.get('perc_ajuste'), '%')}\n"
                    f"*Valor do Ajuste:* {formatar_valor(row.get('valor_ajuste'), 'R$ ')}\n"
                    f"*Data do Evento:* {data_exibicao}\n"
                    f"──────────────────────────────"
                )
            }
            
            res = requests.post(SLACK_WEBHOOK_URL, json=msg_slack)
            
            if res.status_code == 200:
                registrar_envio(id_unico)
                enviados.add(id_unico) # Adiciona ao set para evitar repetição no mesmo ciclo
                print(f"Sucesso: Pedido {pedido_id}")
            else:
                print(f"Erro Slack: {res.status_code}")
        else:
            print(f"Pedido {pedido_id} ignorado (já enviado).")

if __name__ == "__main__":
    main()
