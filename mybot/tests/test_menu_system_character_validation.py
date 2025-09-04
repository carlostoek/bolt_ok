"""
Menu System Character Validation Tests

Tests to ensure Diana's character consistency is maintained across
all menu interactions, interface elements, and user experience flows.
"""

import pytest
import pytest_asyncio
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

from services.diana_character_validator import DianaCharacterValidator, DianaPersonalityTrait
from services.diana_menu_system import DianaMenuSystem
from services.diana_menus.narrative_menu import DianaNarrativeMenu
from services.diana_menus.user_menu import DianaUserMenu
from services.diana_menus.admin_menu import DianaAdminMenu


class TestMainMenuCharacterConsistency:
    """Test character consistency in main menu interactions."""
    
    @pytest_asyncio.fixture
    async def validator(self, session):
        return DianaCharacterValidator(session)
    
    @pytest_asyncio.fixture
    async def menu_system(self, session):
        return DianaMenuSystem(session)
    
    async def test_main_menu_welcome_messages(self, validator):
        """Test that main menu welcome messages maintain Diana's character."""
        
        welcome_messages = [
            # User menu welcome
            """
            💋 **Menú Principal Diana**
            Bienvenido a tu experiencia personalizada con Diana.
            
            Aquí puedes explorar los misterios que he preparado especialmente para ti...
            """,
            
            # VIP user welcome
            """
            👑 **Bienvenido, mi querido VIP**
            Diana te sonríe con esa mirada especial reservada para sus amantes más devotos...
            
            "Ahora que has demostrado tu dedicación", susurra seductoramente, 
            "puedo compartir contigo secretos que otros solo pueden soñar..."
            """,
            
            # Returning user welcome
            """
            💫 **¡Has Vuelto!**
            Los ojos de Diana se iluminan al verte... "Sabía que regresarías", 
            murmura con esa sonrisa enigmática, "había algo inconcluso entre nosotros..."
            """
        ]
        
        for message in welcome_messages:
            result = await validator.validate_text(message, context="menu_response")
            
            assert result.overall_score >= 85.0, (
                f"Welcome message scored too low: {result.overall_score}/100\n"
                f"Message: {message[:100]}...\n"
                f"Welcome messages are first impressions and must maintain excellent character consistency"
            )
    
    async def test_menu_navigation_elements(self, validator):
        """Test that menu navigation maintains Diana's voice."""
        
        navigation_elements = [
            # Button texts that maintain character
            "💋 Continuar Historia",
            "🎒 Mochila de Pistas", 
            "🔮 Centro de Decisiones",
            "🎭 Cambiar Personaje",
            "👑 Momentos VIP",
            "💫 Experiencias Exclusivas",
            "📊 Mi Progreso",
            "✨ Configuración de Intimidad",
            
            # Menu descriptions
            "Tu historia personal de seducción y misterio",
            "Secretos y revelaciones descubiertas",
            "Momentos que definirán vuestra historia", 
            "Elige con quién quieres vivir tu próxima experiencia"
        ]
        
        for element in navigation_elements:
            result = await validator.validate_text(element, context="menu_response")
            
            assert result.overall_score >= 70.0, (
                f"Navigation element scored too low: {result.overall_score}/100\n"
                f"Element: {element}\n"
                f"Navigation elements should maintain Diana's character voice"
            )
    
    async def test_menu_system_icons_consistency(self, menu_system):
        """Test that menu system uses consistent character-appropriate icons."""
        
        # Diana menu system should use appropriate icons
        expected_icons = {
            "user": "💋",      # Seductive user interaction
            "narrative": "📖", # Storytelling
            "vip": "👑",       # VIP experience
            "points": "💰",    # Points/rewards
            "admin": "🎭"      # Admin (mask for mystery)
        }
        
        for key, expected_icon in expected_icons.items():
            actual_icon = menu_system.diana_icons.get(key)
            assert actual_icon == expected_icon, (
                f"Icon mismatch for {key}: expected {expected_icon}, got {actual_icon}\n"
                f"Menu icons should be consistent with Diana's character theme"
            )
    
    async def test_error_messages_in_menus(self, validator):
        """Test that menu error messages maintain Diana's character."""
        
        diana_style_errors = [
            # Connection errors
            """
            💋 Oh, mi querido... parece que algo misterioso interrumpió nuestra conexión...
            Permíteme un momento para restaurar el vínculo entre nosotros...
            """,
            
            # Access denied errors
            """
            🔒 Mi amor, ese contenido íntimo está reservado para una experiencia más profunda...
            ¿Te gustaría convertirte en VIP para desbloquear estos secretos especiales?
            """,
            
            # Loading errors
            """
            ✨ Las estrellas no se han alineado correctamente en este momento...
            Diana te pide paciencia mientras reorganiza los misterios del universo...
            """,
            
            # Invalid selection errors
            """
            🎭 Esa elección no está disponible en este capítulo de nuestra historia...
            Permíteme guiarte hacia las opciones que el destino ha preparado para ti...
            """
        ]
        
        for error_message in diana_style_errors:
            result = await validator.validate_text(error_message, context="error_message")
            
            assert result.overall_score >= 75.0, (
                f"Error message scored too low: {result.overall_score}/100\n"
                f"Message: {error_message[:100]}...\n"
                f"Even error messages must maintain Diana's seductive, mysterious character"
            )
            
            # Error messages should avoid technical language
            assert not any(word in error_message.lower() for word in ['error', 'sistema', 'fallo']), (
                f"Error message contains technical language that breaks immersion:\n{error_message}"
            )


