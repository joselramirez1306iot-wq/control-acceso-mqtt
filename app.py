from flask import Flask, request, jsonify
import os
import json
import requests
import ssl
import paho.mqtt.client as mqtt


# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)


# ============================================================
# EMQX TABLES
# ============================================================

TABLES_URL = os.environ.get(
    "TABLES_URL",
    "https://if56e60e.aka.aws.cloud.emqxtables.com/v1/sql"
)

TABLES_USER = os.environ.get("TABLES_USER")
TABLES_PASSWORD = os.environ.get("TABLES_PASSWORD")


# ============================================================
# MQTT
# ============================================================

MQTT_HOST = os.environ.get(
    "MQTT_HOST",
    "a4abba46.ala.us-east-1.emqxsl.com"
)

MQTT_PORT = int(
    os.environ.get("MQTT_PORT", "8883")
)

MQTT_USER = os.environ.get("MQTT_USER")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")


# ============================================================
# TOPICS MQTT
# ============================================================

TOPIC_RESPUESTA = "control/acceso/respuesta"


# ============================================================
# CLIENTE MQTT
# ============================================================

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


# ============================================================
# CONECTAR MQTT
# ============================================================

def conectar_mqtt():

    print("", flush=True)
    print("==========================================", flush=True)
    print("CONTROL DE ACCESO MQTT", flush=True)
    print("==========================================", flush=True)

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


# ============================================================
# CONSULTAR CLIENTE
# ============================================================

def consultar_cliente(registro):

    print("", flush=True)
    print("==========================================", flush=True)
    print("CONSULTANDO EMQX TABLES", flush=True)
    print("==========================================", flush=True)

    print(
        "Registro:",
        registro,
        flush=True
    )

    # --------------------------------------------------------
    # IMPORTANTE:
    # El registro solamente contiene dígitos.
    # Ya fue validado antes de llegar aquí.
    # --------------------------------------------------------

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

        # ----------------------------------------------------
        # ERROR HTTP
        # ----------------------------------------------------

        if respuesta.status_code != 200:

            print(
                "ERROR: EMQX Tables respondió con error",
                flush=True
            )

            return None

        # ----------------------------------------------------
        # CONVERTIR JSON
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # OBTENER OUTPUT
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # OBTENER RECORDS
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # CLIENTE EXISTE
        # ----------------------------------------------------

        if len(rows) > 0:

            print(
                "CLIENTE EXISTE",
                flush=True
            )

            return True

        # ----------------------------------------------------
        # CLIENTE NO EXISTE
        # ----------------------------------------------------

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


# ============================================================
# CREAR CLIENTE
# ============================================================

def crear_cliente(registro):

    print("", flush=True)
    print("==========================================", flush=True)
    print("CREANDO CLIENTE", flush=True)
    print("==========================================", flush=True)

    print(
        "Registro:",
        registro,
        flush=True
    )

    # --------------------------------------------------------
    # INSERT
    # --------------------------------------------------------

    sql = f"""
INSERT INTO public.clientes
(registro, activo, created_at)
VALUES
('{registro}', true, NOW())
"""

    print(
        "SQL INSERT:",
        flush=True
    )

    print(
        sql,
        flush=True
    )

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
            "Respuesta INSERT:",
            flush=True
        )

        print(
            respuesta.text,
            flush=True
        )

        # ----------------------------------------------------
        # ERROR
        # ----------------------------------------------------

        if respuesta.status_code != 200:

            print(
                "ERROR INSERTANDO CLIENTE",
                flush=True
            )

            return False

        # ----------------------------------------------------
        # CORRECTO
        # ----------------------------------------------------

        print(
            "CLIENTE INSERTADO CORRECTAMENTE",
            flush=True
        )

        return True

    except Exception as e:

        print(
            "ERROR CREANDO CLIENTE:",
            flush=True
        )

        print(
            str(e),
            flush=True
        )

        return False


# ============================================================
# PUBLICAR RESPUESTA MQTT
# ============================================================

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
    print("==========================================", flush=True)
    print("PUBLICANDO RESPUESTA MQTT", flush=True)
    print("==========================================", flush=True)

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


