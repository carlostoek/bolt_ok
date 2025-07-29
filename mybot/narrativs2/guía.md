# 🌸 Guía Completa de Implementación del Bot Diana

## Tabla de Contenido
1. [Preparación del Entorno](#preparación-del-entorno)
2. [Configuración de la Base de Datos](#configuración-de-la-base-de-datos)
3. [Configuración del Bot de Telegram](#configuración-del-bot-de-telegram)
4. [Implementación Paso a Paso](#implementación-paso-a-paso)
5. [Testing y Validación](#testing-y-validación)
6. [Deployment en Producción](#deployment-en-producción)
7. [Monitoreo y Optimización](#monitoreo-y-optimización)
8. [Casos de Uso Específicos](#casos-de-uso-específicos)

---

## Preparación del Entorno

### Requisitos del Sistema

**Servidor Recomendado:**
- CPU: 4 cores mínimo (8 cores recomendado para 1000+ usuarios)
- RAM: 8GB mínimo (16GB recomendado)
- Almacenamiento: 100GB SSD (la base de datos emocional crece aproximadamente 50MB por 1000 usuarios activos por mes)
- Conexión: Latencia baja (importante para las respuestas "naturales" de Diana)

**Software Base:**
```bash
# Ubuntu 22.04 LTS (recomendado)
sudo apt update && sudo apt upgrade -y

# Python 3.11+ (crucial para async performance)
sudo apt install python3.11 python3.11-venv python3.11-dev

# PostgreSQL 15+ (necesario para funciones avanzadas de texto)
sudo apt install postgresql-15 postgresql-contrib-15

# Redis (para cache y sesiones)
sudo apt install redis-server

# Nginx (proxy reverso)
sudo apt install nginx

# Herramientas de monitoreo
sudo apt install htop iotop netstat-nat
```

### Estructura de Proyecto

```
diana_bot/
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── diana_brain_system.py      # Sistema emocional principal
│   │   ├── advanced_systems.py        # Contradicciones y círculos
│   │   ├── database_manager.py        # Gestión de DB
│   │   └── config.py                  # Configuración centralizada
│   ├── telegram/
│   │   ├── __init__.py
│   │   ├── bot_handlers.py            # Manejadores de Telegram
│   │   └── content_scheduler.py       # Sistema de contenido programado
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logging_config.py          # Configuración de logs
│   │   └── metrics.py                 # Sistema de métricas
│   └── main.py                        # Punto de entrada principal
├── tests/
│   ├── test_emotional_engine.py       # Tests del motor emocional
│   ├── test_contradictions.py         # Tests de contradicciones
│   └── test_database.py               # Tests de base de datos
├── deployment/
│   ├── docker-compose.yml             # Orquestación de servicios
│   ├── Dockerfile                     # Imagen del bot
│   ├── nginx.conf                     # Configuración de Nginx
│   └── systemd/                       # Servicios de sistema
├── scripts/
│   ├── setup_database.py              # Configuración inicial de DB
│   ├── backup_emotional_data.py       # Backup de datos emocionales
│   └── migrate_user_data.py           # Migración de datos
├── docs/
│   ├── emotional_theory.md            # Teoría detrás del sistema
│   └── troubleshooting.md             # Solución de problemas
├── requirements.txt                   # Dependencias Python
└── .env.example                       # Variables de entorno
```

---

## Configuración de la Base de Datos

### Paso 1: Configuración de PostgreSQL

```bash
# Crear usuario y base de datos para Diana
sudo -u postgres psql

-- En el shell de PostgreSQL:
CREATE USER diana_bot WITH PASSWORD 'tu_password_super_seguro';
CREATE DATABASE diana_emotional_db OWNER diana_bot;

-- Otorgar permisos necesarios
GRANT ALL PRIVILEGES ON DATABASE diana_emotional_db TO diana_bot;

-- Habilitar extensiones necesarias para búsqueda de texto completo
\c diana_emotional_db
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

\q
```

### Paso 2: Configuración Optimizada para Datos Emocionales

```bash
# Editar configuración de PostgreSQL para optimizar consultas emocionales
sudo nano /etc/postgresql/15/main/postgresql.conf
```

```conf
# Configuración optimizada para el bot Diana
# Estas configuraciones están específicamente diseñadas para consultas 
# emocionales complejas y búsquedas de texto completo

# Memoria
shared_buffers = 2GB                    # 25% de RAM total
effective_cache_size = 6GB              # 75% de RAM total  
work_mem = 64MB                         # Para consultas complejas de emociones
maintenance_work_mem = 512MB            # Para operaciones de mantenimiento

# Conexiones
max_connections = 100                   # Suficiente para el bot
superuser_reserved_connections = 3

# Logs (importante para debugging emocional)
log_statement = 'mod'                   # Log modificaciones
log_duration = on                       # Log duración de queries
log_min_duration_statement = 1000       # Log queries > 1 segundo

# Búsqueda de texto completo (crucial para memorias emocionales)
default_text_search_config = 'spanish'  # Configuración en español
```

### Paso 3: Inicialización de Esquemas

```python
# scripts/setup_database.py
import asyncio
import asyncpg
from pathlib import Path

async def setup_database():
    """
    Configuración inicial de la base de datos emocional.
    
    Este script no solo crea las tablas, sino que también inicializa
    datos base como arquetipos de usuario y plantillas de contradicciones.
    """
    
    # Conectar a la base de datos
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        database='diana_emotional_db',
        user='diana_bot',
        password='tu_password_super_seguro'
    )
    
    # Ejecutar esquema de base de datos
    schema_sql = Path('schemas/emotional_schema.sql').read_text()
    await conn.execute(schema_sql)
    
    # Inicializar datos de arquetipos
    await initialize_user_archetypes(conn)
    
    # Inicializar biblioteca de contradicciones
    await initialize_contradiction_library(conn)
    
    # Crear índices optimizados
    await create_emotional_indexes(conn)
    
    print("✅ Base de datos emocional configurada correctamente")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(setup_database())
```

---

## Configuración del Bot de Telegram

### Paso 1: Crear Bot en Telegram

1. Hablar con @BotFather en Telegram
2. Usar comando `/newbot`
3. Elegir nombre: "Diana - Emotional Companion"
4. Elegir username: algo como `diana_emotional_bot`
5. Guardar el token que te da BotFather

### Paso 2: Configuración Avanzada del Bot

```bash
# Configurar comandos del bot con BotFather
/setcommands

# Comandos que Diana entiende:
start - Comenzar o reiniciar la conexión con Diana
perfil - Ver tu progreso emocional con Diana  
memoria - Revisar momentos especiales compartidos
nivel - Ver tu nivel actual y requisitos para avanzar
configuracion - Ajustar preferencias de interacción
ayuda - Entender cómo conectar mejor con Diana
```

```bash
# Configurar descripción del bot
/setdescription

Diana es una compañera emocional que evoluciona contigo a través de conversaciones profundas y significativas. No es solo un chatbot: es una experiencia de crecimiento personal a través de la conexión auténtica.

# Configurar descripción corta
/setabouttext

Compañera emocional evolutiva. Crecimiento personal a través de conexión auténtica.
```

### Paso 3: Configuración de Webhooks (Producción)

```python
# scripts/setup_webhook.py
import asyncio
from telegram import Bot

async def setup_webhook():
    """
    Configura webhook para recepción eficiente de mensajes.
    
    Los webhooks son cruciales para que Diana responda de manera natural
    sin delays perceptibles que rompan la immersión emocional.
    """
    
    bot = Bot(token="TU_BOT_TOKEN")
    
    webhook_url = "https://tu-dominio.com/webhook/diana"
    
    # Configurar webhook con parámetros optimizados
    await bot.set_webhook(
        url=webhook_url,
        max_connections=10,          # Conexiones simultáneas
        allowed_updates=[            # Solo actualizaciones relevantes
            "message", "callback_query", "inline_query"
        ],
        drop_pending_updates=True    # Limpiar mensajes pendientes
    )
    
    print(f"✅ Webhook configurado: {webhook_url}")

if __name__ == "__main__":
    asyncio.run(setup_webhook())
```

---

## Implementación Paso a Paso

### Fase 1: Configuración Base (Día 1-2)

```bash
# 1. Clonar y configurar proyecto
git clone https://github.com/tu-usuario/diana-bot.git
cd diana-bot

# 2. Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
nano .env
```

```env
# .env - Configuración para Diana
# Estas variables controlan tanto el comportamiento técnico como emocional

# Base de datos emocional
DATABASE_URL=postgresql://diana_bot:tu_password@localhost/diana_emotional_db
REDIS_URL=redis://localhost:6379/0

# Telegram
TELEGRAM_BOT_TOKEN=tu_token_de_botfather
WEBHOOK_URL=https://tu-dominio.com/webhook/diana

# Configuración emocional de Diana
DIANA_RESPONSE_DELAY_MIN=1.5        # Delay mínimo en respuestas (segundos)
DIANA_RESPONSE_DELAY_MAX=8.0        # Delay máximo en respuestas (segundos)
DIANA_MEMORY_DEPTH=20               # Cuántas memorias considera para respuestas
DIANA_SPONTANEOUS_MESSAGE_RATE=0.1  # Probabilidad de mensajes espontáneos

# Límites de interacción (para proteger la experiencia)
MAX_DAILY_INTERACTIONS=50           # Máximo de mensajes por día por usuario
COOLDOWN_BETWEEN_MESSAGES=2         # Segundos entre mensajes del mismo usuario

# Logging y monitoreo
LOG_LEVEL=INFO
EMOTIONAL_METRICS_ENABLED=true
BACKUP_FREQUENCY_HOURS=6

# Seguridad
SECRET_KEY=tu_clave_secreta_super_larga_y_compleja
ALLOWED_HOSTS=tu-dominio.com,localhost
```

### Fase 2: Testing Local (Día 3-4)

```python
# tests/test_emotional_integration.py
import pytest
import asyncio
from app.core.diana_brain_system import DianaResponseSystem
from app.core.database_manager import DatabaseManager

class TestEmotionalIntegration:
    """
    Tests de integración que verifican que Diana responde emocionalmente
    de manera coherente a diferentes tipos de usuarios y situaciones.
    
    Estos tests son cruciales porque verifican no solo funcionalidad técnica,
    sino coherencia emocional - que es el corazón de la experiencia Diana.
    """
    
    @pytest.mark.asyncio
    async def test_new_user_welcome_flow(self):
        """Verifica que la bienvenida inicial se sienta personal y misteriosa."""
        
        # Simular usuario completamente nuevo
        db = DatabaseManager(test_config)
        diana = DianaResponseSystem(db)
        
        # Diana debería crear perfil automáticamente
        response = await diana.process_user_message(12345, "/start")
        
        # Verificar elementos emocionales esperados
        assert "bienvenido" in response.lower()
        assert "curiosidad" in response.lower()
        assert len(response) > 100  # Respuesta sustancial, no genérica
        
        # Verificar que se creó perfil emocional
        profile = await db.get_user_profile(12345)
        assert profile.archetype is not None
        assert profile.emotional_trust_score == 0.0
    
    @pytest.mark.asyncio
    async def test_emotional_growth_detection(self):
        """Verifica que Diana detecta y responde al crecimiento emocional."""
        
        db = DatabaseManager(test_config)
        diana = DianaResponseSystem(db)
        
        # Simular secuencia de mensajes que muestran crecimiento
        user_id = 12346
        
        messages = [
            "Hola Diana, soy nuevo aquí",
            "Me cuesta abrirme emocionalmente a las personas",
            "Después de nuestra conversación, me doy cuenta de que mis miedos me limitan",
            "He estado reflexionando sobre lo que me dijiste. Creo que estoy empezando a entender"
        ]
        
        responses = []
        for message in messages:
            response = await diana.process_user_message(user_id, message)
            responses.append(response)
            await asyncio.sleep(0.1)  # Simular tiempo entre mensajes
        
        # La última respuesta debería reconocer el crecimiento
        final_response = responses[-1]
        growth_indicators = ['crecido', 'evolución', 'cambio', 'diferente', 'crecimiento']
        assert any(indicator in final_response.lower() for indicator in growth_indicators)
        
        # Verificar que las métricas reflejan el crecimiento
        profile = await db.get_user_profile(user_id)
        assert profile.emotional_trust_score > 30  # Debería haber crecido
        assert profile.vulnerability_capacity > 20
    
    @pytest.mark.asyncio
    async def test_contradiction_handling(self):
        """Verifica que el sistema de contradicciones funciona correctamente."""
        
        db = DatabaseManager(test_config)
        diana = DianaResponseSystem(db)
        
        # Crear usuario con nivel suficiente para contradicciones
        user_id = 12347
        await db.create_user_profile(user_id, "test_user")
        
        # Simular progreso hasta el punto donde Diana introduce contradicciones
        profile = await db.get_user_profile(user_id)
        profile.emotional_trust_score = 60
        profile.current_level = 3
        await db.update_user_metrics(user_id, profile)
        
        # Simular múltiples interacciones hasta que aparezca una contradicción
        contradiction_detected = False
        for i in range(10):
            response = await diana.process_user_message(
                user_id, f"Diana, me fascina tu complejidad {i}"
            )
            
            # Buscar signos de contradicción
            if any(word in response.lower() for word in 
                   ['contradicción', 'inconsistente', 'antes dije', 'paradoja']):
                contradiction_detected = True
                break
        
        # Debería haberse detectado al menos una contradicción en 10 interacciones
        # con un usuario de confianza nivel 3
        assert contradiction_detected, "No se detectó ninguna contradicción en el rango esperado"

def run_integration_tests():
    """Ejecuta todos los tests de integración emocional."""
    pytest.main([
        "tests/test_emotional_integration.py",
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])

if __name__ == "__main__":
    run_integration_tests()
```

### Fase 3: Deployment Inicial (Día 5-7)

```yaml
# deployment/docker-compose.yml
version: '3.8'

services:
  # Base de datos emocional
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: diana_emotional_db
      POSTGRES_USER: diana_bot
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./schemas:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    restart: unless-stopped
    
  # Cache para sesiones emocionales
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    
  # Diana Bot Principal
  diana_bot:
    build: 
      context: .
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://diana_bot:${DB_PASSWORD}@postgres:5432/diana_emotional_db
      - REDIS_URL=redis://redis:6379/0
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
    
  # Nginx para webhook
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deployment/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - diana_bot
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Configurar directorio de trabajo
WORKDIR /app

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY app/ ./app/
COPY scripts/ ./scripts/

# Crear usuario no-root para seguridad
RUN useradd --create-home --shell /bin/bash diana
RUN chown -R diana:diana /app
USER diana

# Configurar punto de entrada
CMD ["python", "-m", "app.main"]
```

---

## Testing y Validación

### Sistema de Testing Emocional Automatizado

```python
# tests/emotional_behavior_tests.py
import asyncio
import pytest
from datetime import datetime, timedelta

class EmotionalBehaviorTestSuite:
    """
    Suite de tests que verifica que Diana se comporta emocionalmente
    de manera consistente y creíble en diferentes escenarios.
    
    Estos tests van más allá de la funcionalidad técnica para verificar
    que la experiencia emocional sea coherente y transformadora.
    """
    
    async def test_emotional_memory_consistency(self):
        """
        Verifica que Diana mantiene coherencia emocional entre sesiones.
        
        Diana debería recordar el tono emocional de conversaciones pasadas
        y ajustar su comportamiento actual basándose en esa historia.
        """
        
        user_id = 99999
        
        # Sesión 1: Usuario comparte vulnerabilidad
        vulnerability_message = "Diana, me cuesta mucho confiar en las personas. He sido lastimado antes."
        response1 = await self.diana.process_user_message(user_id, vulnerability_message)
        
        # Verificar que Diana responde con empatía apropiada
        empathy_indicators = ['entiendo', 'comprendo', 'siento', 'dolor', 'lastimado']
        assert any(indicator in response1.lower() for indicator in empathy_indicators)
        
        # Simular pausa de tiempo (24 horas después)
        await self.simulate_time_passage(hours=24)
        
        # Sesión 2: Usuario regresa
        return_message = "Hola Diana, he estado pensando en nuestra conversación"
        response2 = await self.diana.process_user_message(user_id, return_message)
        
        # Diana debería referenciar la vulnerabilidad pasada
        memory_indicators = ['recuerdo', 'dijiste', 'compartiste', 'ayer', 'confianza']
        assert any(indicator in response2.lower() for indicator in memory_indicators)
        
        # Verificar que el tono sigue siendo empático, no que haya "olvidado"
        assert len(response2) > 50  # Respuesta sustancial, no genérica
    
    async def test_archetype_adaptation(self):
        """
        Verifica que Diana adapta su estilo comunicativo al arquetipo del usuario.
        
        Un usuario "directo" debería recibir respuestas diferentes a un usuario "romántico",
        incluso cuando hacen preguntas similares.
        """
        
        # Usuario Directo
        direct_user = 88888
        await self.setup_user_archetype(direct_user, 'direct')
        
        question = "¿Qué sientes por mí, Diana?"
        direct_response = await self.diana.process_user_message(direct_user, question)
        
        # Usuario Romántico  
        romantic_user = 77777
        await self.setup_user_archetype(romantic_user, 'romantic')
        
        romantic_response = await self.diana.process_user_message(romantic_user, question)
        
        # Las respuestas deberían ser marcadamente diferentes
        assert direct_response != romantic_response
        
        # Respuesta directa debería ser más concisa
        assert len(direct_response.split()) < len(romantic_response.split()) * 1.5
        
        # Respuesta romántica debería tener más lenguaje emotivo
        romantic_words = ['corazón', 'alma', 'siento', 'profundo', 'hermoso', 'conexión']
        romantic_score = sum(1 for word in romantic_words if word in romantic_response.lower())
        direct_score = sum(1 for word in romantic_words if word in direct_response.lower())
        
        assert romantic_score > direct_score
    
    async def test_contradict
