from flask import Flask, request,json, jsonify, render_template, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import http.client

import os
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from dotenv import load_dotenv
from translations import get_message
load_dotenv()

#_______________________________________________________________________________________
"""
Descripción: Primer Bot de Whatsapp para la empresa TicAll Media, 
con descarga en Google Sheet de Conversaciones

Caracteristicasz: 
-Elegir idioma
-guardar seleccion del idioma en el id o telefono
-cambiar idioma inicial
-uso de diccionario para respuesta
"""
#_______________________________________________________________________________________
app = Flask(__name__)

#Configuracion de base de datos SQLITE
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metapython.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


#Creación tabla, o modelado
class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_y_hora = db.Column(db.DateTime, default=datetime.utcnow)
    telefono_usuario_id = db.Column(db.Text)
    plataforma = db.Column(db.Text)
    mensaje = db.Column(db.Text)
    estado_usuario = db.Column(db.Text)
    etiqueta_campana = db.Column(db.Text)
    agente = db.Column(db.Text)


#Crear tabla si no existe
with app.app_context():
    db.create_all()

#_______________________________________________________________________________________
#Recursos

#URL de mensaje de bienvenida
IMA_SALUDO_URL= "https://res.cloudinary.com/dioy4cydg/image/upload/v1747884690/imagen_index_wjog6p.jpg"

#Diccionario de seleccioón de idioma
USERS_FILE = 'users.json'

def load_users():
    #carga el idioma del usuario
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    #Guarda la preferencia de idioma del usuario
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def get_user_language(user_id):
    #obtiene el idioma preferido
    users = load_users()
    return users.get(user_id, {}).get("language","en")#por defecto ingles

def set_user_language(user_id, lang):
    #establece el idioma preferido 
    users = load_users()

    if user_id not in users:
        users[user_id]["language"] = lang
        save_users(users)



catalogo = False
agente = "Bot"
language = ""

#_______________________________________________________________________________________
#Ejecucion del Programa
@app.route('/')

#_______________________________________________________________________________________
#Funciones

def index():
    registros = Log.query.all()
    registros_ordenados = ordernar_fecha(registros)
    return render_template('index.html', registros= registros_ordenados)

def ordernar_fecha(registros):
    return sorted(registros, key=lambda x: x.fecha_y_hora, reverse=True)

#agregar informacion a la base de datos
mensajes_log = []

#Funcion para agregar informacicon a la bd

def agregar_mensajes_log(datos_json):
    datos = json.loads(datos_json)
    telefono_usuario_id = datos['telefono_usuario_id']
    plataforma = datos['plataforma']
    mensaje = datos['mensaje']
    estado_usuario = datos['estado_usuario']
    etiqueta_campana = datos['etiqueta_campana']
    agente = datos['agente']

    #guardar mensajes en la base de datos
    nuevo_registro = Log(telefono_usuario_id = telefono_usuario_id, plataforma = plataforma, mensaje = mensaje, estado_usuario = estado_usuario, etiqueta_campana = etiqueta_campana, agente = agente)
    db.session.add(nuevo_registro)
    db.session.commit()

