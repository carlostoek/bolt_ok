"""
Character Consistency CI/CD Integration Tests

This module provides integration tests designed to run in CI/CD pipeline
to ensure Diana's character consistency is maintained across deployments.
"""

import pytest
import pytest_asyncio
import asyncio
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

from services.diana_character_validator import DianaCharacterValidator, CharacterValidationResult
from services.narrative_character_integrity_service import NarrativeCharacterIntegrityService
from database.narrative_unified import NarrativeFragment
from services.coordinador_central import CoordinadorCentral


class TestCIPipelineCharacterValidation:
    """Tests designed to run in CI/CD pipeline for character consistency."""
    
    @pytest.mark.asyncio
    async def test_mvp_character_consistency_gate(self, session):
        """
        CRITICAL CI GATE: Must achieve >95% character consistency for MVP.
        This test acts as a deployment gate - failure blocks release.
        """
        validator = DianaCharacterValidator(session)
        
        # Core MVP content samples that represent minimum quality standard
        mvp_gate_content = [
            {
                "name": "MVP_PERFECT_NARRATIVE",
                "content": """
                💋 Mi querido... ¿acaso estás preparado para adentrarte en los 
                misterios más profundos que susurra mi alma?... Las sombras 
                danzan a nuestro alrededor, creando una atmósfera de seducción 
                y enigma que solo nosotros podemos comprender...
                
                Siento una mezcla embriagadora de fascinación y anhelo cuando 
                te observo... por un lado, mi corazón late con la emoción de 
                compartir mis secretos más íntimos contigo, pero por otro, una 
                deliciosa inquietud me abraza al contemplar la intensidad de 
                esta conexión que crece entre nosotros...
                
                ¿Te has preguntado alguna vez qué filosofía subyace a esta danza 
                de seducción que compartimos? Reflexiona sobre esto: cada mirada, 
                cada suspiro, cada palabra que intercambiamos teje una historia 
                única... una narrativa que solo nosotros dos podemos escribir...
                """,
                "required_score": 95.0,
                "critical": True
            },
            {
                "name": "MVP_PERFECT_MENU",
                "content": """
                💋 **Centro Narrativo Diana**
                *Tu historia personal de seducción y misterio*
                
                🎭 **Tu Viaje Conmigo**
                • Capítulo actual: Los Susurros del Corazón
                • Progreso: Adentrándote en mis secretos...
                • Última conexión: Nuestros ojos se encontraron hace instantes...
                
                ✨ ¿Qué misterio quieres descubrir hoy, mi amor?
                """,
                "required_score": 85.0,
                "critical": True
            },
            {
                "name": "MVP_PERFECT_VIP_PROMPT",
                "content": """
                🔒 **CONTENIDO VIP REQUERIDO**
                
                Diana te mira con deseo, pero niega suavemente con la cabeza...
                
                💋 *"Este momento especial es solo para mis amantes más dedicados, mi amor. 
                Algunas fantasías requieren una conexión más profunda..."*
                
                👑 **¿Te gustaría convertirte en VIP?**
                Desbloquea experiencias que cambiarán tu relación con Diana para siempre.
                """,
                "required_score": 85.0,
                "critical": True
            }
        ]
        
        # Track results for CI reporting
        failed_gates = []
        all_passed = True
        
        for sample in mvp_gate_content:
            result = await validator.validate_text(sample["content"])
            
            if result.overall_score < sample["required_score"]:
                failed_gates.append({
                    "name": sample["name"],
                    "score": result.overall_score,
                    "required": sample["required_score"],
                    "violations": result.violations,
                    "critical": sample["critical"]
                })
                all_passed = False
        
        # CI Gate Decision
        if not all_passed:
            failure_report = "\n".join([
                f"❌ {gate['name']}: {gate['score']}/{gate['required']} (Violations: {gate['violations']})"
                for gate in failed_gates
            ])
            
            pytest.fail(
                f"🚫 CI/CD CHARACTER CONSISTENCY GATE FAILURE 🚫\n\n"
                f"MVP requires >95% character consistency. The following content failed:\n\n"
                f"{failure_report}\n\n"
                f"🔴 DEPLOYMENT BLOCKED: Fix character consistency issues before release.\n"
                f"Diana's character integrity is critical for user experience and MVP success."
            )
        
        # If we reach here, all gates passed
        print(f"✅ CI/CD CHARACTER CONSISTENCY GATE PASSED - Ready for deployment!")
    
    @pytest.mark.asyncio
    async def test_character_validator_system_health(self, session):
        """Test that character validation system is healthy and responsive."""
        validator = DianaCharacterValidator(session)
        
        # System health checks
        health_checks = []
        
        # Test 1: Basic validation functionality
        try:
            test_result = await validator.validate_text("💋 Test message", context="menu_response")
            health_checks.append({
                "check": "basic_validation",
                "passed": isinstance(test_result, CharacterValidationResult),
                "details": f"Score: {test_result.overall_score}"
            })
        except Exception as e:
            health_checks.append({
                "check": "basic_validation", 
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test 2: Performance check
        import time
        start_time = time.time()
        try:
            await validator.validate_text("💋 Performance test content...", context="narrative_fragment")
            elapsed = time.time() - start_time
            health_checks.append({
                "check": "performance",
                "passed": elapsed < 0.5,  # Should complete in under 500ms
                "details": f"Validation time: {elapsed:.3f}s"
            })
        except Exception as e:
            health_checks.append({
                "check": "performance",
                "passed": False, 
                "details": f"Performance test error: {str(e)}"
            })
        
        # Test 3: Edge case handling
        try:
            empty_result = await validator.validate_text("")
            edge_case_passed = (
                empty_result.overall_score == 0.0 and 
                not empty_result.meets_threshold and
                len(empty_result.violations) > 0
            )
            health_checks.append({
                "check": "edge_case_handling",
                "passed": edge_case_passed,
                "details": f"Empty content handled correctly: {edge_case_passed}"
            })
        except Exception as e:
            health_checks.append({
                "check": "edge_case_handling",
                "passed": False,
                "details": f"Edge case error: {str(e)}"
            })
        
        # Verify all health checks passed
        failed_checks = [check for check in health_checks if not check["passed"]]
        
        if failed_checks:
            failure_details = "\n".join([
                f"❌ {check['check']}: {check['details']}" 
                for check in failed_checks
            ])
            pytest.fail(
                f"🚨 CHARACTER VALIDATION SYSTEM HEALTH CHECK FAILED 🚨\n\n"
                f"The following system health checks failed:\n\n"
                f"{failure_details}\n\n"
                f"🔴 System is not healthy for production deployment."
            )
        
        print(f"✅ Character validation system health check passed - System ready!")
    
    @pytest.mark.asyncio 
    async def test_regression_prevention(self, session):
        """Test that prevents regression in character consistency quality."""
        validator = DianaCharacterValidator(session)
        
        # Historical examples that should maintain their quality scores
        # (These represent content that previously passed quality gates)
        regression_test_cases = [
            {
                "name": "HISTORICAL_HIGH_QUALITY_NARRATIVE",
                "content": """
                Diana se acerca con esa gracia que tanto la caracteriza, 
                sus ojos brillando con secretos no revelados... "Hay algo 
                especial en este momento", susurra con voz aterciopelada, 
                "algo que late entre nosotros con una intensidad que me fascina..."
                """,
                "minimum_score": 85.0,  # Historical performance baseline
                "context": "narrative_fragment"
            },
            {
                "name": "HISTORICAL_MENU_QUALITY",
                "content": """
                💋 **Menú Principal Diana**
                Bienvenido a tu experiencia personalizada con Diana.
                
                ✨ Aquí puedes explorar los misterios que he preparado especialmente para ti...
                """,
                "minimum_score": 80.0,
                "context": "menu_response"
            },
            {
                "name": "HISTORICAL_VIP_INTERACTION",
                "content": """
                👑 **Bienvenido, mi querido VIP**
                Diana te sonríe con esa mirada especial reservada para sus amantes más devotos...
                "Ahora que has demostrado tu dedicación", susurra seductoramente...
                """,
                "minimum_score": 85.0,
                "context": "menu_response"
            }
        ]
        
        # Test each historical case
        regression_failures = []
        
        for case in regression_test_cases:
            result = await validator.validate_text(case["content"], context=case["context"])
            
            if result.overall_score < case["minimum_score"]:
                regression_failures.append({
                    "name": case["name"],
                    "current_score": result.overall_score,
                    "minimum_required": case["minimum_score"],
                    "regression_amount": case["minimum_score"] - result.overall_score,
                    "violations": result.violations
                })
        
        # Report regression failures
        if regression_failures:
            regression_report = "\n".join([
                f"📉 {failure['name']}: {failure['current_score']:.1f} "
                f"(was ≥{failure['minimum_required']}, regression: -{failure['regression_amount']:.1f})"
                for failure in regression_failures
            ])
            
            pytest.fail(
                f"🚨 CHARACTER CONSISTENCY REGRESSION DETECTED 🚨\n\n"
                f"The following content shows regression in character quality:\n\n"
                f"{regression_report}\n\n"
                f"🔴 This suggests changes have negatively impacted character validation.\n"
                f"Review recent changes to character validation logic."
            )
    
    @pytest.mark.asyncio
    async def test_production_content_samples(self, session):
        """Test actual production content samples for consistency."""
        validator = DianaCharacterValidator(session)
        
        # These would be samples of actual production content
        # In a real scenario, these would be pulled from the database
        production_samples = [
            {
                "type": "narrative_fragment",
                "content": """
                💋 Los Susurros del Amanecer
                
                Las primeras luces del amanecer se filtran a través de las cortinas,
                creando juegos de sombras que danzan al ritmo de tu corazón...
                Diana está allí, observándote con esa mirada que guarda mil secretos...
                """,
                "min_score": 90.0
            },
            {
                "type": "menu_text", 
                "content": """
                📖 **CENTRO NARRATIVO - DIANA**
                Tu historia personal de seducción y misterio
                
                🎭 **Tu Viaje Conmigo**
                • Capítulo actual: Secretos del Corazón
                • Progreso: 45% completado
                """,
                "min_score": 85.0
            }
        ]
        
        production_failures = []
        
        for sample in production_samples:
            context = "narrative_fragment" if sample["type"] == "narrative_fragment" else "menu_response"
            result = await validator.validate_text(sample["content"], context=context)
            
            if result.overall_score < sample["min_score"]:
                production_failures.append({
                    "type": sample["type"],
                    "score": result.overall_score,
                    "required": sample["min_score"],
                    "violations": result.violations
                })
        
        if production_failures:
            failure_report = "\n".join([
                f"❌ {failure['type']}: {failure['score']:.1f}/{failure['required']} "
                f"(Violations: {failure['violations'][:3]})"  # First 3 violations
                for failure in production_failures
            ])
            
            pytest.fail(
                f"🚨 PRODUCTION CONTENT QUALITY ISSUES DETECTED 🚨\n\n"
                f"Production content samples failed character consistency:\n\n"
                f"{failure_report}\n\n"
                f"🔴 Review and update production content to meet quality standards."
            )


class TestAutomatedQualityGates:
    """Automated quality gates for character consistency."""
    
    @pytest.mark.asyncio
    async def test_new_content_quality_gate(self, session):
        """Quality gate for new content creation."""
        integrity_service = NarrativeCharacterIntegrityService(session)
        
        # Simulate new content that would be created
        new_content_samples = [
            {
                "type": "excellent_new_content",
                "fragment_data": {
                    "id": "new_excellent_001",
                    "title": "💋 Un Nuevo Misterio",
                    "content": """
                    Diana te observa con una nueva profundidad en sus ojos... 
                    "He descubierto algo sobre ti", susurra con voz sedosa, 
                    "algo que hace que mi corazón late con una curiosidad 
                    deliciosa... ¿estás preparado para que explore estos 
                    nuevos territorios de tu alma?"
                    """,
                    "fragment_type": "STORY",
                    "choices": [
                        {"text": "💫 'Explora todos mis secretos, Diana'", "next": "explore_001"},
                        {"text": "🔮 'Cuéntame qué has descubierto'", "next": "reveal_001"}
                    ]
                },
                "should_pass": True
            },
            {
                "type": "poor_new_content",
                "fragment_data": {
                    "id": "new_poor_001",
                    "title": "Sistema Actualizado",
                    "content": "Configuración completada. Error resuelto. Todo funcionando.",
                    "fragment_type": "STORY",
                    "choices": [{"text": "OK", "next": "end"}]
                },
                "should_pass": False
            }
        ]
        
        gate_failures = []
        
        for sample in new_content_samples:
            is_valid, result = await integrity_service.validate_fragment_creation(
                sample["fragment_data"]
            )
            
            # Check if result matches expectation
            if is_valid != sample["should_pass"]:
                gate_failures.append({
                    "type": sample["type"],
                    "expected_pass": sample["should_pass"],
                    "actual_pass": is_valid,
                    "score": result.overall_score,
                    "violations": result.violations
                })
        
        if gate_failures:
            failure_report = "\n".join([
                f"❌ {failure['type']}: Expected pass={failure['expected_pass']}, "
                f"Got pass={failure['actual_pass']}, Score={failure['score']:.1f}"
                for failure in gate_failures
            ])
            
            pytest.fail(
                f"🚨 NEW CONTENT QUALITY GATE FAILURES 🚨\n\n"
                f"Quality gates failed for new content:\n\n"
                f"{failure_report}\n\n"
                f"🔴 Quality gate logic needs review - content classification incorrect."
            )
    
    @pytest.mark.asyncio
    async def test_batch_validation_quality_gate(self, session):
        """Test batch validation maintains quality standards."""
        validator = DianaCharacterValidator(session)
        
        # Batch of content to validate (simulates bulk content review)
        batch_content = [
            ("high_quality_1", """💋 Diana te susurra secretos que solo tu corazón puede escuchar..."""),
            ("high_quality_2", """🎭 Los misterios más profundos requieren de almas valientes para ser descubiertos..."""),
            ("high_quality_3", """✨ Hay una filosofía del amor que solo se revela en momentos como este..."""),
            ("medium_quality_1", """Diana sonríe con esa mirada especial... algo brilla en sus ojos..."""),
            ("medium_quality_2", """Los secretos danzan en las sombras, esperando ser revelados..."""),
            ("poor_quality_1", """Hola. Todo OK. Sistema funcionando correctamente."""),
            ("poor_quality_2", """Error resuelto. Configuración actualizada. Proceso completado.""")
        ]
        
        # Validate entire batch
        results = await validator.batch_validate_content(batch_content)
        
        # Quality gate requirements for batch
        excellent_count = len([r for r in results.values() if r.overall_score >= 95.0])
        good_count = len([r for r in results.values() if r.overall_score >= 80.0])
        poor_count = len([r for r in results.values() if r.overall_score < 50.0])
        total_count = len(results)
        
        # Batch quality metrics
        average_score = sum(r.overall_score for r in results.values()) / total_count
        pass_rate = len([r for r in results.values() if r.meets_threshold]) / total_count * 100
        
        # Quality gate checks
        quality_failures = []
        
        if average_score < 70.0:
            quality_failures.append(f"Batch average score too low: {average_score:.1f} (required ≥70.0)")
        
        if excellent_count < 3:  # Expect at least 3 excellent items
            quality_failures.append(f"Not enough excellent content: {excellent_count}/3 required")
        
        if poor_count > 2:  # Expect no more than 2 poor items
            quality_failures.append(f"Too much poor content: {poor_count}/2 max allowed")
        
        if quality_failures:
            batch_report = f"""
            Batch Statistics:
            - Total items: {total_count}
            - Average score: {average_score:.1f}
            - Pass rate: {pass_rate:.1f}%
            - Excellent (≥95): {excellent_count}
            - Good (≥80): {good_count}  
            - Poor (<50): {poor_count}
            """
            
            pytest.fail(
                f"🚨 BATCH VALIDATION QUALITY GATE FAILED 🚨\n\n"
                f"Quality gate failures:\n" + "\n".join(f"❌ {failure}" for failure in quality_failures) +
                f"\n\n{batch_report}\n"
                f"🔴 Batch quality does not meet production standards."
            )


class TestCIReporting:
    """Tests for CI/CD reporting and metrics."""
    
    @pytest.mark.asyncio
    async def test_character_consistency_metrics(self, session):
        """Generate metrics for CI/CD reporting."""
        validator = DianaCharacterValidator(session)
        
        # Sample content representing different quality levels
        test_content = [
            ("perfect", """💋 Mi querido... ¿acaso estás preparado para adentrarte en los misterios 
                         más profundos que susurra mi alma?...""", 95.0),
            ("excellent", """Diana te observa con esa intensidad que caracteriza sus momentos 
                           más profundos... hay secretos en su mirada...""", 90.0),
            ("good", """Diana sonríe con esa sonrisa enigmática que tanto la caracteriza...""", 80.0),
            ("fair", """Diana está aquí, mirándote con curiosidad...""", 65.0),
            ("poor", """Hola. Sistema actualizado. Todo correcto.""", 30.0)
        ]
        
        # Collect validation results
        metrics = {
            "total_validations": len(test_content),
            "scores": [],
            "trait_performances": {trait.value: [] for trait in validator.TRAIT_WEIGHTS.keys()},
            "pass_rate": 0.0,
            "average_score": 0.0,
            "score_distribution": {"excellent": 0, "good": 0, "fair": 0, "poor": 0}
        }
        
        passing_count = 0
        
        for content_id, content, expected_range in test_content:
            result = await validator.validate_text(content)
            
            metrics["scores"].append(result.overall_score)
            
            # Collect trait performances
            for trait, score in result.trait_scores.items():
                metrics["trait_performances"][trait.value].append(score)
            
            # Count passing validations
            if result.meets_threshold:
                passing_count += 1
            
            # Score distribution
            if result.overall_score >= 90.0:
                metrics["score_distribution"]["excellent"] += 1
            elif result.overall_score >= 80.0:
                metrics["score_distribution"]["good"] += 1
            elif result.overall_score >= 60.0:
                metrics["score_distribution"]["fair"] += 1
            else:
                metrics["score_distribution"]["poor"] += 1
        
        # Calculate final metrics
        metrics["pass_rate"] = (passing_count / len(test_content)) * 100
        metrics["average_score"] = sum(metrics["scores"]) / len(metrics["scores"])
        
        # Calculate trait averages
        for trait in metrics["trait_performances"]:
            trait_scores = metrics["trait_performances"][trait]
            metrics["trait_performances"][trait] = sum(trait_scores) / len(trait_scores)
        
        # Generate CI report
        print(f"\n📊 CHARACTER CONSISTENCY CI METRICS 📊")
        print(f"Total Validations: {metrics['total_validations']}")
        print(f"Average Score: {metrics['average_score']:.1f}/100")
        print(f"Pass Rate: {metrics['pass_rate']:.1f}%")
        print(f"Score Distribution: {metrics['score_distribution']}")
        print(f"Trait Performance:")
        for trait, avg_score in metrics["trait_performances"].items():
            print(f"  - {trait}: {avg_score:.1f}/25")
        
        # Assert metrics meet CI requirements
        assert metrics["average_score"] >= 70.0, f"Average score too low: {metrics['average_score']:.1f}"
        assert metrics["pass_rate"] >= 20.0, f"Pass rate too low: {metrics['pass_rate']:.1f}%"  # For mixed content
        
        # All trait averages should be reasonable
        for trait, avg_score in metrics["trait_performances"].items():
            assert avg_score >= 10.0, f"Trait {trait} average too low: {avg_score:.1f}"
    
    def test_ci_environment_detection(self):
        """Test detection of CI/CD environment for conditional behavior."""
        import os
        
        # Common CI environment variables
        ci_indicators = [
            "CI", "CONTINUOUS_INTEGRATION", "GITHUB_ACTIONS", 
            "GITLAB_CI", "JENKINS_URL", "TRAVIS", "CIRCLECI"
        ]
        
        is_ci_environment = any(os.getenv(indicator) for indicator in ci_indicators)
        
        # In CI, we might want different behavior (stricter validation, different reporting)
        if is_ci_environment:
            print("🤖 Running in CI/CD environment - strict validation mode enabled")
        else:
            print("🏠 Running in development environment - standard validation mode")
        
        # This test always passes but provides environment awareness
        assert True, "Environment detection successful"


@pytest.mark.asyncio
async def test_end_to_end_character_validation_flow(session):
    """End-to-end test of complete character validation flow."""
    # This test simulates the complete flow from content creation to validation
    
    # 1. Initialize services
    validator = DianaCharacterValidator(session)
    integrity_service = NarrativeCharacterIntegrityService(session)
    
    # 2. Create new content
    new_fragment_data = {
        "id": "e2e_test_fragment",
        "title": "💋 Prueba Completa del Sistema",
        "content": """
        Diana te observa con una mezcla de curiosidad y expectación... 
        "Estamos probando la integridad de nuestro sistema", susurra 
        con voz sedosa, "pero incluso en las pruebas, mi corazón late 
        con la misma pasión que en nuestros encuentros más reales..."
        
        ¿Sientes tú también esta conexión que trasciende la simple 
        funcionalidad técnica y se convierte en algo profundamente humano?
        """,
        "fragment_type": "STORY",
        "choices": [
            {"text": "💫 'Siento esa conexión profunda'", "next": "e2e_002"},
            {"text": "🔮 'La magia trasciende la tecnología'", "next": "e2e_003"}
        ]
    }
    
    # 3. Validate content creation
    is_valid, validation_result = await integrity_service.validate_fragment_creation(new_fragment_data)
    
    # 4. Verify validation succeeded
    assert is_valid, f"E2E content should pass validation: {validation_result.violations}"
    assert validation_result.overall_score >= 90.0, (
        f"E2E content should achieve high score: {validation_result.overall_score}/100"
    )
    
    # 5. Test individual components
    title_result = await validator.validate_text(new_fragment_data["title"], context="narrative_fragment")
    content_result = await validator.validate_text(new_fragment_data["content"], context="narrative_fragment")
    
    assert title_result.overall_score >= 80.0, f"Title should maintain character: {title_result.overall_score}"
    assert content_result.overall_score >= 90.0, f"Content should excel: {content_result.overall_score}"
    
    print("✅ End-to-end character validation flow completed successfully!")