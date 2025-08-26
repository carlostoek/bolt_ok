# Escenarios de Integración Avanzados y Casos Edge

## Resumen

Este documento complementa el manual técnico principal documentando escenarios complejos de integración, casos edge y patrones avanzados para el sistema de interfaces del bot Diana.

## Escenarios de Integración Complejos

### Escenario 1: Pipeline de Procesamiento Multi-Interfaz

**Caso de uso:** Usuario completa fragmento narrativo que desencadena análisis emocional, actualización de progreso, otorgamiento de puntos y recomendaciones personalizadas.

```python
async def pipeline_fragmento_complejo(user_id: int, fragment_id: str, 
                                    completion_data: Dict[str, Any], bot):
    """
    Pipeline completo que integra todas las interfaces para procesamiento 
    comprehensivo de completar fragmento narrativo.
    """
    coordinator = CoordinadorCentral(session)
    correlation_id = f"fragment_pipeline_{user_id}_{fragment_id}"
    
    try:
        # Fase 1: Análisis emocional inicial
        emotional_analysis = await coordinator.ejecutar_flujo_async(
            user_id,
            AccionUsuario.ANALIZAR_ESTADO_EMOCIONAL,
            interaction_data={
                "type": "fragment_completion",
                "fragment_id": fragment_id,
                "completion_time": completion_data.get("time_spent", 60),
                "user_choice": completion_data.get("choice_text", "")
            },
            correlation_id=correlation_id,
            bot=bot
        )
        
        if not emotional_analysis["success"]:
            logger.warning(f"Emotional analysis failed for user {user_id}")
        
        # Fase 2: Procesar fragmento narrativo con contexto emocional
        narrative_result = await coordinator.ejecutar_flujo_async(
            user_id,
            AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
            fragment_id=fragment_id,
            emotional_context=emotional_analysis.get("new_state"),
            correlation_id=correlation_id,
            bot=bot
        )
        
        # Fase 3: Obtener recomendaciones basadas en nuevo estado emocional
        if emotional_analysis["success"] and hasattr(coordinator, 'recommendation_service'):
            emotional_context = await coordinator.emotional_state_service.get_user_emotional_state(user_id)
            recommendations = await coordinator.recommendation_service.get_personalized_recommendations(
                user_id, emotional_context, "narrative"
            )
        else:
            recommendations = []
        
        # Fase 4: Crear contenido personalizado para delivery
        recommended_tone = emotional_analysis.get("recommended_tone", "balanced")
        content_template = _get_completion_message_template(recommended_tone)
        
        content_package = await coordinator.content_delivery_service.prepare_content(
            f"completion_{fragment_id}",
            {
                "text": content_template,
                "fragment_title": completion_data.get("fragment_title", "Fragmento"),
                "points_earned": narrative_result.get("mission_points_awarded", 0),
                "recommendations": recommendations[:3],  # Top 3
                "emotional_tone": recommended_tone
            }
        )
        
        personalized_content = await coordinator.content_delivery_service.personalize_content(
            content_package.payload,
            {
                "fragment_title": completion_data.get("fragment_title", "Fragmento"),
                "points_earned": narrative_result.get("mission_points_awarded", 0),
                "emotional_response": _get_emotional_response_text(recommended_tone)
            }
        )
        
        # Fase 5: Entregar contenido
        await coordinator.content_delivery_service.deliver_content(
            ContentPackage(
                content_id=f"completion_{fragment_id}",
                content_type=ContentType.TEXT,
                payload=personalized_content,
                metadata={"reply_markup": _create_recommendations_keyboard(recommendations)},
                delivery_options={}
            ),
            {"bot": bot, "chat_id": user_id}
        )
        
        # Fase 6: Registrar interacción completa
        interaction_result = await coordinator.interaction_processor.process_interaction(
            InteractionContext(
                user_id=user_id,
                interaction_type=InteractionType.NARRATIVE_COMPLETION,
                raw_data={
                    "fragment_id": fragment_id,
                    "completion_data": completion_data,
                    "emotional_state": emotional_analysis.get("new_state"),
                    "points_awarded": narrative_result.get("mission_points_awarded", 0),
                    "recommendations_count": len(recommendations)
                },
                timestamp=datetime.now(),
                session_data={"correlation_id": correlation_id}
            )
        )
        
        return {
            "success": True,
            "pipeline_completed": True,
            "phases": {
                "emotional_analysis": emotional_analysis["success"],
                "narrative_processing": narrative_result["success"],
                "content_delivery": True,
                "interaction_logging": interaction_result.success
            },
            "total_points": narrative_result.get("total_points", 0),
            "emotional_state": emotional_analysis.get("new_state", "unknown"),
            "recommendations": len(recommendations),
            "correlation_id": correlation_id
        }
        
    except Exception as e:
        logger.exception(f"Error in complex fragment pipeline for user {user_id}: {e}")
        
        # Fallback: al menos completar el fragmento básico
        try:
            fallback_result = await coordinator.ejecutar_flujo(
                user_id,
                AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
                fragment_id=fragment_id,
                bot=bot
            )
            
            return {
                "success": False,
                "fallback_completed": fallback_result["success"],
                "error": str(e),
                "message": "Pipeline falló pero fragmento fue procesado básicamente",
                "correlation_id": correlation_id
            }
            
        except Exception as fallback_error:
            logger.critical(f"Critical failure in fragment processing: {fallback_error}")
            return {
                "success": False,
                "critical_failure": True,
                "error": str(e),
                "fallback_error": str(fallback_error),
                "correlation_id": correlation_id
            }

def _get_completion_message_template(tone: str) -> str:
    """Obtiene template de mensaje basado en tono emocional."""
    templates = {
        "supportive": "Diana te mira con comprensión mientras completas '{fragment_title}'...\n\n✨ Has ganado {points_earned} besitos por tu progreso.\n\n{emotional_response}",
        "energetic": "¡Diana sonríe con emoción al verte completar '{fragment_title}'!\n\n🔥 ¡{points_earned} besitos han sido añadidos a tu cuenta!\n\n{emotional_response}",
        "gentle": "Diana te acompaña suavemente mientras terminas '{fragment_title}'...\n\n💫 {points_earned} besitos para ti, con cariño.\n\n{emotional_response}",
        "encouraging": "Diana asiente con satisfacción al ver que completas '{fragment_title}'.\n\n⭐ ¡{points_earned} besitos merecidos!\n\n{emotional_response}",
        "balanced": "Diana observa tu progreso en '{fragment_title}'...\n\n💋 {points_earned} besitos añadidos.\n\n{emotional_response}"
    }
    return templates.get(tone, templates["balanced"])

def _get_emotional_response_text(tone: str) -> str:
    """Genera texto de respuesta emocional basado en tono."""
    responses = {
        "supportive": "Te entiendo perfectamente, sigamos juntos en esta historia.",
        "energetic": "¡Tu energía es contagiosa! ¡Continuemos con más aventuras!",
        "gentle": "Avancemos paso a paso, sin prisa pero sin pausa.",
        "encouraging": "Estás haciendo un excelente trabajo, sigue así.",
        "balanced": "Continuemos descubriendo lo que nos depara esta historia."
    }
    return responses.get(tone, responses["balanced"])

def _create_recommendations_keyboard(recommendations: List[Dict[str, Any]]):
    """Crea teclado con recomendaciones personalizadas."""
    if not recommendations:
        return None
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = []
    for rec in recommendations[:3]:  # Máximo 3 recomendaciones
        keyboard.append([
            InlineKeyboardButton(
                text=f"🌟 {rec.get('title', 'Recomendación')[:30]}",
                callback_data=f"recommendation:{rec.get('id', 'unknown')}"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
```

