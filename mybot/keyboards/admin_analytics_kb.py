from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_analytics_admin_main_kb():
    """Return the enhanced main analytics admin inline keyboard with comprehensive layout."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Análisis principal de narrativa
    builder.button(text="📊 Dashboard General", callback_data="admin_analytics_dashboard")
    builder.button(text="👥 Segmentos de Usuarios", callback_data="admin_analytics_segments")
    builder.button(text="⚡ Tiempo Real", callback_data="admin_analytics_realtime")

    # Fila 2: Análisis de contenido
    builder.button(text="📖 Análisis de Fragmentos", callback_data="admin_analytics_fragments")
    builder.button(text="🎯 Patrones de Decisiones", callback_data="admin_analytics_choices")
    builder.button(text="🗺️ Recorridos de Usuario", callback_data="admin_analytics_journey")

    # Fila 3: Detección de problemas
    builder.button(text="⚠️ Cuellos de Botella", callback_data="admin_analytics_bottlenecks")
    builder.button(text="📈 Embudo de Conversión", callback_data="admin_analytics_funnel")
    builder.button(text="💡 Insights IA", callback_data="admin_analytics_insights")

    # Fila 4: Análisis de personajes (Req 4.3)
    builder.button(text="🎭 Voz de Personajes", callback_data="admin_analytics_characters")
    builder.button(text="💭 Progresión Emocional", callback_data="admin_analytics_emotions")
    builder.button(text="🎨 Consistencia", callback_data="admin_analytics_character_consistency")

    # Fila 5: Herramientas avanzadas
    builder.button(text="📋 Generar Reportes", callback_data="admin_analytics_reports")
    builder.button(text="📤 Exportar Datos", callback_data="admin_analytics_export_options")
    builder.button(text="⚙️ Configuración", callback_data="admin_analytics_config")

    # Fila 6: Navegación
    builder.button(text="🔄 Actualizar", callback_data="admin_analytics_main")
    builder.button(text="↩️ Volver", callback_data="admin_main_menu")

    # Distribución: 3x3, luego 3x3, luego 3x2
    builder.adjust(3, 3, 3, 3, 3, 2)
    return builder.as_markup()


def get_user_segments_kb():
    """Return the user segments analysis keyboard."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Segmentos principales
    builder.button(text="🐋 Whales", callback_data="admin_analytics_segment_whales")
    builder.button(text="🗺️ Exploradores", callback_data="admin_analytics_segment_explorers")

    # Fila 2: Niveles de engagement
    builder.button(text="🔥 Altamente Activos", callback_data="admin_analytics_segment_engaged")
    builder.button(text="😴 Usuarios Estancados", callback_data="admin_analytics_segment_stalled")

    # Fila 3: Estados especiales
    builder.button(text="👶 Nuevos Usuarios", callback_data="admin_analytics_segment_new")
    builder.button(text="💤 Usuarios Inactivos", callback_data="admin_analytics_segment_inactive")

    # Fila 4: Herramientas de segmentación
    builder.button(text="📊 Análisis Completo", callback_data="admin_analytics_segments_full")
    builder.button(text="📈 Tendencias", callback_data="admin_analytics_segments_trends")

    # Fila 5: Navegación
    builder.button(text="🔄 Actualizar", callback_data="admin_analytics_segments")
    builder.button(text="↩️ Volver", callback_data="admin_analytics_main")

    builder.adjust(2, 2, 2, 2, 2)
    return builder.as_markup()


