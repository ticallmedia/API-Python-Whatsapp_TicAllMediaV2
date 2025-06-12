MESSAGES = {
    "es":{
        "welcome_initial": "👋😊!Hola¡ Bienvenido a TicAll Media.",
        "lang_prompt": "Por favor, elige tu idioma: 👆 \n",
        "selected_language": "👌!Idioma configurado en Español¡. ",
        "invalid_option": "Opción no válida. Por favor, selecciona. ",
        "default_response": "¿En qué puedo ayudarte?",
        "change_language": "Claro, ¿a que Idioma te gustaría cambiar?. ", 
        "greeting_text1": "¡Saludos! 🤖 ¿Intrigado por una estrategia de marketing más inteligente?",
        "greeting_text2": "En TicAll Media, tenemos ideas que podrían sorprenderte.\n\n¿Te animas a explorar?",
        "greeting_text3": "----revisar texto alternativo ----",
        "job": "💼 ¿En que industria te desempeñas?", 
        "advice1": "Tenemos experiencia en este mercado, ¿te gustaría agendar una cita con TicAll Media? 🗓️",
        "advice2": "🧐¿Buscas asesoría sobre algún servicio especial? ",
        "portfolio": "🚀 Hola, ¿buscas asesoría sobre algún servicio especial?\n\n📌 Por favor, ingresa un número #️⃣ para recibir información.\n\n1️⃣. DDA And Mobile Campaigns. 📱\n2️⃣. WebSites. 🌐\n3️⃣. Photography. 📸\n4️⃣. Content Marketing. ✍️\n5️⃣. Media Strategy. 📈\n6️⃣. Digital Marketing. 💻\n7️⃣. Paid Social Media. 📊\n8️⃣. Ecommerce Strategy. 🛒\n9️⃣. Display Media Planning. 📺\n0️⃣. Hablar con un Agente. 🗣️",
        "schedule": "¡Perfecto! 😊 \n\\n Selecciona el día y la hora que más te convenga en el siguiente enlace. Nos reuniremos y haremos un diagnóstico gratuito de tu negocio para identificar estrategias de mejora en tus activos y en tu marketing.",
        "calendar": "👉 [Haz clic aquí para agendar tu cita](https://tucalendario.com/nombre)",
        "farewell": "¡Estupendo! La inteligencia en marketing te espera. Te veremos pronto, We will grow together!"


    },
    "en": {
        "welcome_initial": "👋😊!Hi there! Welcome to TicAll Media.",
    "lang_prompt": "Please choose your language: 👆 \n",
    "selected_language": "👌!Language set to English!",
    "invalid_option": "Invalid option. Please select from the available choices. ",
    "default_response": "How can I help you?",
    "change_language": "Sure, what language would you like to switch to? ",
    "greeting_text1": "Greetings! 🤖 Intrigued by a smarter marketing strategy?",
    "greeting_text2": "At TicAll Media, we have ideas that might surprise you.\n\nReady to explore?",
    "greeting_text3": "----review alternative text ----",
    "job": "💼 What industry are you in?",
    "advice1": "We have experience in this market. Would you like to schedule an appointment with TicAll Media? 🗓️",
    "advice2": "🧐 Looking for advice on a special service?",
    "portfolio": "🚀 Hi, are you looking for advice on a special service?\n\n📌 Please enter a number #️⃣ to receive information.\n\n1️⃣. DDA And Mobile Campaigns. 📱\n2️⃣. WebSites. 🌐\n3️⃣. Photography. 📸\n4️⃣. Content Marketing. ✍️\n5️⃣. Media Strategy. 📈\n6️⃣. Digital Marketing. 💻\n7️⃣. Paid Social Media. 📊\n8️⃣. Ecommerce Strategy. 🛒\n9️⃣. Display Media Planning. 📺\n0️⃣. Talk to an Agent. 🗣️",
    "schedule": "Perfect! 😊 \n\\n Select the day and time that suits you best using the following link. We'll meet and provide a free diagnosis of your business to identify improvement strategies for your assets and marketing.",
    "calendar": "👉 [Click here to schedule your appointment](https://yourcalendar.com/name)",
    "farewell": "Awesome! Marketing intelligence awaits you. See you soon, We will grow together!"
    }
}

def get_message(lang,key):
    """
    Obtine el mensaje traducido leyendo el diccionario MESSAGE
    lang: 'en' para inglés, 'es' para español
    key: la clave del mensaje ('welcome_initial','selected_language)    
    """
    #Sí el idioma no existe o no se elige por defecto sera ingles
    return MESSAGES.get(lang, MESSAGES["en"]).get(key,MESSAGES["en"][key])
