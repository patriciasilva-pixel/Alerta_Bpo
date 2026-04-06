import pandas as pd
import requests
import os
from datetime import datetime

# 🔗 URL do Metabase (CSV público)
URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.csv"

# 🔐 Webhook do Slack (vem do GitHub Secrets)
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK")


def formatar_data(data_str):
    try:
        return datetime.strptime(data_str, "%Y-%m-%dT%H:%M:%S").strftime("%d/%m/%Y %H:%M")
    except:
        return data_str


def rodar_alerta():
    df = pd.read_csv(URL)

    # padroniza colunas
    df.columns = df.columns.str.strip().str.lower()

    # filtra BPO
    df = df[df["analista"].str.contains("BPO", case=False, na=False)]

    # filtra críticos
    criticos = df[df["nivel_alerta"].astype(str).str.upper().str.contains("CRIT", na=False)]

    if len(criticos) > 0:
        mensagem = "*ALERTA BPO - AJUSTES FORA DA POLÍTICA*\n\n"

        for _, row in criticos.head(5).iterrows():
            data_formatada = formatar_data(str(row["data_ajuste"]))

            mensagem += (
                f"Pedido: {row['order_number']}\n"
                f"Produto: {row['product']}\n"
                f"Analista: {row['analista']}\n"
                f"Ajuste: R$ {row['valor_ajuste']} ({row['perc_ajuste']}%)\n"
                f"Data: {data_formatada}\n"
                f"-----------------------------\n"
            )

        # envia pro Slack
        requests.post(SLACK_WEBHOOK, json={"text": mensagem})

        print("✅ Enviado para Slack")

    else:
        print("👍 Nenhum crítico novo")


if __name__ == "__main__":
    rodar_alerta()
