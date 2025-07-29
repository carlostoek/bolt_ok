"""
Sistema de Gestión de Base de Datos Emocional para Diana

Este módulo maneja toda la persistencia y consulta de datos emocionales,
permitiendo que Diana mantenga memoria a largo plazo y haga conexiones
complejas entre interacciones pasadas y presentes.
"""

import asyncio
import asyncpg
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import logging
from contextlib import asynccontextmanager

from diana_brain_system import UserProfile, UserArchetype, EmotionalMemory, EmotionalState
from advanced_systems import IntimacyCircle, ContradictionType

@dataclass
class DatabaseConfig:
    """Configuración de la base de datos con parámetros optimizados para consultas emocionales."""
    host: str
    port: int
    database: str
    username: str
    password: str
    min_connections: int = 5
    max_connections: int = 20
    command_timeout: int = 30

class EmotionalQueryBuilder:
    """
    Constructor de consultas especializadas para datos emocionales.
    
    Este sistema permite hacer consultas complejas como "encuentra momentos donde el usuario
    mostró vulnerabilidad pero Diana se mantuvo distante" o "busca patrones de crecimiento
    en los últimos 30 días". Estas consultas son fundamentales para que Diana pueda
    hacer referencias específicas y significativas a la historia compartida.
    """
    
    @staticmethod
    def build_emotional_pattern_query(user_id: int, pattern_type: str, 
                                     timeframe_days: int = 30) -> Tuple[str, List]:
        """
        Construye consultas para detectar patrones emocionales específicos.
        
        Los patrones emocionales incluyen cosas como "momentos de ruptura emocional",
        "progresión de confianza", "respuestas a vulnerabilidad", etc.
        """
        
        queries = {
            'vulnerability_progression': """
                SELECT em.*, 
                       LAG(em.impact_score) OVER (ORDER BY em.timestamp) as previous_impact,
                       LAG(em.timestamp) OVER (ORDER BY em.timestamp) as previous_timestamp
                FROM emotional_memory em
                WHERE em.user_id = $1 
                AND em.interaction_type LIKE '%vulnerability%'
                AND em.timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY em.timestamp
            """,
            
            'trust_building_moments': """
                SELECT em.*, u.emotional_trust_score,
                       (em.impact_score - 
                        LAG(em.impact_score) OVER (ORDER BY em.timestamp)) as trust_delta
                FROM emotional_memory em
                JOIN users u ON em.user_id = u.user_id
                WHERE em.user_id = $1
                AND em.impact_score > 5
                AND em.timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY trust_delta DESC
            """,
            
            'emotional_contradictions_handled': """
                SELECT em.*, dc.resolution_approach
                FROM emotional_memory em
                LEFT JOIN diana_contradictions dc ON em.user_id = dc.user_id
                WHERE em.user_id = $1
                AND em.interaction_type = 'contradiction_response'
                AND em.timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY em.impact_score DESC
            """,
            
            'growth_acceleration_periods': """
                WITH growth_metrics AS (
                    SELECT timestamp, emotional_keywords,
                           COUNT(*) OVER (
                               ORDER BY timestamp 
                               ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                           ) as interaction_density,
                           AVG(impact_score) OVER (
                               ORDER BY timestamp 
                               ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                           ) as avg_impact
                    FROM emotional_memory
                    WHERE user_id = $1
                    AND timestamp >= NOW() - INTERVAL '%s days'
                )
                SELECT * FROM growth_metrics
                WHERE interaction_density >= 3 AND avg_impact > 6
                ORDER BY timestamp
            """
        }
        
        if pattern_type not in queries:
            raise ValueError(f"Patrón emocional desconocido: {pattern_type}")
        
        query = queries[pattern_type] % timeframe_days
        return query, [user_id]
    
    @staticmethod
    def build_memory_reference_query(user_id: int, emotional_context: str, 
                                   exclude_recent_days: int = 1) -> Tuple[str, List]:
        """
        Construye consultas para encontrar memorias específicas que Diana puede referenciar.
        
        Esto permite que Diana diga cosas como "¿Recuerdas hace tres días cuando me dijiste
        que sentías...?" con precisión específica sobre momentos reales.
        """
        
        query = """
            SELECT em.*, 
                   EXTRACT(DAYS FROM NOW() - em.timestamp) as days_ago,
                   ts_rank_cd(
                       to_tsvector('spanish', em.emotional_context || ' ' || em.user_response),
                       plainto_tsquery('spanish', $2)
                   ) as relevance_score
            FROM emotional_memory em
            WHERE em.user_id = $1
            AND em.timestamp <= NOW() - INTERVAL '%s days'
            AND (
                em.emotional_context ILIKE $2 
                OR em.user_response ILIKE $2
                OR em.emotional_keywords::text ILIKE $2
            )
            ORDER BY relevance_score DESC, em.impact_score DESC
            LIMIT 5
        """ % exclude_recent_days
        
        search_term = f"%{emotional_context}%"
        return query, [user_id, search_term]

