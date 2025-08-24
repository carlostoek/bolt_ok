# Diagrama de Flujo: Dinámica Lucien-Diana

Este documento complementa el Plan de Implementación principal y presenta los flujos de interacción clave entre el usuario, Lucien y Diana.

## 1. Flujo de Solicitud de Acceso al Canal

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Usuario     │     │  Sistema     │     │    Lucien    │     │    Diana     │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │                    │
       │  Solicita acceso   │                    │                    │
       │ ─────────────────> │                    │                    │
       │                    │                    │                    │
       │                    │  Programa mensajes │                    │
       │                    │ ─────────────────> │                    │
       │                    │                    │                    │
       │                    │                    │                    │
       │                    │                    │                    │
       │                    │ Después de 5 min   │                    │
       │                    │ ─────────────────> │                    │
       │                    │                    │                    │
       │                    │                    │  Saludo formal     │
       │                    │                    │ ─────────────────> │
       │  Mensaje Lucien    │                    │                    │
       │ <───────────────────────────────────────                    │
       │                    │                    │                    │
       │  Reacciona al      │                    │                    │
       │  canal/mensaje     │                    │                    │
       │ ─────────────────────────────────────> │                    │
       │                    │                    │                    │
       │                    │                    │  Evalúa reacción   │
       │                    │                    │ ─────────────────> │
       │                    │                    │                    │
       │                    │                    │ Si reacción notable│
       │                    │                    │ ─────────────────────────────>
       │                    │                    │                    │
       │                    │                    │                    │ Aparición breve
       │                    │                    │                    │ ───────────>
       │  Mensaje Diana     │                    │                    │
       │ <───────────────────────────────────────────────────────────
       │                    │                    │                    │
       │                    │                    │  Regresa y explica │
       │                    │                    │ ─────────────────> │
       │  Explicación Lucien│                    │                    │
       │ <───────────────────────────────────────                    │
       │                    │                    │                    │
       │                    │ Después de 15 min  │                    │
       │                    │ ─────────────────────────────>         │
       │  Acceso concedido  │                    │                    │
       │ <───────────────────────────────────────                    │
       │                    │                    │                    │
```

## 2. Flujo de Desafío de Observación de Lucien

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Usuario     │     │CoordinadorC. │     │    Lucien    │     │    Diana     │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │                    │
       │  Interactúa con    │                    │                    │
       │  fragmento/canal   │                    │                    │
       │ ─────────────────> │                    │                    │
       │                    │                    │                    │
       │                    │  Determina desafío │                    │
       │                    │ ─────────────────> │                    │
       │                    │                    │                    │
       │                    │                    │  Crea desafío      │
       │                    │                    │ ─────────────────> │
       │                    │                    │                    │
       │                    │ <───────────────── │                    │
       │                    │                    │                    │
       │  Recibe desafío    │                    │                    │
       │ <───────────────── │                    │                    │
       │                    │                    │                    │
       │  Responde al       │                    │                    │
       │  desafío           │                    │                    │
       │ ─────────────────> │                    │                    │
       │                    │                    │                    │
       │                    │  Evalúa respuesta  │                    │
       │                    │ ─────────────────> │                    │
       │                    │                    │                    │
       │                    │                    │  Respuesta formal  │
       │                    │                    │ ─────────────────> │
       │                    │                    │                    │
       │  Recibe evaluación │                    │                    │
       │ <───────────────────────────────────────                    │
       │                    │                    │                    │
       │                    │                    │  Si respuesta      │
       │                    │                    │  excepcional       │
       │                    │                    │ ─────────────────────────────>
       │                    │                    │                    │
       │                    │                    │                    │ Aparición breve
       │  Mensaje Diana     │                    │                    │ de reconocimiento
       │ <───────────────────────────────────────────────────────────
       │                    │                    │                    │
       │                    │                    │  Explica aparición │
       │                    │                    │ ─────────────────> │
       │  Explicación Lucien│                    │                    │
       │ <───────────────────────────────────────                    │
```

## 3. Flujo de Fragmentos Narrativos Cuánticos

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Usuario     │     │QuantumService│     │    Lucien    │     │    Diana     │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │                    │
       │  Toma decisión     │                    │                    │
       │  significativa     │                    │                    │
       │ ─────────────────> │                    │                    │
       │                    │                    │                    │
       │                    │  Procesa decisión  │                    │
       │                    │ ─────────────────> │                    │
       │                    │                    │                    │
       │                    │  Busca fragmentos  │                    │
       │                    │  afectados         │                    │
       │                    │ ─────────────────> │                    │
       │                    │                    │                    │
       │                    │  Modifica percep-  │                    │
       │                    │  ción de fragmentos│                    │
       │                    │  pasados           │                    │
       │                    │ ─────────────────> │                    │
       │                    │                    │                    │
       │                    │                    │  Explica cambios   │
       │                    │                    │  en la narrativa   │
       │                    │                    │ ─────────────────> │
       │                    │                    │                    │
       │  Notificación de   │                    │                    │
       │  cambios narrativos│                    │                    │
       │ <───────────────────────────────────────                    │
       │                    │                    │                    │
       │  Revisa fragmentos │                    │                    │
       │  alterados         │                    │                    │
       │ ─────────────────> │                    │                    │
       │                    │                    │                    │
       │                    │  Solicita nuevas   │                    │
       │                    │  versiones         │                    │
       │                    │ ─────────────────────────────>         │
       │                    │                    │                    │
       │                    │                    │                    │ Proporciona nueva
       │                    │                    │                    │ versión con más
       │                    │                    │                    │ revelaciones
       │                    │ <───────────────────────────────────────
       │                    │                    │                    │
       │  Recibe fragmentos │                    │                    │
       │  con más contexto  │                    │                    │
       │ <───────────────── │                    │                    │
