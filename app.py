from flask import Flask, request, json, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import http.client
import logging
import os
from dotenv import load_dotenv
from translations import get_message
from io import StringIO # Importar StringIO para el manejo de credenciales
import threading

load_dotenv()
#_______________________________________________________________________________________
"""
Version 2:
Descripción: Primer Bot de Whatsapp para la empresa TicAll Media, 
con descarga en Google Sheet de Conversaciones

Caracteristicas: 
-Un solo idioma, debido a que se genera lentitud en la aplicación
-Uso de diccionario: Se crea un diccionario con las respuestas básicas en español e ingles
-Variables de entorno: Se guarda Todas las credenciales de whatsapp y google para una 
administración mas segura.
-Importar threading para tareas en segundo plano
#_______________________________________________________________________________________

Cambios:
-Debido a que apesar de alimentar el google sheet asincronicamente, empeoro la duplicidad 
de los mensajes, no se realizara copia en google.
-Se eliminaran el codgio de consulta de idioma y solo se utilizara uno
-El código solo permanecera en su forma mas básica

"""
#_______________________________________________________________________________________
app = Flask(__name__)

# Configura el logger (útil para depurar en Render)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuración de base de datos SQLITE
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metapython.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Creación tabla, o modelado
class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_y_hora = db.Column(db.DateTime, default=datetime.utcnow)
    telefono_usuario_id = db.Column(db.Text)
    plataforma = db.Column(db.Text)
    mensaje = db.Column(db.Text)
    estado_usuario = db.Column(db.Text)
    etiqueta_campana = db.Column(db.Text)
    agente = db.Column(db.Text)

# Crear tabla si no existe
with app.app_context():
    db.create_all()
#_______________________________________________________________________________________

# --- Recursos ---
IMA_SALUDO_URL = "https://res.cloudinary.com/dioy4cydg/image/upload/v1747884690/imagen_index_wjog6p.jpg"
AGENTE_BOT = "Bot" # Usamos una constante para el agente

#_______________________________________________________________________________________
# --- Funciones de la Aplicación Flask ---
@app.route('/')
def index():
    """Renderiza la página principal con los registros del log."""
    registros = Log.query.all()
    registros_ordenados = sorted(registros, key=lambda x: x.fecha_y_hora, reverse=True)
    return render_template('index.html', registros=registros_ordenados)

def agregar_mensajes_log(datos_json):
    """Agrega un registro de mensaje a la base de datos."""
    datos = json.loads(datos_json)
    nuevo_registro = Log(
        telefono_usuario_id=datos.get('telefono_usuario_id'),
        plataforma=datos.get('plataforma'),
        mensaje=datos.get('mensaje'),
        estado_usuario=datos.get('estado_usuario'),
        etiqueta_campana=datos.get('etiqueta_campana'),
        agente=datos.get('agente')
    )
    db.session.add(nuevo_registro)
    db.session.commit()


def _agregar_mensajes_log_thread_safe(log_data_json):
    """Función para agregar un registro a la base de datos en un hilo."""
    with app.app_context(): # Necesario para interactuar con SQLAlchemy en un hilo
        try:
            datos = json.loads(log_data_json)
            nuevo_registro = Log(
                telefono_usuario_id=datos.get('telefono_usuario_id'),
                plataforma=datos.get('plataforma'),
                mensaje=datos.get('mensaje'),
                estado_usuario=datos.get('estado_usuario'),
                etiqueta_campana=datos.get('etiqueta_campana'),
                agente=datos.get('agente')
            )
            db.session.add(nuevo_registro)
            db.session.commit()
            logging.info(f"Registro de log añadido a DB (hilo): {datos.get('mensaje')}")
        except Exception as e:
            db.session.rollback() # Si hay un error, revertir la transacción
            logging.error(f"Error añadiendo log a DB (hilo): {e}")


# --- API WhatsApp para el envío de mensajes ---
def send_whatsapp_message(data):
    """Envía un mensaje a través de la API de WhatsApp Business."""
    data = json.dumps(data)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['META_WHATSAPP_ACCESS_TOKEN']}"
    }

    connection = http.client.HTTPSConnection("graph.facebook.com")
    try:
        connection.request("POST", f"/{os.environ['API_WHATSAPP_VERSION']}/{os.environ['META_WHATSAPP_PHONE_NUMBER_ID']}/messages", data, headers)
        response = connection.getresponse()
        logging.info(f"Respuesta de WhatsApp API: {response.status} {response.reason}")
    except Exception as e:
        logging.error(f"Error al enviar mensaje a WhatsApp: {e}")
        # No se registra aquí en la DB para evitar redundancia, se registra antes de llamar a esta función
    finally:
        connection.close()

