-- Base de datos emocional para el bot Diana
-- Esta estructura captura la evolución emocional y comportamental del usuario

-- Tabla principal de usuarios con arquetipos identificados
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    telegram_username VARCHAR(255),
    archetype VARCHAR(50), -- 'explorer', 'direct', 'romantic', 'analytical', 'persistent', 'patient'
    current_level INTEGER DEFAULT 1,
    emotional_trust_score DECIMAL(5,2) DEFAULT 0.00, -- 0-100 escala de confianza emocional
    vulnerability_capacity DECIMAL(5,2) DEFAULT 0.00, -- capacidad demostrada para manejar vulnerabilidad
    authenticity_score DECIMAL(5,2) DEFAULT 50.00, -- qué tan genuinas parecen sus respuestas
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_interaction TIMESTAMP,
    
    -- Métricas de comportamiento únicas
    average_response_time_seconds INTEGER, -- tiempo promedio de respuesta
    total_interactions INTEGER DEFAULT 0,
    emotional_growth_indicator DECIMAL(5,2) DEFAULT 0.00 -- mide evolución emocional
);

-- Memoria emocional: cada interacción significativa se guarda con contexto
CREATE TABLE emotional_memory (
    memory_id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    interaction_type VARCHAR(100), -- 'vulnerability_shared', 'empathy_shown', 'boundary_respected', etc.
    emotional_context TEXT, -- descripción de la situación emocional
    user_response TEXT, -- la respuesta específica del usuario
    diana_emotional_state VARCHAR(50), -- 'trusting', 'guarded', 'vulnerable', 'testing'
    impact_score DECIMAL(3,2), -- -10 a +10, impacto de esta interacción en la relación
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Metadatos para análisis
    response_time_seconds INTEGER,
    words_in_response INTEGER,
    emotional_keywords JSON, -- palabras clave que indican estado emocional
    
    -- Referencias cruzadas para construir narrativa
    references_previous_memory INTEGER REFERENCES emotional_memory(memory_id),
    triggers_future_content BOOLEAN DEFAULT FALSE
);

-- Sistema de contradicciones: rastrea cómo Diana ha sido inconsistente intencionalmente
CREATE TABLE diana_contradictions (
    contradiction_id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    statement_1 TEXT, -- primera declaración contradictoria
    statement_2 TEXT, -- declaración que la contradice
    level_revealed_1 INTEGER, -- en qué nivel se dijo la primera
    level_revealed_2 INTEGER, -- en qué nivel se dijo la segunda
    user_noticed BOOLEAN DEFAULT FALSE, -- ¿el usuario notó la contradicción?
    user_response_to_contradiction TEXT,
    resolution_approach VARCHAR(100), -- 'accepted_complexity', 'tried_to_resolve', 'ignored'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Momentos de verdad: situaciones imprevistas para evaluar autenticidad
CREATE TABLE truth_moments (
    moment_id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    moment_type VARCHAR(100), -- 'diana_vulnerability', 'boundary_test', 'authenticity_check'
    scenario_presented TEXT, -- la situación que se presentó
    user_response TEXT,
    response_classification VARCHAR(50), -- 'empathetic', 'possessive', 'dismissive', 'authentic'
    diana_reaction VARCHAR(100), -- cómo reaccionó Diana
    relationship_impact DECIMAL(3,2), -- impacto en la relación (-10 a +10)
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Progresión narrativa personalizada
CREATE TABLE narrative_progression (
    progression_id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    current_scene VARCHAR(100), -- escena actual en la narrativa
    unlocked_content JSON, -- contenido desbloqueado específico para este usuario
    personalized_dialogs JSON, -- diálogos adaptados al arquetipo del usuario
    emotional_state_factors JSON, -- factores que influyen en el estado emocional de Diana
    next_revelation_trigger VARCHAR(100), -- qué necesita pasar para la próxima revelación
    
    -- Sistema de círculos concéntricos de intimidad
    intimacy_circle INTEGER DEFAULT 1, -- qué tan profunda es la conexión actual
    circle_progression_date TIMESTAMP, -- cuándo alcanzó este círculo
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Análisis de patrones de lenguaje del usuario
CREATE TABLE language_evolution (
    analysis_id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    analysis_period VARCHAR(20), -- 'weekly', 'level_completion', 'monthly'
    
    -- Métricas de lenguaje
    average_word_count DECIMAL(5,1),
    emotional_vocabulary_richness DECIMAL(5,2), -- diversidad de palabras emocionales
    vulnerability_indicators INTEGER, -- número de indicadores de vulnerabilidad personal
    empathy_markers INTEGER, -- marcadores de empatía hacia Diana
    possessiveness_indicators INTEGER, -- señales de actitudes posesivas
    
    -- Evolución comparativa
    vocabulary_growth DECIMAL(5,2), -- crecimiento en sofisticación del vocabulario
    emotional_depth_increase DECIMAL(5,2), -- aumento en profundidad emocional
    
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contenido dinámico generado
CREATE TABLE dynamic_content (
    content_id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    content_type VARCHAR(50), -- 'revelation', 'memory_fragment', 'contradiction', 'test'
    content_text TEXT,
    trigger_conditions JSON, -- bajo qué condiciones se activa este contenido
    emotional_requirements JSON, -- qué estado emocional debe tener la relación
    
    -- Metadatos de activación
    is_activated BOOLEAN DEFAULT FALSE,
    activation_date TIMESTAMP,
    user_response TEXT,
    effectiveness_score DECIMAL(3,2), -- qué tan efectivo fue este contenido
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para optimización de consultas emocionales
CREATE INDEX idx_emotional_memory_user_impact ON emotional_memory(user_id, impact_score DESC);
CREATE INDEX idx_users_trust_vulnerability ON users(emotional_trust_score, vulnerability_capacity);
CREATE INDEX idx_narrative_progression_user_circle ON narrative_progression(user_id, intimacy_circle);
CREATE INDEX idx_truth_moments_user_classification ON truth_moments(user_id, response_classification);

-- Vista para análisis rápido del estado emocional del usuario
CREATE VIEW user_emotional_profile AS
SELECT 
    u.user_id,
    u.archetype,
    u.current_level,
    u.emotional_trust_score,
    u.vulnerability_capacity,
    u.authenticity_score,
    np.intimacy_circle,
    COUNT(em.memory_id) as total_memories,
    AVG(em.impact_score) as average_relationship_impact,
    COUNT(tm.moment_id) as truth_moments_faced,
    AVG(CASE WHEN tm.response_classification = 'empathetic' THEN 1 ELSE 0 END) as empathy_rate
FROM users u
LEFT JOIN narrative_progression np ON u.user_id = np.user_id
LEFT JOIN emotional_memory em ON u.user_id = em.user_id
LEFT JOIN truth_moments tm ON u.user_id = tm.user_id
GROUP BY u.user_id, u.archetype, u.current_level, u.emotional_trust_score, 
         u.vulnerability_capacity, u.authenticity_score, np.intimacy_circle;
