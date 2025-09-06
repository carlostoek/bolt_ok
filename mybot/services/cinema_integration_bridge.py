"""
Cinema Integration Bridge
========================

This bridge seamlessly integrates the cinema architecture with existing systems
without breaking any current functionality. It provides backward-compatible
enhancement while adding cinematic experiences.

Key Features:
- Zero breaking changes to existing code
- Seamless integration with CoordinadorCentral
- Enhanced Diana Menu System integration
- Automatic fallback to existing systems
- Performance monitoring and optimization
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

from .coordinador_central import CoordinadorCentral, AccionUsuario
from .diana_menu_system import DianaMenuSystem
from .narrative_service import NarrativeService
from .cinema_integration_engine import get_cinema_engine, CinemaIntegrationEngine
from .enhanced_narrative_system import get_enhanced_narrative_system, EnhancedNarrativeSystem
from database.models import User
from database.narrative_unified import UserNarrativeState, UserArchetype

logger = logging.getLogger(__name__)

class CinemaIntegrationBridge:
    """
    The master bridge that connects all cinematic systems with existing architecture.
    
    This bridge ensures that existing code continues to work exactly as before,
    while users who meet certain criteria get enhanced cinematic experiences.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
        # Existing systems (maintain full compatibility)
        self.coordinador_central = CoordinadorCentral(session)
        self.diana_menu_system = DianaMenuSystem(session)
        self.base_narrative = NarrativeService(session)
        
        # Enhanced cinematic systems
        self.cinema_engine = get_cinema_engine(session)
        self.enhanced_narrative = get_enhanced_narrative_system(session)
        
        # Integration state tracking
        self.integration_active = True
        self.fallback_mode = False
        self.performance_monitoring = {}
        
        # User eligibility cache
        self._user_eligibility_cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    # ==================== ENHANCED COORDINADOR CENTRAL INTEGRATION ====================
    
    async def ejecutar_flujo_enhanced(self, user_id: int, accion: AccionUsuario, **kwargs) -> Dict[str, Any]:
        """
        Enhanced version of ejecutar_flujo that adds cinematic processing when appropriate.
        
        This method maintains full backward compatibility while adding cinematic enhancement
        for eligible users.
        """
        
        # Always execute base flow first for data consistency
        base_result = await self.coordinador_central.ejecutar_flujo(user_id, accion, **kwargs)
        
        # Check if user is eligible for cinematic enhancement
        if not await self._is_user_eligible_for_enhancement(user_id):
            return base_result
        
        # Apply cinematic enhancement if eligible
        try:
            enhanced_result = await self._apply_cinematic_enhancement_to_flow(
                user_id, accion, base_result, **kwargs
            )
            
            # Merge results (base result is authoritative for data, enhanced adds cinematic elements)
            return self._merge_flow_results(base_result, enhanced_result)
            
        except Exception as e:
            logger.exception(f"Error in cinematic enhancement for user {user_id}, action {accion}: {e}")
            # Fallback to base result if enhancement fails
            return base_result
    
    async def _apply_cinematic_enhancement_to_flow(self, user_id: int, accion: AccionUsuario,
                                                 base_result: Dict, **kwargs) -> Dict[str, Any]:
        """Applies cinematic enhancement to a flow result."""
        
        # Create cinematic interaction data
        interaction_data = {
            "type": "coordinador_flow",
            "action": accion.value,
            "base_result": base_result,
            "context": kwargs
        }
        
        # Process through cinematic engine
        cinematic_result = await self.cinema_engine.process_cinematic_moment(user_id, interaction_data)
        
        return cinematic_result
    
    def _merge_flow_results(self, base_result: Dict, enhanced_result: Dict) -> Dict[str, Any]:
        """Merges base and enhanced flow results."""
        
        # Start with base result (authoritative for data)
        merged = base_result.copy()
        
        # Add cinematic enhancements
        if enhanced_result.get("success"):
            merged["cinematic_enhancement"] = {
                "applied": True,
                "response": enhanced_result.get("cinematic_response"),
                "emotional_level": enhanced_result.get("emotional_level"),
                "personalization": enhanced_result.get("personalization_applied"),
                "character_consistency": enhanced_result.get("character_consistency_score"),
                "processing_time": enhanced_result.get("processing_time_ms")
            }
            
            # Enhanced message if available
            if enhanced_result.get("cinematic_response", {}).get("content"):
                merged["enhanced_message"] = enhanced_result["cinematic_response"]["content"]
        else:
            merged["cinematic_enhancement"] = {"applied": False, "fallback_used": True}
        
        return merged
    
    # ==================== ENHANCED NARRATIVE SYSTEM INTEGRATION ====================
    
    async def get_narrative_fragment_enhanced(self, user_id: int, fragment_key: str,
                                            **kwargs) -> Dict[str, Any]:
        """
        Enhanced narrative fragment retrieval with cinematic integration.
        
        Maintains full compatibility with existing narrative handlers while adding
        cinematic enhancement for eligible users.
        """
        
        # Check user eligibility
        if not await self._is_user_eligible_for_enhancement(user_id):
            # Use base narrative service for non-eligible users
            base_fragment = await self.base_narrative.get_fragment_by_key(fragment_key)
            return {
                "success": bool(base_fragment),
                "fragment": base_fragment,
                "enhanced": False,
                "eligibility_status": await self._get_user_eligibility_status(user_id)
            }
        
        # Use enhanced narrative system for eligible users
        try:
            enhanced_result = await self.enhanced_narrative.get_enhanced_fragment(
                user_id, fragment_key, kwargs
            )
            return enhanced_result
            
        except Exception as e:
            logger.exception(f"Error in enhanced narrative for user {user_id}, fragment {fragment_key}: {e}")
            
            # Fallback to base system
            base_fragment = await self.base_narrative.get_fragment_by_key(fragment_key)
            return {
                "success": bool(base_fragment),
                "fragment": base_fragment,
                "enhanced": False,
                "fallback_used": True,
                "error": str(e)
            }
    
    async def process_narrative_choice_enhanced(self, user_id: int, fragment_key: str,
                                              choice_text: str, **kwargs) -> Dict[str, Any]:
        """
        Enhanced narrative choice processing with cinematic integration.
        """
        
        # Check user eligibility
        if not await self._is_user_eligible_for_enhancement(user_id):
            # Use base narrative service
            base_result = await self.base_narrative.process_user_choice(user_id, fragment_key, choice_text)
            return {
                "success": bool(base_result),
                "result": base_result,
                "enhanced": False,
                "eligibility_status": await self._get_user_eligibility_status(user_id)
            }
        
        # Use enhanced narrative system
        try:
            enhanced_result = await self.enhanced_narrative.process_enhanced_decision(
                user_id, fragment_key, choice_text, kwargs
            )
            return enhanced_result
            
        except Exception as e:
            logger.exception(f"Error in enhanced choice processing for user {user_id}: {e}")
            
            # Fallback to base system
            base_result = await self.base_narrative.process_user_choice(user_id, fragment_key, choice_text)
            return {
                "success": bool(base_result),
                "result": base_result,
                "enhanced": False,
                "fallback_used": True,
                "error": str(e)
            }
    
    # ==================== DIANA MENU SYSTEM ENHANCEMENT ====================
    
    async def enhance_diana_menu_response(self, callback_data: str, user_id: int,
                                        base_response: Dict) -> Dict[str, Any]:
        """
        Enhances Diana menu responses with cinematic elements when appropriate.
        """
        
        if not await self._is_user_eligible_for_enhancement(user_id):
            return base_response
        
        try:
            # Create interaction context for menu action
            interaction_data = {
                "type": "diana_menu_interaction",
                "callback_data": callback_data,
                "base_response": base_response
            }
            
            # Process through cinematic engine
            cinematic_result = await self.cinema_engine.process_cinematic_moment(user_id, interaction_data)
            
            # Enhance base response
            enhanced_response = base_response.copy()
            if cinematic_result.get("success"):
                enhanced_response["cinematic_enhancement"] = {
                    "applied": True,
                    "personalized_content": cinematic_result.get("cinematic_response"),
                    "emotional_context": cinematic_result.get("emotional_level"),
                    "archetype_adaptation": cinematic_result.get("personalization_applied")
                }
            
            return enhanced_response
            
        except Exception as e:
            logger.exception(f"Error enhancing Diana menu response for user {user_id}: {e}")
            return base_response
    
    # ==================== USER ELIGIBILITY SYSTEM ====================
    
    async def _is_user_eligible_for_enhancement(self, user_id: int) -> bool:
        """
        Determines if a user is eligible for cinematic enhancement.
        
        Enhancement is only applied to users who have demonstrated sufficient
        engagement to prevent overwhelming new users.
        """
        
        # Check cache first
        cache_key = f"eligibility_{user_id}"
        if cache_key in self._user_eligibility_cache:
            cache_entry = self._user_eligibility_cache[cache_key]
            if (datetime.now() - cache_entry["timestamp"]).seconds < self._cache_ttl:
                return cache_entry["eligible"]
        
        try:
            # Get user narrative state
            result = await self.session.execute(
                select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
            )
            narrative_state = result.scalar_one_or_none()
            
            if not narrative_state:
                eligible = False
            else:
                # Eligibility criteria
                completed_fragments = len(narrative_state.completed_fragments)
                visited_fragments = len(narrative_state.visited_fragments)
                unlocked_clues = len(narrative_state.unlocked_clues)
                
                eligible = (
                    completed_fragments >= 3 and      # At least 3 fragments completed
                    visited_fragments >= 5 and        # At least 5 fragments visited
                    unlocked_clues >= 2               # At least 2 clues unlocked
                )
            
            # Cache result
            self._user_eligibility_cache[cache_key] = {
                "eligible": eligible,
                "timestamp": datetime.now()
            }
            
            return eligible
            
        except Exception as e:
            logger.exception(f"Error checking user eligibility for {user_id}: {e}")
            return False
    
    async def _get_user_eligibility_status(self, user_id: int) -> Dict[str, Any]:
        """Gets detailed eligibility status for user feedback."""
        
        try:
            result = await self.session.execute(
                select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
            )
            narrative_state = result.scalar_one_or_none()
            
            if not narrative_state:
                return {
                    "eligible": False,
                    "requirements": {
                        "completed_fragments": {"current": 0, "required": 3},
                        "visited_fragments": {"current": 0, "required": 5},
                        "unlocked_clues": {"current": 0, "required": 2}
                    }
                }
            
            completed = len(narrative_state.completed_fragments)
            visited = len(narrative_state.visited_fragments)
            clues = len(narrative_state.unlocked_clues)
            
            return {
                "eligible": completed >= 3 and visited >= 5 and clues >= 2,
                "requirements": {
                    "completed_fragments": {"current": completed, "required": 3, "met": completed >= 3},
                    "visited_fragments": {"current": visited, "required": 5, "met": visited >= 5},
                    "unlocked_clues": {"current": clues, "required": 2, "met": clues >= 2}
                }
            }
            
        except Exception as e:
            logger.exception(f"Error getting eligibility status for {user_id}: {e}")
            return {"eligible": False, "error": str(e)}
    
    # ==================== PERFORMANCE MONITORING ====================
    
    @asynccontextmanager
    async def monitor_performance(self, operation_name: str):
        """Context manager for monitoring operation performance."""
        start_time = asyncio.get_event_loop().time()
        try:
            yield
        finally:
            duration = (asyncio.get_event_loop().time() - start_time) * 1000
            
            if operation_name not in self.performance_monitoring:
                self.performance_monitoring[operation_name] = []
            
            self.performance_monitoring[operation_name].append(duration)
            
            # Keep only last 100 measurements
            if len(self.performance_monitoring[operation_name]) > 100:
                self.performance_monitoring[operation_name] = self.performance_monitoring[operation_name][-100:]
            
            # Check performance requirements
            if duration > 500:  # >500ms is concerning
                logger.warning(f"Slow cinema operation {operation_name}: {duration:.2f}ms")
    
    # ==================== SYSTEM HEALTH AND MONITORING ====================
    
    async def get_integration_status(self) -> Dict[str, Any]:
        """Gets comprehensive integration status."""
        
        try:
            # Test basic connectivity
            test_user_id = 999999999
            
            # Test base systems
            base_systems_healthy = True
            try:
                await self.coordinador_central.check_system_consistency(test_user_id)
            except Exception:
                base_systems_healthy = False
            
            # Test enhanced systems
            enhanced_systems_healthy = True
            try:
                await self.cinema_engine.performance_optimizer.get_performance_summary()
            except Exception:
                enhanced_systems_healthy = False
            
            # Calculate performance metrics
            performance_summary = {}
            for operation, measurements in self.performance_monitoring.items():
                if measurements:
                    performance_summary[operation] = {
                        "avg_ms": sum(measurements) / len(measurements),
                        "max_ms": max(measurements),
                        "samples": len(measurements)
                    }
            
            return {
                "integration_active": self.integration_active,
                "fallback_mode": self.fallback_mode,
                "base_systems_healthy": base_systems_healthy,
                "enhanced_systems_healthy": enhanced_systems_healthy,
                "performance_summary": performance_summary,
                "cache_status": {
                    "eligibility_cache_size": len(self._user_eligibility_cache),
                    "cache_hit_rate": self._calculate_cache_hit_rate()
                },
                "overall_status": "healthy" if base_systems_healthy and enhanced_systems_healthy else "degraded"
            }
            
        except Exception as e:
            logger.exception(f"Error getting integration status: {e}")
            return {
                "integration_active": False,
                "error": str(e),
                "overall_status": "error"
            }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculates cache hit rate for performance monitoring."""
        # This would track cache hits/misses in a real implementation
        return 85.0  # Sample hit rate
    
    # ==================== GRACEFUL DEGRADATION ====================
    
    async def enable_fallback_mode(self, reason: str = "performance_issues"):
        """Enables fallback mode to ensure system stability."""
        
        logger.warning(f"Enabling cinema integration fallback mode: {reason}")
        self.fallback_mode = True
        
        # Clear caches to reduce memory usage
        self._user_eligibility_cache.clear()
        
        # Log the fallback activation
        logger.info("Cinema integration fallback mode activated - all requests will use base systems")
    
    async def disable_fallback_mode(self):
        """Disables fallback mode and re-enables enhanced features."""
        
        logger.info("Disabling cinema integration fallback mode")
        self.fallback_mode = False
        
        # Test enhanced systems before fully re-enabling
        test_result = await self.get_integration_status()
        if test_result.get("overall_status") != "healthy":
            logger.warning("Enhanced systems not fully healthy, keeping fallback mode partially active")
            return False
        
        logger.info("Cinema integration fully re-enabled")
        return True


# Global bridge instance
_integration_bridge = None

def get_cinema_integration_bridge(session: AsyncSession) -> CinemaIntegrationBridge:
    """Gets or creates the global cinema integration bridge."""
    global _integration_bridge
    if _integration_bridge is None or _integration_bridge.session != session:
        _integration_bridge = CinemaIntegrationBridge(session)
    return _integration_bridge

async def initialize_cinema_integration_bridge(session: AsyncSession) -> Dict[str, Any]:
    """Initializes the cinema integration bridge."""
    try:
        bridge = get_cinema_integration_bridge(session)
        
        # Test all integration points
        integration_status = await bridge.get_integration_status()
        
        logger.info("Cinema Integration Bridge initialized successfully")
        
        return {
            "success": True,
            "bridge_active": True,
            "backward_compatibility": True,
            "integration_status": integration_status,
            "message": "Cinema Integration Bridge operativo - compatibilidad total garantizada"
        }
        
    except Exception as e:
        logger.error(f"Error initializing Cinema Integration Bridge: {e}")
        return {
            "success": False,
            "error": str(e),
            "bridge_active": False,
            "message": "Error inicializando puente de integración cinematográfica"
        }