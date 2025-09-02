"""
Database Migration: Initialize MVP Narrative Fragments
Creates and validates all Level 1-3 fragments with character consistency.
Version: MVP-1.0.0
"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, text
from database.narrative_unified import Base, NarrativeFragment
from services.mvp_narrative_fragment_service import MVPNarrativeFragmentService
from services.diana_character_validator import DianaCharacterValidator
import os

logger = logging.getLogger(__name__)

class MVPNarrativeFragmentMigration:
    """Migration class for initializing MVP narrative fragments."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
        
    async def initialize_engine(self):
        """Initialize database engine and session factory."""
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_pre_ping=True
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def run_migration(self) -> dict:
        """
        Run the complete MVP fragment migration.
        Returns summary of migration results.
        """
        print("🚀 Starting MVP Narrative Fragments Migration...")
        
        migration_results = {
            'started_at': datetime.utcnow().isoformat(),
            'database_checks': {},
            'fragment_initialization': {},
            'validation_results': {},
            'performance_metrics': {},
            'errors': [],
            'success': False
        }
        
        try:
            await self.initialize_engine()
            
            async with self.session_factory() as session:
                # Step 1: Verify database structure
                print("📋 Verifying database structure...")
                db_check_result = await self._verify_database_structure(session)
                migration_results['database_checks'] = db_check_result
                
                if not db_check_result['tables_exist']:
                    migration_results['errors'].append("Required database tables not found")
                    return migration_results
                
                # Step 2: Initialize MVP narrative fragment service
                print("🔧 Initializing MVP fragment service...")
                fragment_service = MVPNarrativeFragmentService(session)
                
                # Step 3: Initialize fragments with validation
                print("📚 Inserting MVP fragments...")
                fragment_init_result = await fragment_service.initialize_mvp_fragments()
                migration_results['fragment_initialization'] = fragment_init_result
                
                # Step 4: Validate all fragments meet character consistency
                print("🎭 Validating character consistency...")
                validation_result = await self._validate_all_fragments(session)
                migration_results['validation_results'] = validation_result
                
                # Step 5: Performance testing
                print("⚡ Testing performance requirements...")
                performance_result = await self._test_performance_requirements(session)
                migration_results['performance_metrics'] = performance_result
                
                # Step 6: Create sample user states for testing
                print("👤 Creating sample user states...")
                sample_users_result = await self._create_sample_user_states(session)
                migration_results['sample_users'] = sample_users_result
                
                # Final commit
                await session.commit()
                
                migration_results['success'] = True
                migration_results['completed_at'] = datetime.utcnow().isoformat()
                
                print("✅ MVP Narrative Fragments Migration completed successfully!")
                self._print_migration_summary(migration_results)
                
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            migration_results['errors'].append(str(e))
            migration_results['success'] = False
            print(f"❌ Migration failed: {e}")
            
        finally:
            if self.engine:
                await self.engine.dispose()
        
        return migration_results
    
    async def _verify_database_structure(self, session: AsyncSession) -> dict:
        """Verify required database tables exist."""
        try:
            required_tables = [
                'narrative_fragments_unified',
                'user_narrative_states_unified',
                'user_decision_log_unified',
                'user_mission_progress_unified',
                'user_archetypes_unified',
                'narrative_character_validation_unified'
            ]
            
            table_checks = {}
            all_exist = True
            
            for table in required_tables:
                try:
                    result = await session.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                    table_checks[table] = True
                    print(f"  ✅ Table {table} exists")
                except Exception as e:
                    table_checks[table] = False
                    all_exist = False
                    print(f"  ❌ Table {table} missing: {e}")
            
            return {
                'tables_exist': all_exist,
                'individual_checks': table_checks,
                'verified_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error verifying database structure: {e}")
            return {
                'tables_exist': False,
                'error': str(e)
            }
    
    async def _validate_all_fragments(self, session: AsyncSession) -> dict:
        """Validate character consistency for all fragments."""
        try:
            validator = DianaCharacterValidator(session)
            
            stmt = select(NarrativeFragment).where(
                NarrativeFragment.storyline_level.in_([1, 2, 3])
            )
            result = await session.execute(stmt)
            fragments = result.scalars().all()
            
            validation_results = {
                'total_fragments': len(fragments),
                'fragments_validated': 0,
                'passing_validations': 0,
                'failing_validations': 0,
                'average_score': 0.0,
                'fragment_scores': {},
                'issues': []
            }
            
            total_score = 0.0
            
            for fragment in fragments:
                try:
                    validation_result = await validator.validate_text(
                        fragment.content,
                        context=f"fragment_{fragment.id}"
                    )
                    
                    validation_results['fragments_validated'] += 1
                    score = validation_result.overall_score
                    total_score += score
                    
                    validation_results['fragment_scores'][fragment.id] = {
                        'score': score,
                        'meets_requirement': score >= 90.0,
                        'title': fragment.title
                    }
                    
                    if score >= 90.0:
                        validation_results['passing_validations'] += 1
                        print(f"  ✅ Fragment {fragment.id}: {score:.1f}% - {fragment.title}")
                    else:
                        validation_results['failing_validations'] += 1
                        validation_results['issues'].append(
                            f"Fragment {fragment.id} score {score:.1f}% below 90% requirement"
                        )
                        print(f"  ⚠️ Fragment {fragment.id}: {score:.1f}% - {fragment.title}")
                        
                except Exception as e:
                    logger.error(f"Error validating fragment {fragment.id}: {e}")
                    validation_results['issues'].append(f"Fragment {fragment.id}: {str(e)}")
            
            if validation_results['fragments_validated'] > 0:
                validation_results['average_score'] = total_score / validation_results['fragments_validated']
            
            print(f"📊 Validation Summary: {validation_results['passing_validations']}/{validation_results['total_fragments']} passed (avg: {validation_results['average_score']:.1f}%)")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating fragments: {e}")
            return {'error': str(e)}
    
    async def _test_performance_requirements(self, session: AsyncSession) -> dict:
        """Test performance requirements for fragment operations."""
        try:
            from services.mvp_narrative_progression_service import MVPNarrativeProgressionService
            import time
            
            narrative_service = MVPNarrativeProgressionService(session)
            
            performance_results = {
                'fragment_retrieval_times': [],
                'choice_processing_times': [],
                'progress_calculation_times': [],
                'average_retrieval_time': 0.0,
                'average_choice_time': 0.0,
                'average_progress_time': 0.0,
                'meets_500ms_requirement': False
            }
            
            # Test fragment retrieval performance (should be <500ms)
            test_user_id = 99999  # Test user ID
            
            for i in range(5):  # Test 5 times for average
                start_time = time.time()
                await narrative_service.fragment_service.get_user_current_fragment(test_user_id)
                end_time = time.time()
                
                retrieval_time = (end_time - start_time) * 1000  # Convert to ms
                performance_results['fragment_retrieval_times'].append(retrieval_time)
            
            # Test progress calculation performance
            for i in range(5):
                start_time = time.time()
                await narrative_service.get_comprehensive_progress(test_user_id)
                end_time = time.time()
                
                progress_time = (end_time - start_time) * 1000
                performance_results['progress_calculation_times'].append(progress_time)
            
            # Calculate averages
            if performance_results['fragment_retrieval_times']:
                performance_results['average_retrieval_time'] = sum(performance_results['fragment_retrieval_times']) / len(performance_results['fragment_retrieval_times'])
            
            if performance_results['progress_calculation_times']:
                performance_results['average_progress_time'] = sum(performance_results['progress_calculation_times']) / len(performance_results['progress_calculation_times'])
            
            # Check if meets 500ms requirement
            max_time = max(
                performance_results['average_retrieval_time'],
                performance_results['average_progress_time']
            )
            
            performance_results['meets_500ms_requirement'] = max_time < 500.0
            performance_results['max_operation_time'] = max_time
            
            print(f"⚡ Performance Test Results:")
            print(f"  Fragment retrieval: {performance_results['average_retrieval_time']:.2f}ms")
            print(f"  Progress calculation: {performance_results['average_progress_time']:.2f}ms")
            print(f"  Meets <500ms requirement: {performance_results['meets_500ms_requirement']}")
            
            return performance_results
            
        except Exception as e:
            logger.error(f"Error testing performance: {e}")
            return {'error': str(e)}
    
    async def _create_sample_user_states(self, session: AsyncSession) -> dict:
        """Create sample user states for testing purposes."""
        try:
            from database.narrative_unified import UserNarrativeState, UserMissionProgress, UserArchetype
            
            sample_results = {
                'users_created': 0,
                'test_user_ids': [],
                'errors': []
            }
            
            # Create 3 sample users at different progression levels
            sample_users = [
                {'user_id': 99991, 'level': 1, 'tier': 'los_kinkys', 'fragments_completed': []},
                {'user_id': 99992, 'level': 2, 'tier': 'observadores', 'fragments_completed': ['diana_l1_f1_umbral', 'diana_l1_f2_primera_fractura']},
                {'user_id': 99993, 'level': 3, 'tier': 'comprensores', 'fragments_completed': ['diana_l1_f1_umbral', 'diana_l1_f2_primera_fractura', 'diana_l1_f3_mochila_viajero', 'diana_l2_f1_regreso']}
            ]
            
            for user_data in sample_users:
                try:
                    user_id = user_data['user_id']
                    
                    # Create user narrative state
                    user_state = UserNarrativeState(
                        user_id=user_id,
                        current_fragment_id='diana_l1_f1_umbral',
                        visited_fragments=user_data['fragments_completed'],
                        completed_fragments=user_data['fragments_completed'],
                        unlocked_clues=[],
                        current_level=user_data['level'],
                        current_tier=user_data['tier']
                    )
                    session.add(user_state)
                    
                    # Create mission progress
                    mission_progress = UserMissionProgress(
                        user_id=user_id,
                        current_level=user_data['level'],
                        current_tier=user_data['tier']
                    )
                    session.add(mission_progress)
                    
                    # Create basic archetype
                    archetype = UserArchetype(
                        user_id=user_id,
                        explorer_score=10,
                        direct_score=5,
                        romantic_score=0,
                        analytical_score=0,
                        persistent_score=0,
                        patient_score=0,
                        dominant_archetype='explorer'
                    )
                    session.add(archetype)
                    
                    sample_results['users_created'] += 1
                    sample_results['test_user_ids'].append(user_id)
                    
                    print(f"  ✅ Sample user {user_id} created (Level {user_data['level']})")
                    
                except Exception as e:
                    error_msg = f"Error creating sample user {user_data['user_id']}: {e}"
                    sample_results['errors'].append(error_msg)
                    print(f"  ❌ {error_msg}")
            
            return sample_results
            
        except Exception as e:
            logger.error(f"Error creating sample users: {e}")
            return {'error': str(e)}
    
    def _print_migration_summary(self, results: dict):
        """Print comprehensive migration summary."""
        print("\n" + "="*60)
        print("📋 MVP NARRATIVE FRAGMENTS MIGRATION SUMMARY")
        print("="*60)
        
        print(f"🕐 Started: {results['started_at']}")
        print(f"🕐 Completed: {results.get('completed_at', 'Not completed')}")
        print(f"✅ Success: {results['success']}")
        
        # Database checks
        if 'database_checks' in results and results['database_checks']:
            db_checks = results['database_checks']
            print(f"\n📊 Database Structure: {'✅ Valid' if db_checks.get('tables_exist') else '❌ Issues'}")
        
        # Fragment initialization
        if 'fragment_initialization' in results:
            frag_init = results['fragment_initialization']
            print(f"\n📚 Fragment Initialization:")
            print(f"  Processed: {frag_init.get('fragments_processed', 0)}")
            print(f"  Created: {frag_init.get('fragments_created', 0)}")
            print(f"  Updated: {frag_init.get('fragments_updated', 0)}")
        
        # Validation results
        if 'validation_results' in results:
            validation = results['validation_results']
            print(f"\n🎭 Character Validation:")
            print(f"  Total fragments: {validation.get('total_fragments', 0)}")
            print(f"  Passing (≥90%): {validation.get('passing_validations', 0)}")
            print(f"  Failing (<90%): {validation.get('failing_validations', 0)}")
            print(f"  Average score: {validation.get('average_score', 0):.1f}%")
        
        # Performance metrics
        if 'performance_metrics' in results:
            perf = results['performance_metrics']
            print(f"\n⚡ Performance Testing:")
            print(f"  Fragment retrieval: {perf.get('average_retrieval_time', 0):.2f}ms")
            print(f"  Progress calculation: {perf.get('average_progress_time', 0):.2f}ms")
            print(f"  Meets <500ms requirement: {perf.get('meets_500ms_requirement', False)}")
        
        # Sample users
        if 'sample_users' in results:
            samples = results['sample_users']
            print(f"\n👤 Sample Users Created: {samples.get('users_created', 0)}")
        
        # Errors
        if results.get('errors'):
            print(f"\n❌ Errors ({len(results['errors'])}):")
            for error in results['errors'][:5]:  # Show first 5 errors
                print(f"  • {error}")
        
        print("\n" + "="*60)

# CLI execution
async def main():
    """Main execution function."""
    # Get database URL from environment or default
    database_url = os.getenv(
        'DATABASE_URL',
        'postgresql+asyncpg://username:password@localhost/diana_bot'
    )
    
    # Note: In production, this should use actual database configuration
    print(f"🔗 Using database URL: {database_url[:50]}...")
    
    migration = MVPNarrativeFragmentMigration(database_url)
    results = await migration.run_migration()
    
    if results['success']:
        print("\n🎉 MVP Narrative Fragments Migration completed successfully!")
        return 0
    else:
        print("\n💥 MVP Narrative Fragments Migration failed!")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)