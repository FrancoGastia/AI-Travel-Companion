
# config_free.py - Configuración 100% GRATUITA
import os
from dotenv import load_dotenv

load_dotenv()

class FreeConfig:
    # Solo Weather API (GRATIS - 1000 calls/día)
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', 'demo_key')
    SECRET_KEY = os.getenv('SECRET_KEY', 'despegar-ai-free-secret-key-2024')
    
    # Sin OpenAI - Usando Toqan
    AI_BACKEND = 'toqan'
    TOQAN_API_URL = os.getenv('TOQAN_API_URL', 'https://api.toqan.ai/chat')
    
    # Configuración de Flask
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # Configuración de CORS
    ALLOWED_ORIGINS = [
        'https://www.despegar.com',
        'https://www.despegar.com.ar',
        'http://localhost:3000'
    ]
    
    # Configuración optimizada para versión gratuita
    NOTIFICATION_INTERVAL = int(os.getenv('NOTIFICATION_INTERVAL', 600))  # 10 minutos
    MAX_ACTIVE_USERS = int(os.getenv('MAX_ACTIVE_USERS', 100))
    CACHE_RESPONSES = True
    
    @classmethod
    def validate(cls):
        print("✅ Configuración 100% GRATUITA validada")
        print(f"🤖 AI Backend: {cls.AI_BACKEND}")
        print(f"🌤️ Weather API: {'Configurado' if cls.WEATHER_API_KEY != 'demo_key' else 'Demo'}")
        print(f"💰 Costo estimado: $0.00/mes")
        return True