class TestNarrativeMenuCharacterConsistency:
    """Test character consistency specifically in narrative menu interactions."""
    
    async def test_narrative_hub_presentation(self, session):
        """Test that narrative hub maintains Diana's character."""
        validator = DianaCharacterValidator(session)
        
        # Sample narrative hub content
        narrative_hub_text = """
        📖 **CENTRO NARRATIVO - DIANA**
        *Tu historia personal de seducción y misterio*
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        💋 **Tu Viaje con Diana**
        • Capítulo actual: Los Susurros del Corazón
        • Progreso: 67% completado
        • Última interacción: Te observé con esos ojos llenos de secretos...
        
        🗝️ **Pistas Narrativas**  
        • Desbloqueadas: 8 revelaciones íntimas
        • Disponibles: 2 misterios esperando
        • Próxima pista: Continúa la historia para más secretos
        
        🔮 **Decisiones Pendientes**
        • Momentos de elección: 1 decisión crucial
        • Impacto acumulado: Profundizando la conexión
        • Caminos abiertos: El destino nos ofrece múltiples senderos
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━
        💋 *Diana susurra: "Cada momento contigo teje una historia única... ¿listos para el siguiente capítulo?"*
        """
        
        result = await validator.validate_text(narrative_hub_text, context="menu_response")
        
        assert result.overall_score >= 90.0, (
            f"Narrative hub scored too low: {result.overall_score}/100\n"
            f"The narrative hub is central to user experience and must excel in character consistency"
        )
        
        # Should excel in mysterious and seductive traits
        mysterious_score = result.trait_scores[DianaPersonalityTrait.MYSTERIOUS]
        seductive_score = result.trait_scores[DianaPersonalityTrait.SEDUCTIVE]
        
        assert mysterious_score >= 22.0, f"Narrative hub should be highly mysterious: {mysterious_score}/25"
        assert seductive_score >= 22.0, f"Narrative hub should be highly seductive: {seductive_score}/25"
    
    async def test_character_selection_menu(self, session):
        """Test character selection menu maintains personality consistency."""
        validator = DianaCharacterValidator(session)
        
        character_selection_text = """
        🎭 **SELECCIÓN DE PERSONAJE**
        *Elige con quién quieres vivir tu próxima experiencia*
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        💋 **DIANA - La Seductora**
        • Personalidad: Apasionada, misteriosa, seductora
        • Especialidad: Romance intenso y pasión
        • Historia completada: 65%
        • Momentos íntimos: 8 encuentros especiales
        
        🖤 **LUCIEN - El Enigma**  
        • Personalidad: Misterioso, intelectual, intenso
        • Especialidad: Intriga psicológica y tensión
        • Historia completada: 20%
        • Momentos íntimos: 2 encuentros profundos
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        ✨ **Experiencias Exclusivas**
        Desbloquea contenido único con cada personaje según tu elección y progreso
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━
        *¿Con quién quieres continuar tu historia de pasión y misterio?*
        """
        
        result = await validator.validate_text(character_selection_text, context="menu_response")
        
        assert result.overall_score >= 85.0, (
            f"Character selection menu scored too low: {result.overall_score}/100\n"
            f"Character selection should maintain high consistency while presenting choices"
        )
    
    async def test_vip_upgrade_prompts(self, session):
        """Test that VIP upgrade prompts maintain Diana's seductive character."""
        validator = DianaCharacterValidator(session)
        
        vip_upgrade_prompts = [
            # Subtle VIP prompt
            """
            🔒 **CONTENIDO VIP REQUERIDO**
            
            Diana te mira con deseo, pero niega suavemente con la cabeza...
            
            💋 *"Este momento especial es solo para mis amantes más dedicados, mi amor. 
            Algunas fantasías requieren una conexión más profunda..."*
            
            👑 **¿Te gustaría convertirte en VIP?**
            Desbloquea experiencias que cambiarán tu relación con Diana para siempre.
            """,
            
            # Direct but character-consistent prompt
            """
            ✨ **Momentos Exclusivos Te Esperan**
            
            "Veo el deseo en tus ojos", susurra Diana, "y mi corazón anhela compartir 
            contigo esos secretos íntimos que reservo para mis compañeros más especiales..."
            
            💫 **Beneficios VIP:**
            • Acceso a momentos íntimos exclusivos
            • Decisiones que transforman la historia  
            • Contenido para adultos sin censura
            • Personajes y escenarios únicos
            """
        ]
        
        for prompt in vip_upgrade_prompts:
            result = await validator.validate_text(prompt, context="menu_response")
            
            assert result.overall_score >= 85.0, (
                f"VIP upgrade prompt scored too low: {result.overall_score}/100\n"
                f"VIP prompts must maintain Diana's character while encouraging upgrades"
            )
            
            # Should maintain seductive trait while being commercial
            seductive_score = result.trait_scores[DianaPersonalityTrait.SEDUCTIVE]
            assert seductive_score >= 20.0, (
                f"VIP prompt should maintain seductive appeal: {seductive_score}/25"
            )


