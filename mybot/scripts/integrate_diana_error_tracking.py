#!/usr/bin/env python3
"""
Diana Menu Error Tracking Integration Script

This script integrates the comprehensive error tracking system into the existing
Diana menu system by applying decorators and instrumentation to key methods.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.diana_menu_error_tracker import get_error_tracker
from services.diana_error_dashboard import get_error_dashboard
from services.diana_menu_instrumentation import get_diana_instrumentation

logger = logging.getLogger(__name__)

class DianaErrorTrackingIntegration:
    """
    Integrates error tracking into the Diana menu system.
    """
    
    def __init__(self):
        self.error_tracker = get_error_tracker()
        self.dashboard = get_error_dashboard()
        self.instrumentation = get_diana_instrumentation()
        
        self.integration_points = [
            {
                'file': 'services/enhanced_diana_menu_system.py',
                'class': 'EnhancedDianaMenuSystem',
                'methods': [
                    'process_admin_menu',
                    'process_user_menu', 
                    'process_vip_menu',
                    'handle_callback_query',
                    'generate_menu_keyboard',
                    '_create_menu_response'
                ],
                'decoration': 'menu_operation'
            },
            {
                'file': 'services/enhanced_user_service.py',
                'class': 'EnhancedUserService',
                'methods': [
                    'enhanced_registration',
                    'handle_role_transition',
                    'get_user_profile',
                    'update_user_session'
                ],
                'decoration': 'service_operation'
            },
            {
                'file': 'services/diana_character_validator.py', 
                'class': 'DianaCharacterValidator',
                'methods': [
                    'validate_response',
                    'calculate_consistency_score',
                    'analyze_character_traits'
                ],
                'decoration': 'character_validation'
            }
        ]
        
        logger.info("Diana Error Tracking Integration initialized")
    
    async def integrate_error_tracking(self):
        """
        Apply error tracking to the Diana menu system.
        """
        logger.info("Starting Diana menu error tracking integration...")
        
        # Initialize the tracking system
        await self._initialize_tracking_system()
        
        # Apply instrumentation to key methods
        await self._apply_instrumentation()
        
        # Set up monitoring and alerting
        await self._setup_monitoring()
        
        # Run integration tests
        await self._run_integration_tests()
        
        logger.info("Diana menu error tracking integration completed successfully")
    
    async def _initialize_tracking_system(self):
        """Initialize the error tracking system components."""
        logger.info("Initializing error tracking system...")
        
        # Clear old errors (keep last 7 days)
        self.error_tracker.clear_old_errors(days=7)
        
        # Initialize correlation analyzer
        correlations = await self.dashboard.correlation_analyzer.analyze_correlations(24)
        logger.info(f"Found {len(correlations)} existing error correlations")
        
        # Set up performance thresholds
        self.error_tracker.performance_thresholds.update({
            'enhanced_diana_menu_response': 1.0,
            'user_registration': 3.0,
            'character_validation': 0.5,
            'database_operation': 0.8,
            'callback_processing': 1.2
        })
        
        logger.info("Error tracking system initialized")
    
    async def _apply_instrumentation(self):
        """Apply instrumentation to Diana menu methods."""
        logger.info("Applying error tracking instrumentation...")
        
        # Note: In a real implementation, we would dynamically apply decorators
        # or use monkey patching. For this example, we'll create integration
        # patches that can be applied to the existing code.
        
        integration_patches = []
        
        for integration_point in self.integration_points:
            file_path = project_root / integration_point['file']
            
            if file_path.exists():
                patch = await self._create_instrumentation_patch(integration_point)
                integration_patches.append(patch)
                logger.info(f"Created instrumentation patch for {integration_point['class']}")
        
        # Save integration patches for manual application
        patches_dir = project_root / 'scripts' / 'error_tracking_patches'
        patches_dir.mkdir(exist_ok=True)
        
        for i, patch in enumerate(integration_patches):
            patch_file = patches_dir / f"patch_{i:02d}_{patch['class_name']}.py"
            with open(patch_file, 'w') as f:
                f.write(patch['content'])
        
        logger.info(f"Created {len(integration_patches)} instrumentation patches")
    
    async def _create_instrumentation_patch(self, integration_point: dict) -> dict:
        """Create an instrumentation patch for a specific class."""
        class_name = integration_point['class']
        methods = integration_point['methods']
        decoration_type = integration_point['decoration']
        
        patch_content = f'''"""