### Escenario 2: Recovery y Fallback en Caso de Fallas Parciales

**Caso de uso:** Manejo robusto cuando algunos servicios fallan pero otros siguen funcionando.

```python
class RobustIntegrationHandler:
    """
    Handler que implementa patrones de resilience para integraciones complejas.
    """
    
    def __init__(self, coordinator: CoordinadorCentral):
        self.coordinator = coordinator
        self.fallback_strategies = {
            "emotional_analysis": self._fallback_emotional_analysis,
            "content_delivery": self._fallback_content_delivery,
            "narrative_processing": self._fallback_narrative_processing
        }
    
    async def robust_user_interaction(self, user_id: int, interaction_data: Dict[str, Any], 
                                    bot) -> Dict[str, Any]:
        """
        Procesa interacción de usuario con recuperación automática en caso de fallas.
        """
        results = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "services_attempted": [],
            "services_successful": [],
            "services_failed": [],
            "fallbacks_used": [],
            "final_result": None
        }
        
        # 1. Intentar análisis emocional
        try:
            results["services_attempted"].append("emotional_analysis")
            emotional_result = await self.coordinator.ejecutar_flujo_async(
                user_id,
                AccionUsuario.ANALIZAR_ESTADO_EMOCIONAL,
                interaction_data=interaction_data,
                timeout=5.0  # Timeout corto para evitar bloqueos
            )
            
            if emotional_result["success"]:
                results["services_successful"].append("emotional_analysis")
                results["emotional_context"] = emotional_result.get("new_state")
            else:
                raise Exception(f"Emotional analysis failed: {emotional_result.get('error')}")
                
        except Exception as e:
            logger.warning(f"Emotional analysis failed for user {user_id}: {e}")
            results["services_failed"].append("emotional_analysis")
            results["fallbacks_used"].append("emotional_analysis")
            
            # Usar fallback
            emotional_context = await self._fallback_emotional_analysis(user_id, interaction_data)
            results["emotional_context"] = emotional_context
        
        # 2. Intentar procesamiento de interacción
        try:
            results["services_attempted"].append("interaction_processing")
            
            # Usar procesador de interacciones
            interaction_context = InteractionContext(
                user_id=user_id,
                interaction_type=InteractionType.MESSAGE,  # Determinar dinámicamente
                raw_data=interaction_data,
                timestamp=datetime.now(),
                session_data={"emotional_context": results.get("emotional_context")}
            )
            
            interaction_result = await self.coordinator.interaction_processor.process_interaction(
                interaction_context
            )
            
            if interaction_result.success:
                results["services_successful"].append("interaction_processing")
                results["interaction_result"] = {
                    "points_awarded": interaction_result.points_awarded,
                    "emotional_impact": interaction_result.emotional_impact.value if interaction_result.emotional_impact else None,
                    "side_effects": interaction_result.side_effects
                }
            else:
                raise Exception("Interaction processing failed")
                
        except Exception as e:
            logger.warning(f"Interaction processing failed for user {user_id}: {e}")
            results["services_failed"].append("interaction_processing")
            results["fallbacks_used"].append("interaction_processing")
            
            # Fallback: procesamiento básico
            results["interaction_result"] = await self._fallback_interaction_processing(
                user_id, interaction_data
            )
        
        # 3. Intentar entrega de contenido personalizado
        try:
            results["services_attempted"].append("content_delivery")
            
            # Preparar contenido basado en contexto emocional
            emotional_tone = await self.coordinator.emotional_state_service.get_recommended_content_tone(user_id)
            
            content_package = await self.coordinator.content_delivery_service.prepare_content(
                f"interaction_response_{user_id}",
                {
                    "text": self._generate_response_text(emotional_tone, results["interaction_result"]),
                    "tone": emotional_tone,
                    "interaction_data": interaction_data
                }
            )
            
            delivery_success = await self.coordinator.content_delivery_service.deliver_content(
                content_package,
                {"bot": bot, "chat_id": user_id}
            )
            
            if delivery_success:
                results["services_successful"].append("content_delivery")
                results["content_delivered"] = True
            else:
                raise Exception("Content delivery failed")
                
        except Exception as e:
            logger.warning(f"Content delivery failed for user {user_id}: {e}")
            results["services_failed"].append("content_delivery")
            results["fallbacks_used"].append("content_delivery")
            
            # Fallback: mensaje básico
            await self._fallback_content_delivery(user_id, interaction_data, bot)
            results["content_delivered"] = True
        
        # 4. Evaluar resultado final
        success_rate = len(results["services_successful"]) / len(results["services_attempted"])
        results["success_rate"] = success_rate
        results["overall_success"] = success_rate >= 0.5  # Al menos 50% de servicios exitosos
        
        # Log resultado para monitoring
        if success_rate < 1.0:
            logger.warning(f"Partial failure in robust interaction for user {user_id}: "
                         f"{success_rate:.1%} success rate. "
                         f"Failed services: {results['services_failed']}")
        
        results["final_result"] = {
            "success": results["overall_success"],
            "message": "Interacción procesada" if results["overall_success"] else "Interacción procesada parcialmente",
            "details": results
        }
        
        return results
    
    async def _fallback_emotional_analysis(self, user_id: int, interaction_data: Dict[str, Any]) -> str:
        """Fallback simple para análisis emocional."""
        # Usar heurísticas básicas sin acceso a base de datos
        interaction_type = interaction_data.get("type", "")
        
        if "completion" in interaction_type:
            return "satisfied"
        elif "failed" in interaction_type or "error" in interaction_type:
            return "frustrated"
        elif "choice" in interaction_type or "selection" in interaction_type:
            return "engaged"
        else:
            return "neutral"
    
    async def _fallback_interaction_processing(self, user_id: int, 
                                             interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback para procesamiento de interacciones."""
        return {
            "points_awarded": 1,  # Mínimo
            "emotional_impact": None,
            "side_effects": ["fallback_processing_used"],
            "message": "Procesado con método básico"
        }
    
    async def _fallback_content_delivery(self, user_id: int, interaction_data: Dict[str, Any], bot):
        """Fallback para entrega de contenido."""
        basic_message = "Diana te sonríe suavemente... 💋"
        
        try:
            await bot.send_message(
                chat_id=user_id,
                text=basic_message
            )
        except Exception as e:
            logger.error(f"Even fallback content delivery failed for user {user_id}: {e}")
    
    def _generate_response_text(self, tone: str, interaction_result: Dict[str, Any]) -> str:
        """Genera texto de respuesta basado en tono y resultado de interacción."""
        points = interaction_result.get("points_awarded", 0)
        
        base_responses = {
            "supportive": f"Diana te comprende y te acompaña... +{points} besitos 💋",
            "energetic": f"¡Diana celebra tu acción! ¡+{points} besitos! 🔥💋",
            "gentle": f"Diana sonríe dulcemente... +{points} besitos 🌸💋",
            "encouraging": f"Diana asiente con aprobación... +{points} besitos ⭐💋",
            "balanced": f"Diana observa tu progreso... +{points} besitos 💋"
        }
        
        return base_responses.get(tone, base_responses["balanced"])
```

