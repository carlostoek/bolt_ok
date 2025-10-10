# Script de Gestión de Usuarios y Narrativa

Este script unificado (`manage_users.py`) combina y mejora las funcionalidades de gestión de usuarios y narrativa que anteriormente estaban en scripts separados.

## 🎯 Funcionalidades

El script ofrece 6 operaciones principales:

### 1️⃣ Ver información de un usuario
Muestra información completa de un usuario específico:
- Datos básicos (username, nombre, puntos, nivel, rol)
- Misiones completadas
- Compras realizadas
- Fragmentos narrativos desbloqueados
- Progreso narrativo actual

### 2️⃣ Reiniciar progreso narrativo de un usuario
Reinicia **únicamente** el progreso narrativo de un usuario específico:
- ✅ Elimina: Estado narrativo (fragmento actual, fragmentos visitados, decisiones tomadas)
- ✅ Mantiene: Usuario, puntos, nivel, misiones, compras, etc.
- El usuario comenzará desde el inicio cuando acceda a `/historia`

### 3️⃣ Reiniciar progreso narrativo de TODOS los usuarios
Reinicia el progreso narrativo de **todos** los usuarios del sistema:
- Útil después de hacer cambios mayores en la narrativa
- Todos los usuarios comenzarán desde el inicio
- Mantiene todos los demás datos de usuarios intactos

### 4️⃣ Eliminar usuario completamente
Elimina un usuario y **todos** sus datos relacionados:
- ⚠️ **OPERACIÓN IRREVERSIBLE**
- Elimina: Usuario, progreso narrativo, misiones, compras, logros, etc.
- Elimina completamente el usuario del sistema

### 5️⃣ Limpiar TODOS los fragmentos narrativos (cambio de narrativa)
**🆕 Nueva funcionalidad** - Limpia completamente la narrativa para permitir cambio de historia:
- Elimina **todos** los fragmentos narrativos (`story_fragments`)
- Elimina **todas** las decisiones narrativas (`narrative_choices`)
- Reinicia el progreso de **todos** los usuarios
- La base de datos queda lista para cargar una nueva narrativa

### 6️⃣ Ver estadísticas generales
Muestra estadísticas del sistema:
- Total de usuarios
- Usuarios con progreso narrativo
- Total de fragmentos narrativos en BD
- Total de decisiones narrativas en BD

## 📖 Uso

### Modo Interactivo (Recomendado)

```bash
python scripts/manage_users.py
```

Esto abrirá un menú interactivo donde puedes seleccionar la operación deseada.

### Modo Línea de Comandos

```bash
# Ver ayuda
python scripts/manage_users.py --help

# Ver información de un usuario
python scripts/manage_users.py --info 123456789

# Reiniciar progreso narrativo de un usuario
python scripts/manage_users.py --reset-narrative 123456789

# Eliminar usuario completamente
python scripts/manage_users.py --delete-user 123456789

# Limpiar todos los fragmentos narrativos
python scripts/manage_users.py --clear-fragments

# Ver estadísticas generales
python scripts/manage_users.py --stats
```

## 🔄 Flujo para Cambio de Narrativa

Cuando necesites cambiar completamente de narrativa:

1. **Respalda tu narrativa actual** (opcional pero recomendado)
   ```bash
   # Exportar narrativa actual si es necesario
   python scripts/export_narrative.py
   ```

2. **Limpia los fragmentos actuales**
   ```bash
   python scripts/manage_users.py --clear-fragments
   ```
   - Esto eliminará todos los fragmentos narrativos
   - Reiniciará el progreso de todos los usuarios
   - La BD quedará lista para la nueva narrativa

3. **Carga la nueva narrativa**
   ```bash
   python scripts/load_narrative.py nueva_narrativa.json
   ```

4. **Verifica la carga**
   ```bash
   python scripts/manage_users.py --stats
   ```

## ⚠️ Advertencias de Seguridad

### Operaciones Peligrosas

Las siguientes operaciones requieren confirmación explícita:

- **Eliminar usuario**: Debes escribir `ELIMINAR` para confirmar
- **Reiniciar todos los usuarios**: Debes escribir `SI TODOS` para confirmar
- **Limpiar fragmentos**: Debes escribir `LIMPIAR TODO` para confirmar

Estas confirmaciones previenen eliminaciones accidentales.

## 📊 Comparación con Scripts Anteriores

| Script Anterior | Funcionalidad | Nuevo Script |
|----------------|---------------|--------------|
| `reset_narrative_progress.py` | Reiniciar progreso narrativo | ✅ Incluido (opciones 2 y 3) |
| `delete_user.py` | Eliminar usuarios | ✅ Incluido (opción 4) |
| N/A | Limpiar fragmentos narrativos | 🆕 **Nueva funcionalidad** (opción 5) |
| N/A | Ver info de usuario | 🆕 **Nueva funcionalidad** (opción 1) |
| N/A | Estadísticas generales | 🆕 **Nueva funcionalidad** (opción 6) |

## 🔧 Mantenimiento

### Scripts Obsoletos

Los siguientes scripts pueden ser marcados como obsoletos ya que su funcionalidad está integrada:

- `migrations/reset_narrative_progress.py` → Usar `manage_users.py` opciones 2 y 3
- `scripts/delete_user.py` → Usar `manage_users.py` opción 4

**No elimines** los scripts antiguos inmediatamente. Márcalos como obsoletos y mantén referencias por si necesitas alguna funcionalidad específica.

## 🐛 Troubleshooting

### Error: "BOT_TOKEN environment variable is not set"

El script requiere que las variables de entorno estén configuradas. Asegúrate de que:
- El archivo `.env` existe en el directorio raíz
- Contiene las variables necesarias (BOT_TOKEN, DATABASE_URL, etc.)

### Error al conectar a la base de datos

Verifica que:
- La base de datos esté en ejecución
- La variable `DATABASE_URL` en `.env` sea correcta
- Tengas permisos para acceder a la base de datos

## 📝 Notas Adicionales

- **Backups**: Siempre considera hacer backups antes de operaciones destructivas
- **Testing**: Prueba primero en un entorno de desarrollo
- **Logs**: El script genera logs detallados de todas las operaciones
- **Atomicidad**: Todas las operaciones son transaccionales (rollback en caso de error)

## 🆕 Changelog

### v1.0.0 (2024-10-10)
- ✨ Script unificado que integra todas las funcionalidades de gestión
- ✨ Nueva función: Limpiar todos los fragmentos narrativos
- ✨ Nueva función: Ver información completa de usuario
- ✨ Nueva función: Estadísticas generales del sistema
- ✨ Modo interactivo mejorado con menú de opciones
- ✨ Confirmaciones de seguridad para operaciones destructivas
- 📚 Documentación completa