#_______________________________________________________________________________________
#API de Google Sheet para exportar información
def exportar_eventos():
    try:
        # Obtener eventos desde SQLAlchemy
        eventos = Log.query.all()

        creds_dict = get_google_credentials_from_env()

        # Configurar acceso a Google Sheets
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]   

        # Convertir el diccionario a un objeto tipo archivo usando json.dumps + StringIO
        from io import StringIO
        json_creds = json.dumps(creds_dict)
        
        # Obtener credenciales desde variables de entorno
        creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(json_creds), scope)

        # Autenticar con gspread
        client = gspread.authorize(creds)

        # Acceder al Google Sheet
        sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/15dzMHXaVdssg9mHXiepkFn6ajAhaAlss9HAL6NHM6G0/edit?usp=drive_link').sheet1
        #sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1juGRsV5fSs_4LFvAiJNQE8TUMVr8c5KAW-pMaEo6Rh4/edit?usp=drive_link').sheet1
        
        #buscar un texto
        titulos = []

        cells = sheet.findall('ID')
        for i in cells:
            titulos.append(i.address)
            
        if not titulos:    
            # Escribir encabezados
            sheet.clear()
            sheet.append_row(["ID", "Fecha y Hora", "Teléfono - Usuario ID", "Plataforma", "Mensaje", "Estado Usuario", "Etiqueta - Campaña", "Agente"])

            # aplicando formato y color al titulo
            formato = {
                "backgroundColor": {
                    "red": 0.2,  # Un poco de rojo
                    "green": 0.4, # Un poco de verde
                    "blue": 0.8, # Azul más pronunciado para un tono medio
                },
                "textFormat": {
                    "bold": True,
                    "foregroundColor": {
                        "red": 1.0,
                        "green": 1.0,
                        "blue": 1.0,
                    }
                }
            }
            sheet.format("A1:H1", formato)

        # Asegúrate de que la lista no esté vacía
        if eventos:
            ultimo_evento = eventos[-1]
            sheet.append_row([
                ultimo_evento.id,
                ultimo_evento.fecha_y_hora.strftime('%Y-%m-%d %H:%M:%S'),
                ultimo_evento.telefono_usuario_id,
                ultimo_evento.plataforma,
                ultimo_evento.mensaje,
                ultimo_evento.estado_usuario,
                ultimo_evento.etiqueta_campana,
                ultimo_evento.agente
            ])


        return jsonify({'message': 'Eventos exportados exitosamente a Google Sheets'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

#credenciales google en variables de entorno
def get_google_credentials_from_env():
    creds_dict = {
        "type": os.environ["GOOGLE_TYPE"],
        "project_id": os.environ["GOOGLE_PROJECT_ID"],
        "private_key_id": os.environ["GOOGLE_PRIVATE_KEY_ID"],
        "private_key": os.environ["GOOGLE_PRIVATE_KEY"].replace("\\n", "\n"),
        "client_email": os.environ["GOOGLE_CLIENT_EMAIL"],
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "auth_uri": os.environ["GOOGLE_AUTH_URI"],
        "token_uri": os.environ["GOOGLE_TOKEN_URI"],
        "auth_provider_x509_cert_url": os.environ["GOOGLE_AUTH_PROVIDER_CERT_URL"],
        "client_x509_cert_url": os.environ["GOOGLE_CLIENT_CERT_URL"]
    }
    return creds_dict


#_______________________________________________________________________________________
#Uso del Token y recepcion de mensajes

TOKEN_CODE = 'TICALLCODE'

@app.route('/webhook', methods = ['GET','POST'])

def webhook():
    if request.method == 'GET':
        challenge = verificar_token(request)
        return challenge
    elif request.method == 'POST':
        reponse = recibir_mensajes(request)
        return reponse

def verificar_token(req):
    token = req.args.get('hub.verify_token')
    challenge = req.args.get('hub.challenge')

    if challenge and token == TOKEN_CODE:
        return challenge
    else:
        return jsonify({'error': 'Token Invalido'}),401

def recibir_mensajes(req):
    try:
        req = request.get_json()
        entry = req['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        objeto_mensaje = value['messages']

        #identificaion del tipo de dato
        if objeto_mensaje:
            messages = objeto_mensaje[0]

            if "type" in messages:
                tipo = messages['type']

                if tipo == 'interactive':
                    return 0
                    """
                    tipo_interactivo = messages['interactive']['type']

                    if tipo_interactivo == "button_reply":
                        mensaje = messages['interactive']['button_reply']['id']
                        telefono_id = messages['from']

                        agregar_mensajes_log(json.dumps({'telefono_usuario_id': telefono_id, 'plataforma': 'whatsapp 📞📱💬', 'mensaje': mensaje, 'estado_usuario': 'nuevo', 'etiqueta_campana': 'Vacaciones', 'agente': 'ninguno' }))
                        exportar_eventos()
                        enviar_mensaje_whatsapp(telefono_id,mensaje)
                    """
                if "text" in messages:
                    mensaje  = messages['text']['body']
                    telefono_id = messages['from']

                    agregar_mensajes_log(json.dumps({'telefono_usuario_id': telefono_id, 'plataforma': 'whatsapp 📞📱💬', 'mensaje': mensaje, 'estado_usuario': 'nuevo', 'etiqueta_campana': 'Vacaciones', 'agente': 'ninguno' }))
                    exportar_eventos()
                    enviar_mensaje_whatsapp(telefono_id,mensaje)

        return jsonify({'message':'EVENT_RECEIVED'})
    except Exception as e:
        return jsonify({'message':'EVENT_RECEIVED'})
    
#_______________________________________________________________________________________
#Enviar mensajes a whatsapp
def enviar_mensaje_whatsapp(telefono_id,mensaje):
    mensaje = mensaje.lower()
    MESSAGE_RESPONSE = ""
    
    user_language = get_user_language(telefono_id)
    response_idioma = ""

    if "hi" in mensaje or "hola" in mensaje or "start":
        response_idioma = get_message(user_language,"welcome_initial")
        
        MESSAGE_RESPONSE = response_idioma
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": telefono_id,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": MESSAGE_RESPONSE
            }
        }
    elif "1" in mensaje:
        set_user_language(telefono_id,"en")
        response_idioma = get_message("en", "selected_language")

        MESSAGE_RESPONSE = response_idioma
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": telefono_id,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": MESSAGE_RESPONSE
            }
        }
    elif "2" in mensaje:
        set_user_language(telefono_id,"es")
        response_idioma = get_message("es", "selected_language")

        MESSAGE_RESPONSE = response_idioma
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": telefono_id,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": MESSAGE_RESPONSE
            }
        }
    else:
        response_idioma = get_message("en","lang_prompt")
    
        MESSAGE_RESPONSE = response_idioma
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": telefono_id,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": MESSAGE_RESPONSE
            }
        }

        """
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": telefono_id,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "🚀 Hola, visita mi web https://ticallmedia.com/.com para más información.\n \n📌Por favor, ingresa un número #️⃣ para recibir información.\n \n1️⃣. Información de los Servicios. 💼\n2️⃣. Ubicación del local. 📍\n3️⃣. Enviar catalogo en PDF. 📄\n4️⃣. Audio explicando a mayor detalle. 🎧\n5️⃣. Video de Introducción. ⏯️\n6️⃣. Hablar con un Agente. 🙋‍♂️\n7️⃣. Horario de Atención. 🕜 \n0️⃣. Regresar al Menú. 🕜"
            }
        }
        
        if user_language:
            response_idioma = get_message(user_language,"default_response")

            MESSAGE_RESPONSE = response_idioma
            data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": telefono_id,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": MESSAGE_RESPONSE
                }
            }
        else:
            response_idioma = get_message("en","lang_prompt")
        
            MESSAGE_RESPONSE = response_idioma
            data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": telefono_id,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": MESSAGE_RESPONSE
                }
            }
        """


    
    agregar_mensajes_log(json.dumps({'telefono_usuario_id': telefono_id, 'plataforma': 'whatsapp 📞📱💬', 'mensaje': MESSAGE_RESPONSE, 'estado_usuario': 'nuevo', 'etiqueta_campana': 'Vacaciones', 'agente': agente }))
    exportar_eventos()

    data = json.dumps(data)

    #datos META
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer EAASP0HB8jAsBOymZAoWysh3biLLOVLS3dYoAYZA9jl2xKZBpZAm3W2TxEdKRMTsZB3hEVbze2OJP4HKPe5pujCqXUUo7ZBAk0eLgVzGHyKScY33aqhoAtPouk9oPC1XigqXM3bq2KLWSMIdRklJOGYr5SYzalpn0EsA1GlQg67d4qBInlt8oTigoHgh43KLXt4LgZDZD"
    }

    connection = http.client.HTTPSConnection("graph.facebook.com")

    try:
        connection.request("POST","/v22.0/593835203818298/messages",data, headers)
        response = connection.getresponse()
        print(response.status, response.reason)
    
    except Exception as e:
        agregar_mensajes_log(json.dumps(e))
    finally:
        connection.close()



#_______________________________________________________________________________________

if __name__=='__main__':
    app.run(host='0.0.0.0',port=80,debug=True)
#_______________________________________________________________________________________