### Escenario 3: Procesamiento Batch con Optimizaciones

**Caso de uso:** Procesar múltiples interacciones de usuarios de forma eficiente.

```python
class BatchInteractionProcessor:
    """
    Procesador optimizado para manejar múltiples interacciones de usuarios en lote.
    """
    
    def __init__(self, coordinator: CoordinadorCentral):
        self.coordinator = coordinator
        self.batch_size = 50
        self.max_concurrent = 10
    
    async def process_user_interactions_batch(self, 
                                            interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Procesa múltiples interacciones de usuarios con optimizaciones de performance.
        
        Args:
            interactions: Lista de diccionarios con user_id, interaction_data, etc.
        """
        total_interactions = len(interactions)
        processed = 0
        successful = 0
        failed = 0
        batch_results = []
        
        logger.info(f"Starting batch processing of {total_interactions} interactions")
        
        # Procesar en batches para evitar sobrecarga
        for i in range(0, total_interactions, self.batch_size):
            batch = interactions[i:i + self.batch_size]
            batch_result = await self._process_batch_chunk(batch)
            
            batch_results.extend(batch_result["results"])
            processed += batch_result["processed"]
            successful += batch_result["successful"]
            failed += batch_result["failed"]
            
            # Log progreso
            progress = (i + len(batch)) / total_interactions
            logger.info(f"Batch processing progress: {progress:.1%} "
                       f"({successful} successful, {failed} failed)")
        
        # Análisis post-procesamiento
        final_stats = await self._analyze_batch_results(batch_results)
        
        return {
            "total_interactions": total_interactions,
            "processed": processed,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / processed if processed > 0 else 0,
            "batch_results": batch_results,
            "analysis": final_stats
        }
    
    async def _process_batch_chunk(self, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Procesa un chunk del batch con concurrencia limitada."""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_single_interaction(interaction_data: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                try:
                    user_id = interaction_data["user_id"]
                    interaction_type = interaction_data.get("type", "unknown")
                    
                    # Crear handler robusto
                    robust_handler = RobustIntegrationHandler(self.coordinator)
                    
                    # Procesar con timeout
                    result = await asyncio.wait_for(
                        robust_handler.robust_user_interaction(
                            user_id,
                            interaction_data.get("data", {}),
                            interaction_data.get("bot")
                        ),
                        timeout=30.0
                    )
                    
                    return {
                        "user_id": user_id,
                        "interaction_type": interaction_type,
                        "success": result.get("overall_success", False),
                        "details": result,
                        "processing_time": time.time() - interaction_data.get("start_time", time.time())
                    }
                    
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout processing interaction for user {user_id}")
                    return {
                        "user_id": interaction_data.get("user_id"),
                        "success": False,
                        "error": "timeout",
                        "processing_time": 30.0
                    }
                    
                except Exception as e:
                    logger.exception(f"Error processing interaction: {e}")
                    return {
                        "user_id": interaction_data.get("user_id"),
                        "success": False,
                        "error": str(e),
                        "processing_time": time.time() - interaction_data.get("start_time", time.time())
                    }
        
        # Ejecutar todas las interacciones del batch en paralelo
        tasks = [process_single_interaction(interaction) for interaction in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados
        processed_results = []
        successful_count = 0
        failed_count = 0
        
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": f"Exception: {str(result)}"
                })
                failed_count += 1
            else:
                processed_results.append(result)
                if result.get("success", False):
                    successful_count += 1
                else:
                    failed_count += 1
        
        return {
            "processed": len(processed_results),
            "successful": successful_count,
            "failed": failed_count,
            "results": processed_results
        }
    
    async def _analyze_batch_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza resultados del batch para obtener insights."""
        if not results:
            return {"error": "No results to analyze"}
        
        # Estadísticas básicas
        total_processing_time = sum(r.get("processing_time", 0) for r in results)
        avg_processing_time = total_processing_time / len(results)
        
        # Análisis de errores
        error_types = {}
        for result in results:
            if not result.get("success", False):
                error = result.get("error", "unknown")
                error_types[error] = error_types.get(error, 0) + 1
        
        # Análisis de performance
        slow_interactions = [r for r in results if r.get("processing_time", 0) > 10.0]
        
        # Usuarios con problemas frecuentes
        user_failure_counts = {}
        for result in results:
            if not result.get("success", False):
                user_id = result.get("user_id")
                if user_id:
                    user_failure_counts[user_id] = user_failure_counts.get(user_id, 0) + 1
        
        return {
            "performance": {
                "total_processing_time": total_processing_time,
                "avg_processing_time": avg_processing_time,
                "slow_interactions_count": len(slow_interactions),
                "slowest_interaction_time": max((r.get("processing_time", 0) for r in results), default=0)
            },
            "errors": {
                "error_types": error_types,
                "most_common_error": max(error_types.items(), key=lambda x: x[1])[0] if error_types else None
            },
            "users": {
                "users_with_failures": len(user_failure_counts),
                "users_with_multiple_failures": len([k for k, v in user_failure_counts.items() if v > 1])
            },
            "recommendations": self._generate_recommendations(error_types, slow_interactions)
        }
    
    def _generate_recommendations(self, error_types: Dict[str, int], 
                                slow_interactions: List[Dict[str, Any]]) -> List[str]:
        """Genera recomendaciones basadas en el análisis."""
        recommendations = []
        
        if error_types.get("timeout", 0) > 5:
            recommendations.append("Consider increasing timeout values or optimizing slow operations")
        
        if len(slow_interactions) > 10:
            recommendations.append("Review performance bottlenecks in interaction processing")
        
        if error_types.get("database_error", 0) > 0:
            recommendations.append("Check database connectivity and performance")
        
        if error_types.get("emotional_analysis", 0) > 5:
            recommendations.append("Review emotional analysis service stability")
        
        return recommendations
```

