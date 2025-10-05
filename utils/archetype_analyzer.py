"""
Sistema de Análisis de Arquetipos de Usuario
============================================

Clasifica usuarios en arquetipos basándose en sus decisiones narrativas.
Diseñado para ser:
- Simple (no ML, solo conteo de tags)
- Invisible (usuario no ve su clasificación directamente)
- Funcional (permite personalización de CTAs y contenido)
- Fijo (se define después de 3 decisiones, no cambia)

Arquetipos:
- 🔥 Aventurero: Directo, rápido, transparente
- 💭 Romántico: Analítico, lento, reservado
- ⚖️ Equilibrado: Mixto, moderado, selectivo
- 🎭 Explorador: Curioso, variable, experimental
"""

from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# TAGS DE DECISIONES NARRATIVAS
# ═══════════════════════════════════════════════════════════════════

# Mapeo de destination_fragment_key → tags de personalidad
# Basado en complete_story.json y fragmentos narrativos existentes

DECISION_TAGS = {
    # Inicio - Primera impresión
    "diana_echo": {
        "approach": "curious",      # Pregunta sobre Diana
        "speed": "moderate"
    },
    "lucien_selection": {
        "approach": "analytical",   # Pregunta sobre sí mismo
        "speed": "moderate"
    },
    "threshold_entry": {
        "approach": "direct",       # Listo para entrar
        "speed": "fast"
    },

    # Hesitación vs Confianza
    "hesitation_1": {
        "approach": "cautious",
        "speed": "slow",
        "depth": "reserved"
    },

    # Nivel 2 - Reflexión
    "hall_of_mirrors": {
        "approach": "direct",       # Acepta el reflejo
        "speed": "fast"
    },
    "lucien_reflection": {
        "approach": "analytical",   # Pregunta sobre intenciones
        "speed": "moderate"
    },
    "slow_path": {
        "approach": "cautious",
        "speed": "slow",
        "depth": "reserved"         # No quiere ser visto del todo
    },

    # Encuentro con Diana - Nivel 3
    "diana_seek": {
        "approach": "direct",       # "Te busco a ti"
        "depth": "transparent"
    },
    "diana_mirror_1": {
        "approach": "analytical",   # "Huyo de mí"
        "depth": "transparent"      # Admite vulnerabilidad
    },
    "diana_uncertain": {
        "approach": "cautious",     # "No sé aún"
        "speed": "slow"
    },

    # Nivel profundo
    "vip_chamber": {
        "approach": "direct",       # "Muéstrate tal como eres"
        "speed": "fast",
        "depth": "transparent"
    },
    "imagined_diana": {
        "approach": "cautious",     # "Prefiero imaginarte"
        "depth": "reserved"
    },

    # Ritual VIP
    "vip_ritual": {
        "approach": "direct",
        "speed": "fast",
        "depth": "transparent"
    },
    "diana_closure": {
        "approach": "cautious",     # "Aún no"
        "speed": "slow"
    }
}

# ═══════════════════════════════════════════════════════════════════
# ARQUETIPOS Y SUS CARACTERÍSTICAS
# ═══════════════════════════════════════════════════════════════════

ARCHETYPES = {
    "adventurer": {
        "emoji": "🔥",
        "name": "Aventurero",
        "traits": {
            "approach": "direct",
            "speed": "fast",
            "depth": "transparent"
        },
        "description": "Va directo al contenido, sin rodeos. Transparente y decidido."
    },
    "romantic": {
        "emoji": "💭",
        "name": "Romántico",
        "traits": {
            "approach": "analytical",
            "speed": "slow",
            "depth": "reserved"
        },
        "description": "Disfruta la tensión y el misterio. Pausado y reflexivo."
    },
    "balanced": {
        "emoji": "⚖️",
        "name": "Equilibrado",
        "traits": {
            "approach": "moderate",
            "speed": "moderate",
            "depth": "selective"
        },
        "description": "Balancea fantasía y realidad. Selectivo y adaptable."
    },
    "explorer": {
        "emoji": "🎭",
        "name": "Explorador",
        "traits": {
            "approach": "curious",
            "speed": "variable",
            "depth": "experimental"
        },
        "description": "Prueba todo, múltiples caminos. Curioso y experimental."
    },
    "undetermined": {
        "emoji": "❓",
        "name": "Indeterminado",
        "traits": {},
        "description": "Aún explorando. Necesita más interacciones para definir patrón."
    }
}

# Número mínimo de decisiones para clasificar
MIN_DECISIONS_FOR_CLASSIFICATION = 3


# ═══════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL DE ANÁLISIS
# ═══════════════════════════════════════════════════════════════════

