from flask import Flask, request, jsonify
import os
import json
import requests
import ssl
import paho.mqtt.client as mqtt


# =========================================================
# FLASK
# =========================================================

app = Flask(__name__)


# =========================================================
# CONFIGURACIÓN EMQX TABLES
# =========================================================

TABLES_URL = os.environ.get(
    "TABLES_URL",
    "https://if56e60e.aka.aws.cloud.emqxTables.com/v1/sql"
)

TABLES_USER = os.environ.get("TABLES_USER")
TABLES_PASSWORD = os.environ.get("TABLES_PASSWORD")


# =========================================================
# CONFIGURACIÓN MQTT
# =========================================================

MQTT_HOST = os.environ.get(
    "MQTT_HOST",
    "a4abba46.ala.us-east-1.emqxsl.com"
)

MQTT_PORT = int(
    os.environ.get("MQTT_PORT", "8883")
)

MQTT_USER = os.environ.get("MQTT_USER")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")


# =========================================================
# TOPICS
# =========================================================

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
# CONEXIÓN MQTT
# =========================================================

def conectar_mqtt():

    print("", flush=True)
    print("===================================", flush=True)
    print("CONTROL DE ACCESO MQTT", flush=True)
    print("===================================", flush=True)

    print("Conectando a MQTT...", flush=True)

    try:

        mqtt_client.connect(
            MQTT_HOST,
            MQTT_PORT,
            60
        )

        mqtt_client.loop_start()

        print(
            "MQTT conectado correctamente",
            flush=True
        )

        return True

    except Exception as e:

        print(
            "ERROR MQTT:",
            flush=True
        )

        print(
            str(e),
            flush=True
        )

        return False


# =========================================================
# CONSULTAR EMQX TABLES
# =========================================================

def consultar_cliente(registro):

    print("", flush=True)
    print("===================================", flush=True)
    print("CONSULTANDO EMQX TABLES", flush=True)
    print("Registro:", registro, flush=True)
    print("===================================", flush=True)

    # El registro ya fue validado como exactamente
    # 4 dígitos antes de llegar aquí.
    sql = f"""
SELECT registro
FROM public.clientes
WHERE registro = '{registro}'
AND activo = true
"""

    print("SQL:", flush=True)
    print(sql, flush=True)

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

        print(
            "HTTP Tables:",
            respuesta.status_code,
            flush=True
        )

        print(
            "Respuesta Tables:",
            flush=True
        )

        print(
            respuesta.text,
            flush=True
        )

        # ---------------------------------------------
        # ERROR HTTP
        # ---------------------------------------------

        if respuesta.status_code != 200:

            print(
                "ERROR: EMQX Tables respondió con error",
                flush=True
            )

            return None

        # ---------------------------------------------
        # CONVERTIR RESPUESTA JSON
        # ---------------------------------------------

        try:

            datos = respuesta.json()

        except Exception as e:

            print(
                "ERROR CONVIRTIENDO RESPUESTA A JSON:",
                flush=True
            )

            print(
                str(e),
                flush=True
            )

            return None

        print(
            "JSON recibido correctamente",
            flush=True
        )

        # ---------------------------------------------
        # OBTENER OUTPUT
        # ---------------------------------------------

        output = datos.get(
            "output",
            []
        )

        if not output:

            print(
                "No existe output en la respuesta",
                flush=True
            )

            return False

        # ---------------------------------------------
        # OBTENER RECORDS
        # ---------------------------------------------

        records = output[0].get(
            "records",
            {}
        )

        rows = records.get(
            "rows",
            []
        )

        print(
            "Cantidad de filas encontradas:",
            len(rows),
            flush=True
        )

        # ---------------------------------------------
        # CLIENTE ENCONTRADO
        # ---------------------------------------------

        if len(rows) > 0:

            print(
                "CLIENTE EXISTE",
                flush=True
            )

            return True

        # ---------------------------------------------
        # CLIENTE NO ENCONTRADO
        # ---------------------------------------------

        print(
            "CLIENTE NO EXISTE",
            flush=True
        )

        return False

    except Exception as e:

        print(
            "ERROR CONSULTANDO EMQX TABLES:",
            flush=True
        )

        print(
            str(e),
            flush=True
        )

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

    print("", flush=True)
    print("===================================", flush=True)
    print("PUBLICANDO RESPUESTA MQTT", flush=True)
    print("===================================", flush=True)

    print(
        "Topic:",
        TOPIC_RESPUESTA,
        flush=True
    )

    print(
        "Payload:",
        payload,
        flush=True
    )

    try:

        resultado_mqtt = mqtt_client.publish(
            TOPIC_RESPUESTA,
            payload,
            qos=0
        )

        resultado_mqtt.wait_for_publish()

        print(
            "RESPUESTA MQTT PUBLICADA",
            flush=True
        )

        return True

    except Exception as e:

        print(
            "ERROR PUBLICANDO MQTT:",
            flush=True
        )

        print(
            str(e),
            flush=True
        )

        return False