def get_fragment_analytics_kb():
    """Return the fragment analytics keyboard."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Métricas principales
    builder.button(text="👁️ Engagement por Fragmento", callback_data="admin_analytics_fragment_engagement")
    builder.button(text="⏱️ Tiempo de Permanencia", callback_data="admin_analytics_fragment_time")

    # Fila 2: Análisis de navegación
    builder.button(text="🚪 Puntos de Entrada", callback_data="admin_analytics_fragment_entry")
    builder.button(text="🚶 Puntos de Salida", callback_data="admin_analytics_fragment_exit")

    # Fila 3: Popularidad y rendimiento
    builder.button(text="⭐ Fragmentos Populares", callback_data="admin_analytics_fragment_popular")
    builder.button(text="📉 Fragmentos Problemáticos", callback_data="admin_analytics_fragment_issues")

    # Fila 4: Herramientas de búsqueda
    builder.button(text="🔍 Buscar Fragmento", callback_data="admin_analytics_fragment_search")
    builder.button(text="📊 Comparar Fragmentos", callback_data="admin_analytics_fragment_compare")

    # Fila 5: Navegación
    builder.button(text="🔄 Actualizar", callback_data="admin_analytics_fragments")
    builder.button(text="↩️ Volver", callback_data="admin_analytics_main")

    builder.adjust(2, 2, 2, 2, 2)
    return builder.as_markup()


def get_choice_patterns_kb():
    """Return the choice patterns analysis keyboard."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Distribución general
    builder.button(text="📊 Distribución Global", callback_data="admin_analytics_choice_global")
    builder.button(text="🎯 Decisiones Populares", callback_data="admin_analytics_choice_popular")

    # Fila 2: Análisis por fragmento
    builder.button(text="📖 Por Fragmento", callback_data="admin_analytics_choice_fragment")
    builder.button(text="🔀 Diversidad de Opciones", callback_data="admin_analytics_choice_diversity")

    # Fila 3: Patrones temporales
    builder.button(text="⏰ Tendencias Temporales", callback_data="admin_analytics_choice_temporal")
    builder.button(text="📈 Evolución de Preferencias", callback_data="admin_analytics_choice_evolution")

    # Fila 4: Navegación
    builder.button(text="🔄 Actualizar", callback_data="admin_analytics_choices")
    builder.button(text="↩️ Volver", callback_data="admin_analytics_main")

    builder.adjust(2, 2, 2, 2)
    return builder.as_markup()


def get_bottlenecks_kb():
    """Return the bottlenecks analysis keyboard."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Tipos de problemas
    builder.button(text="🔴 Críticos", callback_data="admin_analytics_bottleneck_critical")
    builder.button(text="🟡 Advertencias", callback_data="admin_analytics_bottleneck_warning")

    # Fila 2: Análisis específicos
    builder.button(text="📉 Alto Abandono", callback_data="admin_analytics_bottleneck_dropout")
    builder.button(text="🔄 Alto Retorno", callback_data="admin_analytics_bottleneck_return")

    # Fila 3: Usuarios estancados
    builder.button(text="😴 Puntos de Estancamiento", callback_data="admin_analytics_bottleneck_stalled")
    builder.button(text="🗺️ Mapa de Calor", callback_data="admin_analytics_bottleneck_heatmap")

    # Fila 4: Recomendaciones
    builder.button(text="💡 Recomendaciones", callback_data="admin_analytics_bottleneck_recommendations")
    builder.button(text="🎯 Plan de Acción", callback_data="admin_analytics_bottleneck_action")

    # Fila 5: Navegación
    builder.button(text="🔄 Actualizar", callback_data="admin_analytics_bottlenecks")
    builder.button(text="↩️ Volver", callback_data="admin_analytics_main")

    builder.adjust(2, 2, 2, 2, 2)
    return builder.as_markup()


def get_character_voice_kb():
    """Return enhanced character voice analytics keyboard with granular analysis options."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Análisis por personaje específico
    builder.button(text="👸 Análisis Diana", callback_data="admin_analytics_char_diana")
    builder.button(text="🤴 Análisis Lucien", callback_data="admin_analytics_char_lucien")
    builder.button(text="👥 Otros Personajes", callback_data="admin_analytics_char_others")

    # Fila 2: Métricas de efectividad
    builder.button(text="🎭 Efectividad por Personaje", callback_data="admin_analytics_char_effectiveness")
    builder.button(text="💬 Interacciones Totales", callback_data="admin_analytics_char_interactions")
    builder.button(text="📊 Patrones de Respuesta", callback_data="admin_analytics_char_response_patterns")

    # Fila 3: Progresión emocional avanzada
    builder.button(text="💭 Estados Emocionales", callback_data="admin_analytics_char_emotions")
    builder.button(text="📈 Progresión Emocional", callback_data="admin_analytics_char_progression")
    builder.button(text="🌡️ Intensidad Emocional", callback_data="admin_analytics_char_emotion_intensity")

    # Fila 4: Análisis comparativo y consistencia
    builder.button(text="⚖️ Comparar Personajes", callback_data="admin_analytics_char_compare")
    builder.button(text="🎯 Personaje Dominante", callback_data="admin_analytics_char_dominant")
    builder.button(text="🔍 Consistencia de Voz", callback_data="admin_analytics_char_consistency")

    # Fila 5: Herramientas avanzadas
    builder.button(text="📊 Dashboard Completo", callback_data="admin_analytics_char_dashboard")
    builder.button(text="💡 Insights IA", callback_data="admin_analytics_char_ai_insights")
    builder.button(text="📤 Exportar Personajes", callback_data="admin_analytics_char_export")

    # Fila 6: Navegación
    builder.button(text="🔄 Actualizar", callback_data="admin_analytics_characters")
    builder.button(text="↩️ Volver", callback_data="admin_analytics_main")

    builder.adjust(3, 3, 3, 3, 3, 2)
    return builder.as_markup()


