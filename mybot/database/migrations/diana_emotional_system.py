"""
Migration for Diana Emotional System.
Creates tables for tracking character emotional states and history.
"""
from sqlalchemy import Table, Column, Integer, String, Text, ForeignKey, BigInteger, JSON, Float, Boolean
from sqlalchemy.types import DateTime
from sqlalchemy.sql import func

def upgrade(metadata, session):
    """
    Upgrade database with emotional system tables.
    """
    # Character Emotional State table
    CharacterEmotionalState = Table(
        'character_emotional_states',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('user_id', BigInteger, ForeignKey('users.id'), nullable=False, index=True),
        Column('character_name', String(50), nullable=False, index=True),
        
        # Emotional state values
        Column('joy', Float, default=50.0),
        Column('trust', Float, default=30.0),
        Column('fear', Float, default=20.0),
        Column('sadness', Float, default=15.0),
        Column('anger', Float, default=10.0),
        Column('surprise', Float, default=25.0),
        Column('anticipation', Float, default=40.0),
        Column('disgust', Float, default=5.0),
        
        # Additional metadata
        Column('dominant_emotion', String(20), default="neutral"),
        Column('relationship_level', Integer, default=1),
        Column('relationship_status', String(20), default="neutral"),
        
        # Historical data reference
        Column('history_entries', JSON, default=list),
        Column('last_updated', DateTime, default=func.now()),
    )
    
    # Emotional History Entry table
    EmotionalHistoryEntry = Table(
        'emotional_history_entries',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('user_id', BigInteger, ForeignKey('users.id'), nullable=False, index=True),
        Column('character_name', String(50), nullable=False, index=True),
        Column('timestamp', DateTime, default=func.now(), index=True),
        
        # The JSON representation of the emotional state at this point
        Column('emotional_state', JSON, nullable=False),
        
        # Context of this emotional state change
        Column('context_type', String(50), nullable=False, default="interaction"),
        Column('context_description', Text, nullable=True),
        Column('context_reference_id', String(50), nullable=True),
    )
    
    # Emotional Response Template table
    EmotionalResponseTemplate = Table(
        'emotional_response_templates',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('character_name', String(50), nullable=False, index=True),
        Column('emotion', String(20), nullable=False, index=True),
        Column('intensity_level', String(10), nullable=False),
        
        # Template components
        Column('text_prefixes', JSON, default=list),
        Column('text_suffixes', JSON, default=list),
        Column('style_suggestions', JSON, default=list),
        Column('emoji_suggestions', JSON, default=list),
        
        # Sample phrases for this emotional state
        Column('sample_phrases', JSON, default=list),
        
        Column('created_at', DateTime, default=func.now()),
        Column('updated_at', DateTime, default=func.now()),
    )
    
    metadata.create_all()
    
    # Add seed data for emotional response templates
    _insert_default_response_templates(session)

def _insert_default_response_templates(session):
    """
    Insert default emotional response templates for Diana and Lucien.
    """
    templates = [
        # Diana's templates
        {
            "character_name": "Diana",
            "emotion": "joy",
            "intensity_level": "high",
            "text_prefixes": ["¡", "Oh, "],
            "text_suffixes": ["!"],
            "style_suggestions": ["tono alegre", "palabras positivas"],
            "emoji_suggestions": ["😁", "🥰", "✨"],
            "sample_phrases": [
                "¡Eso es maravilloso!",
                "¡Me encanta cuando haces eso!",
                "¡Qué agradable sorpresa!"
            ]
        },
        {
            "character_name": "Diana",
            "emotion": "joy",
            "intensity_level": "medium",
            "text_prefixes": ["¡", "Oh, "],
            "text_suffixes": ["!"],
            "style_suggestions": ["tono alegre", "palabras positivas"],
            "emoji_suggestions": ["😊", "😄"],
            "sample_phrases": [
                "Eso me hace feliz.",
                "Me alegra escuchar eso.",
                "Qué buena elección."
            ]
        },
        {
            "character_name": "Diana",
            "emotion": "trust",
            "intensity_level": "high",
            "text_prefixes": ["Confío en que ", "Creo que "],
            "text_suffixes": [".", "..."],
            "style_suggestions": ["tono confiado", "palabras reconfortantes"],
            "emoji_suggestions": ["❤️", "🫂"],
            "sample_phrases": [
                "Confío plenamente en ti.",
                "Sé que podemos lograrlo juntos.",
                "Tienes mi confianza absoluta."
            ]
        },
        
        # Lucien's templates
        {
            "character_name": "Lucien",
            "emotion": "joy",
            "intensity_level": "high",
            "text_prefixes": ["¡", "Excelente, "],
            "text_suffixes": ["!", "."],
            "style_suggestions": ["tono formal alegre", "palabras elegantes"],
            "emoji_suggestions": ["😁", "✨"],
            "sample_phrases": [
                "¡Excelente elección, si me permite decirlo!",
                "¡Un resultado magnífico, sin duda!",
                "¡Es un verdadero placer ver su progreso!"
            ]
        },
        {
            "character_name": "Lucien",
            "emotion": "trust",
            "intensity_level": "high",
            "text_prefixes": ["Con toda confianza, ", "Si me permite, "],
            "text_suffixes": [".", ", por supuesto."],
            "style_suggestions": ["tono formal", "palabras elegantes"],
            "emoji_suggestions": ["🤝", "🎩"],
            "sample_phrases": [
                "Confío plenamente en su criterio.",
                "Tiene mi más sincera confianza.",
                "Estaré a su lado en todo momento."
            ]
        }
    ]
    
    # In a real implementation, we would insert these into the database
    # For now, we're just defining the structure
    pass