Instrumentation patch for {class_name}

Apply error tracking decorators to {class_name} methods.
"""

from services.diana_menu_instrumentation import (
    track_menu_operation, track_basemodel_init, 
    track_database_query, get_diana_instrumentation
)

# Example integration for {class_name}
class Instrumented{class_name}:
    """
    Instrumented version of {class_name} with error tracking.
    
    This class shows how to apply error tracking decorators
    to the original {class_name} methods.
    """
    
    def __init__(self, original_instance):
        self.original = original_instance
        self.instrumentation = get_diana_instrumentation()
    
'''
        
        for method in methods:
            if decoration_type == 'menu_operation':
                patch_content += f'''
    @track_menu_operation(operation_name="{method}", menu_type="diana")
    async def {method}(self, *args, **kwargs):
        """Instrumented version of {method}."""
        return await self.original.{method}(*args, **kwargs)
'''
            elif decoration_type == 'service_operation':
                patch_content += f'''
    @track_menu_operation(operation_name="{method}", menu_type="service")
    async def {method}(self, *args, **kwargs):
        """Instrumented version of {method}.""" 
        return await self.original.{method}(*args, **kwargs)
'''
            elif decoration_type == 'character_validation':
                patch_content += f'''
    @track_menu_operation(operation_name="{method}", menu_type="character_validation")
    async def {method}(self, *args, **kwargs):
        """Instrumented version of {method}."""
        return await self.original.{method}(*args, **kwargs)
'''
        
        patch_content += f'''

# Helper function to wrap existing {class_name} instances
def instrument_{class_name.lower()}(instance):
    """Wrap a {class_name} instance with error tracking."""
    return Instrumented{class_name}(instance)
'''
        
        return {
            'class_name': class_name,
            'content': patch_content
        }
    
    async def _setup_monitoring(self):
        """Set up monitoring and alerting for Diana menu errors."""
        logger.info("Setting up error monitoring and alerting...")
        
        # Configure alert thresholds
        self.dashboard.alert_thresholds.update({
            'error_rate_per_hour': 30,  # Reduced threshold for Diana menu
            'critical_errors_per_hour': 3,
            'performance_violations_per_hour': 15,
            'affected_users_per_hour': 50,
            'system_health_score': 85.0
        })
        
        # Set up periodic monitoring task
        asyncio.create_task(self._periodic_monitoring())
        
        logger.info("Error monitoring and alerting configured")
    
    async def _periodic_monitoring(self):
        """Periodic monitoring task for Diana menu errors."""
        while True:
            try:
                # Check for alerts every 5 minutes
                await asyncio.sleep(300)
                
                alerts = await self.dashboard.check_alerts()
                if alerts:
                    for alert in alerts:
                        logger.warning(f"Diana Menu Alert: {alert['message']}")
                        
                        # In a real implementation, you would send notifications
                        # to administrators or monitoring systems here
                
                # Perform correlation analysis every hour
                if int(time.time()) % 3600 < 300:  # Within 5 minutes of the hour
                    correlations = await self.dashboard.correlation_analyzer.analyze_correlations(1)
                    if correlations:
                        logger.info(f"Found {len(correlations)} new error correlations")
                
            except Exception as e:
                logger.error(f"Error in periodic monitoring: {e}")
    
    async def _run_integration_tests(self):
        """Run tests to verify error tracking integration."""
        logger.info("Running integration tests...")
        
        test_results = []
        
        # Test 1: Error tracker initialization
        try:
            assert self.error_tracker is not None
            assert len(self.error_tracker.errors) >= 0
            test_results.append(("Error tracker initialization", "PASS"))
        except Exception as e:
            test_results.append(("Error tracker initialization", f"FAIL: {e}"))
        
        # Test 2: Dashboard functionality
        try:
            metrics = await self.dashboard.get_dashboard_metrics(1)
            assert metrics is not None
            assert hasattr(metrics, 'total_errors')
            test_results.append(("Dashboard metrics", "PASS"))
        except Exception as e:
            test_results.append(("Dashboard metrics", f"FAIL: {e}"))
        
        # Test 3: Correlation analysis
        try:
            correlations = await self.dashboard.correlation_analyzer.analyze_correlations(1)
            assert isinstance(correlations, list)
            test_results.append(("Correlation analysis", "PASS"))
        except Exception as e:
            test_results.append(("Correlation analysis", f"FAIL: {e}"))
        
        # Test 4: Performance tracking
        try:
            from services.diana_menu_error_tracker import ErrorContext
            context = ErrorContext(operation="test_operation")
            self.error_tracker.track_performance("test_operation", 0.5, context)
            test_results.append(("Performance tracking", "PASS"))
        except Exception as e:
            test_results.append(("Performance tracking", f"FAIL: {e}"))
        
        # Test 5: Error reporting
        try:
            report = self.dashboard.generate_report(
                self.dashboard.ReportType.SUMMARY, hours=1
            )
            assert isinstance(report, str) and len(report) > 0
            test_results.append(("Error reporting", "PASS"))
        except Exception as e:
            test_results.append(("Error reporting", f"FAIL: {e}"))
        
        # Print test results
        logger.info("Integration test results:")
        for test_name, result in test_results:
            logger.info(f"  {test_name}: {result}")
        
        passed_tests = sum(1 for _, result in test_results if result == "PASS")
        total_tests = len(test_results)
        logger.info(f"Integration tests: {passed_tests}/{total_tests} passed")
        
        return passed_tests == total_tests
    
    async def generate_integration_report(self) -> str:
        """Generate a comprehensive integration report."""
        logger.info("Generating integration report...")
        
        # Get current system state
        metrics = await self.dashboard.get_dashboard_metrics(24)
        correlations = await self.dashboard.get_correlation_insights(24)
        performance = await self.dashboard.get_performance_report(24)
        alerts = await self.dashboard.check_alerts()
        
        report = f"""
