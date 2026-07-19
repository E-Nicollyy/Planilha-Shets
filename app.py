from flask import Flask, render_template, request
from datetime import datetime
import os
import requests

app = Flask(__name__)

# URL do Web App do Google Apps Script (Implantar > Nova implantação > App da Web)
ENDPOINT = "https://script.google.com/macros/s/AKfycbwV_y-JvgQoch2AxjTX4Tw2tSxhpTNgeqng-ZugTQHIvB0VoQO3mVjDzByHskssdA/exec"

# Valor fixo esperado por mês (regra de negócio da mensalidade)
VALOR_ESPERADO = 68.0


@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None  # guarda a mensagem de sucesso/erro para mostrar na tela
    resumo = None      # guarda o resumo do pagamento para mostrar na tela

    if request.method == "POST":
        # Pega os dados enviados pelo formulário HTML
        nome = request.form.get("nome", "").strip()
        mes = int(request.form.get("mes"))
        valor_pago = float(request.form.get("valor_pago"))

        # Ano atual (usado só para exibir no resumo e para montar a data no Apps Script)
        ano = datetime.now().year

        # Calcula a diferença entre o que foi pago e o que era esperado
        diferenca = valor_pago - VALOR_ESPERADO
        status = "Concluído" if diferenca >= 0 else "Pendente"

        # Monta o resumo para exibir na tela antes/depois do envio
        resumo = {
            "nome": nome,
            "referencia": f"{mes:02d}/{ano}",
            "valor_esperado": VALOR_ESPERADO,
            "valor_pago": valor_pago,
            "diferenca": diferenca,
            "status": status,
        }

        # Monta o payload para enviar ao Google Apps Script
        # Envia "mes" e "ano" separados para o script escolher a aba certa e montar a data
        dados = {
            "nome": nome,
            "mes": mes,
            "ano": ano,
            "valor_pago": valor_pago,
            "valor_esperado": VALOR_ESPERADO,
            "sobra_falta": diferenca,
            "status": status,
        }

        try:
            resposta = requests.post(ENDPOINT, json=dados, timeout=10)

            # O Apps Script sempre responde com status 200, mesmo em erro de negócio
            # (ex: aba não encontrada). Por isso é essencial checar o JSON, não só o status HTTP.
            try:
                corpo = resposta.json()
            except ValueError:
                corpo = None

            if resposta.status_code == 200 and corpo and corpo.get("resultado") == "ok":
                resultado = {"ok": True, "mensagem": "Pagamento registrado com sucesso!"}
            elif corpo and corpo.get("mensagem"):
                # Erro de negócio reportado pelo próprio Apps Script (ex: aba não encontrada)
                resultado = {"ok": False, "mensagem": corpo["mensagem"]}
            else:
                resultado = {
                    "ok": False,
                    "mensagem": f"Erro ao enviar: {resposta.status_code} - {resposta.text}",
                }
        except requests.exceptions.RequestException as erro:
            resultado = {"ok": False, "mensagem": f"Falha na conexão: {erro}"}

    return render_template("index.html", resultado=resultado, resumo=resumo)


if __name__ == "__main__":
    # Esse bloco só roda quando você executa "python app.py" localmente.
    # No Render, quem sobe o app é o Gunicorn (comando de start: gunicorn app:app),
    # então esse trecho nem é executado em produção — pode manter debug=True aqui sem risco.
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta, debug=True)