# ============================================================
# RUTA PRINCIPAL
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def inicio():

    return jsonify({

        "estado": "OK",

        "servicio":
            "Control Acceso MQTT"

    })


# ============================================================
# VERIFICAR CLIENTE
# ============================================================

@app.route(
    "/verificar",
    methods=["POST"]
)
def verificar():

    print("", flush=True)
    print("==========================================", flush=True)
    print("PETICIÓN VERIFICAR RECIBIDA", flush=True)
    print("==========================================", flush=True)

    # --------------------------------------------------------
    # MOSTRAR HEADERS
    # --------------------------------------------------------

    print(
        "Headers:",
        flush=True
    )

    print(
        dict(request.headers),
        flush=True
    )

    # --------------------------------------------------------
    # BODY
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # VALIDAR JSON
    # --------------------------------------------------------

    if not datos:

        print(
            "ERROR: NO SE RECIBIÓ JSON",
            flush=True
        )

        return jsonify({

            "estado": "ERROR",

            "mensaje":
                "No se recibió JSON"

        }), 400

    # --------------------------------------------------------
    # OBTENER REGISTRO
    # --------------------------------------------------------

    registro = datos.get(
        "registro"
    )

    print(
        "Registro recibido:",
        registro,
        flush=True
    )

    if registro is None:

        print(
            "ERROR: NO SE RECIBIÓ REGISTRO",
            flush=True
        )

        return jsonify({

            "estado": "ERROR",

            "mensaje":
                "No se recibió registro"

        }), 400

    registro = str(
        registro
    )

    # --------------------------------------------------------
    # VALIDAR REGISTRO
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # CONSULTAR
    # --------------------------------------------------------

    existe = consultar_cliente(
        registro
    )

    if existe is None:

        print(
            "ERROR: NO SE PUDO CONSULTAR EMQX TABLES",
            flush=True
        )

        return jsonify({

            "estado": "ERROR",

            "registro": registro

        }), 500

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    if existe:

        resultado = "EXISTE"

    else:

        resultado = "NO_EXISTE"

    print("", flush=True)
    print("==========================================", flush=True)
    print("RESULTADO FINAL", flush=True)
    print("==========================================", flush=True)

    print(
        "Registro:",
        registro,
        flush=True
    )

    print(
        "Resultado:",
        resultado,
        flush=True
    )

    # --------------------------------------------------------
    # PUBLICAR MQTT
    # --------------------------------------------------------

    publicado = publicar_respuesta(

        registro,

        resultado
    )

    if not publicado:

        print(
            "ERROR: NO SE PUDO PUBLICAR MQTT",
            flush=True
        )

        return jsonify({

            "estado":
                "ERROR_MQTT",

            "registro":
                registro,

            "resultado":
                resultado

        }), 500

    print(
        "PROCESO COMPLETADO CORRECTAMENTE",
        flush=True
    )

    return jsonify({

        "estado":
            "OK",

        "registro":
            registro,

        "resultado":
            resultado

    }), 200


# ============================================================
# AGREGAR CLIENTE
# ============================================================