## Casos Edge y Manejo de Errores

### Edge Case 1: Estado Emocional Corrupto

```python
async def handle_corrupted_emotional_state(coordinator: CoordinadorCentral, user_id: int):
    """
    Maneja casos donde el estado emocional del usuario está corrupto o inconsistente.
    """
    try:
        # Intentar obtener estado actual
        current_state = await coordinator.emotional_state_service.get_user_emotional_state(user_id)
        
        # Validar consistencia
        if not _validate_emotional_state_consistency(current_state):
            logger.warning(f"Corrupted emotional state detected for user {user_id}")
            
            # Crear backup del estado corrupto
            await _backup_corrupted_state(user_id, current_state)
            
            # Reset a estado neutral
            await coordinator.emotional_state_service.update_emotional_state(
                user_id,
                EmotionalState.NEUTRAL,
                0.5,
                "system_recovery_from_corruption"
            )
            
            logger.info(f"Emotional state reset to neutral for user {user_id}")
            
            return {
                "success": True,
                "action": "state_reset",
                "message": "Tu estado emocional fue reiniciado por seguridad"
            }
        
        return {
            "success": True,
            "action": "state_validated",
            "current_state": current_state.primary_state.value
        }
        
    except Exception as e:
        logger.exception(f"Error handling corrupted emotional state for user {user_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "action": "error_during_recovery"
        }

def _validate_emotional_state_consistency(context: EmotionalContext) -> bool:
    """Valida la consistencia de un contexto emocional."""
    try:
        # Validar intensidad en rango válido
        if not 0.0 <= context.intensity <= 1.0:
            return False
        
        # Validar que el estado primario es válido
        if context.primary_state not in EmotionalState:
            return False
        
        # Validar estados secundarios
        for state, intensity in context.secondary_states.items():
            if state not in EmotionalState or not 0.0 <= intensity <= 1.0:
                return False
        
        # Validar que la fecha de actualización no es futura
        if context.last_updated > datetime.now():
            return False
        
        return True
        
    except Exception:
        return False

async def _backup_corrupted_state(user_id: int, corrupted_state: EmotionalContext):
    """Respalda estado corrupto para análisis posterior."""
    backup_data = {
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "corrupted_state": {
            "primary_state": corrupted_state.primary_state.value,
            "intensity": corrupted_state.intensity,
            "secondary_states": {k.value: v for k, v in corrupted_state.secondary_states.items()},
            "last_updated": corrupted_state.last_updated.isoformat(),
            "triggers": corrupted_state.triggers
        }
    }
    
    # Guardar en log para análisis
    logger.error(f"CORRUPTED_STATE_BACKUP: {json.dumps(backup_data)}")
```

