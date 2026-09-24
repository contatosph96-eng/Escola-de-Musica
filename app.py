import json
import os
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

  dados_brutos = carregar_json()

  # Filtro flexível: garante que só traz alunos com nome e com horário preenchido que não seja inválido
  dados_filtrados = []
  for s in dados_brutos:
    nome = str(s.get("nome", "")).strip()
    dh = str(s.get("diaHorario", "")).strip().lower()

    # Verifica se tem nome e se o horário NÃO é vazio, NÃO é "número inválido" e NÃO é "inválido"
    if nome and dh and "inválido" not in dh and "numero" not in dh:
      dados_filtrados.append(s)

  return jsonify(dados_filtrados)


@app.route("/api/alunos", methods=["POST"])
def post_alunos():
  try:
    req = request.json
    dados_locais = carregar_json()
    acao = req.get("action")

    if acao == "delete":
      row_id = req.get("rowId")
      dados_locais = [s for s in dados_locais if s.get("rowId") != row_id]

    elif acao == "edit":
      row_id = req.get("rowId")
      for s in dados_locais:
        if s.get("rowId") == row_id:
          s["nome"] = req.get("nome")
          s["diaHorario"] = req.get("diaHorario")
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