@app.route(
    "/agregar",
    methods=["POST"]
)
def agregar():

    print("", flush=True)
    print("==========================================", flush=True)
    print("PETICIÓN AGREGAR RECIBIDA", flush=True)
    print("==========================================", flush=True)

    # --------------------------------------------------------
    # BODY
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # VALIDAR JSON
    # --------------------------------------------------------

    if not datos:

        print(
            "ERROR: NO SE RECIBIÓ JSON",
            flush=True
        )

        return jsonify({

            "estado":
                "ERROR",

            "mensaje":
                "No se recibió JSON"

        }), 400

    # --------------------------------------------------------
    # OBTENER REGISTRO
    # --------------------------------------------------------

    registro = datos.get(
        "registro"
    )

    print(
        "Registro recibido:",
        registro,
        flush=True
    )

    if registro is None:

        print(
            "ERROR: NO SE RECIBIÓ REGISTRO",
            flush=True
        )

        return jsonify({

            "estado":
                "ERROR",

            "mensaje":
                "No se recibió registro"

        }), 400

    registro = str(
        registro
    )

    # --------------------------------------------------------
    # VALIDAR REGISTRO
    # --------------------------------------------------------

    if (
        len(registro) != 4
        or not registro.isdigit()
    ):

        print(
            "ERROR: REGISTRO INVÁLIDO",
            flush=True
        )

        return jsonify({

            "estado":
                "ERROR",

            "mensaje":
                "El registro debe tener exactamente 4 dígitos"

        }), 400

    print(
        "Registro válido:",
        registro,
        flush=True
    )

    # ========================================================
    # PRIMERO COMPROBAR SI YA EXISTE
    # ========================================================

    print("", flush=True)
    print(
        "COMPROBANDO SI EL CLIENTE YA EXISTE...",
        flush=True
    )

    existe = consultar_cliente(
        registro
    )

    # --------------------------------------------------------
    # ERROR DE CONSULTA
    # --------------------------------------------------------

    if existe is None:

        print(
            "ERROR: NO SE PUDO CONSULTAR EMQX TABLES",
            flush=True
        )

        return jsonify({

            "estado":
                "ERROR",

            "registro":
                registro

        }), 500

    # ========================================================
    # YA EXISTE
    # ========================================================

    if existe:

        resultado = "YA_EXISTE"

        print("", flush=True)
        print(
            "==========================================",
            flush=True
        )

        print(
            "EL CLIENTE YA EXISTE",
            flush=True
        )

        print(
            "NO SE REALIZARÁ INSERT",
            flush=True
        )

        print(
            "==========================================",
            flush=True
        )

    # ========================================================
    # NO EXISTE -> CREAR
    # ========================================================

    else:

        print("", flush=True)

        print(
            "CLIENTE NO EXISTE",
            flush=True
        )

        print(
            "PROCEDIENDO A CREAR...",
            flush=True
        )

        creado = crear_cliente(
            registro
        )

        # ----------------------------------------------------
        # ERROR INSERT
        # ----------------------------------------------------

        if not creado:

            print(
                "ERROR: NO SE PUDO CREAR EL CLIENTE",
                flush=True
            )

            return jsonify({

                "estado":
                    "ERROR_INSERT",

                "registro":
                    registro

            }), 500

        # ----------------------------------------------------
        # CREADO
        # ----------------------------------------------------

        resultado = "CREADO"

        print("", flush=True)
        print(
            "==========================================",
            flush=True
        )

        print(
            "CLIENTE CREADO CORRECTAMENTE",
            flush=True
        )

        print(
            "==========================================",
            flush=True
        )

    # ========================================================
    # PUBLICAR RESULTADO POR MQTT
    # ========================================================

    publicado = publicar_respuesta(

        registro,

        resultado
    )

    if not publicado:

        print(
            "ERROR: NO SE PUDO PUBLICAR MQTT",
            flush=True
        )

        return jsonify({

            "estado":
                "ERROR_MQTT",

            "registro":
                registro,

            "resultado":
                resultado

        }), 500

    # ========================================================
    # RESPUESTA HTTP A EMQX
    # ========================================================

    print("", flush=True)
    print(
        "==========================================",
        flush=True
    )

    print(
        "PROCESO AGREGAR COMPLETADO",
        flush=True
    )

    print(
        "Registro:",
        registro,
        flush=True
    )

    print(
        "Resultado:",
        resultado,
        flush=True
    )

    print(
        "==========================================",
        flush=True
    )

    return jsonify({

        "estado":
            "OK",

        "registro":
            registro,

        "resultado":
            resultado

    }), 200


# ============================================================
# INICIAR SERVIDOR
# ============================================================

if __name__ == "__main__":

    conectar_mqtt()

    puerto = int(
        os.environ.get(
            "PORT",
            "10000"
        )
    )

    print("", flush=True)

    print(
        "==========================================",
        flush=True
    )

    print(
        "INICIANDO FLASK",
        flush=True
    )

    print(
        "Puerto:",
        puerto,
        flush=True
    )

    print(
        "==========================================",
        flush=True
    )

    app.run(

        host="0.0.0.0",

        port=puerto

    )
