from flask import Flask, request,json, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import http.client

#_______________________________________________________________________________________
"""
Descripción: Primer Bot de Whatsapp para la empresa TicAll Media, 
con descarga en Google Sheet de Conversaciones


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
    """
    prueba1 = Log(telefono_usuario_id = '111111', plataforma = 'whatsapp', mensaje = 'Mensaje prueba 1', estado_usuario = 'Nuevo', etiqueta_campana = 'Vacaciones', agente = 'Ninguno')
    db.session.add(prueba1)
    db.session.commit()
    """
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

#llamar la fucion de mesajes de ejemplo
#agregar_mensajes_log(json.dump('test1'))
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

                if "text" in messages:
                    mensaje  = messages['text']['body']
                    telefono_id = messages['from']

                    agregar_mensajes_log(json.dumps({'telefono_usuario_id': telefono_id, 'plataforma': 'whatsapp', 'mensaje': mensaje, 'estado_usuario': 'nuevo', 'etiqueta_campana': 'Vacaciones', 'agente': 'ninguno' }))
                    enviar_mensaje_whatsapp(telefono_id,mensaje)

        return jsonify({'message':'EVENT_RECEIVED'})
    except Exception as e:
        return jsonify({'message':'EVENT_RECEIVED'})
    
#_______________________________________________________________________________________
#Enviar mensajes a whatsapp
def enviar_mensaje_whatsapp(telefono_id,mensaje):
    mensaje = mensaje.lower()
    body_mensaje = ""

    if "hola" in mensaje:
        body_mensaje = "🚀 Hola, ¿Cómo estás? Bienvenido."
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": telefono_id,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": body_mensaje
            }
        }
    else:
        body_mensaje = "🚀 Hola, ¿Cómo estás? Bienvenido."
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": telefono_id,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": body_mensaje
            }
        }
    
    agregar_mensajes_log(json.dumps({'telefono_usuario_id': telefono_id, 'plataforma': 'whatsapp', 'mensaje': mensaje, 'estado_usuario': 'nuevo', 'etiqueta_campana': 'Vacaciones', 'agente': 'ninguno' }))

    data = json.dumps(data)

    #datos META
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer EAASP0HB8jAsBO9kB0xCrOpOMo3HxLzqCdQ9RQjvYM00andK9mgAcyONYtz8onfeDwNMGOVSO9fruwWZC2bnsNzpzuLtikUSUnSZBXiRZC51OSI3SyD60XdNseDg8aHAW304sQDI7VE5YfpZC0tZCOlVZAdiHweEalSZCR9bVm0SZCdfWT7jzEjmrxKX1g5BTcMRoyYbqOcVmgCnZCP2vZApwBdxBQibU1RCvFA3msZD"
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