# =========================================================
# PÁGINA PRINCIPAL
# =========================================================

@app.route(
    "/",
    methods=["GET"]
)
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

    print("", flush=True)
    print("===================================", flush=True)
    print("PETICIÓN HTTP RECIBIDA", flush=True)
    print("===================================", flush=True)

    # ---------------------------------------------
    # MOSTRAR HEADERS
    # ---------------------------------------------

    print(
        "Headers:",
        flush=True
    )

    print(
        dict(request.headers),
        flush=True
    )

    # ---------------------------------------------
    # OBTENER BODY
    # ---------------------------------------------

    body_raw = request.get_data(
        as_text=True
    )

    print(
        "Body RAW:",
        flush=True
    )

    print(
        body_raw,
        flush=True
    )

    # ---------------------------------------------
    # LEER JSON
    # ---------------------------------------------

    datos = request.get_json(
        silent=True
    )

    print(
        "JSON:",
        flush=True
    )

    print(
        datos,
        flush=True
    )

    # ---------------------------------------------
    # VALIDAR JSON
    # ---------------------------------------------

    if not datos:

        print(
            "ERROR: NO SE RECIBIÓ JSON",
            flush=True
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": "No se recibió JSON"
        }), 400

    # ---------------------------------------------
    # OBTENER REGISTRO
    # ---------------------------------------------

    registro = datos.get(
        "registro"
    )

    print(
        "Registro recibido:",
        registro,
        flush=True
    )

    # ---------------------------------------------
    # VALIDAR REGISTRO
    # ---------------------------------------------

    if registro is None:

        print(
            "ERROR: NO SE RECIBIÓ REGISTRO",
            flush=True
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje": "No se recibió registro"
        }), 400

    registro = str(
        registro
    )

    # ---------------------------------------------
    # DEBE SER EXACTAMENTE 4 DÍGITOS
    # ---------------------------------------------

    if (
        len(registro) != 4
        or not registro.isdigit()
    ):

        print(
            "ERROR: REGISTRO INVÁLIDO",
            flush=True
        )

        return jsonify({
            "estado": "ERROR",
            "mensaje":
                "El registro debe tener exactamente 4 dígitos"
        }), 400

    print(
        "Registro válido:",
        registro,
        flush=True
    )

    # ---------------------------------------------
    # CONSULTAR BASE DE DATOS
    # ---------------------------------------------

    existe = consultar_cliente(
        registro
    )

    # ---------------------------------------------
    # ERROR DE CONSULTA
    # ---------------------------------------------

    if existe is None:

        print(
            "ERROR: NO SE PUDO CONSULTAR EMQX TABLES",
            flush=True
        )

        return jsonify({
            "estado": "ERROR",
            "registro": registro
        }), 500

    # ---------------------------------------------
    # DETERMINAR RESULTADO
    # ---------------------------------------------

    if existe:

        resultado = "EXISTE"

    else:

        resultado = "NO_EXISTE"

    print("", flush=True)
    print("===================================", flush=True)
    print("RESULTADO FINAL", flush=True)
    print("Registro:", registro, flush=True)
    print("Resultado:", resultado, flush=True)
    print("===================================", flush=True)

    # ---------------------------------------------
    # PUBLICAR POR MQTT
    # ---------------------------------------------

    publicado = publicar_respuesta(
        registro,
        resultado
    )

    # ---------------------------------------------
    # ERROR MQTT
    # ---------------------------------------------

    if not publicado:

        print(
            "ERROR: NO SE PUDO PUBLICAR MQTT",
            flush=True
        )

        return jsonify({
            "estado": "ERROR_MQTT",
            "registro": registro,
            "resultado": resultado
        }), 500

    # ---------------------------------------------
    # RESPUESTA HTTP A EMQX
    # ---------------------------------------------

    print(
        "PROCESO COMPLETADO CORRECTAMENTE",
        flush=True
    )

    return jsonify({
        "estado": "OK",
        "registro": registro,
        "resultado": resultado
    }), 200


# =========================================================
# INICIAR SERVIDOR
# =========================================================

if __name__ == "__main__":

    conectar_mqtt()

    puerto = int(
        os.environ.get(
            "PORT",
            "10000"
        )
    )

    print(
        "Iniciando Flask en puerto:",
        puerto,
        flush=True
    )

    app.run(
        host="0.0.0.0",
        port=puerto
    )
