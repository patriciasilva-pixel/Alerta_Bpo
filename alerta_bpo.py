import pandas as pd
import requests
import os
from datetime import datetime

URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.csv"

SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK")

ARQUIVO_CONTROLE = "enviados.csv"


def formatar_data(data_str):
    try:
        return datetime.strptime(data_str, "%Y-%m-%dT%H:%M:%S").strftime("%d/%m/%Y %H:%M")
    except:
        return data_str


def rodar_alerta():
    df = pd.read_csv(URL)
    df.columns = df.columns.str.strip().str.lower()

    df = df[df["analista"].str.contains("BPO", case=False, na=False)]
    criticos = df[df["nivel_alerta"].astype(str).str.upper().str.contains("CRIT", na=False)].copy()

    # cria id único
    criticos["id_unico"] = (
        criticos["order_number"].astype(str) + "_" +
        criticos["product"].astype(str) + "_" +
        criticos["data_ajuste"].astype(str)
    )

    # lê histórico
    if os.path.exists(ARQUIVO_CONTROLE):
        enviados = pd.read_csv(ARQUIVO_CONTROLE)
        ids_enviados = set(enviados["id_unico"])
    else:
        ids_enviados = set()

    # filtra novos
    novos = criticos[~criticos["id_unico"].isin(ids_enviados)]

    if len(novos) > 0:
        mensagem = "*ALERTA BPO - NOVOS AJUSTES CRÍTICOS*\n\n"

        for _, row in novos.iterrows():
            data_formatada = formatar_data(str(row["data_ajuste"]))

            mensagem += (
                f"Pedido: {row['order_number']}\n"
                f"Produto: {row['product']}\n"
                f"Analista: {row['analista']}\n"
                f"Ajuste: R$ {row['valor_ajuste']} ({row['perc_ajuste']}%)\n"
                f"Data: {data_formatada}\n"
                f"-----------------------------\n"
            )

        requests.post(SLACK_WEBHOOK, json={"text": mensagem})

        # salva novos
        novos[["id_unico"]].to_csv(
            ARQUIVO_CONTROLE,
            mode="a",
            header=not os.path.exists(ARQUIVO_CONTROLE),
            index=False
        )

        print("✅ Novos alertas enviados")

    else:
        print("👍 Nenhum novo crítico")


if __name__ == "__main__":
    rodar_alerta()
