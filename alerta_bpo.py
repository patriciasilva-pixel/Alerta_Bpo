import pandas as pd
import requests
import os

URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.csv"

SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK")

ARQUIVO_CONTROLE = "enviados.csv"

def rodar_alerta():
    print("Rodando verificação...")

    df = pd.read_csv(URL)
    df.columns = df.columns.str.strip().str.lower()

    # 🔥 AGORA PEGA TODOS (não filtra mais CRIT)
    df = df[df["analista"].str.contains("BPO", case=False, na=False)]

    # cria ID único
    df["id_unico"] = df["order_number"].astype(str) + "_" + df["data_ajuste"].astype(str)

    # carrega histórico
    if os.path.exists(ARQUIVO_CONTROLE):
        enviados = pd.read_csv(ARQUIVO_CONTROLE)
        enviados_ids = set(enviados["id"].astype(str))
    else:
        enviados_ids = set()

    novos = df[~df["id_unico"].isin(enviados_ids)]

    print(f"Novos registros: {len(novos)}")

    # 🧠 PRIMEIRA EXECUÇÃO (não envia)
    if len(enviados_ids) == 0:
        print("Primeira execução - carregando base sem enviar alerta")

        df[["id_unico"]] \
            .rename(columns={"id_unico": "id"}) \
            .drop_duplicates() \
            .to_csv(ARQUIVO_CONTROLE, index=False)

    # 🚨 EXECUÇÕES NORMAIS
    elif len(novos) > 0:
        mensagem = "ALERTA BPO - ATUALIZAÇÕES DE PEDIDOS\n\n"

        for _, row in novos.head(10).iterrows():
            data_formatada = pd.to_datetime(row["data_ajuste"]).strftime("%d/%m/%Y %H:%M")

            nivel = str(row.get("nivel_alerta", "SEM INFO")).upper()

            mensagem += f"""Pedido: {row['order_number']}
Produto: {row['product']}
Analista: {row['analista']}
Nível: {nivel}
Ajuste: R$ {row['valor_ajuste']} ({row['perc_ajuste']}%)
Data: {data_formatada}
----------------------
"""

        requests.post(SLACK_WEBHOOK, json={"text": mensagem})

        # atualiza histórico
        novos_ids = novos[["id_unico"]].rename(columns={"id_unico": "id"})

        enviados_atualizado = pd.concat([
            pd.DataFrame({"id": list(enviados_ids)}),
            novos_ids
        ])

        enviados_atualizado.drop_duplicates().to_csv(ARQUIVO_CONTROLE, index=False)

    else:
        print("Nenhum registro novo")

if __name__ == "__main__":
    rodar_alerta()
