
from flask import Flask, request, jsonify
import requests
import os
import json
import uuid
import tempfile
import threading
from datetime import datetime

app = Flask(__name__)

INSTANCE = os.getenv("INSTANCE_NAME", "app1")
PEERS = [
    peer.strip()
    for peer in os.getenv("PEERS", "").split(",")
    if peer.strip()
]

DATA_DIR = "/data"
MESSAGES_FILE = os.path.join(DATA_DIR, f"{INSTANCE}.json")
LOG_FILE = os.path.join(DATA_DIR, f"{INSTANCE}.log")

os.makedirs(DATA_DIR, exist_ok=True)

file_lock = threading.Lock()


def inicializar_arquivos():
    with file_lock:
        if not os.path.exists(MESSAGES_FILE):
            with open(MESSAGES_FILE, "w", encoding="utf-8") as arquivo:
                json.dump([], arquivo)


def salvar_mensagem(mensagem):
    with file_lock:
        with open(MESSAGES_FILE, "r", encoding="utf-8") as arquivo:
            mensagens = json.load(arquivo)

        if any(item["id"] == mensagem["id"] for item in mensagens):
            return False

        mensagens.append(mensagem)

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=DATA_DIR,
            delete=False
        ) as temporario:
            json.dump(mensagens, temporario, ensure_ascii=False, indent=4)
            caminho_temporario = temporario.name

        os.replace(caminho_temporario, MESSAGES_FILE)
        return True


def registrar_log(evento, mensagem):
    registro = {
        "evento": evento,
        "container": INSTANCE,
        "message_id": mensagem["id"],
        "message": mensagem["message"],
        "timestamp": datetime.now().astimezone().isoformat()
    }

    with file_lock:
        with open(LOG_FILE, "a", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")


def buscar_mensagens():
    with file_lock:
        with open(MESSAGES_FILE, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)


def replicar_mensagem(mensagem):
    resultados = {}

    for peer in PEERS:
        try:
            resposta = requests.post(
                f"http://{peer}:5000/send",
                json=mensagem,
                timeout=5
            )

            resultados[peer] = {
                "status": resposta.status_code,
                "sucesso": resposta.status_code in (200, 201)
            }

        except requests.RequestException as erro:
            resultados[peer] = {
                "sucesso": False,
                "erro": str(erro)
            }

    return resultados


@app.route("/send", methods=["POST"])
def send():
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({"erro": "Corpo da requisição inválido"}), 400

    if not isinstance(dados.get("message"), str) or not dados["message"].strip():
        return jsonify({"erro": "Mensagem inválida"}), 400

    recebida = all(
        campo in dados
        for campo in ("id", "origin", "timestamp")
    )

    if recebida:
        mensagem = {
            "id": dados["id"],
            "message": dados["message"],
            "origin": dados["origin"],
            "timestamp": dados["timestamp"]
        }

        if not all(isinstance(valor, str) for valor in mensagem.values()):
            return jsonify({"erro": "Formato dos dados inválido"}), 400

        try:
            uuid.UUID(mensagem["id"])
            datetime.fromisoformat(mensagem["timestamp"])
        except ValueError:
            return jsonify({"erro": "ID ou data inválidos"}), 400

        nova = salvar_mensagem(mensagem)

        if nova:
            registrar_log("recebida", mensagem)

        return jsonify({
            "status": "Mensagem recebida",
            "container": INSTANCE,
            "nova_copia": nova
        }), 201 if nova else 200

    mensagem = {
        "id": str(uuid.uuid4()),
        "message": dados["message"],
        "origin": INSTANCE,
        "timestamp": datetime.now().astimezone().isoformat()
    }

    salvar_mensagem(mensagem)
    registrar_log("enviada", mensagem)

    resultados = replicar_mensagem(mensagem)

    return jsonify({
        "status": "Mensagem enviada",
        "container_origem": INSTANCE,
        "mensagem": mensagem,
        "replicacao": resultados
    }), 201


@app.route("/messages", methods=["GET"])
def messages():
    return jsonify({
        "container": INSTANCE,
        "messages": buscar_mensagens()
    })


if __name__ == "__main__":
    inicializar_arquivos()
    app.run(host="0.0.0.0", port=5000, threaded=True)