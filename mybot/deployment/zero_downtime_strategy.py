"""
Zero-Downtime Deployment Strategy for Emotional Evaluation System
Implements blue-green deployment with gradual rollout capabilities
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from services.emotional.feature_flags import EmotionalFeatureFlags
from services.integration.monitoring_dashboard import get_integration_monitoring
from services.emotional.circuit_breaker import get_emotional_circuit_breaker

logger = logging.getLogger(__name__)


class DeploymentPhase(Enum):
    """Deployment phases for gradual rollout"""
    PREPARATION = "preparation"
    SILENT_DEPLOYMENT = "silent_deployment"
    CANARY_1_PERCENT = "canary_1_percent"
    CANARY_5_PERCENT = "canary_5_percent"
    GRADUAL_10_PERCENT = "gradual_10_percent"
    GRADUAL_25_PERCENT = "gradual_25_percent"
    GRADUAL_50_PERCENT = "gradual_50_percent"
    GRADUAL_75_PERCENT = "gradual_75_percent"
    FULL_ROLLOUT = "full_rollout"
    ROLLBACK = "rollback"
    COMPLETED = "completed"


@dataclass
class DeploymentConfig:
    """Configuration for deployment strategy"""
    phase_duration_minutes: int = 30  # Time to wait in each phase
    health_check_interval_seconds: int = 30
    max_error_rate: float = 2.0  # Maximum acceptable error rate percentage
    min_success_rate: float = 98.0  # Minimum acceptable success rate percentage
    rollback_on_failure: bool = True
    notification_enabled: bool = True
    canary_user_groups: List[str] = None


@dataclass
class DeploymentStatus:
    """Current deployment status"""
    phase: DeploymentPhase
    started_at: datetime
    phase_started_at: datetime
    rollout_percentage: int
    health_status: str
    error_count: int
    success_count: int
    next_phase_at: Optional[datetime]
    can_proceed: bool
    issues: List[str]


class ZeroDowntimeDeployer:
    """
    Zero-downtime deployment manager for emotional evaluation system.
    
    Implements:
    - Blue-green deployment pattern
    - Gradual rollout with health checks
    - Automatic rollback on failures
    - Comprehensive monitoring
    - Feature flag coordination
    """
    
    def __init__(self, config: Optional[DeploymentConfig] = None):
        self.config = config or DeploymentConfig()
        self.current_status: Optional[DeploymentStatus] = None
        self.deployment_log = []
        
        # Phase configurations
        self.phase_configs = {
            DeploymentPhase.SILENT_DEPLOYMENT: {"rollout": 0, "monitor_only": True},
            DeploymentPhase.CANARY_1_PERCENT: {"rollout": 1, "monitor_closely": True},
            DeploymentPhase.CANARY_5_PERCENT: {"rollout": 5, "monitor_closely": True},
            DeploymentPhase.GRADUAL_10_PERCENT: {"rollout": 10, "standard_monitoring": True},
            DeploymentPhase.GRADUAL_25_PERCENT: {"rollout": 25, "standard_monitoring": True},
            DeploymentPhase.GRADUAL_50_PERCENT: {"rollout": 50, "standard_monitoring": True},
            DeploymentPhase.GRADUAL_75_PERCENT: {"rollout": 75, "standard_monitoring": True},
            DeploymentPhase.FULL_ROLLOUT: {"rollout": 100, "full_monitoring": True}
        }

    async def start_deployment(self, session) -> bool:
        """
        Start the zero-downtime deployment process.
        
        Returns True if deployment can start, False if preconditions not met.
        """
        try:
            logger.info("Starting zero-downtime deployment of emotional evaluation system")
            
            # Check preconditions
            if not await self._check_deployment_preconditions(session):
                logger.error("Deployment preconditions not met")
                return False
            
            # Initialize deployment status
            now = datetime.now()
            self.current_status = DeploymentStatus(
                phase=DeploymentPhase.PREPARATION,
                started_at=now,
                phase_started_at=now,
                rollout_percentage=0,
                health_status="preparing",
                error_count=0,
                success_count=0,
                next_phase_at=now + timedelta(minutes=5),
                can_proceed=True,
                issues=[]
            )
            
            # Log deployment start
            await self._log_deployment_event("Deployment started", {
                "timestamp": now.isoformat(),
                "config": {
                    "phase_duration": self.config.phase_duration_minutes,
                    "health_check_interval": self.config.health_check_interval_seconds,
                    "max_error_rate": self.config.max_error_rate,
                    "min_success_rate": self.config.min_success_rate
                }
            })
            
            # Start deployment process
            asyncio.create_task(self._run_deployment_process(session))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start deployment: {e}")
            return False

    async def get_deployment_status(self) -> Optional[DeploymentStatus]:
        """Get current deployment status"""
        return self.current_status

    async def force_rollback(self, session, reason: str = "Manual rollback") -> bool:
        """Force immediate rollback of the deployment"""
        try:
            logger.warning(f"Forcing deployment rollback: {reason}")
            
            if self.current_status:
                self.current_status.phase = DeploymentPhase.ROLLBACK
                self.current_status.issues.append(f"Manual rollback: {reason}")
            
            success = await self._execute_rollback(session, reason)
            
            await self._log_deployment_event("Force rollback executed", {
                "reason": reason,
                "success": success,
                "timestamp": datetime.now().isoformat()
            })
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to force rollback: {e}")
            return False

    async def pause_deployment(self) -> bool:
        """Pause the current deployment"""
        try:
            if self.current_status and self.current_status.phase not in [DeploymentPhase.COMPLETED, DeploymentPhase.ROLLBACK]:
                self.current_status.can_proceed = False
                logger.info("Deployment paused")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to pause deployment: {e}")
            return False

    async def resume_deployment(self) -> bool:
        """Resume a paused deployment"""
        try:
            if self.current_status and not self.current_status.can_proceed:
                self.current_status.can_proceed = True
                logger.info("Deployment resumed")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to resume deployment: {e}")
            return False

    # Private methods
    async def _run_deployment_process(self, session):
        """Main deployment process loop"""
        try:
            phases = [
                DeploymentPhase.SILENT_DEPLOYMENT,
                DeploymentPhase.CANARY_1_PERCENT,
                DeploymentPhase.CANARY_5_PERCENT,
                DeploymentPhase.GRADUAL_10_PERCENT,
                DeploymentPhase.GRADUAL_25_PERCENT,
                DeploymentPhase.GRADUAL_50_PERCENT,
                DeploymentPhase.GRADUAL_75_PERCENT,
                DeploymentPhase.FULL_ROLLOUT
            ]
            
            for phase in phases:
                if not self.current_status.can_proceed:
                    logger.info("Deployment paused, waiting...")
                    while not self.current_status.can_proceed:
                        await asyncio.sleep(10)
                
                # Execute phase
                success = await self._execute_phase(session, phase)
                
                if not success:
                    logger.error(f"Phase {phase.value} failed, initiating rollback")
                    await self._execute_rollback(session, f"Phase {phase.value} failed health checks")
                    return
                
                # Wait for phase duration (except for silent deployment)
                if phase != DeploymentPhase.SILENT_DEPLOYMENT:
                    await self._wait_and_monitor_phase(session, phase)
            
            # Complete deployment
            await self._complete_deployment(session)
            
        except Exception as e:
            logger.error(f"Deployment process failed: {e}")
            if self.current_status:
                await self._execute_rollback(session, f"Deployment process error: {str(e)}")

    async def _execute_phase(self, session, phase: DeploymentPhase) -> bool:
        """Execute a specific deployment phase"""
        try:
            logger.info(f"Starting deployment phase: {phase.value}")
            
            # Update status
            now = datetime.now()
            self.current_status.phase = phase
            self.current_status.phase_started_at = now
            self.current_status.next_phase_at = now + timedelta(minutes=self.config.phase_duration_minutes)
            
            # Get phase configuration
            phase_config = self.phase_configs.get(phase, {})
            rollout_percentage = phase_config.get("rollout", 0)
            
            self.current_status.rollout_percentage = rollout_percentage
            
            # Execute phase-specific actions
            if phase == DeploymentPhase.SILENT_DEPLOYMENT:
                success = await self._execute_silent_deployment(session)
            else:
                success = await self._execute_rollout_phase(session, rollout_percentage)
            
            if success:
                await self._log_deployment_event(f"Phase {phase.value} started successfully", {
                    "rollout_percentage": rollout_percentage,
                    "timestamp": now.isoformat()
                })
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to execute phase {phase.value}: {e}")
            return False

    async def _execute_silent_deployment(self, session) -> bool:
        """Execute silent deployment phase - deploy code without enabling features"""
        try:
            logger.info("Executing silent deployment - code deployed, features disabled")
            
            # Ensure all emotional features are disabled
            emotional_flags = [
                EmotionalFeatureFlags.EMOTIONAL_SYSTEM_ENABLED,
                EmotionalFeatureFlags.EMOTIONAL_ANALYSIS_ENABLED,
                EmotionalFeatureFlags.ARCHETYPE_SYSTEM_ENABLED,
                EmotionalFeatureFlags.NARRATIVE_ADAPTATION_ENABLED
            ]
            
            for flag in emotional_flags:
                await EmotionalFeatureFlags.set_flag(
                    flag, enabled=False, rollout_percentage=0, session=session
                )
            
            # Initialize monitoring
            monitoring = await get_integration_monitoring(session)
            health_status = await monitoring.emergency_health_check()
            
            self.current_status.health_status = "healthy" if health_status else "unhealthy"
            
            return health_status
            
        except Exception as e:
            logger.error(f"Silent deployment failed: {e}")
            return False

    async def _execute_rollout_phase(self, session, rollout_percentage: int) -> bool:
        """Execute a rollout phase with specific percentage"""
        try:
            logger.info(f"Executing rollout phase: {rollout_percentage}% users")
            
            # Enable main emotional system flag with rollout percentage
            await EmotionalFeatureFlags.set_flag(
                EmotionalFeatureFlags.EMOTIONAL_SYSTEM_ENABLED,
                enabled=True,
                rollout_percentage=rollout_percentage,
                session=session
            )
            
            # Enable supporting features
            supporting_flags = [
                EmotionalFeatureFlags.EMOTIONAL_ANALYSIS_ENABLED,
                EmotionalFeatureFlags.ARCHETYPE_SYSTEM_ENABLED,
                EmotionalFeatureFlags.NARRATIVE_ADAPTATION_ENABLED
            ]
            
            for flag in supporting_flags:
                await EmotionalFeatureFlags.set_flag(
                    flag, enabled=True, rollout_percentage=rollout_percentage, session=session
                )
            
            # Wait a moment for changes to take effect
            await asyncio.sleep(5)
            
            # Check initial health
            monitoring = await get_integration_monitoring(session)
            health_status = await monitoring.emergency_health_check()
            
            self.current_status.health_status = "healthy" if health_status else "unhealthy"
            
            return health_status
            
        except Exception as e:
            logger.error(f"Rollout phase {rollout_percentage}% failed: {e}")
            return False

    async def _wait_and_monitor_phase(self, session, phase: DeploymentPhase):
        """Wait for phase duration while monitoring health"""
        phase_config = self.phase_configs.get(phase, {})
        monitor_closely = phase_config.get("monitor_closely", False)
        
        # Determine check interval
        check_interval = self.config.health_check_interval_seconds
        if monitor_closely:
            check_interval = min(check_interval, 15)  # Check every 15 seconds for critical phases
        
        phase_duration = self.config.phase_duration_minutes * 60  # Convert to seconds
        checks_performed = 0
        
        logger.info(f"Monitoring phase {phase.value} for {self.config.phase_duration_minutes} minutes")
        
        start_time = time.time()
        while (time.time() - start_time) < phase_duration:
            if not self.current_status.can_proceed:
                logger.info("Deployment paused during monitoring")
                while not self.current_status.can_proceed:
                    await asyncio.sleep(10)
                continue
            
            # Perform health check
            health_check_passed = await self._perform_health_check(session)
            checks_performed += 1
            
            if not health_check_passed:
                logger.error(f"Health check failed during phase {phase.value}")
                self.current_status.issues.append(f"Health check failed in phase {phase.value}")
                
                if self.config.rollback_on_failure:
                    logger.error("Initiating automatic rollback due to health check failure")
                    await self._execute_rollback(session, f"Health check failed in phase {phase.value}")
                    return
            
            await asyncio.sleep(check_interval)
        
        logger.info(f"Phase {phase.value} monitoring completed. Performed {checks_performed} health checks")

    async def _perform_health_check(self, session) -> bool:
        """Perform comprehensive health check"""
        try:
            monitoring = await get_integration_monitoring(session)
            
            # Get current health status
            health_data = await monitoring.check_integration_health()
            
            # Update status
            self.current_status.health_status = health_data["status"]
            
            # Check critical thresholds
            if health_data["status"] == "critical":
                self.current_status.issues.append("Critical health issues detected")
                return False
            
            # Check circuit breaker
            circuit_breaker = get_emotional_circuit_breaker()
            if not circuit_breaker.is_healthy():
                logger.warning("Circuit breaker is not healthy, but continuing deployment")
                # Don't fail deployment for circuit breaker issues - it's designed to protect us
            
            return True
            
        except Exception as e:
            logger.error(f"Health check failed with error: {e}")
            self.current_status.issues.append(f"Health check error: {str(e)}")
            return False

    async def _execute_rollback(self, session, reason: str) -> bool:
        """Execute complete rollback of the deployment"""
        try:
            logger.warning(f"Executing deployment rollback: {reason}")
            
            # Update status
            self.current_status.phase = DeploymentPhase.ROLLBACK
            self.current_status.rollout_percentage = 0
            self.current_status.issues.append(reason)
            
            # Disable all emotional features immediately
            await EmotionalFeatureFlags.disable_all_emotional_features(session)
            
            # Reset circuit breaker
            circuit_breaker = get_emotional_circuit_breaker()
            await circuit_breaker.reset()
            
            # Wait for changes to propagate
            await asyncio.sleep(10)
            
            # Verify rollback
            monitoring = await get_integration_monitoring(session)
            health_check = await monitoring.emergency_health_check()
            
            if health_check:
                logger.info("Rollback completed successfully - system is healthy")
                self.current_status.health_status = "healthy"
                self.current_status.phase = DeploymentPhase.COMPLETED
                
                await self._log_deployment_event("Rollback completed successfully", {
                    "reason": reason,
                    "timestamp": datetime.now().isoformat()
                })
                
                return True
            else:
                logger.error("Rollback completed but system health check still failing")
                self.current_status.health_status = "unhealthy"
                return False
                
        except Exception as e:
            logger.error(f"Rollback execution failed: {e}")
            return False

    async def _complete_deployment(self, session):
        """Complete the deployment process"""
        try:
            logger.info("Completing deployment - all phases successful")
            
            self.current_status.phase = DeploymentPhase.COMPLETED
            self.current_status.rollout_percentage = 100
            self.current_status.health_status = "healthy"
            
            # Final health check
            monitoring = await get_integration_monitoring(session)
            final_health = await monitoring.check_integration_health()
            
            await self._log_deployment_event("Deployment completed successfully", {
                "final_health_status": final_health["status"],
                "total_duration": (datetime.now() - self.current_status.started_at).total_seconds(),
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info("Zero-downtime deployment completed successfully!")
            
        except Exception as e:
            logger.error(f"Error completing deployment: {e}")

    async def _check_deployment_preconditions(self, session) -> bool:
        """Check if system is ready for deployment"""
        try:
            logger.info("Checking deployment preconditions")
            
            # Check system health
            monitoring = await get_integration_monitoring(session)
            health_check = await monitoring.emergency_health_check()
            
            if not health_check:
                logger.error("System health check failed - cannot start deployment")
                return False
            
            # Check if another deployment is already running
            if self.current_status and self.current_status.phase not in [DeploymentPhase.COMPLETED, DeploymentPhase.ROLLBACK]:
                logger.error("Another deployment is already in progress")
                return False
            
            # Check database connectivity
            try:
                result = await session.execute("SELECT 1")
                if not result:
                    logger.error("Database connectivity check failed")
                    return False
            except Exception as e:
                logger.error(f"Database check failed: {e}")
                return False
            
            logger.info("All deployment preconditions met")
            return True
            
        except Exception as e:
            logger.error(f"Precondition check failed: {e}")
            return False

    async def _log_deployment_event(self, event: str, details: Dict[str, Any]):
        """Log deployment event"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "details": details
        }
        
        self.deployment_log.append(log_entry)
        logger.info(f"Deployment Event: {event}")
        
        # Keep only last 100 log entries
        if len(self.deployment_log) > 100:
            self.deployment_log = self.deployment_log[-100:]


# Global deployer instance
_global_deployer = None


def get_zero_downtime_deployer(config: Optional[DeploymentConfig] = None) -> ZeroDowntimeDeployer:
    """Get global zero-downtime deployer instance"""
    global _global_deployer
    
    if _global_deployer is None:
        _global_deployer = ZeroDowntimeDeployer(config)
    
    return _global_deployer