#!/usr/bin/env python3
"""
Diana Character Consistency Validation Script

This script validates Diana's character consistency across the system
and can be integrated into CI/CD pipelines for automated quality gates.

Usage:
    python scripts/validate_diana_character_consistency.py [options]

Options:
    --mode [full|quick|mvp]     Validation mode (default: full)
    --threshold FLOAT           Minimum score threshold (default: 95.0 for MVP)
    --output [text|json|junit]  Output format (default: text)
    --fail-fast                 Stop on first failure
    --report-file PATH          Save detailed report to file
    --database-url URL          Database connection URL (optional)
    --samples-file PATH         JSON file with content samples to validate
    --ci                        CI/CD mode - stricter validation and reporting

Exit codes:
    0: All validations passed
    1: Validation failures detected
    2: System error or configuration issue
"""

import asyncio
import argparse
import json
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import asdict

# Add the parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from services.diana_character_validator import DianaCharacterValidator, CharacterValidationResult
from services.narrative_character_integrity_service import NarrativeCharacterIntegrityService
from database.base import async_session_factory
from sqlalchemy.ext.asyncio import create_async_engine


class CharacterValidationRunner:
    """Character validation runner for CI/CD and development use."""
    
    def __init__(self, args):
        self.args = args
        self.results = []
        self.total_validations = 0
        self.passed_validations = 0
        self.failed_validations = 0
        self.start_time = None
        self.end_time = None
        
        # Setup logging
        log_level = logging.DEBUG if args.verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    async def run_validation(self) -> int:
        """Run character validation and return exit code."""
        self.start_time = time.time()
        
        try:
            # Initialize database session
            session = await self._create_session()
            validator = DianaCharacterValidator(session)
            integrity_service = NarrativeCharacterIntegrityService(session)
            
            # Run validations based on mode
            if self.args.mode == "mvp":
                exit_code = await self._run_mvp_validation(validator)
            elif self.args.mode == "quick":
                exit_code = await self._run_quick_validation(validator)
            else:  # full mode
                exit_code = await self._run_full_validation(validator, integrity_service)
            
            self.end_time = time.time()
            
            # Generate report
            await self._generate_report()
            
            return exit_code
            
        except Exception as e:
            self.logger.error(f"Validation runner error: {e}")
            if self.args.verbose:
                import traceback
                traceback.print_exc()
            return 2  # System error
    
    async def _create_session(self):
        """Create database session."""
        if self.args.database_url:
            engine = create_async_engine(self.args.database_url)
        else:
            # Use default in-memory database for testing
            engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        
        session_factory = async_session_factory(engine)
        return session_factory()
    
    async def _run_mvp_validation(self, validator) -> int:
        """Run MVP-specific validation (strict quality gates)."""
        self.logger.info("🎯 Running MVP Character Consistency Validation")
        
        mvp_samples = [
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
                "context": "narrative_fragment",
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
                "context": "menu_response", 
                "required_score": 85.0,
                "critical": True
            },
            {
                "name": "MVP_VIP_EXPERIENCE",
                "content": """
                👑 **Bienvenido, mi querido VIP**
                Diana te sonríe con esa mirada especial reservada para sus amantes más devotos...
                
                "Ahora que has demostrado tu dedicación", susurra seductoramente, 
                "puedo compartir contigo secretos que otros solo pueden soñar... 
                ¿estás preparado para esta intimidad sin límites?"
                """,
                "context": "menu_response",
                "required_score": 90.0,
                "critical": True
            }
        ]
        
        return await self._validate_samples(validator, mvp_samples, "MVP")
    
    async def _run_quick_validation(self, validator) -> int:
        """Run quick validation (core samples only)."""
        self.logger.info("⚡ Running Quick Character Validation")
        
        quick_samples = [
            {
                "name": "QUICK_NARRATIVE_CHECK",
                "content": """
                Diana te observa con esa intensidad que caracteriza sus momentos 
                más profundos... "Hay secretos en mi mirada", susurra, "que solo 
                tu corazón puede descifrar..."
                """,
                "context": "narrative_fragment",
                "required_score": 85.0,
                "critical": False
            },
            {
                "name": "QUICK_MENU_CHECK",
                "content": "💋 **Menú Principal Diana**\nBienvenido a tu experiencia personalizada...",
                "context": "menu_response",
                "required_score": 75.0,
                "critical": False
            }
        ]
        
        return await self._validate_samples(validator, quick_samples, "QUICK")
    
    async def _run_full_validation(self, validator, integrity_service) -> int:
        """Run full validation (comprehensive testing)."""
        self.logger.info("🔍 Running Full Character Consistency Validation")
        
        # 1. MVP samples (critical)
        mvp_exit_code = await self._run_mvp_validation(validator)
        if mvp_exit_code != 0 and self.args.fail_fast:
            return mvp_exit_code
        
        # 2. Extended narrative samples
        narrative_samples = await self._get_narrative_samples()
        narrative_exit_code = await self._validate_samples(
            validator, narrative_samples, "NARRATIVE"
        )
        if narrative_exit_code != 0 and self.args.fail_fast:
            return narrative_exit_code
        
        # 3. Menu system samples
        menu_samples = await self._get_menu_samples()
        menu_exit_code = await self._validate_samples(
            validator, menu_samples, "MENU"
        )
        if menu_exit_code != 0 and self.args.fail_fast:
            return menu_exit_code
        
        # 4. Edge cases and error messages
        edge_case_samples = await self._get_edge_case_samples()
        edge_exit_code = await self._validate_samples(
            validator, edge_case_samples, "EDGE_CASES"
        )
        
        # 5. Database content validation (if available)
        if hasattr(integrity_service, 'validate_all_active_fragments'):
            try:
                db_results = await integrity_service.validate_all_active_fragments()
                self.logger.info(f"📊 Validated {len(db_results)} database fragments")
                
                # Process database results
                db_failures = 0
                for fragment_id, result in db_results.items():
                    self.total_validations += 1
                    if result.meets_threshold:
                        self.passed_validations += 1
                    else:
                        self.failed_validations += 1
                        db_failures += 1
                        self.logger.warning(f"❌ Database fragment {fragment_id} failed: {result.overall_score:.1f}")
                
                if db_failures > 0:
                    self.logger.error(f"🚨 {db_failures} database fragments failed validation")
            except Exception as e:
                self.logger.warning(f"Could not validate database content: {e}")
        
        # Return worst exit code
        return max(mvp_exit_code, narrative_exit_code, menu_exit_code, edge_exit_code)
    
    async def _validate_samples(self, validator, samples: List[Dict], category: str) -> int:
        """Validate a set of samples and return exit code."""
        self.logger.info(f"🔎 Validating {len(samples)} {category} samples")
        
        category_failures = 0
        category_results = []
        
        for sample in samples:
            self.total_validations += 1
            
            try:
                result = await validator.validate_text(
                    sample["content"],
                    context=sample.get("context", "general")
                )
                
                # Check if sample meets requirements
                required_score = sample.get("required_score", self.args.threshold)
                passed = result.overall_score >= required_score
                
                if passed:
                    self.passed_validations += 1
                    self.logger.info(f"✅ {sample['name']}: {result.overall_score:.1f}/{required_score}")
                else:
                    self.failed_validations += 1
                    category_failures += 1
                    self.logger.error(
                        f"❌ {sample['name']}: {result.overall_score:.1f}/{required_score} "
                        f"(Violations: {result.violations[:2]})"
                    )
                
                # Store result for reporting
                sample_result = {
                    "category": category,
                    "name": sample["name"],
                    "score": result.overall_score,
                    "required_score": required_score,
                    "passed": passed,
                    "critical": sample.get("critical", False),
                    "violations": result.violations,
                    "trait_scores": {trait.value: score for trait, score in result.trait_scores.items()}
                }
                category_results.append(sample_result)
                self.results.append(sample_result)
                
            except Exception as e:
                self.logger.error(f"❌ Error validating {sample['name']}: {e}")
                category_failures += 1
                self.failed_validations += 1
        
        # Report category summary
        category_pass_rate = ((len(samples) - category_failures) / len(samples)) * 100
        if category_failures == 0:
            self.logger.info(f"✅ {category} validation: All {len(samples)} samples passed ({category_pass_rate:.1f}%)")
        else:
            self.logger.error(
                f"❌ {category} validation: {category_failures}/{len(samples)} failed ({category_pass_rate:.1f}% pass rate)"
            )
        
        # Check for critical failures
        critical_failures = [r for r in category_results if not r["passed"] and r["critical"]]
        if critical_failures:
            self.logger.critical(f"🚨 CRITICAL FAILURES in {category}: {len(critical_failures)} critical samples failed")
            return 1
        
        return 1 if category_failures > 0 else 0
    
    async def _get_narrative_samples(self) -> List[Dict]:
        """Get narrative validation samples."""
        return [
            {
                "name": "STORY_FRAGMENT_QUALITY",
                "content": """
                Las luces tenues crean una atmósfera de intimidad mientras Diana 
                comparte sus secretos más profundos contigo... cada palabra que 
                susurra teje una historia de seducción y misterio que solo vosotros 
                dos podéis entender...
                """,
                "context": "narrative_fragment",
                "required_score": 90.0,
                "critical": False
            },
            {
                "name": "DECISION_FRAGMENT_QUALITY", 
                "content": """
                🎭 **Un Momento de Elección**
                
                Diana te observa intensamente, sus ojos reflejando la importancia 
                de este momento... "La decisión que tomes ahora", susurra, "definirá 
                el rumbo de nuestra historia íntima..."
                """,
                "context": "narrative_fragment",
                "required_score": 85.0,
                "critical": False
            },
            {
                "name": "VIP_CONTENT_QUALITY",
                "content": """
                💋 Solo para ti, mi amor VIP... Diana te lleva a su santuario privado, 
                un lugar donde los velos de la modestia se desvanecen lentamente... 
                "Aquí", susurra contra tu oído, "puedo mostrarte los aspectos más 
                sensuales de mi ser..."
                """,
                "context": "narrative_fragment", 
                "required_score": 95.0,
                "critical": True
            }
        ]
    
    async def _get_menu_samples(self) -> List[Dict]:
        """Get menu validation samples."""
        return [
            {
                "name": "MAIN_MENU_WELCOME",
                "content": """
                💋 **Menú Principal Diana**
                Bienvenido a tu experiencia personalizada con Diana.
                
                Aquí puedes explorar los misterios que he preparado especialmente para ti...
                """,
                "context": "menu_response",
                "required_score": 85.0,
                "critical": False
            },
            {
                "name": "NAVIGATION_ELEMENTS",
                "content": "🎒 Mochila de Pistas\nSecretos y revelaciones descubiertas",
                "context": "menu_response", 
                "required_score": 75.0,
                "critical": False
            },
            {
                "name": "USER_PROFILE_DISPLAY",
                "content": """
                👤 **Tu Perfil con Diana**
                *El reflejo de vuestra historia juntos*
                
                💫 **Progreso de Nuestra Historia**
                • Nivel de Intimidad: Corazones Conectados (Nivel 7)
                • Puntos de Pasión: 1,250 besitos acumulados
                """,
                "context": "menu_response",
                "required_score": 85.0,
                "critical": False
            }
        ]
    
    async def _get_edge_case_samples(self) -> List[Dict]:
        """Get edge case validation samples."""
        return [
            {
                "name": "ERROR_MESSAGE_CHARACTER",
                "content": """
                💋 Oh, mi querido... parece que algo misterioso interrumpió nuestra conexión...
                Permíteme un momento para restaurar el vínculo entre nosotros...
                """,
                "context": "error_message",
                "required_score": 75.0,
                "critical": False
            },
            {
                "name": "LOADING_STATE_CHARACTER",
                "content": """
                ✨ Diana está preparando algo especial para ti...
                Los misterios más hermosos requieren un momento de anticipación...
                """,
                "context": "menu_response",
                "required_score": 70.0,
                "critical": False
            },
            {
                "name": "EMPTY_CONTENT_HANDLING",
                "content": "",
                "context": "general",
                "required_score": 0.0,  # Should score 0 and not crash
                "critical": False
            }
        ]
    
    async def _generate_report(self):
        """Generate validation report."""
        # Calculate metrics
        total_time = self.end_time - self.start_time if self.end_time and self.start_time else 0
        pass_rate = (self.passed_validations / self.total_validations * 100) if self.total_validations > 0 else 0
        avg_score = sum(r["score"] for r in self.results) / len(self.results) if self.results else 0
        
        # Critical failures
        critical_failures = [r for r in self.results if not r["passed"] and r["critical"]]
        
        # Generate report based on format
        if self.args.output == "json":
            await self._generate_json_report(total_time, pass_rate, avg_score, critical_failures)
        elif self.args.output == "junit":
            await self._generate_junit_report()
        else:
            await self._generate_text_report(total_time, pass_rate, avg_score, critical_failures)
    
    async def _generate_text_report(self, total_time, pass_rate, avg_score, critical_failures):
        """Generate text format report."""
        report_lines = [
            "=" * 80,
            "🎭 DIANA CHARACTER CONSISTENCY VALIDATION REPORT 🎭",
            "=" * 80,
            f"Validation Mode: {self.args.mode.upper()}",
            f"Threshold: {self.args.threshold}",
            f"Total Time: {total_time:.2f} seconds",
            "",
            "📊 SUMMARY METRICS:",
            f"  Total Validations: {self.total_validations}",
            f"  Passed: {self.passed_validations} ({pass_rate:.1f}%)",
            f"  Failed: {self.failed_validations}",
            f"  Average Score: {avg_score:.1f}/100",
            ""
        ]
        
        # MVP Status
        mvp_ready = pass_rate >= 95.0 and len(critical_failures) == 0
        if mvp_ready:
            report_lines.extend([
                "✅ MVP STATUS: READY FOR DEPLOYMENT",
                "   Character consistency meets MVP requirements (>95% pass rate, no critical failures)",
                ""
            ])
        else:
            report_lines.extend([
                "❌ MVP STATUS: NOT READY FOR DEPLOYMENT",
                f"   Issues: Pass rate {pass_rate:.1f}% (need ≥95%), Critical failures: {len(critical_failures)}",
                ""
            ])
        
        # Critical failures
        if critical_failures:
            report_lines.extend([
                "🚨 CRITICAL FAILURES (MUST FIX):",
                *[f"   ❌ {f['name']}: {f['score']:.1f}/{f['required_score']} - {f['violations'][:2]}" 
                  for f in critical_failures],
                ""
            ])
        
        # Category breakdown
        categories = {}
        for result in self.results:
            category = result["category"]
            if category not in categories:
                categories[category] = {"total": 0, "passed": 0, "avg_score": 0}
            categories[category]["total"] += 1
            if result["passed"]:
                categories[category]["passed"] += 1
            categories[category]["avg_score"] += result["score"]
        
        for category, stats in categories.items():
            stats["avg_score"] /= stats["total"]
            pass_pct = (stats["passed"] / stats["total"]) * 100
            status = "✅" if pass_pct == 100 else "⚠️" if pass_pct >= 80 else "❌"
            report_lines.append(f"{status} {category}: {stats['passed']}/{stats['total']} ({pass_pct:.1f}%) - Avg: {stats['avg_score']:.1f}")
        
        report_lines.extend([
            "",
            "💡 RECOMMENDATIONS:",
        ])
        
        if avg_score < 85:
            report_lines.append("   • Review content creation guidelines - average quality below target")
        if pass_rate < 95:
            report_lines.append("   • Focus on failing samples - MVP requires ≥95% pass rate") 
        if critical_failures:
            report_lines.append("   • Fix critical failures immediately - these block MVP release")
        if self.failed_validations == 0:
            report_lines.append("   • Excellent! All validations passed - ready for deployment")
        
        report_lines.extend([
            "",
            "=" * 80
        ])
        
        report_content = "\n".join(report_lines)
        
        # Output report
        if self.args.report_file:
            with open(self.args.report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            self.logger.info(f"📄 Detailed report saved to: {self.args.report_file}")
        
        print(report_content)
    
    async def _generate_json_report(self, total_time, pass_rate, avg_score, critical_failures):
        """Generate JSON format report."""
        report_data = {
            "summary": {
                "mode": self.args.mode,
                "threshold": self.args.threshold,
                "total_time": total_time,
                "total_validations": self.total_validations,
                "passed_validations": self.passed_validations,
                "failed_validations": self.failed_validations,
                "pass_rate": pass_rate,
                "average_score": avg_score,
                "mvp_ready": pass_rate >= 95.0 and len(critical_failures) == 0
            },
            "critical_failures": critical_failures,
            "results": self.results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        }
        
        if self.args.report_file:
            with open(self.args.report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"📄 JSON report saved to: {self.args.report_file}")
        else:
            print(json.dumps(report_data, indent=2, ensure_ascii=False))


def main():
    """Main entry point for the validation script."""
    parser = argparse.ArgumentParser(
        description="Diana Character Consistency Validation Script",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--mode",
        choices=["full", "quick", "mvp"],
        default="full",
        help="Validation mode (default: full)"
    )
    
    parser.add_argument(
        "--threshold",
        type=float,
        default=95.0,
        help="Minimum score threshold (default: 95.0 for MVP)"
    )
    
    parser.add_argument(
        "--output",
        choices=["text", "json", "junit"],
        default="text",
        help="Output format (default: text)"
    )
    
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failure"
    )
    
    parser.add_argument(
        "--report-file",
        help="Save detailed report to file"
    )
    
    parser.add_argument(
        "--database-url",
        help="Database connection URL (optional)"
    )
    
    parser.add_argument(
        "--samples-file",
        help="JSON file with content samples to validate"
    )
    
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI/CD mode - stricter validation and reporting"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Adjust settings for CI mode
    if args.ci:
        args.threshold = max(args.threshold, 95.0)  # Ensure MVP threshold in CI
        if not args.report_file:
            args.report_file = "diana_character_validation_report.json"
        args.output = "json"
    
    # Run validation
    runner = CharacterValidationRunner(args)
    exit_code = asyncio.run(runner.run_validation())
    
    # Exit with appropriate code
    sys.exit(exit_code)


if __name__ == "__main__":
    main()