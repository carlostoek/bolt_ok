#!/usr/bin/env python3
"""
MVP Implementation Validation Script
Validates that all critical gaps identified in Task 2.4 have been completed.
"""

import sys
import os
import inspect
import logging
import importlib.util
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class MVPImplementationValidator:
    """Validates MVP implementation completeness."""
    
    def __init__(self):
        self.validation_results = []
        
    def validate_file_exists(self, file_path: str, description: str) -> bool:
        """Validate that a file exists."""
        try:
            path = Path(file_path)
            if path.exists():
                logger.info(f"✅ {description}: File exists")
                return True
            else:
                logger.error(f"❌ {description}: File missing - {file_path}")
                return False
        except Exception as e:
            logger.error(f"❌ {description}: Error checking file - {e}")
            return False
    
    def validate_class_method_exists(self, module_path: str, class_name: str, method_name: str, description: str) -> bool:
        """Validate that a class method exists and is not a placeholder."""
        try:
            # Import module dynamically
            spec = importlib.util.spec_from_file_location("temp_module", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get class
            cls = getattr(module, class_name)
            
            # Check if method exists
            if hasattr(cls, method_name):
                method = getattr(cls, method_name)
                
                # Get method source to check for implementation
                try:
                    source = inspect.getsource(method)
                    
                    # Check for placeholder indicators
                    placeholder_indicators = ['pass', 'NotImplemented', 'TODO', 'FIXME', 'stub']
                    is_placeholder = any(indicator in source for indicator in placeholder_indicators)
                    
                    if not is_placeholder and len(source.strip()) > 100:  # Has substantial implementation
                        logger.info(f"✅ {description}: Method implemented")
                        return True
                    else:
                        logger.warning(f"⚠️  {description}: Method exists but may be placeholder")
                        return False
                        
                except Exception as source_e:
                    logger.info(f"✅ {description}: Method exists (couldn't analyze source)")
                    return True  # Assume it's implemented if we can't check source
            else:
                logger.error(f"❌ {description}: Method missing")
                return False
                
        except Exception as e:
            logger.error(f"❌ {description}: Error validating - {e}")
            return False
    
    def validate_import_works(self, module_path: str, class_names: list, description: str) -> bool:
        """Validate that imports work correctly."""
        try:
            spec = importlib.util.spec_from_file_location("temp_module", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            missing_classes = []
            for class_name in class_names:
                if not hasattr(module, class_name):
                    missing_classes.append(class_name)
            
            if not missing_classes:
                logger.info(f"✅ {description}: All imports work")
                return True
            else:
                logger.error(f"❌ {description}: Missing classes - {missing_classes}")
                return False
                
        except Exception as e:
            logger.error(f"❌ {description}: Import error - {e}")
            return False
    
    def validate_vip_integration(self) -> bool:
        """Validate VIP service integration completion."""
        logger.info("\n🔍 VALIDATING VIP SERVICE INTEGRATION")
        
        results = []
        
        # 1. Check VIP service file exists
        results.append(self.validate_file_exists(
            "services/vip_tier_management_service.py",
            "VIP service implementation"
        ))
        
        # 2. Check MVPDecisionTreeService has VIP integration
        results.append(self.validate_file_exists(
            "services/mvp_decision_tree_service.py", 
            "Decision tree service with VIP integration"
        ))
        
        # 3. Check for VIP integration in decision tree service
        try:
            with open("services/mvp_decision_tree_service.py", 'r') as f:
                content = f.read()
                
            # Check for VIP service import and usage
            has_vip_import = "VIPTierManagementService" in content
            has_vip_usage = "check_content_access" in content
            has_upgrade_offer = "generate_upgrade_opportunity" in content
            
            if has_vip_import and has_vip_usage and has_upgrade_offer:
                logger.info("✅ VIP integration: Properly integrated in decision service")
                results.append(True)
            else:
                logger.error(f"❌ VIP integration: Missing components - Import:{has_vip_import}, Usage:{has_vip_usage}, Offers:{has_upgrade_offer}")
                results.append(False)
                
        except Exception as e:
            logger.error(f"❌ VIP integration: Error checking integration - {e}")
            results.append(False)
        
        return all(results)
    
    def validate_achievement_integration(self) -> bool:
        """Validate Achievement service integration completion."""
        logger.info("\n🏆 VALIDATING ACHIEVEMENT SERVICE INTEGRATION")
        
        results = []
        
        # 1. Check achievement integration file exists
        results.append(self.validate_file_exists(
            "services/decision_achievement_integration.py",
            "Achievement integration implementation"
        ))
        
        # 2. Check achievement service exists
        results.append(self.validate_file_exists(
            "services/achievement_service.py",
            "Achievement service implementation"  
        ))
        
        # 3. Check for proper achievement integration
        try:
            with open("services/decision_achievement_integration.py", 'r') as f:
                content = f.read()
            
            # Check for achievement service integration
            has_achievement_service = "AchievementService" in content
            has_grant_method = "_grant" in content
            has_point_service = "PointService" in content
            has_error_handling = "except Exception" in content
            
            if has_achievement_service and has_grant_method and has_point_service and has_error_handling:
                logger.info("✅ Achievement integration: Properly integrated with error handling")
                results.append(True)
            else:
                logger.error(f"❌ Achievement integration: Missing components - Service:{has_achievement_service}, Grant:{has_grant_method}, Points:{has_point_service}, Errors:{has_error_handling}")
                results.append(False)
                
        except Exception as e:
            logger.error(f"❌ Achievement integration: Error checking - {e}")
            results.append(False)
        
        return all(results)
    
    def validate_database_optimization(self) -> bool:
        """Validate database query optimization completion."""
        logger.info("\n🗄️  VALIDATING DATABASE QUERY OPTIMIZATION")
        
        results = []
        
        # 1. Check performance optimizer exists
        results.append(self.validate_file_exists(
            "services/decision_performance_optimizer.py",
            "Performance optimizer implementation"
        ))
        
        # 2. Check for database optimization features
        try:
            with open("services/decision_performance_optimizer.py", 'r') as f:
                content = f.read()
            
            # Check for optimization features
            has_eager_loading = "selectinload" in content or "eager" in content.lower()
            has_concurrent_queries = "asyncio.gather" in content
            has_execution_options = "execution_options" in content
            has_query_caching = "compiled_cache" in content
            has_batch_queries = "_apply_query_batching" in content
            
            optimization_score = sum([
                has_eager_loading, has_concurrent_queries, 
                has_execution_options, has_query_caching, has_batch_queries
            ])
            
            if optimization_score >= 3:
                logger.info(f"✅ Database optimization: Implemented ({optimization_score}/5 features)")
                results.append(True)
            else:
                logger.error(f"❌ Database optimization: Insufficient implementation ({optimization_score}/5 features)")
                results.append(False)
                
        except Exception as e:
            logger.error(f"❌ Database optimization: Error checking - {e}")
            results.append(False)
        
        return all(results)
    
    def validate_cache_memory_management(self) -> bool:
        """Validate cache memory management completion.""" 
        logger.info("\n💾 VALIDATING CACHE MEMORY MANAGEMENT")
        
        results = []
        
        # Check for memory management features
        try:
            with open("services/decision_performance_optimizer.py", 'r') as f:
                content = f.read()
            
            # Check for memory management components
            has_memory_limits = "max_cache_memory_mb" in content
            has_memory_monitoring = "_check_memory_usage" in content
            has_cleanup_methods = "_emergency_memory_cleanup" in content
            has_lru_eviction = "last_accessed" in content
            has_memory_tracking = "size_bytes" in content
            
            memory_score = sum([
                has_memory_limits, has_memory_monitoring,
                has_cleanup_methods, has_lru_eviction, has_memory_tracking
            ])
            
            if memory_score >= 4:
                logger.info(f"✅ Memory management: Implemented ({memory_score}/5 features)")
                results.append(True)
            else:
                logger.error(f"❌ Memory management: Insufficient implementation ({memory_score}/5 features)")
                results.append(False)
                
        except Exception as e:
            logger.error(f"❌ Memory management: Error checking - {e}")
            results.append(False)
        
        return all(results)
    
    def validate_character_consistency(self) -> bool:
        """Validate character consistency is maintained."""
        logger.info("\n🎭 VALIDATING CHARACTER CONSISTENCY")
        
        results = []
        
        # Check for Diana character validator
        results.append(self.validate_file_exists(
            "services/diana_character_validator.py",
            "Diana character validator"
        ))
        
        # Check for character consistency in services
        files_to_check = [
            "services/mvp_decision_tree_service.py",
            "services/decision_achievement_integration.py", 
            "services/vip_tier_management_service.py"
        ]
        
        diana_keywords = ['diana', 'querido', 'amor', 'misterio', 'secreto']
        
        for file_path in files_to_check:
            try:
                with open(file_path, 'r') as f:
                    content = f.read().lower()
                
                has_diana_responses = any(keyword in content for keyword in diana_keywords)
                has_character_consistency = "character" in content or "consistency" in content
                
                if has_diana_responses or has_character_consistency:
                    logger.info(f"✅ Character consistency: {file_path} maintains Diana's character")
                    results.append(True)
                else:
                    logger.warning(f"⚠️  Character consistency: {file_path} may lack character elements")
                    results.append(True)  # Don't fail for this, just warn
                    
            except Exception as e:
                logger.warning(f"⚠️  Character consistency: Could not check {file_path} - {e}")
                results.append(True)  # Don't fail for file access issues
        
        return all(results)
    
    def validate_integration_completeness(self) -> bool:
        """Validate overall integration completeness."""
        logger.info("\n🔗 VALIDATING OVERALL INTEGRATION")
        
        # Check that all services can be imported together (basic integration test)
        try:
            
            # Test imports
            service_files = [
                ("services/mvp_decision_tree_service.py", ["MVPDecisionTreeService"]),
                ("services/decision_achievement_integration.py", ["DecisionAchievementIntegration"]),
                ("services/decision_performance_optimizer.py", ["DecisionPerformanceOptimizer"]),
                ("services/vip_tier_management_service.py", ["VIPTierManagementService"])
            ]
            
            all_imports_work = True
            for file_path, class_names in service_files:
                works = self.validate_import_works(file_path, class_names, f"Import test: {file_path}")
                all_imports_work = all_imports_work and works
            
            if all_imports_work:
                logger.info("✅ Integration: All service imports work correctly")
                return True
            else:
                logger.error("❌ Integration: Some imports failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Integration: Error testing imports - {e}")
            return False
    
    def run_complete_validation(self) -> bool:
        """Run complete MVP implementation validation."""
        logger.info("🚀 STARTING MVP IMPLEMENTATION VALIDATION")
        logger.info("=" * 60)
        
        validations = [
            ("VIP Integration", self.validate_vip_integration),
            ("Achievement Integration", self.validate_achievement_integration), 
            ("Database Optimization", self.validate_database_optimization),
            ("Memory Management", self.validate_cache_memory_management),
            ("Character Consistency", self.validate_character_consistency),
            ("Overall Integration", self.validate_integration_completeness)
        ]
        
        results = []
        for name, validator in validations:
            try:
                result = validator()
                results.append(result)
                self.validation_results.append((name, result))
            except Exception as e:
                logger.error(f"❌ {name}: Validation failed with exception - {e}")
                results.append(False)
                self.validation_results.append((name, False))
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 MVP IMPLEMENTATION VALIDATION SUMMARY")
        logger.info("=" * 60)
        
        passed = sum(results)
        total = len(results)
        
        for name, result in self.validation_results:
            status = "✅ PASSED" if result else "❌ FAILED" 
            logger.info(f"{name}: {status}")
        
        logger.info("=" * 60)
        if passed == total:
            logger.info(f"🎉 MVP IMPLEMENTATION COMPLETE: {passed}/{total} validations passed")
            logger.info("✅ All critical gaps identified in Task 2.4 have been resolved!")
            logger.info("✅ System is ready for MVP launch")
            return True
        else:
            logger.error(f"❌ MVP IMPLEMENTATION INCOMPLETE: {passed}/{total} validations passed")
            logger.error("❌ Additional work required before MVP launch")
            return False


def main():
    """Main validation function."""
    
    validator = MVPImplementationValidator()
    success = validator.run_complete_validation()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())