def get_export_options_kb():
    """Return enhanced export options keyboard with multiple format and date range support."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Formatos de exportación principales
    builder.button(text="📄 JSON Completo", callback_data="admin_analytics_export_json_full")
    builder.button(text="📋 CSV Básico", callback_data="admin_analytics_export_csv_basic")
    builder.button(text="📊 Excel Avanzado", callback_data="admin_analytics_export_excel")

    # Fila 2: Rangos de fecha específicos
    builder.button(text="📅 Última Semana", callback_data="admin_analytics_export_week")
    builder.button(text="📆 Último Mes", callback_data="admin_analytics_export_month")
    builder.button(text="📋 Últimos 3 Meses", callback_data="admin_analytics_export_quarter")

    # Fila 3: Exportaciones específicas por tipo
    builder.button(text="👥 Solo Usuarios", callback_data="admin_analytics_export_users")
    builder.button(text="📖 Solo Fragmentos", callback_data="admin_analytics_export_fragments")
    builder.button(text="🎭 Solo Personajes", callback_data="admin_analytics_export_characters")

    # Fila 4: Reportes personalizados
    builder.button(text="🔧 Rango Personalizado", callback_data="admin_analytics_export_custom_range")
    builder.button(text="⚙️ Configurar Campos", callback_data="admin_analytics_export_configure")

    # Fila 5: Navegación
    builder.button(text="🔄 Actualizar", callback_data="admin_analytics_export_options")
    builder.button(text="↩️ Volver", callback_data="admin_analytics_main")

    builder.adjust(3, 3, 3, 2, 2)
    return builder.as_markup()


def get_analytics_detail_kb(detail_type: str):
    """Return keyboard for detailed analytics view."""
    builder = InlineKeyboardBuilder()

    # Botones comunes para detalles
    builder.button(text="📊 Ver Gráficos", callback_data=f"admin_analytics_{detail_type}_charts")
    builder.button(text="📋 Ver Datos", callback_data=f"admin_analytics_{detail_type}_data")

    # Navegación
    builder.button(text="🔄 Actualizar", callback_data=f"admin_analytics_{detail_type}")
    builder.button(text="↩️ Volver", callback_data="admin_analytics_main")

    builder.adjust(2, 2)
    return builder.as_markup()


def get_analytics_pagination_kb(current_page: int = 0, total_pages: int = 1, callback_prefix: str = "admin_analytics_page"):
    """Return pagination keyboard for analytics lists."""
    builder = InlineKeyboardBuilder()

    if total_pages > 1:
        # Navegación de páginas
        if current_page > 0:
            builder.button(text="⬅️ Anterior", callback_data=f"{callback_prefix}_{current_page - 1}")

        builder.button(text=f"📄 {current_page + 1}/{total_pages}", callback_data=f"{callback_prefix}_info")

        if current_page < total_pages - 1:
            builder.button(text="➡️ Siguiente", callback_data=f"{callback_prefix}_{current_page + 1}")

    # Navegación principal
    builder.button(text="🔄 Actualizar", callback_data=f"{callback_prefix}_refresh")
    builder.button(text="↩️ Volver", callback_data="admin_analytics_main")

    # Ajustar según el número de botones
    if total_pages > 1:
        if current_page == 0 or current_page == total_pages - 1:
            builder.adjust(2, 2)  # Sin un botón de navegación
        else:
            builder.adjust(3, 2)  # Con ambos botones
    else:
        builder.adjust(2)

    return builder.as_markup()


def get_character_specific_kb(character_name: str):
    """Return keyboard for individual character analytics analysis."""
    builder = InlineKeyboardBuilder()

    # Character display names
    display_names = {
        "diana": "Diana 👸",
        "lucien": "Lucien 🤴",
        "others": "Otros Personajes 👥"
    }

    char_display = display_names.get(character_name.lower(), character_name)

    # Fila 1: Métricas principales del personaje
    builder.button(text="📊 Métricas Generales", callback_data=f"admin_analytics_char_{character_name}_metrics")
    builder.button(text="💬 Dialogues Efectivos", callback_data=f"admin_analytics_char_{character_name}_dialogues")

    # Fila 2: Análisis emocional específico
    builder.button(text="💭 Mapa Emocional", callback_data=f"admin_analytics_char_{character_name}_emotion_map")
    builder.button(text="📈 Evolución Emocional", callback_data=f"admin_analytics_char_{character_name}_emotion_evolution")

    # Fila 3: Interacciones y respuestas
    builder.button(text="🎯 Respuestas por Usuario", callback_data=f"admin_analytics_char_{character_name}_user_responses")
    builder.button(text="⚡ Tiempo de Respuesta", callback_data=f"admin_analytics_char_{character_name}_response_time")

    # Fila 4: Consistencia y calidad
    builder.button(text="🔍 Análisis de Consistencia", callback_data=f"admin_analytics_char_{character_name}_consistency")
    builder.button(text="⭐ Rating de Calidad", callback_data=f"admin_analytics_char_{character_name}_quality")

    # Fila 5: Exportación específica
    builder.button(text=f"📤 Exportar {char_display}", callback_data=f"admin_analytics_char_{character_name}_export")

    # Fila 6: Navegación
    builder.button(text="🔄 Actualizar", callback_data=f"admin_analytics_char_{character_name}")
    builder.button(text="↩️ Volver a Personajes", callback_data="admin_analytics_characters")

    builder.adjust(2, 2, 2, 2, 1, 2)
    return builder.as_markup()


def get_user_journey_analytics_kb():
    """Return enhanced user journey analytics keyboard."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Análisis de recorrido general
    builder.button(text="🗺️ Mapa de Recorridos", callback_data="admin_analytics_journey_map")
    builder.button(text="📊 Patrones de Navegación", callback_data="admin_analytics_journey_patterns")
    builder.button(text="⏱️ Tiempo por Fragmento", callback_data="admin_analytics_journey_timing")

    # Fila 2: Análisis de abandono y retorno
    builder.button(text="🚪 Puntos de Abandono", callback_data="admin_analytics_journey_dropoff")
    builder.button(text="🔄 Patrones de Retorno", callback_data="admin_analytics_journey_return")
    builder.button(text="⚠️ Rutas Problemáticas", callback_data="admin_analytics_journey_problems")

    # Fila 3: Segmentación de usuarios
    builder.button(text="🎯 Rutas Más Populares", callback_data="admin_analytics_journey_popular")
    builder.button(text="🔍 Rutas Alternativas", callback_data="admin_analytics_journey_alternative")
    builder.button(text="💎 Rutas de Éxito", callback_data="admin_analytics_journey_success")

    # Fila 4: Análisis temporal
    builder.button(text="📅 Evolución Temporal", callback_data="admin_analytics_journey_temporal")
    builder.button(text="🕒 Análisis por Horarios", callback_data="admin_analytics_journey_schedule")
    builder.button(text="📈 Tendencias de Uso", callback_data="admin_analytics_journey_trends")

    # Fila 5: Herramientas avanzadas
    builder.button(text="🤖 Predicciones IA", callback_data="admin_analytics_journey_predictions")
    builder.button(text="💡 Recomendaciones", callback_data="admin_analytics_journey_recommendations")

    # Fila 6: Navegación
    builder.button(text="🔄 Actualizar", callback_data="admin_analytics_journey")
    builder.button(text="↩️ Volver", callback_data="admin_analytics_main")

    builder.adjust(3, 3, 3, 3, 2, 2)
    return builder.as_markup()


