#!/usr/bin/env python3
"""
Script to create initial compatibility quiz with Diana.

Creates a sample quiz with 10 questions about personality,
interests, and values to test compatibility.

Usage:
    python scripts/create_initial_quiz.py
    OR
    cd /path/to/mybot && python scripts/create_initial_quiz.py
"""

import asyncio
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from database.midivan_models import CompatibilityQuiz, QuizQuestion, QuizOption
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


QUIZ_DATA = {
    "title": "¿Qué tan compatible eres con Diana?",
    "description": "Descubre tu nivel de compatibilidad con Diana a través de 10 preguntas sobre personalidad, intereses y valores.",
    "besitos_reward": 100,
    "questions": [
        {
            "number": 1,
            "category": "personality",
            "text": "¿Cómo te describes en una fiesta?",
            "options": [
                {
                    "text": "Soy el alma de la fiesta, me encanta socializar",
                    "score": 85,
                    "response": "¡Me encanta tu energía! Yo también disfruto conectar con gente."
                },
                {
                    "text": "Prefiero conversaciones profundas con pocas personas",
                    "score": 95,
                    "response": "Eso me fascina. Las conversaciones íntimas son las mejores."
                },
                {
                    "text": "Alterno entre socializar y momentos a solas",
                    "score": 100,
                    "response": "¡Equilibrio perfecto! Así soy yo también."
                },
                {
                    "text": "Prefiero no ir a fiestas",
                    "score": 60,
                    "response": "Respeto eso. A veces lo íntimo supera lo multitudinario."
                }
            ]
        },
        {
            "number": 2,
            "category": "interests",
            "text": "¿Qué tipo de contenido te gusta consumir?",
            "options": [
                {
                    "text": "Contenido educativo y documentales",
                    "score": 80,
                    "response": "Me gusta aprender cosas nuevas también."
                },
                {
                    "text": "Series y películas de drama/suspenso",
                    "score": 90,
                    "response": "¡Las emociones intensas son lo mejor!"
                },
                {
                    "text": "Contenido erótico y sensual",
                    "score": 100,
                    "response": "Claramente compartimos gustos... Me gusta tu sinceridad."
                },
                {
                    "text": "Comedias y contenido ligero",
                    "score": 70,
                    "response": "Reír es importante, aunque me gusta mezclar géneros."
                }
            ]
        },
        {
            "number": 3,
            "category": "values",
            "text": "¿Qué valoras más en una conexión?",
            "options": [
                {
                    "text": "Honestidad absoluta",
                    "score": 95,
                    "response": "La sinceridad lo es todo para mí."
                },
                {
                    "text": "Química y atracción física",
                    "score": 85,
                    "response": "La química es fundamental, no puedo negarlo."
                },
                {
                    "text": "Conexión emocional profunda",
                    "score": 100,
                    "response": "Eso es exactamente lo que busco. Alguien que me entienda."
                },
                {
                    "text": "Diversión y aventura",
                    "score": 75,
                    "response": "La vida sin diversión es aburrida, ¿no crees?"
                }
            ]
        },
        {
            "number": 4,
            "category": "personality",
            "text": "¿Cómo manejas los conflictos?",
            "options": [
                {
                    "text": "Los evito a toda costa",
                    "score": 50,
                    "response": "A veces hay que enfrentarlos para crecer."
                },
                {
                    "text": "Los enfrento directamente",
                    "score": 85,
                    "response": "Me gusta tu valentía."
                },
                {
                    "text": "Busco resolver con diálogo y empatía",
                    "score": 100,
                    "response": "Perfecto. La comunicación es clave."
                },
                {
                    "text": "Depende de la situación",
                    "score": 80,
                    "response": "La flexibilidad es importante."
                }
            ]
        },
        {
            "number": 5,
            "category": "interests",
            "text": "¿Qué prefieres en una cita ideal?",
            "options": [
                {
                    "text": "Cena romántica con velas",
                    "score": 85,
                    "response": "Clásico y efectivo. Me gusta."
                },
                {
                    "text": "Algo emocionante y diferente",
                    "score": 95,
                    "response": "¡Me encanta la espontaneidad!"
                },
                {
                    "text": "Noche íntima en casa",
                    "score": 100,
                    "response": "Lo íntimo supera cualquier plan extravagante."
                },
                {
                    "text": "Actividad al aire libre",
                    "score": 70,
                    "response": "La naturaleza tiene su encanto."
                }
            ]
        },
        {
            "number": 6,
            "category": "values",
            "text": "¿Qué opinas sobre expresar tus deseos?",
            "options": [
                {
                    "text": "Me da pena, prefiero que adivinen",
                    "score": 40,
                    "response": "La comunicación es mejor que adivinar."
                },
                {
                    "text": "Los expreso claramente",
                    "score": 100,
                    "response": "¡Exacto! La claridad es sexy."
                },
                {
                    "text": "Doy pistas sutiles",
                    "score": 70,
                    "response": "Las pistas pueden ser divertidas, pero la claridad es mejor."
                },
                {
                    "text": "Depende de la confianza",
                    "score": 85,
                    "response": "La confianza es fundamental para abrirse."
                }
            ]
        },
        {
            "number": 7,
            "category": "personality",
            "text": "¿Qué te motiva más en la vida?",
            "options": [
                {
                    "text": "Alcanzar el éxito profesional",
                    "score": 75,
                    "response": "La ambición es atractiva."
                },
                {
                    "text": "Tener relaciones significativas",
                    "score": 100,
                    "response": "Las conexiones humanas son lo más importante."
                },
                {
                    "text": "Vivir experiencias nuevas",
                    "score": 90,
                    "response": "¡Vivir al máximo! Me identifico con eso."
                },
                {
                    "text": "Encontrar paz interior",
                    "score": 85,
                    "response": "El equilibrio interno es hermoso."
                }
            ]
        },
        {
            "number": 8,
            "category": "interests",
            "text": "¿Qué libro o género te atrae más?",
            "options": [
                {
                    "text": "Romance y erótica",
                    "score": 100,
                    "response": "Veo que compartimos gustos literarios..."
                },
                {
                    "text": "Misterio y suspenso",
                    "score": 85,
                    "response": "El misterio tiene su encanto."
                },
                {
                    "text": "Filosofía y autoayuda",
                    "score": 80,
                    "response": "Me gusta gente que busca crecer."
                },
                {
                    "text": "No leo mucho",
                    "score": 50,
                    "response": "Nunca es tarde para empezar."
                }
            ]
        },
        {
            "number": 9,
            "category": "values",
            "text": "¿Qué importancia tiene la intimidad física para ti?",
            "options": [
                {
                    "text": "Es fundamental en una relación",
                    "score": 100,
                    "response": "Estamos en la misma sintonía."
                },
                {
                    "text": "Es importante pero no lo principal",
                    "score": 85,
                    "response": "El equilibrio es sabio."
                },
                {
                    "text": "Prefiero primero conexión emocional",
                    "score": 90,
                    "response": "La base emocional hace todo mejor."
                },
                {
                    "text": "No es prioritario para mí",
                    "score": 40,
                    "response": "Respeto tu perspectiva, aunque difiere de la mía."
                }
            ]
        },
        {
            "number": 10,
            "category": "personality",
            "text": "¿Cómo te describes en pocas palabras?",
            "options": [
                {
                    "text": "Apasionado/a y espontáneo/a",
                    "score": 100,
                    "response": "¡Mi tipo de persona! La pasión lo es todo."
                },
                {
                    "text": "Reflexivo/a y profundo/a",
                    "score": 95,
                    "response": "La profundidad es muy atractiva."
                },
                {
                    "text": "Divertido/a y despreocupado/a",
                    "score": 75,
                    "response": "La alegría es contagiosa."
                },
                {
                    "text": "Equilibrado/a y estable",
                    "score": 80,
                    "response": "El equilibrio es una virtud."
                }
            ]
        }
    ]
}


