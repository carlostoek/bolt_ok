-- Migración: Sistema de VIP Grants
-- Fecha: 2025-10-04
-- Descripción: Agrega tabla vip_grants para auditoría y campo vip_days a rewards

-- 1. Crear tabla vip_grants para registro de accesos VIP gratuitos
CREATE TABLE IF NOT EXISTS vip_grants (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    days_granted INT NOT NULL,
    source VARCHAR(50) NOT NULL,  -- 'narrative', 'reward', 'achievement', 'admin'
    source_id INT,  -- fragment_id, reward_id, achievement_id, etc.
    granted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    invite_link VARCHAR(255)
);

-- Índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_vip_grants_user_id ON vip_grants(user_id);
CREATE INDEX IF NOT EXISTS idx_vip_grants_source ON vip_grants(source);
CREATE INDEX IF NOT EXISTS idx_vip_grants_granted_at ON vip_grants(granted_at DESC);

-- 2. Agregar campo vip_days a tabla rewards
ALTER TABLE rewards
ADD COLUMN IF NOT EXISTS vip_days INT;

-- Comentarios para documentación
COMMENT ON TABLE vip_grants IS 'Registro de accesos VIP gratuitos otorgados para auditoría y analytics';
COMMENT ON COLUMN vip_grants.source IS 'Fuente del grant: narrative, reward, achievement, admin';
COMMENT ON COLUMN vip_grants.source_id IS 'ID de la fuente específica (opcional)';
COMMENT ON COLUMN vip_grants.invite_link IS 'Link de invitación al canal VIP generado (24h)';

COMMENT ON COLUMN rewards.vip_days IS 'Días de acceso VIP si reward_type=vip_access (NULL para rewards normales)';