def get_report_generation_kb():
    """Return comprehensive report generation keyboard."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Reportes predefinidos
    builder.button(text="📋 Reporte Ejecutivo", callback_data="admin_analytics_report_executive")
    builder.button(text="📊 Reporte Detallado", callback_data="admin_analytics_report_detailed")
    builder.button(text="🎯 Reporte de KPIs", callback_data="admin_analytics_report_kpis")

    # Fila 2: Reportes específicos
    builder.button(text="👥 Reporte de Usuarios", callback_data="admin_analytics_report_users")
    builder.button(text="📖 Reporte de Contenido", callback_data="admin_analytics_report_content")
    builder.button(text="🎭 Reporte de Personajes", callback_data="admin_analytics_report_characters")

    # Fila 3: Reportes temporales
    builder.button(text="📅 Reporte Diario", callback_data="admin_analytics_report_daily")
    builder.button(text="📆 Reporte Semanal", callback_data="admin_analytics_report_weekly")
    builder.button(text="🗓️ Reporte Mensual", callback_data="admin_analytics_report_monthly")

    # Fila 4: Configuración personalizada
    builder.button(text="⚙️ Crear Reporte Custom", callback_data="admin_analytics_report_custom")
    builder.button(text="📝 Plantillas", callback_data="admin_analytics_report_templates")
    builder.button(text="🔧 Configuración", callback_data="admin_analytics_report_config")

    # Fila 5: Programación y automatización
    builder.button(text="⏰ Programar Reporte", callback_data="admin_analytics_report_schedule")
    builder.button(text="🤖 Reporte Automático", callback_data="admin_analytics_report_auto")

    # Fila 6: Navegación
    builder.button(text="🔄 Actualizar", callback_data="admin_analytics_reports")
    builder.button(text="↩️ Volver", callback_data="admin_analytics_main")

    builder.adjust(3, 3, 3, 3, 2, 2)
    return builder.as_markup()


def get_advanced_export_kb():
    """Return advanced export configuration keyboard."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Formatos avanzados
    builder.button(text="📊 PDF con Gráficos", callback_data="admin_analytics_export_pdf_charts")
    builder.button(text="💾 Base de Datos", callback_data="admin_analytics_export_database")
    builder.button(text="☁️ Cloud Storage", callback_data="admin_analytics_export_cloud")

    # Fila 2: Configuración de campos
    builder.button(text="✅ Seleccionar Campos", callback_data="admin_analytics_export_fields")
    builder.button(text="🔢 Agregaciones", callback_data="admin_analytics_export_aggregations")
    builder.button(text="🎨 Formato Visual", callback_data="admin_analytics_export_formatting")

    # Fila 3: Filtros avanzados
    builder.button(text="🎯 Filtros por Usuario", callback_data="admin_analytics_export_filter_users")
    builder.button(text="📅 Filtros por Fecha", callback_data="admin_analytics_export_filter_dates")
    builder.button(text="🏷️ Filtros por Tags", callback_data="admin_analytics_export_filter_tags")

    # Fila 4: Configuración de entrega
    builder.button(text="📧 Envío por Email", callback_data="admin_analytics_export_email")
    builder.button(text="📱 Notificación Push", callback_data="admin_analytics_export_notification")
    builder.button(text="🔗 Link de Descarga", callback_data="admin_analytics_export_download")

    # Fila 5: Navegación
    builder.button(text="💾 Guardar Configuración", callback_data="admin_analytics_export_save_config")
    builder.button(text="↩️ Volver a Exportar", callback_data="admin_analytics_export_options")

    builder.adjust(3, 3, 3, 3, 2)
    return builder.as_markup()


