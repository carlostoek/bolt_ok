# Documentación del Bot

## 📚 Índice de Documentación

### 🎭 Mi Diván - Sistema VIP
- [Resumen de Implementación](MIDIVAN_IMPLEMENTATION_SUMMARY.md) - Visión general del módulo Mi Diván
- [Características VIP](MIDIVAN_VIP_FEATURES.md) - Funcionalidades exclusivas para usuarios VIP
- [Flujo de Usuario](MIDIVAN_USER_FLOW_EXAMPLES.md) - Ejemplos de interacción del usuario
- [Localización - Resumen](LOCALIZATION_SUMMARY.md) - Implementación del sistema de localización
- [Localización - Ejemplos](LOCALIZATION_EXAMPLE.md) - Ejemplos antes/después de localización

### 🎮 Sistema de Menús
- [Actualizaciones del Sistema de Menús](SESSION_2025-10-01_MENU_SYSTEM_UPDATES.md) - Mejoras implementadas
- [Guía del Mapa de Menús](guia_mapa_menus.md) - Navegación entre menús

### 🛒 Sistema de Tienda
- [Guía del Panel Admin](admin_shop_panel_guide.md) - Panel de administración de la tienda
- [Guía de Edición](admin_shop_edit_guide.md) - Cómo editar items
- [Feature: Disponibilidad](admin_shop_availability_feature.md) - Sistema de disponibilidad de items
- [Feature: Stock](admin_shop_stock_feature.md) - Sistema de inventario
- [Feature: Imágenes](admin_shop_image_feature.md) - Sistema de imágenes para items
- [Feature: Requisitos Compuestos](admin_shop_compound_requirements.md) - Requisitos complejos para items
- [Análisis Tienda y Contenido](analisis_tienda_y_contenido_narrativo.md) - Análisis del sistema

### 📖 Sistema Narrativo
- [Narrativo](Narrativo.md) - Sistema narrativo principal
- [Ramificado](ramificado.md) - Sistema de ramificación narrativa
- [Concepto](concepto.md) - Concepto general del bot

### 🎯 Onboarding y Evaluación
- [Flujo de Onboarding](ONBOARDING_FLUJO.md) - Proceso de incorporación de usuarios
- [Test de Evaluación](README_test_evaluation.md) - Sistema de evaluación de usuarios

### 🔧 Sistema Técnico
- [Mejoras Críticas Implementadas](CRITICAL_IMPROVEMENTS_IMPLEMENTED.md) - Mejoras importantes del sistema
- [Implementación de Voz de Personajes](CHARACTER_VOICE_IMPLEMENTATION.md) - Sistema de voces
- [Integración de Tracking Emocional](EMOTIONAL_TRACKING_INTEGRATION.md) - Sistema de emociones
- [Reporte de Auditoría del Coordinador](COORDINATOR_AUDIT_REPORT.md) - Auditoría del sistema coordinador
- [Reporte de Salud de Base de Datos](database_health_report.md) - Estado de la base de datos
- [Reporte de Refactorización](refactoring_report.md) - Mejoras de código

### 🔐 Sistema de Administración
- [Sistema de Navegación Admin](admin_navigation_system.md) - Navegación en panel admin
- [Migración Decision Requirements](migracion_decision_requirements.md) - Migración de requisitos

### 📝 Scripts y Herramientas
- [README Quiz](../scripts/README_QUIZ.md) - Documentación para crear quizzes de compatibilidad

## 🗂️ Organización

```
mybot/
├── docs/                    # Documentación general (este directorio)
│   ├── README.md           # Este archivo (índice)
│   ├── *.md               # Archivos de documentación
│
├── scripts/
│   └── README_QUIZ.md     # Documentación específica de scripts
│
└── ...                    # Código fuente
```

## 🔍 Búsqueda Rápida

### Por Funcionalidad
- **Mi Diván VIP**: `MIDIVAN_*.md`, `LOCALIZATION_*.md`
- **Tienda**: `admin_shop_*.md`, `analisis_tienda_*.md`
- **Narrativa**: `Narrativo.md`, `ramificado.md`
- **Admin**: `admin_*.md`
- **Sistema**: `CRITICAL_*.md`, `*_IMPLEMENTATION.md`

### Por Tipo
- **Guías de Usuario**: `*_guide.md`
- **Features**: `*_feature.md`
- **Reportes**: `*_report.md`
- **Implementaciones**: `*_IMPLEMENTATION.md`

## 📅 Última Actualización

- **Mi Diván - Localización**: 2025-10-02
- **Organización de Docs**: 2025-10-02