### Edge Case 2: Deadlock en Transacciones Múltiples

```python
class DeadlockSafeTransactionManager:
    """
    Manager de transacciones que previene deadlocks en operaciones complejas.
    """
    
    def __init__(self, coordinator: CoordinadorCentral):
        self.coordinator = coordinator
        self.transaction_locks = {}
        self.lock = asyncio.Lock()
    
    async def execute_safe_multi_service_transaction(self, user_id: int, 
                                                   operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ejecuta múltiples operaciones de servicios con prevención de deadlock.
        """
        transaction_id = f"multi_tx_{user_id}_{int(time.time())}"
        
        # Ordenar operaciones para prevenir deadlock (alphabetical order by service)
        sorted_operations = sorted(operations, key=lambda x: x.get("service", ""))
        
        async with self.lock:
            if user_id in self.transaction_locks:
                # Usuario ya tiene transacción activa, hacer queue
                logger.warning(f"User {user_id} already has active transaction, queuing...")
                await self.transaction_locks[user_id].wait()
            
            # Crear lock para este usuario
            self.transaction_locks[user_id] = asyncio.Event()
        
        try:
            results = []
            
            async with self.coordinator.session.begin() as transaction:
                for i, operation in enumerate(sorted_operations):
                    try:
                        # Timeout por operación individual
                        result = await asyncio.wait_for(
                            self._execute_single_operation(user_id, operation, transaction_id),
                            timeout=10.0
                        )
                        
                        results.append({
                            "operation_index": i,
                            "service": operation.get("service"),
                            "success": True,
                            "result": result
                        })
                        
                    except asyncio.TimeoutError:
                        logger.error(f"Timeout in operation {i} for user {user_id}")
                        results.append({
                            "operation_index": i,
                            "service": operation.get("service"),
                            "success": False,
                            "error": "timeout"
                        })
                        # No romper la transacción por timeout individual
                        
                    except Exception as e:
                        logger.exception(f"Error in operation {i} for user {user_id}: {e}")
                        results.append({
                            "operation_index": i,
                            "service": operation.get("service"),
                            "success": False,
                            "error": str(e)
                        })
                        
                        # Decidir si continuar o abortar basado en criticidad
                        if operation.get("critical", False):
                            raise  # Abortar transacción completa
                
                # Si llegamos aquí, commit automático
                successful_ops = [r for r in results if r["success"]]
                logger.info(f"Multi-service transaction completed for user {user_id}: "
                           f"{len(successful_ops)}/{len(operations)} operations successful")
        
        finally:
            # Liberar lock
            async with self.lock:
                if user_id in self.transaction_locks:
                    self.transaction_locks[user_id].set()
                    del self.transaction_locks[user_id]
        
        return {
            "transaction_id": transaction_id,
            "user_id": user_id,
            "total_operations": len(operations),
            "successful_operations": len([r for r in results if r["success"]]),
            "results": results,
            "overall_success": all(r["success"] or not operations[r["operation_index"]].get("critical", False) 
                                 for r in results)
        }
    
    async def _execute_single_operation(self, user_id: int, operation: Dict[str, Any], 
                                      transaction_id: str) -> Dict[str, Any]:
        """Ejecuta una operación individual dentro de la transacción."""
        service_name = operation.get("service", "unknown")
        action = operation.get("action", "unknown")
        params = operation.get("params", {})
        
        if service_name == "emotional_state":
            if action == "update":
                return await self.coordinator.emotional_state_service.update_emotional_state(
                    user_id, 
                    EmotionalState(params["state"]),
                    params["intensity"],
                    params.get("trigger", f"tx_{transaction_id}")
                )
        
        elif service_name == "narrative":
            if action == "complete_fragment":
                return await self.coordinator.ejecutar_flujo(
                    user_id,
                    AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
                    fragment_id=params["fragment_id"],
                    skip_unified_notifications=True  # Evitar notificaciones múltiples
                )
        
        elif service_name == "points":
            if action == "award":
                return await self.coordinator.point_service.award_points(
                    user_id,
                    params["points"],
                    params.get("reason", f"tx_{transaction_id}")
                )
        
        else:
            raise ValueError(f"Unknown service or action: {service_name}.{action}")
```

