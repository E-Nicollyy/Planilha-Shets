from flask import Flask, render_template, request
from datetime import datetime
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

        # Monta a data de referência (dd/mm/aaaa) usando o ano atual
        ano = datetime.now().year
        data_referencia = f"01/{mes:02d}/{ano}"

        # Calcula a diferença entre o que foi pago e o que era esperado
        diferenca = valor_pago - VALOR_ESPERADO
        status = "Concluído"

        # Monta o resumo para exibir na tela antes/depois do envio
        resumo = {
            "nome": nome,
            "referencia": data_referencia,
            "valor_esperado": VALOR_ESPERADO,
            "valor_pago": valor_pago,
            "diferenca": diferenca,
            "status": status,
        }

        # Monta o payload para enviar ao Google Apps Script
        dados = {
            "nome": nome,
            "referencia": data_referencia,
            "valor_pago": valor_pago,
            "valor_esperado": VALOR_ESPERADO,
            "sobra_falta": diferenca,
            "status": status,
            "ano": ano,
        }

        try:
            resposta = requests.post(ENDPOINT, json=dados, timeout=10)
            if resposta.status_code == 200:
                resultado = {"ok": True, "mensagem": "Pagamento registrado com sucesso!"}
            else:
                resultado = {
                    "ok": False,
                    "mensagem": f"Erro ao enviar: {resposta.status_code} - {resposta.text}",
                }
        except requests.exceptions.RequestException as erro:
            resultado = {"ok": False, "mensagem": f"Falha na conexão: {erro}"}

    return render_template("index.html", resultado=resultado, resumo=resumo)


if __name__ == "__main__":
    # debug=True facilita o desenvolvimento (recarrega sozinho e mostra erros)
    app.run(debug=True)