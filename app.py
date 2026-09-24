from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/", methods=["GET"])
def inicio():
    return jsonify({
        "estado": "OK",
        "servicio": "Control Acceso MQTT"
    })


@app.route("/verificar", methods=["POST"])
def verificar():
    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({
            "error": "No se recibió JSON"
        }), 400

    registro = datos.get("registro")

    if not registro:
        return jsonify({
            "error": "No se recibió registro"
        }), 400

    registro = str(registro)

    if len(registro) != 4 or not registro.isdigit():
        return jsonify({
            "error": "El registro debe tener exactamente 4 dígitos"
        }), 400

    print("===================================")
    print("SOLICITUD RECIBIDA")
    print("Registro:", registro)
    print("===================================")

    # POR AHORA solamente confirmamos que
    # Render está recibiendo correctamente
    # la solicitud de EMQX.

    return jsonify({
        "estado": "RECIBIDO",
        "registro": registro
    })


if __name__ == "__main__":
    import os

    puerto = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=puerto
    )