class TestUserProgressAndStatisticsDisplay:
    """Test character consistency in user progress and statistics displays."""
    
    async def test_user_profile_display(self, session):
        """Test that user profile displays maintain Diana's voice."""
        validator = DianaCharacterValidator(session)
        
        profile_display = """
        👤 **TU PERFIL CON DIANA**
        *El reflejo de vuestra historia juntos*
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        💫 **Progreso de Nuestra Historia**
        • Nivel de Intimidad: Corazones Conectados (Nivel 7)
        • Puntos de Pasión: 1,250 besitos acumulados  
        • Días juntos: 23 días de conexión profunda
        • Última actividad: Diana susurró secretos para ti hace 2 horas
        
        🎭 **Tu Personalidad Descubierta**
        • Tipo de amante: Romántico Apasionado
        • Afinidad con Diana: 89% - "Conexión Extraordinaria"
        • Decisiones tomadas: 45 momentos que definieron vuestra historia
        • Secretos desbloqueados: 12 revelaciones íntimas
        
        🏆 **Logros en el Arte del Amor**
        • 🌹 "Conquistador de Corazones" - Completado
        • 💋 "Confidente de Secretos" - En progreso  
        • ✨ "Filósofo de la Pasión" - Desbloqueado
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        💋 *Diana te observa con orgullo: "Has crecido tanto en el arte de la seducción... 
        cada día me sorprendes más con la profundidad de tu alma..."*
        """
        
        result = await validator.validate_text(profile_display, context="menu_response")
        
        assert result.overall_score >= 90.0, (
            f"User profile display scored too low: {result.overall_score}/100\n"
            f"Profile displays should maintain excellent character consistency"
        )
        
        # Should avoid technical gaming language
        technical_violations = [v for v in result.violations if "technical" in v.lower()]
        assert len(technical_violations) == 0, (
            f"Profile should avoid technical language: {technical_violations}"
        )
    
    async def test_achievement_notifications(self, session):
        """Test that achievement notifications maintain Diana's character."""
        validator = DianaCharacterValidator(session)
        
        achievement_notifications = [
            # New achievement unlocked
            """
            🏆 **¡NUEVO LOGRO DESBLOQUEADO!**
            
            💋 **"Conquistador de Corazones"**
            *Has demostrado una dedicación extraordinaria a Diana*
            
            "Mi querido", susurra Diana con los ojos brillando de orgullo, 
            "has logrado algo especial... tu constancia y pasión han tocado 
            las fibras más profundas de mi corazón..."
            
            ✨ **Recompensa:** +500 besitos & Acceso a contenido íntimo especial
            """,
            
            # Level up notification  
            """
            💫 **¡NIVEL DE INTIMIDAD AUMENTADO!**
            
            🎭 **Ahora eres: "Amante Devoto" (Nivel 5)**
            
            Diana te toma de las manos con una sonrisa radiante...
            "Siento cómo nuestra conexión se profundiza", murmura con voz sedosa, 
            "cada día que pasa te adentras más en los misterios de mi corazón..."
            
            🔓 **Nuevos secretos desbloqueados para tu nivel de intimidad**
            """
        ]
        
        for notification in achievement_notifications:
            result = await validator.validate_text(notification, context="menu_response")
            
            assert result.overall_score >= 85.0, (
                f"Achievement notification scored too low: {result.overall_score}/100\n"
                f"Notifications should maintain character while celebrating user progress"
            )


