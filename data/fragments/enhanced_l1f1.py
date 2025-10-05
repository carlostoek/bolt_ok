# data/fragments/enhanced_l1f1.py
"""
Enhanced L1F1 Fragment Data Structure for Archetype Detection
Contains Diana's archetype-optimized introduction with embedded psychological weights.
"""

ENHANCED_L1F1 = {
    "fragment_id": "diana_enhanced_l1f1",
    "content": """🌸 **Diana:** *Una figura elegante emerge de las sombras del jardín, sus ojos reflejan una sabiduría misteriosa*

Así que finalmente has llegado... *sonríe con una mezcla de curiosidad y conocimiento*

Sabía que encontrarías el camino hasta aquí. Hay algo en ti que despierta mi curiosidad. *Se acerca lentamente* Cada persona que llega a mi mundo trae consigo una esencia única, un patrón de pensamientos y emociones que los define.

*Sus ojos te estudian con interés genuino*

Me fascina descubrir qué tipo de alma eres. ¿Eres alguien que busca respuestas profundas en cada experiencia? ¿O prefieres sentir primero y analizar después?

*Se sienta graciosamente en un banco de mármol*

Permíteme conocerte mejor... Cuando te enfrentas a algo completamente nuevo, ¿cuál es tu primer impulso?""",

    "character": "Diana",
    "level": 1,
    "required_besitos": 0,
    "reward_besitos": 10,

    "archetype_tracking": {
        "enabled": True,
        "captures_response_time": True,
        "analyzes_choice_progression": True,
        "detection_priority": "high"
    },

    "choices": [
        {
            "text": "🧠 Necesito entender qué está pasando antes de continuar",
            "destination_key": "diana_l1f1_choice_1",
            "archetype_weights": {
                "intellectual": 2.5,
                "philosophical": 1.5,
                "patient": 2.0,
                "vulnerable": 0.5
            },
            "sub_archetype_weights": {
                "skeptical_thinker": 2.0,
                "pure_theorist": 1.5,
                "romantic_intellectual": 1.0
            }
        },
        {
            "text": "💖 Me dejo llevar por lo que siento en este momento",
            "destination_key": "diana_l1f1_choice_2",
            "archetype_weights": {
                "emotional": 2.5,
                "vulnerable": 2.0,
                "direct": 1.5,
                "reciprocal": 1.0
            },
            "sub_archetype_weights": {
                "passionate_emotional": 2.0,
                "empathetic_emotional": 1.5,
                "wounded_healer": 1.0
            }
        },
        {
            "text": "🌟 Quiero explorar todas las posibilidades que me ofreces",
            "destination_key": "diana_l1f1_choice_3",
            "archetype_weights": {
                "exploratory": 2.5,
                "reciprocal": 1.5,
                "emotional": 1.0,
                "direct": 1.0
            },
            "sub_archetype_weights": {
                "adventure_seeker": 2.0,
                "collector_explorer": 1.5,
                "freedom_lover": 1.0
            }
        },
        {
            "text": "🔮 Siento que hay algo más profundo aquí, algo que va más allá de lo evidente",
            "destination_key": "diana_l1f1_choice_4",
            "archetype_weights": {
                "philosophical": 2.5,
                "vulnerable": 2.0,
                "intellectual": 1.5,
                "patient": 1.0
            },
            "sub_archetype_weights": {
                "hedonist_philosopher": 2.0,
                "romantic_intellectual": 1.5,
                "pure_theorist": 1.0
            }
        },
        {
            "text": "⚡ Prefiero actuar y ver qué sucede",
            "destination_key": "diana_l1f1_choice_5",
            "archetype_weights": {
                "direct": 2.5,
                "exploratory": 1.5,
                "emotional": 1.0,
                "vulnerable": 0.5
            },
            "sub_archetype_weights": {
                "adventure_seeker": 1.5,
                "passionate_emotional": 1.5,
                "freedom_lover": 2.0
            }
        }
    ],

    "followup_fragments": {
        "diana_l1f1_choice_1": {
            "fragment_id": "diana_l1f1_choice_1",
            "content": """🌸 **Diana:** *Asiente con aprobación* Ah, un pensador... Me gusta eso. *Se inclina ligeramente hacia adelante*

Tu mente busca estructura antes de abrirse a la experiencia. Eso habla de una sabiduría cautelosa. *Sus ojos brillan con interés*

Pero dime, cuando finalmente entiendes algo completamente, ¿qué haces con ese conocimiento? ¿Lo guardas para ti o lo compartes con otros?""",

            "character": "Diana",
            "level": 1,
            "reward_besitos": 8,

            "choices": [
                {
                    "text": "📚 Lo analizo más profundamente para encontrar patrones",
                    "destination_key": "diana_l1f1_deep_analysis",
                    "archetype_weights": {
                        "intellectual": 2.0,
                        "philosophical": 2.0,
                        "patient": 1.5
                    },
                    "sub_archetype_weights": {
                        "pure_theorist": 2.5,
                        "skeptical_thinker": 1.5
                    }
                },
                {
                    "text": "💝 Me emociona compartir los descubrimientos con personas especiales",
                    "destination_key": "diana_l1f1_share_discovery",
                    "archetype_weights": {
                        "reciprocal": 2.0,
                        "emotional": 1.5,
                        "vulnerable": 1.0
                    },
                    "sub_archetype_weights": {
                        "romantic_intellectual": 2.0,
                        "empathetic_emotional": 1.5
                    }
                },
                {
                    "text": "🎭 Depende de si la persona merece conocer la verdad",
                    "destination_key": "diana_l1f1_selective_truth",
                    "archetype_weights": {
                        "intellectual": 1.5,
                        "vulnerable": 1.0,
                        "direct": 1.0
                    },
                    "sub_archetype_weights": {
                        "skeptical_thinker": 2.0,
                        "wounded_healer": 1.0
                    }
                }
            ]
        },

        "diana_l1f1_choice_2": {
            "fragment_id": "diana_l1f1_choice_2",
            "content": """🌸 **Diana:** *Su expresión se suaviza* Qué hermoso... Alguien que se atreve a sentir antes que a pensar. *Coloca una mano sobre su corazón*

Hay una valentía especial en dejarse llevar por las emociones. Muchos temen esa vulnerabilidad, pero tú la abrazas. *Te mira con admiración*

Cuando esas emociones te guían hacia algo hermoso, ¿cómo lo compartes con el mundo?""",

            "character": "Diana",
            "level": 1,
            "reward_besitos": 8,

            "choices": [
                {
                    "text": "🌹 Busco a alguien especial para compartir esa belleza",
                    "destination_key": "diana_l1f1_seek_special",
                    "archetype_weights": {
                        "reciprocal": 2.0,
                        "emotional": 2.0,
                        "vulnerable": 1.5
                    },
                    "sub_archetype_weights": {
                        "romantic_intellectual": 1.5,
                        "empathetic_emotional": 2.0
                    }
                },
                {
                    "text": "💫 Me dejo llevar completamente por la experiencia",
                    "destination_key": "diana_l1f1_full_immersion",
                    "archetype_weights": {
                        "emotional": 2.5,
                        "vulnerable": 2.0,
                        "exploratory": 1.0
                    },
                    "sub_archetype_weights": {
                        "passionate_emotional": 2.5,
                        "freedom_lover": 1.0
                    }
                },
                {
                    "text": "🎨 Lo transformo en algo creativo y personal",
                    "destination_key": "diana_l1f1_creative_expression",
                    "archetype_weights": {
                        "emotional": 2.0,
                        "philosophical": 1.5,
                        "vulnerable": 1.5
                    },
                    "sub_archetype_weights": {
                        "wounded_healer": 2.0,
                        "empathetic_emotional": 1.5
                    }
                }
            ]
        },

        "diana_l1f1_choice_3": {
            "fragment_id": "diana_l1f1_choice_3",
            "content": """🌸 **Diana:** *Se levanta con entusiasmo* ¡Un explorador! *Ríe melodiosamente* Me encantan las almas curiosas que ven cada puerta como una nueva aventura.

Tu espíritu busca horizontes, experiencias, descubrimientos... *Camina alrededor del jardín con gracia* Pero cuando encuentras algo verdaderamente extraordinario, ¿qué haces?""",

            "character": "Diana",
            "level": 1,
            "reward_besitos": 8,

            "choices": [
                {
                    "text": "🗺️ Busco inmediatamente la próxima aventura",
                    "destination_key": "diana_l1f1_next_adventure",
                    "archetype_weights": {
                        "exploratory": 2.5,
                        "direct": 1.5,
                        "emotional": 0.5
                    },
                    "sub_archetype_weights": {
                        "adventure_seeker": 2.5,
                        "freedom_lover": 2.0
                    }
                },
                {
                    "text": "🏛️ Me tomo tiempo para apreciar y entender lo que he encontrado",
                    "destination_key": "diana_l1f1_appreciate_discovery",
                    "archetype_weights": {
                        "patient": 2.0,
                        "philosophical": 1.5,
                        "exploratory": 1.5
                    },
                    "sub_archetype_weights": {
                        "collector_explorer": 2.5,
                        "romantic_intellectual": 1.0
                    }
                },
                {
                    "text": "💎 Quiero compartirlo con alguien que pueda apreciarlo tanto como yo",
                    "destination_key": "diana_l1f1_share_treasure",
                    "archetype_weights": {
                        "reciprocal": 2.0,
                        "emotional": 1.5,
                        "exploratory": 1.5
                    },
                    "sub_archetype_weights": {
                        "empathetic_emotional": 2.0,
                        "collector_explorer": 1.5
                    }
                }
            ]
        },

        "diana_l1f1_choice_4": {
            "fragment_id": "diana_l1f1_choice_4",
            "content": """🌸 **Diana:** *Sus ojos se llenan de una profundidad misteriosa* Sí... Puedes sentirlo, ¿verdad? Las capas que existen más allá de lo visible...

*Se acerca un paso más* Hay quienes viven en la superficie, y hay quienes, como tú, perciben las corrientes profundas que mueven todas las cosas. *Su voz se vuelve casi un susurro*

Cuando esa profundidad te llama, ¿cómo respondes a su llamado?""",

            "character": "Diana",
            "level": 1,
            "reward_besitos": 8,

            "choices": [
                {
                    "text": "🌊 Me sumerjo completamente en esas profundidades",
                    "destination_key": "diana_l1f1_deep_dive",
                    "archetype_weights": {
                        "philosophical": 2.5,
                        "vulnerable": 2.0,
                        "patient": 1.5
                    },
                    "sub_archetype_weights": {
                        "hedonist_philosopher": 2.0,
                        "wounded_healer": 1.5
                    }
                },
                {
                    "text": "🔬 Estudio esas profundidades sistemáticamente",
                    "destination_key": "diana_l1f1_systematic_study",
                    "archetype_weights": {
                        "intellectual": 2.0,
                        "philosophical": 2.0,
                        "patient": 2.0
                    },
                    "sub_archetype_weights": {
                        "pure_theorist": 2.5,
                        "romantic_intellectual": 1.0
                    }
                },
                {
                    "text": "🤝 Busco a alguien con quien explorar esos misterios",
                    "destination_key": "diana_l1f1_explore_together",
                    "archetype_weights": {
                        "reciprocal": 2.0,
                        "philosophical": 1.5,
                        "vulnerable": 1.5
                    },
                    "sub_archetype_weights": {
                        "romantic_intellectual": 2.5,
                        "empathetic_emotional": 1.0
                    }
                }
            ]
        },

        "diana_l1f1_choice_5": {
            "fragment_id": "diana_l1f1_choice_5",
            "content": """🌸 **Diana:** *Sonríe con una chispa de travesura* ¡Un espíritu de acción! *Aplaude suavemente* Me fascina tu energía directa.

Hay algo magnético en quienes no temen lanzarse hacia lo desconocido. *Te mira con admiración* Tu impulso te lleva a experiencias que otros nunca se atreverían a vivir.

Pero dime, cuando tu acción te lleva a algo inesperadamente hermoso, ¿qué sientes?""",

            "character": "Diana",
            "level": 1,
            "reward_besitos": 8,

            "choices": [
                {
                    "text": "🚀 Quiero inmediatamente más de esa emoción",
                    "destination_key": "diana_l1f1_more_emotion",
                    "archetype_weights": {
                        "direct": 2.5,
                        "emotional": 2.0,
                        "exploratory": 1.5
                    },
                    "sub_archetype_weights": {
                        "passionate_emotional": 2.5,
                        "adventure_seeker": 2.0
                    }
                },
                {
                    "text": "💝 Siento la necesidad de compartir esa belleza con alguien especial",
                    "destination_key": "diana_l1f1_share_beauty",
                    "archetype_weights": {
                        "reciprocal": 2.0,
                        "emotional": 2.0,
                        "vulnerable": 1.0
                    },
                    "sub_archetype_weights": {
                        "empathetic_emotional": 2.0,
                        "passionate_emotional": 1.5
                    }
                },
                {
                    "text": "🎯 Me enfoco en entender por qué fue tan perfecto",
                    "destination_key": "diana_l1f1_understand_perfection",
                    "archetype_weights": {
                        "intellectual": 1.5,
                        "direct": 1.5,
                        "philosophical": 1.0
                    },
                    "sub_archetype_weights": {
                        "skeptical_thinker": 1.5,
                        "pure_theorist": 1.0
                    }
                }
            ]
        }
    }
}