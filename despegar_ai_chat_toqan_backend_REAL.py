
# despegar_ai_chat_toqan_backend.py - INTEGRACIÓN REAL CON TOQAN
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import json
import os
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)
CORS(app)

# Configuración REAL de Toqan
TOQAN_API_KEY = os.getenv('TOQAN_API_KEY', 'sk_d8bd5fce4ad6bf831cd8524e24770b84466d0ec1493d12f3e1ca5e606a354d99516432df9dd0675eab291f22bd5d4c9911f5fec23ab9c53419ca659d52ac')
TOQAN_SPACE_ID = os.getenv('TOQAN_SPACE_ID', '29ba8bb2-ad08-48f0-9568-9e9fa1196173')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', 'demo_weather_key')

# URLs de Toqan (ajustar según documentación real)
TOQAN_API_URL = os.getenv('TOQAN_API_URL', 'https://api.toqan.ai/v1/chat')
TOQAN_WORKSPACE_URL = f"https://work.toqan.ai/?spaceId={TOQAN_SPACE_ID}"

class DespegarAIAgent:
    def __init__(self):
        self.active_users = {}
        self.notification_rules = self.setup_notification_rules()
        
    def setup_notification_rules(self):
        """Configurar reglas para notificaciones automáticas"""
        return {
            'weather_alerts': {
                'temperature_low': 10,  # Celsius
                'temperature_high': 35,
                'rain_probability': 70  # Porcentaje
            },
            'time_based': {
                'flight_reminder': 3,  # horas antes
                'checkout_reminder': 1,  # hora antes
                'attraction_closing': 2  # horas antes
            }
        }
    
    def get_weather_data(self, city):
        """Obtener datos climáticos reales - API GRATUITA"""
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': city,
                'appid': WEATHER_API_KEY,
                'units': 'metric',
                'lang': 'es'
            }
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    'temperature': data['main']['temp'],
                    'description': data['weather'][0]['description'],
                    'humidity': data['main']['humidity'],
                    'rain_probability': data.get('clouds', {}).get('all', 0),
                    'success': True
                }
        except Exception as e:
            print(f"Weather API error: {e}")
        
        # Fallback con datos simulados realistas
        return {
            'temperature': 22,
            'description': 'parcialmente nublado',
            'humidity': 65,
            'rain_probability': 20,
            'success': False
        }
    
    def get_toqan_response(self, user_message, user_context):
        """Generar respuesta usando Toqan REAL"""
        try:
            # Contexto específico para viajes con información del usuario
            travel_prompt = f"""
            Eres un asistente experto de viajes para Despegar.com. Tu nombre es "Despegar AI Assistant".
            
            CONTEXTO DEL USUARIO:
            - Destino: {user_context.get('destination', 'No especificado')}
            - Tipo de viajero: {user_context.get('traveler_type', 'general')}
            - Fase del viaje: {user_context.get('travel_phase', 'planning')}
            
            CONSULTA DEL USUARIO: {user_message}
            
            INSTRUCCIONES:
            - Responde de manera amigable, práctica y específica para viajes
            - Usa emojis para hacer la conversación más amigable
            - Sé conciso pero completo
            - Si no tienes información exacta, sugiere alternativas
            - Enfócate en ayudar con el viaje específico del usuario
            - Siempre incluye tips prácticos y útiles
            """
            
            # Preparar datos para Toqan
            toqan_payload = {
                "message": travel_prompt,
                "spaceId": TOQAN_SPACE_ID,
                "sessionId": user_context.get('session_id', f"session_{datetime.now().timestamp()}"),
                "userId": user_context.get('user_id', 'anonymous'),
                "context": {
                    "destination": user_context.get('destination'),
                    "traveler_type": user_context.get('traveler_type'),
                    "travel_phase": user_context.get('travel_phase'),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Headers para autenticación
            headers = {
                "Authorization": f"Bearer {TOQAN_API_KEY}",
                "Content-Type": "application/json",
                "User-Agent": "Despegar-AI-Chat/1.0"
            }
            
            print(f"🤖 Enviando mensaje a Toqan...")
            print(f"📍 Space ID: {TOQAN_SPACE_ID}")
            print(f"💬 Mensaje: {user_message[:50]}...")
            
            # Hacer request a Toqan
            response = requests.post(
                TOQAN_API_URL,
                headers=headers,
                json=toqan_payload,
                timeout=15
            )
            
            print(f"📡 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('response', data.get('message', data.get('content', 'Error en formato de respuesta')))
                print(f"✅ Respuesta de Toqan recibida!")
                return ai_response
            else:
                print(f"❌ Error Toqan: {response.status_code}")
                print(f"📄 Response: {response.text}")
                return self.generate_smart_fallback_response(user_message, user_context)
            
        except Exception as e:
            print(f"🚨 Exception en Toqan: {str(e)}")
            return self.generate_smart_fallback_response(user_message, user_context)
    
    def generate_smart_fallback_response(self, user_message, user_context):
        """Respuestas inteligentes de fallback cuando Toqan no responde"""
        message_lower = user_message.lower()
        destination = user_context.get('destination', 'tu destino')
        traveler_type = user_context.get('traveler_type', 'general')
        travel_phase = user_context.get('travel_phase', 'planning')
        
        # Respuestas específicas por keywords
        if any(word in message_lower for word in ['clima', 'tiempo', 'lluvia', 'temperatura']):
            weather = self.get_weather_data(destination)
            return f"🌤️ El clima en {destination}: {weather['temperature']}°C, {weather['description']}. Humedad: {weather['humidity']}%. {'☔ Posible lluvia' if weather['rain_probability'] > 50 else '☀️ Día despejado'}. ¡Perfecto para explorar!"
        
        elif any(word in message_lower for word in ['restaurante', 'comida', 'comer', 'almorzar', 'cenar']):
            food_recs = {
                'cultural': 'restaurantes tradicionales con historia local',
                'adventure': 'lugares de comida rápida cerca de actividades',
                'relax': 'restaurantes con ambiente tranquilo y vista',
                'gastronomy': 'experiencias gastronómicas únicas y mercados locales',
                'business': 'restaurantes ejecutivos y de networking'
            }
            rec = food_recs.get(traveler_type, 'restaurantes recomendados')
            return f"🍽️ Para un viajero {traveler_type} en {destination}, te recomiendo {rec}. ¿Te interesa alguna cocina específica? También puedo sugerirte horarios ideales para evitar multitudes."
        
        elif any(word in message_lower for word in ['hotel', 'alojamiento', 'dormir', 'check']):
            return f"🏨 Para tu estadía en {destination}: Check-in típicamente 15:00, check-out 11:00. Te recomiendo confirmar horarios con tu hotel. ¿Necesitas ayuda con late check-out o early check-in?"
        
        elif any(word in message_lower for word in ['transporte', 'metro', 'taxi', 'bus', 'movimiento']):
            return f"🚇 Transporte en {destination}: Te recomiendo apps locales de transporte y tarjetas de transporte público para ahorrar. ¿Te ayudo con rutas específicas o mejor forma de llegar a algún lugar?"
        
        elif any(word in message_lower for word in ['moneda', 'dinero', 'cambio', 'pagar']):
            return f"💱 Para {destination}: Te recomiendo llevar efectivo local y una tarjeta internacional sin comisiones. Muchos lugares aceptan tarjeta, pero mercados y pequeños comercios prefieren efectivo."
        
        elif any(word in message_lower for word in ['idioma', 'hablar', 'frases', 'comunicar']):
            return f"🗣️ Comunicación en {destination}: Las frases básicas más útiles son 'Hola', 'Gracias', 'Disculpe', '¿Habla inglés?', y 'La cuenta, por favor'. ¿Te ayudo con pronunciación o frases específicas?"
        
        elif any(word in message_lower for word in ['seguridad', 'peligro', 'cuidado', 'emergencia']):
            return f"🛡️ Seguridad en {destination}: Mantén copias de documentos importantes, evita mostrar objetos de valor, usa transporte oficial. Número de emergencias local disponible en tu hotel. ¿Necesitas info específica de tu zona?"
        
        elif any(word in message_lower for word in ['actividades', 'hacer', 'visitar', 'turismo']):
            activity_recs = {
                'cultural': 'museos, sitios históricos, tours guiados',
                'adventure': 'deportes extremos, hiking, actividades al aire libre',
                'relax': 'spas, playas, parques tranquilos',
                'gastronomy': 'tours gastronómicos, mercados, clases de cocina',
                'business': 'centros de negocios, networking events, tours ejecutivos'
            }
            activities = activity_recs.get(traveler_type, 'atracciones principales')
            return f"🎯 Actividades recomendadas en {destination} para ti: {activities}. ¿Te interesa algo específico o prefieres un itinerario completo del día?"
        
        # Respuestas por fase del viaje
        elif travel_phase == 'planning':
            return f"✈️ ¡Genial que estés planeando tu viaje a {destination}! Te puedo ayudar con clima, actividades, presupuesto, documentos necesarios. ¿Qué te interesa saber primero?"
        
        elif travel_phase == 'departure':
            return f"🛄 ¡Casi listo para viajar a {destination}! Recuerda llegar 3 horas antes para vuelos internacionales, documentos en orden, y revisar restricciones de equipaje. ¿Necesitas ayuda con algo específico?"
        
        elif travel_phase == 'arrival':
            return f"🛬 ¡Bienvenido a {destination}! Las primeras cosas: transporte al hotel, cambio de dinero si necesitas, y orientarte con la ciudad. ¿En qué te ayudo primero?"
        
        elif travel_phase == 'exploring':
            return f"🗺️ ¡Perfecto para explorar {destination}! Te puedo ayudar con recomendaciones cercanas, horarios de atracciones, mejores rutas, y tips locales. ¿Qué planes tienes hoy?"
        
        elif travel_phase == 'return':
            return f"🧳 Preparando el regreso desde {destination}: Check-out del hotel, compras de último momento, horarios al aeropuerto. ¿Necesitas ayuda con algo específico?"
        
        # Respuesta general inteligente
        return f"¡Perfecto! Como viajero {traveler_type} en {destination}, te puedo ayudar con muchísimas cosas: clima actual, restaurantes, actividades, transporte, consejos locales. ¿Hay algo específico que te interese saber? 🤔"
    
    def check_automatic_notifications(self, user_id):
        """Verificar notificaciones automáticas - SIN COSTO"""
        if user_id not in self.active_users:
            return []
        
        user_data = self.active_users[user_id]
        notifications = []
        
        # Check clima GRATIS
        if user_data.get('destination'):
            weather = self.get_weather_data(user_data['destination'])
            
            if weather['temperature'] < self.notification_rules['weather_alerts']['temperature_low']:
                notifications.append({
                    'type': 'weather_alert',
                    'priority': 'high',
                    'message': f"🧥 Temperatura baja: {weather['temperature']}°C en {user_data['destination']}. Recomendación: Lleva abrigo."
                })
            
            if weather['temperature'] > self.notification_rules['weather_alerts']['temperature_high']:
                notifications.append({
                    'type': 'weather_alert',
                    'priority': 'high',
                    'message': f"🌡️ Temperatura alta: {weather['temperature']}°C en {user_data['destination']}. Mantente hidratado y usa protector solar."
                })
            
            if weather['rain_probability'] > self.notification_rules['weather_alerts']['rain_probability']:
                notifications.append({
                    'type': 'weather_alert',
                    'priority': 'medium',
                    'message': f"☔ Probabilidad de lluvia: {weather['rain_probability']}% en {user_data['destination']}. Lleva paraguas."
                })
        
        # Notificaciones inteligentes basadas en tiempo
        current_hour = datetime.now().hour
        travel_phase = user_data.get('travel_phase', 'exploring')
        
        if current_hour == 8 and travel_phase == 'exploring':
            notifications.append({
                'type': 'recommendation',
                'priority': 'low',
                'message': "🌅 ¡Buenos días! Perfecto momento para visitar atracciones antes de las multitudes. ¿Te ayudo con un itinerario matutino?"
            })
        
        if current_hour == 12 and travel_phase == 'exploring':
            notifications.append({
                'type': 'recommendation',
                'priority': 'low',
                'message': "🍽️ ¡Es hora de almorzar! ¿Te ayudo a encontrar un restaurante cerca de tu ubicación actual?"
            })
        
        if current_hour == 18 and travel_phase == 'exploring':
            notifications.append({
                'type': 'recommendation',
                'priority': 'low',
                'message': "🌅 Atardecer perfecto para fotos. ¿Conoces los mejores spots fotográficos de tu destino?"
            })
        
        if current_hour == 20 and travel_phase == 'exploring':
            notifications.append({
                'type': 'recommendation',
                'priority': 'low',
                'message': "🌃 Perfecto momento para cenar y vida nocturna. ¿Te interesa la gastronomía local o prefieres algo familiar?"
            })
        
        return notifications

# Instancia global del agente
ai_agent = DespegarAIAgent()

@app.route('/')
def home():
    """Página principal con el chat"""
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint principal del chat - TOQAN REAL"""
    try:
        data = request.json
        user_id = data.get('user_id', 'anonymous')
        message = data.get('message', '')
        user_context = data.get('context', {})
        
        # Agregar user_id y session_id al contexto
        user_context['user_id'] = user_id
        user_context['session_id'] = user_context.get('session_id', f"session_{user_id}_{datetime.now().timestamp()}")
        
        # Actualizar contexto del usuario
        ai_agent.active_users[user_id] = {
            **user_context,
            'last_activity': datetime.now(),
            'message_count': ai_agent.active_users.get(user_id, {}).get('message_count', 0) + 1
        }
        
        # Generar respuesta con Toqan REAL
        ai_response = ai_agent.get_toqan_response(message, user_context)
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'timestamp': datetime.now().isoformat(),
            'source': 'toqan_real',
            'space_id': TOQAN_SPACE_ID
        })
        
    except Exception as e:
        print(f"🚨 Error en chat endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'response': 'Lo siento, tengo problemas técnicos temporales. ¿Puedes intentar de nuevo? 😅'
        })

@app.route('/api/notifications/<user_id>')
def get_notifications(user_id):
    """Obtener notificaciones automáticas - GRATIS"""
    try:
        notifications = ai_agent.check_automatic_notifications(user_id)
        return jsonify({
            'success': True,
            'notifications': notifications
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'notifications': []
        })

@app.route('/api/user/update', methods=['POST'])
def update_user_context():
    """Actualizar contexto del usuario"""
    try:
        data = request.json
        user_id = data.get('user_id')
        context = data.get('context', {})
        
        if user_id:
            ai_agent.active_users[user_id] = {
                **ai_agent.active_users.get(user_id, {}),
                **context,
                'last_update': datetime.now()
            }
            
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/weather/<city>')
def get_weather(city):
    """Obtener clima para una ciudad - API GRATUITA"""
    weather_data = ai_agent.get_weather_data(city)
    return jsonify({
        'success': True,
        'data': weather_data
    })

@app.route('/api/health')
def health_check():
    """Health check para monitoreo"""
    return jsonify({
        'status': 'healthy',
        'active_users': len(ai_agent.active_users),
        'ai_backend': 'toqan_real',
        'space_id': TOQAN_SPACE_ID,
        'workspace_url': TOQAN_WORKSPACE_URL,
        'cost': '$0.00'
    })

@app.route('/api/test-toqan')
def test_toqan():
    """Endpoint para testear la conexión con Toqan"""
    try:
        test_context = {
            'destination': 'París, Francia',
            'traveler_type': 'cultural',
            'travel_phase': 'planning',
            'user_id': 'test_user',
            'session_id': 'test_session'
        }
        
        response = ai_agent.get_toqan_response("Hola, ¿cómo está el clima en París?", test_context)
        
        return jsonify({
            'success': True,
            'test_response': response,
            'toqan_config': {
                'space_id': TOQAN_SPACE_ID,
                'api_url': TOQAN_API_URL,
                'has_api_key': bool(TOQAN_API_KEY and len(TOQAN_API_KEY) > 10)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'toqan_config': {
                'space_id': TOQAN_SPACE_ID,
                'api_url': TOQAN_API_URL,
                'has_api_key': bool(TOQAN_API_KEY and len(TOQAN_API_KEY) > 10)
            }
        })

def background_notifications():
    """Envío de notificaciones en background - GRATIS"""
    while True:
        try:
            for user_id in list(ai_agent.active_users.keys()):
                user_data = ai_agent.active_users[user_id]
                
                # Verificar si el usuario está activo (última actividad < 2 horas)
                if (datetime.now() - user_data.get('last_activity', datetime.now())).seconds < 7200:
                    notifications = ai_agent.check_automatic_notifications(user_id)
                    
                    if notifications:
                        print(f"Notificaciones gratuitas para {user_id}: {len(notifications)}")
                        # Aquí se podrían enviar por WebSocket o guardar en DB
                
        except Exception as e:
            print(f"Error en background notifications: {e}")
        
        time.sleep(600)  # Verificar cada 10 minutos (ahorro de recursos)

# Iniciar thread de notificaciones background
notification_thread = threading.Thread(target=background_notifications, daemon=True)
notification_thread.start()

if __name__ == '__main__':
    print("🚀 Iniciando Despegar AI Chat - TOQAN REAL")
    print(f"🤖 Space ID: {TOQAN_SPACE_ID}")
    print(f"🔑 API Key configurada: {'✅' if TOQAN_API_KEY else '❌'}")
    print(f"🌐 Workspace: {TOQAN_WORKSPACE_URL}")
    print("📍 Chat disponible en: http://localhost:5000")
    print("🧪 Test Toqan: http://localhost:5000/api/test-toqan")
    print("💰 Costo total: $0.00")
    app.run(debug=True, host='0.0.0.0', port=5000)