class TestMenuSystemEdgeCases:
    """Test menu system character consistency in edge cases."""
    
    async def test_empty_or_loading_states(self, session):
        """Test character consistency in empty/loading states."""
        validator = DianaCharacterValidator(session)
        
        loading_messages = [
            # Loading narrative content
            """
            ✨ Diana está preparando algo especial para ti...
            Los misterios más hermosos requieren un momento de anticipación...
            """,
            
            # Empty progress state
            """
            🌹 **Tu Historia Está Comenzando**
            
            Diana te observa con curiosidad y expectación...
            "Estamos en el umbral de algo maravilloso", susurra, 
            "¿listos para escribir el primer capítulo de nuestra historia?"
            """,
            
            # No VIP content available
            """
            💫 **Momentos Especiales En Preparación**
            
            "Estoy creando experiencias únicas solo para ti", murmura Diana 
            con esa sonrisa misteriosa, "los secretos más hermosos requieren 
            tiempo para florecer..."
            """
        ]
        
        for message in loading_messages:
            result = await validator.validate_text(message, context="menu_response")
            
            assert result.overall_score >= 75.0, (
                f"Loading message scored too low: {result.overall_score}/100\n"
                f"Even loading states should maintain Diana's character"
            )
    
    async def test_menu_accessibility_with_character(self, session):
        """Test that accessibility features maintain character consistency."""
        validator = DianaCharacterValidator(session)
        
        # Screen reader friendly descriptions that maintain character
        accessible_descriptions = [
            # Button descriptions
            "Botón: Continuar Historia. Diana te invita a adentrarte en el próximo capítulo de vuestra historia íntima.",
            
            # Menu navigation help
            """
            💋 **Navegación del Menú**
            Diana te guía suavemente: "Usa las flechas para explorar las opciones, 
            mi amor. Cada botón te llevará a una nueva faceta de nuestra experiencia juntos..."
            """,
            
            # Content warnings with character voice
            """
            🎭 **Aviso de Contenido Íntimo**
            Diana te susurra: "Lo que estás a punto de descubrir contiene 
            pasión y sensualidad para adultos... ¿tu corazón está preparado 
            para esta intensidad?"
            """
        ]
        
        for description in accessible_descriptions:
            result = await validator.validate_text(description, context="menu_response")
            
            assert result.overall_score >= 70.0, (
                f"Accessible description scored too low: {result.overall_score}/100\n"
                f"Accessibility features should maintain character while being functional"
            )
    
    async def test_multilingual_menu_consistency(self, session):
        """Test that multilingual elements maintain character when present."""
        validator = DianaCharacterValidator(session)
        
        # Test mixed language content (common in international apps)
        mixed_content = [
            # English with Spanish elements
            """
            💋 **Main Menu - Diana**
            Bienvenido to your personalized experience with Diana...
            "Welcome, mi amor", she whispers with that mysterious smile...
            """,
            
            # Spanish with English elements  
            """
            🎭 **Centro Narrativo**
            Tu historia personal de seduction and mystery...
            Diana te observa: "Ready para el próximo chapter, my love?"
            """
        ]
        
        for content in mixed_content:
            result = await validator.validate_text(content, context="menu_response")
            
            # Should still maintain reasonable character consistency
            assert result.overall_score >= 60.0, (
                f"Multilingual content scored too low: {result.overall_score}/100\n"
                f"Mixed language content should still maintain Diana's personality patterns"
            )


