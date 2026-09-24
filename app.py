from flask import Flask, request, jsonify
import os
import json
import requests
import ssl
import paho.mqtt.client as mqtt

app = Flask(__name__)


# =========================================================
# CONFIGURACIÓN
# =========================================================

TABLES_URL = os.environ.get(
    "TABLES_URL",
    "https://if56e60e.aka.aws.cloud.emqxtables.com/v1/sql"
)

TABLES_USER = os.environ.get("TABLES_USER")
TABLES_PASSWORD = os.environ.get("TABLES_PASSWORD")

MQTT_HOST = os.environ.get(
    "MQTT_HOST",
    "a4abba46.ala.us-east-1.emqxsl.com"
)

MQTT_PORT = int(
    os.environ.get("MQTT_PORT", "8883")
)

MQTT_USER = os.environ.get("MQTT_USER")

MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")

TOPIC_RESPUESTA = "control/acceso/respuesta"


# =========================================================
# CLIENTE MQTT
# =========================================================

mqtt_client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2
)

mqtt_client.username_pw_set(
    MQTT_USER,
    MQTT_PASSWORD
)

mqtt_client.tls_set(
    cert_reqs=ssl.CERT_REQUIRED
)


# =========================================================
# CONECTAR MQTT
# =========================================================

def conectar_mqtt():

    print("Conectando a MQTT...")

    try:

        mqtt_client.connect(
            MQTT_HOST,
            MQTT_PORT,
            60
        )

        mqtt_client.loop_start()

        print("MQTT conectado correctamente")

        return True

    except Exception as e:

        print("ERROR MQTT:")
        print(e)

        return False


# =========================================================
# CONSULTAR EMQX TABLES
# =========================================================

def consultar_cliente(registro):

    sql = f"""
    SELECT registro
    FROM public.clientes
    WHERE registro = '{registro}'
    AND activo = true
    """

    print("SQL:")
    print(sql)

    try:

        respuesta = requests.post(
            TABLES_URL,
            auth=(
                TABLES_USER,
                TABLES_PASSWORD
            ),
            headers={
                "Content-Type":
                "application/x-www-form-urlencoded"
            },
            data={
                "sql": sql
            },
            timeout=15
        )

        print("HTTP Tables:", respuesta.status_code)
        print("Respuesta Tables:")
        print(respuesta.text)

        if respuesta.status_code != 200:

            print("ERROR CONSULTANDO EMQX TABLES")

            return None

        datos = respuesta.json()

        output = datos.get("output", [])

        if not output:

            return False

        records = output[0].get(
            "records",
            {}
        )

        rows = records.get(
            "rows",
            []
        )

        if len(rows) > 0:

            return True

        return False

    except Exception as e:

        print("ERROR TABLES:")
        print(e)

        return None


# =========================================================
# PUBLICAR RESPUESTA MQTT
# =========================================================

def publicar_respuesta(
    registro,
    resultado
):

    mensaje = {
        "registro": registro,
        "resultado": resultado
    }

    payload = json.dumps(
        mensaje
    )

    print("===================================")
    print("PUBLICANDO RESPUESTA MQTT")
    print("Topic:", TOPIC_RESPUESTA)
    print("Payload:", payload)
    print("===================================")

    try:

        resultado_mqtt = mqtt_client.publish(
            TOPIC_RESPUESTA,
            payload,
            qos=0
        )

        resultado_mqtt.wait_for_publish()

        print("RESPUESTA MQTT PUBLICADA")

        return True

    except Exception as e:

        print("ERROR PUBLICANDO MQTT:")
        print(e)

        return False


# =========================================================
# RUTA PRINCIPAL
# =========================================================

@app.route("/", methods=["GET"])
def inicio():

    return jsonify({
        "estado": "OK",
        "servicio": "Control Acceso MQTT"
    })


# =========================================================
# VERIFICAR CLIENTE
# =========================================================

@app.route(
    "/verificar",
    methods=["POST"]
)
def verificar():

    datos = request.get_json(
        silent=True
    )

    if not datos:

        return jsonify({
            "error": "No se recibió JSON"
        }), 400

    registro = datos.get(
        "registro"
    )

    if not registro:

        return jsonify({
            "error": "No se recibió registro"
        }), 400

    registro = str(
        registro
    )

    # -----------------------------------------
    # VALIDAR REGISTRO
    # -----------------------------------------

    if (
        len(registro) != 4
        or not registro.isdigit()
    ):

        return jsonify({
            "error":
            "El registro debe tener exactamente 4 dígitos"
        }), 400

    print("")
    print("===================================")
    print("SOLICITUD DE VERIFICACIÓN")
    print("Registro:", registro)
    print("===================================")

    # -----------------------------------------
    # CONSULTAR TABLES
    # -----------------------------------------

    existe = consultar_cliente(
        registro
    )

    # -----------------------------------------
    # ERROR DE CONSULTA
    # -----------------------------------------

    if existe is None:

        print(
            "NO SE PUDO CONSULTAR LA BASE DE DATOS"
        )

        return jsonify({
            "estado": "ERROR",
            "registro": registro
        }), 500

    # -----------------------------------------
    # CLIENTE EXISTE
    # -----------------------------------------

    if existe:

        resultado = "EXISTE"

        print(
            "CLIENTE ENCONTRADO"
        )

    # -----------------------------------------
    # CLIENTE NO EXISTE
    # -----------------------------------------

    else:

        resultado = "NO_EXISTE"

        print(
            "CLIENTE NO ENCONTRADO"
        )

    # -----------------------------------------
    # PUBLICAR MQTT
    # -----------------------------------------

    publicado = publicar_respuesta(
        registro,
        resultado
    )

    if not publicado:

        return jsonify({
            "estado": "ERROR_MQTT",
            "registro": registro,
            "resultado": resultado
        }), 500

    print(
        "PROCESO COMPLETADO"
    )

    return jsonify({
        "estado": "OK",
        "registro": registro,
        "resultado": resultado
    })


# =========================================================
# INICIO DEL SERVIDOR
# =========================================================

if __name__ == "__main__":

    print("")
    print("===================================")
    print("CONTROL DE ACCESO MQTT")
    print("===================================")

    conectar_mqtt()

    puerto = int(
        os.environ.get(
            "PORT",
            "10000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=puerto
    )