```

## 4. Flujo de Apariciones Temporales de Diana

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Usuario     │     │TemporalService│    │    Lucien    │     │    Diana     │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │                    │
       │  Interactúa en     │                    │                    │
       │  horario específico│                    │                    │
       │ ─────────────────> │                    │                    │
       │                    │                    │                    │
       │                    │  Verifica momento  │                    │
       │                    │  temporal          │                    │
       │                    │ ─────────────────> │                    │
       │                    │                    │                    │
       │                    │                    │  Prepara momento   │
       │                    │                    │  especial          │
       │                    │                    │ ─────────────────> │
       │                    │                    │                    │
       │  Notificación de   │                    │                    │
       │  momento especial  │                    │                    │
       │ <───────────────────────────────────────                    │
       │                    │                    │                    │
       │  Accede al momento │                    │                    │
       │  temporal          │                    │                    │
       │ ─────────────────> │                    │                    │
       │                    │                    │                    │
       │                    │  Solicita aparición│                    │
       │                    │ ─────────────────────────────>         │
       │                    │                    │                    │
       │                    │                    │                    │ Aparición temporal
       │                    │                    │                    │ más extensa
       │  Interacción con   │                    │                    │
       │  Diana temporal    │                    │                    │
       │ <───────────────────────────────────────────────────────────
       │                    │                    │                    │
       │  Responde a Diana  │                    │                    │
       │ ─────────────────────────────────────────────────────────> │
       │                    │                    │                    │
       │                    │                    │                    │ Respuesta final
       │  Respuesta final   │                    │                    │ antes de partir
       │ <───────────────────────────────────────────────────────────
       │                    │                    │                    │
       │                    │                    │  Retoma y          │
       │                    │                    │  contextualiza     │
       │                    │                    │ ─────────────────> │
       │                    │                    │                    │
       │  Contextualización │                    │                    │
       │  de Lucien         │                    │                    │
       │ <───────────────────────────────────────                    │
```

## 5. Flujo de Progresión de Confianza y Nivel VIP

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Usuario     │     │CoordinadorC. │     │    Lucien    │     │    Diana     │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │                    │
       │  Múltiples         │                    │                    │
       │  interacciones     │                    │                    │
       │  positivas         │                    │                    │
       │ ─────────────────> │                    │                    │
       │                    │                    │                    │
       │                    │  Actualiza nivel   │                    │
       │                    │  de confianza      │                    │
       │                    │ ─────────────────> │                    │
       │                    │                    │                    │
       │                    │                    │  Alcanza umbral    │
       │                    │                    │  de confianza      │
       │                    │                    │ ─────────────────> │
       │                    │                    │                    │
       │                    │                    │  Notifica          │
       │                    │                    │  elegibilidad VIP  │
       │                    │                    │ ─────────────────> │
       │                    │                    │                    │
       │  Notificación de   │                    │                    │
       │  elegibilidad VIP  │                    │                    │
       │ <───────────────────────────────────────                    │
       │                    │                    │                    │
       │  Activa            │                    │                    │
       │  suscripción VIP   │                    │                    │
       │ ─────────────────> │                    │                    │
       │                    │                    │                    │
       │                    │  Actualiza estado  │                    │
       │                    │  a VIP             │                    │
       │                    │ ─────────────────> │                    │
       │                    │                    │                    │
       │                    │                    │  Presenta invitación│
       │                    │                    │  formal a El Diván │
       │                    │                    │ ─────────────────> │
       │                    │                    │                    │
       │  Invitación formal │                    │                    │
       │  a El Diván        │                    │                    │
       │ <───────────────────────────────────────                    │
       │                    │                    │                    │
       │  Acepta invitación │                    │                    │
       │ ─────────────────> │                    │                    │
       │                    │                    │                    │
       │                    │  Otorga acceso a   │                    │
       │                    │  canal VIP         │                    │
       │                    │ ─────────────────> │                    │
       │                    │                    │                    │
       │                    │                    │                    │ Primera aparición
       │                    │                    │                    │ extendida en VIP
       │  Bienvenida Diana  │                    │                    │
       │  en El Diván       │                    │                    │
       │ <───────────────────────────────────────────────────────────
       │                    │                    │                    │
       │                    │                    │  Explica nuevas    │
       │                    │                    │  dinámicas VIP     │
       │                    │                    │ ─────────────────> │
       │                    │                    │                    │
       │  Explicación de    │                    │                    │
       │  dinámicas VIP     │                    │                    │
       │ <───────────────────────────────────────                    │
```

## Notas Importantes

1. **Transiciones Fluidas**: En todos los flujos, las transiciones entre Lucien y Diana deben ser fluidas pero claramente diferenciadas. Lucien siempre introduce y contextualiza las apariciones de Diana.

2. **Estado de Confianza**: El nivel de confianza con Lucien es el principal determinante de la frecuencia e intensidad de las apariciones de Diana.

3. **Progresión Narrativa**: Conforme avanza el nivel narrativo, las explicaciones de Lucien revelan más sobre la relación entre él y Diana.

4. **Momentos Temporales**: Los momentos temporales son especialmente importantes para crear sentido de exclusividad y urgencia en la narrativa.

5. **Desafíos Observacionales**: Los desafíos de Lucien funcionan como mecanismo de evaluación y filtro para determinar quién es "digno" de la atención de Diana.

Este diagrama de flujo complementa el plan de implementación y proporciona una visualización de las interacciones clave que constituyen la experiencia del "Mayordomo del Diván".