async def create_quiz(session):
    """Create the initial compatibility quiz."""
    try:
        # Create quiz
        quiz = CompatibilityQuiz(
            title=QUIZ_DATA["title"],
            description=QUIZ_DATA["description"],
            besitos_reward=QUIZ_DATA["besitos_reward"],
            total_questions=len(QUIZ_DATA["questions"]),
            is_active=True
        )

        session.add(quiz)
        await session.flush()  # Get quiz.id

        logger.info(f"Created quiz: {quiz.title}")

        # Create questions and options
        for q_data in QUIZ_DATA["questions"]:
            question = QuizQuestion(
                quiz_id=quiz.id,
                question_number=q_data["number"],
                question_text=q_data["text"],
                category=q_data.get("category")
            )

            session.add(question)
            await session.flush()  # Get question.id

            logger.info(f"  Created question {q_data['number']}: {q_data['text'][:50]}...")

            # Create options
            for idx, opt_data in enumerate(q_data["options"], 1):
                option = QuizOption(
                    question_id=question.id,
                    option_number=idx,
                    option_text=opt_data["text"],
                    compatibility_score=opt_data["score"],
                    diana_response=opt_data.get("response")
                )

                session.add(option)

            logger.info(f"    Added {len(q_data['options'])} options")

        await session.commit()
        logger.info("Quiz created successfully!")
        return True

    except Exception as e:
        logger.error(f"Error creating quiz: {e}")
        await session.rollback()
        return False


async def main():
    """Main function"""
    import os
    try:
        # Set a dummy BOT_TOKEN for migration purposes
        if not os.environ.get("BOT_TOKEN"):
            os.environ["BOT_TOKEN"] = "MIGRATION_DUMMY_TOKEN"

        from utils.config import Config
        DATABASE_URL = Config.DATABASE_URL
    except Exception:
        logger.error("Could not import DATABASE_URL from config")
        DATABASE_URL = "sqlite+aiosqlite:///bot.db"

    logger.info("=" * 60)
    logger.info("Creating Initial Compatibility Quiz")
    logger.info("=" * 60)

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        # Check if quiz with same title already exists
        from sqlalchemy import select
        stmt = select(CompatibilityQuiz).where(
            CompatibilityQuiz.title == QUIZ_DATA["title"]
        ).order_by(CompatibilityQuiz.created_at.desc())
        result = await session.execute(stmt)
        existing_quizzes = result.scalars().all()
        existing = existing_quizzes[0] if existing_quizzes else None

        if existing:
            logger.warning("=" * 60)
            logger.warning(f"⚠️  Quiz already exists: {existing.title} (ID: {existing.id})")
            logger.warning("=" * 60)
            logger.warning("Options:")
            logger.warning("1. Change the 'title' in QUIZ_DATA to create a different quiz")
            logger.warning("2. Delete the existing quiz from the database first")
            logger.warning("3. Use the admin panel to manage existing quizzes")
            logger.warning("")
            logger.warning("To avoid duplicates, aborting creation.")
            return 1

        success = await create_quiz(session)

        if success:
            logger.info("=" * 60)
            logger.info("✅ Quiz created successfully!")
            logger.info("=" * 60)
            logger.info(f"Title: {QUIZ_DATA['title']}")
            logger.info(f"Questions: {len(QUIZ_DATA['questions'])}")
            logger.info(f"Reward: {QUIZ_DATA['besitos_reward']} besitos")
            logger.info("")
            logger.info("VIP users can now take the quiz in Mi Diván!")
            return 0
        else:
            logger.error("Failed to create quiz")
            return 1

    await engine.dispose()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
