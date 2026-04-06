import pandas as pd
import requests
import os

URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.csv"

SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK")

def rodar_alerta():
    df = pd.read_csv(URL)
    df.columns = df.columns.str.strip().str.lower()

    df = df[df["analista"].str.contains("BPO", case=False, na=False)]
    criticos = df[df["nivel_alerta"].astype(str).str.upper().str.contains("CRIT", na=False)]

    if len(criticos) > 0:
        mensagem = "ALERTA BPO - AJUSTES FORA DA POLÍTICA\n\n"

        for _, row in criticos.head(5).iterrows():
            mensagem += f"""Pedido: {row['order_number']}
Produto: {row['product']}
Analista: {row['analista']}
Ajuste: R$ {row['valor_ajuste']} ({row['perc_ajuste']}%)
Data: {row['data_ajuste']}
---
"""

        requests.post(SLACK_WEBHOOK, json={"text": mensagem})

if __name__ == "__main__":
    rodar_alerta()
