# Desencadenadores de conversión específicos por ruta
CONVERSION_TRIGGERS = {
    'intellectual': {
        'threshold': 6.0,
        'base_hook': 'Laboratorio Mental VIP - Conversaciones exclusivas que otros no entenderían',
        'conversion_type': 'filosofa_vip',
        'requirements': {
            'intellectual_trust': 5.0,
            'addiction_to_player_mind': 4.0,
            'mask_level': 4.0  # Menos máscara = más autenticidad
        },
        'content_templates': {
            'romantic_intellectual': "Conversaciones íntimas que fusionan mente y corazón",
            'pure_theorist': "Laboratorio mental donde exploramos ideas prohibidas",
            'skeptical_thinker': "Espacio donde puedo ser vulnerable sin perder mi mente crítica"
        }
    },
    'emotional': {
        'threshold': 6.0,
        'base_hook': 'Jardín Secreto VIP - Mi vulnerabilidad más profunda',
        'conversion_type': 'corazon_vip',
        'requirements': {
            'emotional_openness': 5.0,
            'soul_seen_level': 4.0,
            'vulnerability_level': 4.0
        },
        'content_templates': {
            'empathetic_emotional': "Jardín donde nuestras almas pueden sanarse mutuamente",
            'passionate_emotional': "Santuario donde la intensidad emocional es celebrada",
            'wounded_healer': "Espacio sagrado de vulnerabilidad y sanación compartida"
        }
    },
    'wild': {
        'threshold': 6.0,
        'base_hook': 'Atlas Infinito VIP - Aventuras únicas que nadie más vivirá',
        'conversion_type': 'aventurera_vip',
        'requirements': {
            'adventure_readiness': 5.0,
            'wild_self_acceptance': 4.0,
            'comfortable_with_unknown': 3.0
        },
        'content_templates': {
            'adventure_seeker': "Atlas infinito de aventuras que nadie más vivirá",
            'freedom_lover': "Territorio sin límites donde puedo ser todas mis versiones",
            'collector_explorer': "Acceso completo a todos mis universos internos"
        }
    }
}

# Matriz de precios
PRICING_MATRIX = {
    'filosofa_vip': {
        'base_price': 50,
        'multiplier_range': (1.0, 2.0),
        'multiplier_factors': {
            'romantic_intellectual': 1.2,
            'pure_theorist': 1.1,
            'skeptical_thinker': 1.15
        }
    },
    'corazon_vip': {
        'base_price': 45,
        'multiplier_range': (1.0, 2.0),
        'multiplier_factors': {
            'empathetic_emotional': 1.1,
            'passionate_emotional': 1.0,
            'wounded_healer': 1.25
        }
    },
    'aventurera_vip': {
        'base_price': 55,
        'multiplier_range': (1.0, 2.0),
        'multiplier_factors': {
            'adventure_seeker': 1.0,
            'freedom_lover': 1.0,
            'collector_explorer': 1.3
        }
    }
}