class DatabaseManager:
    """
    Gestor principal de la base de datos emocional.
    
    Este sistema no solo almacena datos, sino que los interpreta emocionalmente.
    Cada consulta está diseñada para ayudar a Diana a entender no solo qué pasó,
    sino qué significó emocionalmente y cómo se conecta con el presente.
    """
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self.query_builder = EmotionalQueryBuilder()
        
        # Cache de consultas frecuentes para optimización
        self._query_cache = {}
        self._cache_ttl = 300  # 5 minutos
        
    async def initialize(self):
        """
        Inicializa la conexión a la base de datos y configura índices optimizados.
        
        Los índices están específicamente diseñados para consultas emocionales complejas
        que involucran tiempo, impacto emocional, y búsqueda de texto completo.
        """
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=self.config.command_timeout
            )
            
            # Verificar y crear índices emocionales si no existen
            await self._ensure_emotional_indexes()
            
            logging.info("Base de datos emocional inicializada correctamente")
            
        except Exception as e:
            logging.error(f"Error al inicializar base de datos: {e}")
            raise
    
    async def _ensure_emotional_indexes(self):
        """
        Crea índices especializados para consultas emocionales eficientes.
        
        Estos índices permiten que Diana haga consultas complejas sobre patrones
        emocionales sin degradar el rendimiento, incluso con miles de usuarios.
        """
        
        indexes = [
            # Índice para búsquedas de patrones emocionales por usuario y tiempo
            """
            CREATE INDEX IF NOT EXISTS idx_emotional_memory_user_time_impact 
            ON emotional_memory(user_id, timestamp DESC, impact_score DESC)
            """,
            
            # Índice para búsqueda de texto completo en contenido emocional
            """
            CREATE INDEX IF NOT EXISTS idx_emotional_memory_fulltext 
            ON emotional_memory USING gin(
                to_tsvector('spanish', emotional_context || ' ' || user_response)
            )
            """,
            
            # Índice para análisis de progresión de círculos de intimidad
            """
            CREATE INDEX IF NOT EXISTS idx_narrative_progression_circle_date 
            ON narrative_progression(user_id, intimacy_circle, circle_progression_date DESC)
            """,
            
            # Índice para consultas de contradicciones y resoluciones
            """
            CREATE INDEX IF NOT EXISTS idx_contradictions_user_resolution 
            ON diana_contradictions(user_id, resolution_approach, user_noticed)
            """,
            
            # Índice para análisis de crecimiento emocional temporal
            """
            CREATE INDEX IF NOT EXISTS idx_language_evolution_user_period 
            ON language_evolution(user_id, analysis_period, analysis_date DESC)
            """
        ]
        
        async with self.pool.acquire() as conn:
            for index_sql in indexes:
                try:
                    await conn.execute(index_sql)
                except Exception as e:
                    logging.warning(f"No se pudo crear índice: {e}")
    
    async def create_user_profile(self, user_id: int, username: str) -> Dict:
        """
        Crea un nuevo perfil de usuario con métricas emocionales inicializadas.
        
        El perfil inicial está calibrado para detectar el arquetipo del usuario
        basándose en sus primeras interacciones.
        """
        
        async with self.pool.acquire() as conn:
            # Crear usuario base
            user_data = await conn.fetchrow("""
                INSERT INTO users (
                    user_id, telegram_username, archetype, current_level,
                    emotional_trust_score, vulnerability_capacity, authenticity_score,
                    total_interactions, emotional_growth_indicator
                ) VALUES (
                    $1, $2, 'explorer', 1, 0.0, 0.0, 50.0, 0, 0.0
                ) RETURNING *
            """, user_id, username)
            
            # Crear progresión narrativa inicial
            await conn.execute("""
                INSERT INTO narrative_progression (
                    user_id, current_scene, unlocked_content, 
                    personalized_dialogs, emotional_state_factors,
                    intimacy_circle, next_revelation_trigger
                ) VALUES (
                    $1, 'level1_scene1_welcome', '{}', '{}', '{}', 1, 'demonstrate_curiosity'
                )
            """, user_id)
            
            return dict(user_data)
    
    async def get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """
        Obtiene el perfil completo del usuario incluyendo su historia emocional.
        
        Esta función construye un objeto UserProfile que contiene todo lo que Diana
        necesita para entender la relación actual con el usuario.
        """
        
        async with self.pool.acquire() as conn:
            # Obtener datos básicos del usuario
            user_data = await conn.fetchrow("""
                SELECT u.*, np.intimacy_circle, np.current_scene
                FROM users u
                LEFT JOIN narrative_progression np ON u.user_id = np.user_id
                WHERE u.user_id = $1
            """, user_id)
            
            if not user_data:
                return None
            
            # Obtener memorias emocionales recientes (últimas 20)
            memories_data = await conn.fetch("""
                SELECT * FROM emotional_memory
                WHERE user_id = $1
                ORDER BY timestamp DESC
                LIMIT 20
            """, user_id)
            
            # Convertir a objetos EmotionalMemory
            memories = [
                EmotionalMemory(
                    memory_id=mem['memory_id'],
                    interaction_type=mem['interaction_type'],
                    emotional_context=mem['emotional_context'],
                    user_response=mem['user_response'],
                    impact_score=mem['impact_score'],
                    timestamp=mem['timestamp'],
                    emotional_keywords=mem['emotional_keywords'] or []
                )
                for mem in memories_data
            ]
            
            # Construir perfil completo
            profile = UserProfile(
                user_id=user_data['user_id'],
                archetype=UserArchetype(user_data['archetype']),
                emotional_trust_score=user_data['emotional_trust_score'],
                vulnerability_capacity=user_data['vulnerability_capacity'],
                authenticity_score=user_data['authenticity_score'],
                intimacy_circle=user_data['intimacy_circle'] or 1,
                total_interactions=user_data['total_interactions'],
                memories=memories
            )
            
            return profile
    
    async def save_emotional_memory(self, user_id: int, interaction_type: str,
                                  emotional_context: str, user_response: str,
                                  diana_state: EmotionalState, impact_score: float,
                                  response_time_seconds: int, emotional_keywords: List[str]) -> int:
        """
        Guarda una nueva memoria emocional con análisis contextual completo.
        
        Cada memoria se guarda con metadatos ricos que permiten a Diana hacer
        conexiones sofisticadas entre experiencias pasadas y presentes.
        """
        
        async with self.pool.acquire() as conn:
            # Calcular métricas adicionales
            words_in_response = len(user_response.split())
            
            # Determinar si esta memoria debería triggear contenido futuro
            triggers_future_content = (
                impact_score > 7 or
                'vulnerability' in interaction_type or
                'growth' in ' '.join(emotional_keywords)
            )
            
            memory_id = await conn.fetchval("""
                INSERT INTO emotional_memory (
                    user_id, interaction_type, emotional_context, user_response,
                    diana_emotional_state, impact_score, response_time_seconds,
                    words_in_response, emotional_keywords, triggers_future_content
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
                ) RETURNING memory_id
            """, user_id, interaction_type, emotional_context, user_response,
                diana_state.value, impact_score, response_time_seconds,
                words_in_response, json.dumps(emotional_keywords), triggers_future_content)
            
            # Actualizar métricas del usuario basándose en esta interacción
            await self._update_user_metrics_from_memory(user_id, impact_score, emotional_keywords)
            
            return memory_id
    
    async def _update_user_metrics_from_memory(self, user_id: int, impact_score: float, 
                                             emotional_keywords: List[str]):
        """
        Actualiza las métricas emocionales del usuario basándose en la nueva memoria.
        
        Estas actualizaciones permiten que Diana "aprenda" sobre el usuario con cada
        interacción, refinando su comprensión de cómo responder emocionalmente.
        """
        
        async with self.pool.acquire() as conn:
            # Calcular ajustes a las métricas emocionales
            trust_adjustment = min(impact_score * 0.5, 5.0) if impact_score > 0 else max(impact_score * 0.3, -3.0)
            
            vulnerability_adjustment = 0
            if 'vulnerable' in emotional_keywords or 'intimate' in emotional_keywords:
                vulnerability_adjustment = min(impact_score * 0.3, 3.0)
            
            authenticity_adjustment = 0
            if 'authentic' in emotional_keywords or 'genuine' in emotional_keywords:
                authenticity_adjustment = min(impact_score * 0.2, 2.0)
            elif 'calculated' in emotional_keywords:
                authenticity_adjustment = max(-impact_score * 0.2, -2.0)
            
            # Aplicar ajustes con límites naturales
            await conn.execute("""
                UPDATE users SET
                    emotional_trust_score = LEAST(100, GREATEST(0, emotional_trust_score + $2)),
                    vulnerability_capacity = LEAST(100, GREATEST(0, vulnerability_capacity + $3)),
                    authenticity_score = LEAST(100, GREATEST(0, authenticity_score + $4)),
                    total_interactions = total_interactions + 1,
                    last_interaction = NOW()
                WHERE user_id = $1
            """, user_id, trust_adjustment, vulnerability_adjustment, authenticity_adjustment)
    
    async def find_relevant_memories_for_reference(self, user_id: int, current_context: str,
                                                 emotional_state: EmotionalState) -> List[Dict]:
        """
        Encuentra memorias específicas que Diana puede referenciar en el contexto actual.
        
        Esta función permite que Diana haga comentarios específicos como "¿Recuerdas cuando
        me dijiste que...?" con precisión emocional y temporal.
        """
        
        # Usar query builder para construir consulta contextual
        query, params = self.query_builder.build_memory_reference_query(
            user_id, current_context, exclude_recent_days=1
        )
        
        async with self.pool.acquire() as conn:
            memories = await conn.fetch(query, *params)
            
            # Filtrar memorias basándose en el estado emocional actual de Diana
            relevant_memories = []
            for memory in memories:
                if self._is_memory_relevant_for_state(memory, emotional_state):
                    relevant_memories.append(dict(memory))
            
            return relevant_memories[:3]  # Máximo 3 memorias más relevantes
    
    def _is_memory_relevant_for_state(self, memory: Dict, current_diana_state: EmotionalState) -> bool:
        """
        Determina si una memoria es relevante para el estado emocional actual de Diana.
        
        Diana no referencias cualquier memoria - solo aquellas que conectan emocionalmente
        con cómo se siente en el momento presente.
        """
        
        memory_state = EmotionalState(memory['diana_emotional_state'])
        impact_score = memory['impact_score']
        
        # Mapeo de estados que se conectan emocionalmente
        state_connections = {
            EmotionalState.VULNERABLE: [EmotionalState.TRUSTING, EmotionalState.INTIMATE, EmotionalState.VULNERABLE],
            EmotionalState.TRUSTING: [EmotionalState.CURIOUS, EmotionalState.TRUSTING, EmotionalState.VULNERABLE],
            EmotionalState.TESTING: [EmotionalState.GUARDED, EmotionalState.TESTING, EmotionalState.WITHDRAWING],
            EmotionalState.INTIMATE: [EmotionalState.VULNERABLE, EmotionalState.INTIMATE, EmotionalState.TRUSTING]
        }
        
        # Una memoria es relevante si:
        # 1. El estado emocional conecta con el actual
        # 2. El impacto fue significativo (positivo o negativo)
        # 3. No es demasiado reciente (ya filtrado por la query)
        
        return (
           