def analyze_user_archetype(choices_made: List[Dict]) -> str:
    """
    Analiza las decisiones del usuario y retorna su arquetipo.

    Args:
        choices_made: Lista de decisiones del usuario desde UserNarrativeState.choices_made
                     Formato: [{"destination_fragment_key": "...", ...}, ...]

    Returns:
        str: Código del arquetipo ("adventurer", "romantic", "balanced", "explorer", "undetermined")

    Lógica:
        1. Si < 3 decisiones → "undetermined"
        2. Contar tags por categoría (approach, speed, depth)
        3. Clasificar según patrón dominante
    """
    if not choices_made or len(choices_made) < MIN_DECISIONS_FOR_CLASSIFICATION:
        logger.debug(f"Insufficient decisions for classification: {len(choices_made) if choices_made else 0}")
        return "undetermined"

    # Contador de tags
    tags_counter = {
        "direct": 0,
        "curious": 0,
        "analytical": 0,
        "cautious": 0,
        "fast": 0,
        "moderate": 0,
        "slow": 0,
        "transparent": 0,
        "reserved": 0,
        "selective": 0,
        "experimental": 0,
        "variable": 0
    }

    # Contar tags de cada decisión
    decisions_with_tags = 0
    for choice in choices_made:
        dest_key = choice.get("destination_fragment_key")
        if not dest_key:
            continue

        if dest_key in DECISION_TAGS:
            decisions_with_tags += 1
            for category, tag in DECISION_TAGS[dest_key].items():
                if tag in tags_counter:
                    tags_counter[tag] += 1

    # Si no hay decisiones con tags, retornar undetermined
    if decisions_with_tags == 0:
        logger.debug("No decisions with tags found")
        return "undetermined"

    logger.debug(f"Tag counts: {tags_counter}")

    # ═══════════════════════════════════════════════════════════════════
    # LÓGICA DE CLASIFICACIÓN
    # ═══════════════════════════════════════════════════════════════════

    # 1. AVENTURERO: Directo + Rápido + Transparente
    if (tags_counter["direct"] >= 2 and
        tags_counter["fast"] >= 1 and
        tags_counter["transparent"] >= 1):
        return "adventurer"

    # 2. ROMÁNTICO: Analítico/Cauteloso + Lento + Reservado
    if ((tags_counter["analytical"] >= 1 or tags_counter["cautious"] >= 1) and
        tags_counter["slow"] >= 2 and
        tags_counter["reserved"] >= 1):
        return "romantic"

    # 3. EXPLORADOR: Alto en Curioso/Experimental o caminos variados
    if (tags_counter["curious"] >= 2 or
        tags_counter["experimental"] >= 1 or
        # Detectar si toma caminos variados (mix de fast/slow)
        (tags_counter["fast"] >= 1 and tags_counter["slow"] >= 1 and tags_counter["curious"] >= 1)):
        return "explorer"

    # 4. EQUILIBRADO: Todo lo demás (no cae en extremos)
    return "balanced"


def get_archetype_info(archetype_code: str) -> Dict:
    """
    Obtiene la información completa de un arquetipo.

    Args:
        archetype_code: Código del arquetipo

    Returns:
        Dict con emoji, name, traits, description
    """
    return ARCHETYPES.get(archetype_code, ARCHETYPES["undetermined"])


def get_archetype_emoji(archetype_code: str) -> str:
    """Retorna solo el emoji del arquetipo."""
    return ARCHETYPES.get(archetype_code, ARCHETYPES["undetermined"])["emoji"]


def get_archetype_name(archetype_code: str) -> str:
    """Retorna solo el nombre del arquetipo."""
    return ARCHETYPES.get(archetype_code, ARCHETYPES["undetermined"])["name"]


# ═══════════════════════════════════════════════════════════════════
# UTILIDADES DE DEBUG
# ═══════════════════════════════════════════════════════════════════

def debug_archetype_analysis(choices_made: List[Dict]) -> Dict:
    """
    Análisis detallado para debugging/admin.

    Returns:
        Dict con archetype, tag_counts, decisions_analyzed, classification_reason
    """
    archetype = analyze_user_archetype(choices_made)

    tags_counter = {
        "direct": 0, "curious": 0, "analytical": 0, "cautious": 0,
        "fast": 0, "moderate": 0, "slow": 0,
        "transparent": 0, "reserved": 0
    }

    for choice in choices_made:
        dest_key = choice.get("destination_fragment_key")
        if dest_key in DECISION_TAGS:
            for category, tag in DECISION_TAGS[dest_key].items():
                if tag in tags_counter:
                    tags_counter[tag] += 1

    return {
        "archetype": archetype,
        "archetype_info": get_archetype_info(archetype),
        "tag_counts": tags_counter,
        "decisions_analyzed": len(choices_made),
        "decisions_with_tags": sum(1 for c in choices_made if c.get("destination_fragment_key") in DECISION_TAGS)
    }