### Edge Case 3: Memory Leaks en Event Subscriptions

```python
class EventSubscriptionManager:
    """
    Manager que previene memory leaks en suscripciones de eventos.
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.subscriptions = {}  # Track active subscriptions
        self.subscription_counter = 0
        self.cleanup_interval = 3600  # 1 hour
        self.last_cleanup = time.time()
    
    def register_subscription(self, event_type: EventType, handler: Callable, 
                            context: str = None, ttl: int = None) -> str:
        """
        Registra suscripción con tracking automático para cleanup.
        
        Args:
            event_type: Tipo de evento
            handler: Handler function
            context: Contexto descriptivo (ej: "user_handler_123456")
            ttl: Time-to-live en segundos (opcional)
        
        Returns:
            subscription_id: ID único de la suscripción
        """
        subscription_id = f"sub_{self.subscription_counter}"
        self.subscription_counter += 1
        
        # Registrar en event bus
        self.event_bus.subscribe(event_type, handler)
        
        # Track subscription
        self.subscriptions[subscription_id] = {
            "event_type": event_type,
            "handler": handler,
            "context": context,
            "created_at": time.time(),
            "ttl": ttl,
            "active": True
        }
        
        # Trigger cleanup si es necesario
        if time.time() - self.last_cleanup > self.cleanup_interval:
            asyncio.create_task(self._cleanup_expired_subscriptions())
        
        return subscription_id
    
    def unregister_subscription(self, subscription_id: str) -> bool:
        """Cancela suscripción específica."""
        if subscription_id not in self.subscriptions:
            return False
        
        subscription = self.subscriptions[subscription_id]
        
        if subscription["active"]:
            # Unsubscribe from event bus
            success = self.event_bus.unsubscribe(
                subscription["event_type"],
                subscription["handler"]
            )
            
            # Mark as inactive
            subscription["active"] = False
            subscription["unregistered_at"] = time.time()
            
            return success
        
        return False
    
    async def _cleanup_expired_subscriptions(self):
        """Limpia suscripciones expiradas automáticamente."""
        current_time = time.time()
        expired_subscriptions = []
        
        for sub_id, subscription in self.subscriptions.items():
            if not subscription["active"]:
                continue
                
            # Check TTL expiration
            if subscription["ttl"]:
                if current_time - subscription["created_at"] > subscription["ttl"]:
                    expired_subscriptions.append(sub_id)
            
            # Check for orphaned handlers (handlers that might reference deleted objects)
            try:
                # Weak reference check - if handler is bound method and object is gone
                if hasattr(subscription["handler"], "__self__"):
                    # Try to access the bound object
                    _ = subscription["handler"].__self__
            except (AttributeError, ReferenceError):
                logger.warning(f"Orphaned handler detected in subscription {sub_id}")
                expired_subscriptions.append(sub_id)
        
        # Cleanup expired subscriptions
        for sub_id in expired_subscriptions:
            success = self.unregister_subscription(sub_id)
            if success:
                logger.info(f"Cleaned up expired subscription {sub_id}")
        
        self.last_cleanup = current_time
        
        # Also cleanup inactive subscriptions older than 24 hours
        old_inactive = [
            sub_id for sub_id, sub in self.subscriptions.items()
            if not sub["active"] and 
            current_time - sub.get("unregistered_at", current_time) > 86400
        ]
        
        for sub_id in old_inactive:
            del self.subscriptions[sub_id]
        
        logger.info(f"Event subscription cleanup completed. "
                   f"Expired: {len(expired_subscriptions)}, "
                   f"Removed inactive: {len(old_inactive)}")
    
    def get_subscription_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de suscripciones."""
        active = len([s for s in self.subscriptions.values() if s["active"]])
        inactive = len([s for s in self.subscriptions.values() if not s["active"]])
        
        # Group by event type
        by_event_type = {}
        for subscription in self.subscriptions.values():
            if subscription["active"]:
                event_type = subscription["event_type"].value
                by_event_type[event_type] = by_event_type.get(event_type, 0) + 1
        
        return {
            "total_subscriptions": len(self.subscriptions),
            "active_subscriptions": active,
            "inactive_subscriptions": inactive,
            "subscriptions_by_event_type": by_event_type,
            "last_cleanup": self.last_cleanup,
            "next_cleanup_in": max(0, self.cleanup_interval - (time.time() - self.last_cleanup))
        }

# Factory function para crear manager global
_subscription_manager = None

def get_subscription_manager() -> EventSubscriptionManager:
    """Obtiene el manager global de suscripciones."""
    global _subscription_manager
    if _subscription_manager is None:
        _subscription_manager = EventSubscriptionManager(get_event_bus())
    return _subscription_manager
```

---

*Este documento complementa el manual técnico principal con escenarios avanzados y casos edge documentados del sistema real implementado.*