class TestMenuSystemIntegrationValidation:
    """Test integration between menu system and character validation."""
    
    async def test_menu_system_validation_integration(self, session):
        """Test that menu system integrates with character validation."""
        menu_system = DianaMenuSystem(session)
        validator = DianaCharacterValidator(session)
        
        # Test that menu system has the necessary components
        assert hasattr(menu_system, 'diana_icons'), "Menu system should have character icons"
        assert hasattr(menu_system, 'session'), "Menu system should have database session"
        
        # Test integration with validation would work
        sample_menu_text = "💋 Diana te da la bienvenida a su mundo de misterios..."
        result = await validator.validate_text(sample_menu_text, context="menu_response")
        
        # Should be able to validate menu content
        assert result.overall_score > 0, "Menu validation should work"
        assert isinstance(result.overall_score, (int, float)), "Should return numeric score"
    
    @patch('services.diana_menu_system.DianaMenuSystem._get_character_quote')
    async def test_dynamic_menu_content_validation(self, mock_get_quote, session):
        """Test validation of dynamically generated menu content."""
        validator = DianaCharacterValidator(session)
        
        # Mock dynamic content generation
        mock_get_quote.return_value = (
            "Apenas comenzamos a conocernos, pero ya siento la conexión..."
        )
        
        # Test that dynamically generated content would maintain character
        dynamic_content = f"""
        💋 **Tu Progreso con Diana**
        {mock_get_quote.return_value}
        
        ✨ Continúa explorando los misterios que he preparado para ti...
        """
        
        result = await validator.validate_text(dynamic_content, context="menu_response")
        
        assert result.overall_score >= 75.0, (
            f"Dynamic menu content scored too low: {result.overall_score}/100\n"
            f"Dynamically generated content should maintain character consistency"
        )
    
    async def test_menu_performance_with_validation(self, session):
        """Test that menu validation doesn't impact performance significantly."""
        validator = DianaCharacterValidator(session)
        
        import time
        
        # Test multiple menu validations for performance
        menu_texts = [
            "💋 Menú Principal Diana",
            "📖 Centro Narrativo", 
            "🎒 Mochila de Pistas",
            "🔮 Centro de Decisiones",
            "👑 Momentos VIP"
        ] * 5  # 25 validations total
        
        start_time = time.time()
        
        for text in menu_texts:
            await validator.validate_text(text, context="menu_response")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Performance requirement: 25 menu validations should complete quickly
        assert total_time < 1.0, f"Menu validations too slow: {total_time}s for 25 validations"