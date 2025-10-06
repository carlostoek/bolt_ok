# Fragmentos del nivel 1
LEVEL1_FRAGMENTS = {
    "l1_f1": {
        "id": "diana_l1_f1_arquetipo_analyzer",
        "title": "Holis, Bienvenido a Los Kinkys - El Umbral de las Posibilidades",
        "content": "Holis hermoso 😍\n\nLlegaste justo cuando estaba pensando en algo fascinante... ¿Sabes esa sensación cuando conoces a alguien y sientes que hay capas esperando ser descubiertas?\n\n*[Se acomoda, con una curiosidad inteligente]*\n\nBienvenido a Los Kinkys. Te voy a ser honesta desde el inicio: esto funciona diferente para cada persona.\n\nAlgunos llegan buscando conversaciones que los desafíen mentalmente. Otros quieren conexión emocional profunda. Hay quienes disfrutan explorar posibilidades nuevas...\n\n*[Sus ojos te evalúan con genuina curiosidad]*\n\nMe fascina descubrir qué tipo de hambre trae cada persona. Cómo procesan, cómo sienten, qué los mueve realmente...\n\n*[Una sonrisa intrigante]*\n\nPor eso tengo curiosidad: ¿qué te trajo hasta aquí realmente?",
        "fragment_type": "ARCHETYPE_ANALYSIS",
        "choices": [
            {
                "id": "choice_l1_curiosity_intellectual",
                "text": "🤔 Me intriga entender cómo funciona esto psicológicamente",
                "archetype_weights": {
                    "intellectual": 3.0,
                    "philosophical": 2.0,
                    "analytical": 1.0
                },
                "sub_archetype_weights": {
                    "pure_theorist": 2.0,
                    "skeptical_thinker": 1.0
                }
            },
            {
                "id": "choice_l1_curiosity_emotional",
                "text": "💫 Busco una conexión que vaya más allá de lo superficial",
                "archetype_weights": {
                    "emotional": 3.0,
                    "vulnerable": 2.0,
                    "reciprocal": 1.0
                },
                "sub_archetype_weights": {
                    "empathetic_emotional": 2.0,
                    "wounded_healer": 1.0
                }
            },
            {
                "id": "choice_l1_curiosity_exploratory",
                "text": "🗺️ Me gusta descubrir experiencias que no sabía que existían",
                "archetype_weights": {
                    "exploratory": 3.0,
                    "direct": 1.0
                },
                "sub_archetype_weights": {
                    "adventure_seeker": 2.0,
                    "collector_explorer": 1.0
                }
            },
            {
                "id": "choice_l1_curiosity_romantic_intellectual",
                "text": "🎭 Me atraen las mentes que pueden seducir con ideas",
                "archetype_weights": {
                    "intellectual": 2.0,
                    "emotional": 2.0,
                    "philosophical": 1.0
                },
                "sub_archetype_weights": {
                    "romantic_intellectual": 3.0,
                    "hedonist_philosopher": 1.0
                }
            },
            {
                "id": "choice_l1_curiosity_freedom",
                "text": "🦋 Quiero algo sin expectativas ni ataduras",
                "archetype_weights": {
                    "exploratory": 2.0,
                    "direct": 2.0
                },
                "sub_archetype_weights": {
                    "freedom_lover": 3.0,
                    "adventure_seeker": 1.0
                }
            }
        ],
        "tracking": {
            "response_time": True,
            "choice_progression": True,
            "hesitation_patterns": True
        }
    }
}