#_______________________________________________________________________________________
# --- Uso del Token y recepción de mensajes ---
TOKEN_CODE = os.getenv('META_WHATSAPP_TOKEN_CODE')

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Maneja las solicitudes GET y POST del webhook de WhatsApp."""
    if request.method == 'GET':
        challenge = verificar_token(request)
        return challenge
    elif request.method == 'POST':
        response = recibir_mensajes(request)
        return response

def verificar_token(req):
    """Verifica el token de verificación de WhatsApp."""
    token = req.args.get('hub.verify_token')
    challenge = req.args.get('hub.challenge')

    if challenge and token == TOKEN_CODE:
        return challenge
    else:
        return jsonify({'error': 'Token Invalido'}), 401

def recibir_mensajes(req):
    """Procesa los mensajes entrantes del webhook de WhatsApp."""
    try:
        data_json = req.get_json()
        logging.info(f"Mensaje recibido: {json.dumps(data_json, indent=2)}")

        entry = data_json.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        objeto_mensaje = value.get('messages', [])

        if objeto_mensaje:
            message = objeto_mensaje[0]
            telefono_id = message.get('from')
            tipo_mensaje = message.get('type')
            
            mensaje_texto = ""
            if tipo_mensaje == 'interactive':
                interactive_type = message.get('interactive', {}).get('type')
                if interactive_type == "button_reply":
                    mensaje_texto = message.get('interactive', {}).get('button_reply', {}).get('id')
            elif tipo_mensaje == 'text':
                mensaje_texto = message.get('text', {}).get('body')

            if telefono_id and mensaje_texto:
                procesar_y_responder_mensaje(telefono_id, mensaje_texto)
            else:
                logging.info("Mensaje no procesable (sin ID de teléfono o texto de mensaje).")
        
        return jsonify({'message': 'EVENT_RECEIVED'}), 200
    except Exception as e:
        logging.error(f"Error en recibir_mensajes: {e}")
        return jsonify({'message': 'EVENT_RECEIVED_ERROR'}), 500

def procesar_y_responder_mensaje(telefono_id, mensaje_recibido):
    """
    Procesa un mensaje recibido, determina el idioma del usuario y envía la respuesta adecuada.
    Registra el mensaje entrante y la respuesta en la base de datos y Google Sheets.
    """
    mensaje_procesado = mensaje_recibido.lower()
    user_language = ""
    
    # Primero, registra el mensaje entrante
    log_data_in = {
        'telefono_usuario_id': telefono_id,
        'plataforma': 'whatsapp 📞📱💬',
        'mensaje': mensaje_recibido,
        'estado_usuario': 'recibido',
        'etiqueta_campana': 'Vacaciones',
        'agente': AGENTE_BOT
    }
    #agregar_mensajes_log(json.dumps(log_data_in))
    #exportar_eventos() # Exportar después de cada registro de mensaje

    # Delega el registro en la DB y la exportación a Google Sheets a un hilo
    threading.Thread(target=_agregar_mensajes_log_thread_safe, args=(json.dumps(log_data_in),)).start()

    # Lógica para seleccionar idioma
    if mensaje_procesado == "btn_es":
        user_language = "es"
        send_initial_messages(telefono_id, user_language)
    elif mensaje_procesado == "btn_en":
        user_language = "en"
        send_initial_messages(telefono_id, user_language)
    elif user_language in ["es", "en"]: # Si ya tiene idioma, procesar el mensaje normal
        enviar_respuesta_interactiva(telefono_id, mensaje_procesado, user_language)
    elif mensaje_procesado == "btn_si1":
        #user_language = "es"
        enviar_preguntas_interactiva(telefono_id, mensaje_procesado, user_language)
    elif mensaje_procesado == "btn_talvez1":
        #user_language = "es"
        enviar_preguntas_interactiva(telefono_id, mensaje_procesado, user_language)
    else: # Si no tiene idioma, pedirle que lo seleccione
        send_language_selection_prompt(telefono_id)


def send_initial_messages(telefono_id, lang):
    """Envía los mensajes iniciales (bienvenida, imagen, botones Si/No) después de seleccionar idioma."""
    # Saludo en el idioma elegido
    message_response = get_message(lang, "selected_language")
    send_message_and_log(telefono_id, message_response, 'text')

    # Imagen
    message_response = get_message(lang, "default_response") # Quizás 'greeting_image_caption' sea más apropiado aquí
    send_message_and_log(telefono_id, message_response, 'image')

    #Botones pregunta1
    if lang == "es":
        si = "Si"
        talvez = "Tal vez"
    else:
        si = "Yes"
        talvez = "Maybe"

    message_response = get_message(lang, "greeting_text")
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": telefono_id,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": message_response},
            "footer": {"text": "Select one of the options:"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "btn_si1", "title": si}},
                    {"type": "reply", "reply": {"id": "btn_talvez1", "title": talvez}}
                ]
            }
        }
    }

"""
    # Botones Si/No
    button_title_opcion1 = get_message(lang, "button_yes")
    button_title_opcion2 = get_message(lang, "button_no")
    message_response = get_message(lang, "greeting_text")
    send_message_and_log(telefono_id, message_response, 'button', 
                         button_titles=[button_title_opcion1, button_title_opcion2],
                         button_ids=['btn_si', 'btn_no'])

    """

def enviar_respuesta_interactiva(telefono_id, mensaje_procesado, user_language):

    #PRUEBA EN ESPAÑOL
    user_language = "es"

    """Gestiona las respuestas interactivas basadas en los botones Si/No."""
    message_response = ""
    if mensaje_procesado == "btn_si":
        message_response = get_message(user_language, "job")
    elif mensaje_procesado == "btn_no":
        message_response = get_message(user_language, "advice")
    else: # Cualquier otro mensaje de texto cuando el idioma ya está establecido
        message_response = get_message(user_language, "default_response")
    
    send_message_and_log(telefono_id, message_response, 'text')


def send_language_selection_prompt(telefono_id):
    """Envía el mensaje de bienvenida inicial y los botones de selección de idioma."""
    # Mensaje de bienvenida inicial
    message_response = get_message("es", "welcome_initial")
    send_message_and_log(telefono_id, message_response, 'text')

    # Botones para seleccionar idioma
    message_response = get_message("es", "lang_prompt")
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": telefono_id,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": message_response},
            "footer": {"text": "Select one of the options:"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "btn_es", "title": "Español"}},
                    {"type": "reply", "reply": {"id": "btn_en", "title": "English"}}
                ]
            }
        }
    }

    log_data_out = {
        'telefono_usuario_id': telefono_id,
        'plataforma': 'whatsapp 📞📱💬',
        'mensaje': message_response, # El cuerpo del mensaje interactivo
        'estado_usuario': 'enviado',
        'etiqueta_campana': 'Selección de Idioma',
        'agente': AGENTE_BOT
    }
    

    threading.Thread(target=_agregar_mensajes_log_thread_safe, args=(json.dumps(log_data_out),)).start()

    send_whatsapp_message(data)


def enviar_preguntas_interactiva(telefono_id, mensaje_procesado, user_language):

    #user_language = "es"

    """Gestiona las respuestas interactivas basadas en los botones Si/No."""
    message_response = ""
    if mensaje_procesado == "btn_si1":
        message_response = get_message(user_language, "job")
    elif mensaje_procesado == "btn_talvez1":
        message_response = get_message(user_language, "advice")
    else: # Cualquier otro mensaje de texto cuando el idioma ya está establecido
        message_response = get_message(user_language, "default_response")
    
    send_message_and_log(telefono_id, message_response, 'text')

    
def send_message_and_log(telefono_id, message_text, message_type='text', button_titles=None, button_ids=None):
    """
    Construye y envía un mensaje de WhatsApp, y registra la interacción.
    :param telefono_id: ID del teléfono del destinatario.
    :param message_text: Texto principal del mensaje.
    :param message_type: Tipo de mensaje ('text', 'image', 'button').
    :param button_titles: Lista de títulos para botones (solo para 'button' type).
    :param button_ids: Lista de IDs para botones (solo para 'button' type).
    """
    data = {}
    if message_type == 'text':
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": telefono_id,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message_text
            }
        }
    elif message_type == 'image':
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": telefono_id,
            "type": "image",
            "image": {
                "link": IMA_SALUDO_URL,
                "caption": message_text # El texto se usa como descripción de la imagen
            }
        }
    elif message_type == 'button' and button_titles and button_ids and len(button_titles) == len(button_ids):
        buttons = []
        for i in range(len(button_titles)):
            buttons.append({
                "type": "reply",
                "reply": {"id": button_ids[i], "title": button_titles[i]}
            })
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": telefono_id,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": message_text},
                "footer": {"text": "Select one of the options:"},
                "action": {"buttons": buttons}
            }
        }
    else:
        logging.warning(f"Tipo de mensaje no soportado o parámetros incompletos: {message_type}")
        return # No procesar si el tipo es incorrecto o faltan parámetros

    # Registrar el mensaje de salida y enviarlo
    log_data_out = {
        'telefono_usuario_id': telefono_id,
        'plataforma': 'whatsapp 📞📱💬',
        'mensaje': message_text, # El texto del mensaje que se envía
        'estado_usuario': 'enviado',
        'etiqueta_campana': 'Respuesta Bot',
        'agente': AGENTE_BOT
    }
    #agregar_mensajes_log(json.dumps(log_data_out))
    #exportar_eventos()

    threading.Thread(target=_agregar_mensajes_log_thread_safe, args=(json.dumps(log_data_out),)).start()

    send_whatsapp_message(data)

# --- Ejecución del Programa ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)


    