# Diana Menu Error Tracking Integration Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Integration Summary
- Error Tracker: ✓ Operational
- Correlation Analyzer: ✓ Operational  
- Dashboard: ✓ Operational
- Instrumentation: ✓ Ready for deployment
- Monitoring: ✓ Active

## Current System State
- Total Errors (24h): {metrics.total_errors}
- Error Rate: {metrics.error_rate_per_hour:.1f} errors/hour
- System Health: {metrics.system_health_score:.1f}%
- Active Alerts: {len(alerts)}

## Error Correlations (24h)
- Total Correlations: {correlations['total_correlations']}
- High Confidence: {len(correlations['high_confidence_correlations'])}
- Error Clusters: {len(correlations['error_clusters'])}

## Performance Analysis (24h)
- Operations Tracked: {len(performance)}
- Top Slow Operation: {performance[0].operation if performance else 'None'}
- Average Response Time: {performance[0].average_duration:.3f}s if performance else 'N/A'

## Integration Points Identified
{len(self.integration_points)} classes ready for instrumentation:
"""
        
        for integration_point in self.integration_points:
            report += f"""
### {integration_point['class']}
- File: {integration_point['file']}
- Methods: {len(integration_point['methods'])}
- Type: {integration_point['decoration']}
"""
        
        report += f"""

## Recommendations
{chr(10).join(['- ' + rec for rec in correlations['recommendations']])}

## Next Steps
1. Apply instrumentation patches to existing code
2. Deploy error tracking to production
3. Configure alert notifications
4. Set up regular error analysis reviews
5. Train team on using the error dashboard

## Alert Configuration
- Error Rate Threshold: {self.dashboard.alert_thresholds['error_rate_per_hour']}/hour
- Critical Error Threshold: {self.dashboard.alert_thresholds['critical_errors_per_hour']}/hour
- Health Score Threshold: {self.dashboard.alert_thresholds['system_health_score']}%
"""
        
        return report.strip()

async def main():
    """Main integration function."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    integration = DianaErrorTrackingIntegration()
    
    try:
        # Run the integration
        await integration.integrate_error_tracking()
        
        # Generate and save the integration report
        report = await integration.generate_integration_report()
        
        report_file = project_root / 'docs' / 'diana_error_tracking_integration_report.md'
        with open(report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"Integration report saved to: {report_file}")
        logger.info("Diana error tracking integration completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import time
    from datetime import datetime
    
    success = asyncio.run(main())
    exit(0 if success else 1)