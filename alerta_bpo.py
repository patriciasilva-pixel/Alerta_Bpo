import pandas as pd
import requests
import os

URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.csv"
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")

ARQUIVO_CONTROLE = "enviados.csv"

def rodar_alerta():
    print("Rodando alerta...")

    df = pd.read_csv(URL)

    # 🔧 padroniza colunas
    df.columns = df.columns.str.strip().str.lower()

    # 🔥 pega só update
    df = df[df['email'].str.contains('actionline', na=False)]

    # 🔥 evita erro de nulo
    df['perc_ajuste'] = df['perc_ajuste'].fillna(0)

    # 🔥 cria ID único
    df['id_unico'] = df['order_number'].astype(str) + "_" + df['data_ajuste'].astype(str)

    # 📂 histórico
    try:
        enviados = pd.read_csv(ARQUIVO_CONTROLE)
        ids_enviados = set(enviados['id'])
    except:
        ids_enviados = set()

    novos = df[~df['id_unico'].isin(ids_enviados)]

    print(f"Novos encontrados: {len(novos)}")

    if novos.empty:
        print("Nada novo.")
        return

    for _, row in novos.iterrows():

        preco = f"R$ {row.get('preco_ajustado', 0):.2f}".replace(".", ",")

        mensagem = f"""
🚨 *ALERTA BPO - ATUALIZAÇÃO*

📦 *Pedido:* {row.get('order_number')}
📌 *Produto:* {row.get('product')}
👤 *Analista:* {row.get('analista')}
📊 *Nível:* {row.get('nivel_alerta')}

💰 *Preço:* {preco}
📅 *Data:* {row.get('data_ajuste')}
"""

        requests.post(SLACK_WEBHOOK, json={"text": mensagem})

    # 💾 salva histórico
    novos_ids = pd.DataFrame({'id': novos['id_unico']})

    if os.path.exists(ARQUIVO_CONTROLE):
        antigos = pd.read_csv(ARQUIVO_CONTROLE)
        final = pd.concat([antigos, novos_ids])
    else:
        final = novos_ids

    final.to_csv(ARQUIVO_CONTROLE, index=False)

    print("Envio concluído!")

if __name__ == "__main__":
    rodar_alerta()