def get_analytics_insights_kb():
    """Return analytics insights and AI recommendations keyboard."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Insights automáticos
    builder.button(text="🤖 Insights IA", callback_data="admin_analytics_insights_ai")
    builder.button(text="📈 Tendencias Detectadas", callback_data="admin_analytics_insights_trends")
    builder.button(text="⚠️ Alertas Automáticas", callback_data="admin_analytics_insights_alerts")

    # Fila 2: Predicciones
    builder.button(text="🔮 Predicciones", callback_data="admin_analytics_insights_predictions")
    builder.button(text="📊 Modelado Predictivo", callback_data="admin_analytics_insights_modeling")
    builder.button(text="🎯 Objetivos Sugeridos", callback_data="admin_analytics_insights_goals")

    # Fila 3: Recomendaciones
    builder.button(text="💡 Recomendaciones", callback_data="admin_analytics_insights_recommendations")
    builder.button(text="🚀 Plan de Mejora", callback_data="admin_analytics_insights_improvement")
    builder.button(text="⚡ Acciones Rápidas", callback_data="admin_analytics_insights_quick_actions")

    # Fila 4: Benchmarking
    builder.button(text="📏 Comparar con Baseline", callback_data="admin_analytics_insights_baseline")
    builder.button(text="🏆 Mejores Prácticas", callback_data="admin_analytics_insights_best_practices")

    # Fila 5: Navegación
    builder.button(text="🔄 Generar Nuevos Insights", callback_data="admin_analytics_insights_generate")
    builder.button(text="↩️ Volver", callback_data="admin_analytics_main")

    builder.adjust(3, 3, 3, 2, 2)
    return builder.as_markup()


def get_real_time_analytics_kb():
    """Return real-time analytics monitoring keyboard."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Monitoreo en tiempo real
    builder.button(text="⚡ Dashboard en Vivo", callback_data="admin_analytics_realtime_dashboard")
    builder.button(text="👥 Usuarios Activos", callback_data="admin_analytics_realtime_active_users")
    builder.button(text="📊 Métricas en Vivo", callback_data="admin_analytics_realtime_metrics")

    # Fila 2: Eventos recientes
    builder.button(text="🔔 Eventos Recientes", callback_data="admin_analytics_realtime_events")
    builder.button(text="📈 Picos de Actividad", callback_data="admin_analytics_realtime_spikes")
    builder.button(text="⚠️ Problemas Detectados", callback_data="admin_analytics_realtime_issues")

    # Fila 3: Análisis inmediato
    builder.button(text="🎯 Fragmento Actual", callback_data="admin_analytics_realtime_current_fragment")
    builder.button(text="💬 Interacciones Ahora", callback_data="admin_analytics_realtime_interactions")
    builder.button(text="🛤️ Flujo de Usuarios", callback_data="admin_analytics_realtime_user_flow")

    # Fila 4: Configuración de alertas
    builder.button(text="🚨 Configurar Alertas", callback_data="admin_analytics_realtime_alerts_config")
    builder.button(text="📱 Notificaciones", callback_data="admin_analytics_realtime_notifications")

    # Fila 5: Navegación
    builder.button(text="🔄 Auto-Actualizar", callback_data="admin_analytics_realtime_auto_refresh")
    builder.button(text="↩️ Volver", callback_data="admin_analytics_main")

    builder.adjust(3, 3, 3, 2, 2)
    return builder.as_markup()