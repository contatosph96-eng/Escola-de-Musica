import json
import os
import re
from flask import Flask, jsonify, render_template, request
import requests

app = Flask(__name__)

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwnNemO5REfd8H-Wfvd4DJFC20J5AiohCM7SZKZGb0nj53MfPsDqa-j8uLtTcpTqXbxJA/exec"
JSON_FILE = "dados.json"


def carregar_json():
  if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r", encoding="utf-8") as f:
      try:
        return json.load(f)
      except:
        return []
  return []


def salvar_json(dados):
  with open(JSON_FILE, "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=4)


def gerar_dh_code(texto_dia_horario):
  """Converte o texto digitado.

  Se contiver 'le' ou 'lista', define como 'Lista de Espera'. Caso contrário,
  aplica a formatação padrão da coluna B.
  """
  texto = texto_dia_horario.lower().strip()

  # Se o usuário digitar 'le' ou 'lista de espera'
  if "le" in texto or "lista" in texto:
    return "Lista de Espera"

  prefixo = "1"  # Padrão Segunda
  if "terça" in texto or "terca" in texto:
    prefixo = "3"
  elif "quarta" in texto:
    prefixo = "2"

  horas_encontradas = re.findall(r"\d+", texto)
  hora_num = horas_encontradas[0] if horas_encontradas else "0"

  return f"{prefixo},{hora_num}" if horas_encontradas else texto_dia_horario


@app.route("/")
def index():
  return render_template("index.html")


@app.route("/admin")
def admin():
  return render_template("admin.html")


@app.route("/aluno")
def escala():
  return render_template("aluno.html")


@app.route("/api/alunos", methods=["GET"])
def get_alunos():
  try:
    response = requests.get(WEB_APP_URL, allow_redirects=True, timeout=5)
    data = response.json()
    if isinstance(data, list) and len(data) > 0:
      salvar_json(data)
  except Exception as e:
    print("Modo Offline / Usando JSON local:", e)

  return jsonify(carregar_json())


@app.route("/api/alunos", methods=["POST"])
def post_alunos():
  try:
    req = request.json
    dados_locais = carregar_json()
    acao = req.get("action")

    texto_dia = req.get("diaHorario", "")
    dh_code_gerado = gerar_dh_code(texto_dia)
    req["dhCode"] = dh_code_gerado

    if acao == "delete":
      row_id = req.get("rowId")
      dados_locais = [s for s in dados_locais if s.get("rowId") != row_id]

    elif acao == "edit":
      row_id = req.get("rowId")
      for s in dados_locais:
        if s.get("rowId") == row_id:
          s["nome"] = req.get("nome")
          s["diaHorario"] = req.get("diaHorario")
          s["dhCode"] = dh_code_gerado
          s["instrumento"] = req.get("instrumento")
          s["telefone"] = req.get("telefone", "")

    else:  # Novo cadastro
      nuevo_id = (
          max([s.get("rowId", 0) for s in dados_locais], default=0) + 1
      )
      novo_aluno = {
          "rowId": nuevo_id,
          "nome": req.get("nome"),
          "diaHorario": req.get("diaHorario"),
          "dhCode": dh_code_gerado,
          "instrumento": req.get("instrumento"),
          "telefone": req.get("telefone", ""),
      }
      dados_locais.append(novo_aluno)

    salvar_json(dados_locais)

    try:
      requests.post(WEB_APP_URL, json=req, timeout=3)
    except Exception as ex:
      print("Aviso sync sheets:", ex)

    return jsonify({"result": "success"})
  except Exception as e:
    return jsonify({"result": "error", "message": str(e)})


if __name__ == "__main__":
  app.run(debug=True, port=5000)
