# 🎨 Arquitectura del Editor Web de Narrativa

## 📋 Resumen

Editor visual basado en React + React Flow para gestionar la narrativa completa del bot mediante un archivo JSON.

---

## 🏗️ Stack Tecnológico

```yaml
Frontend:
  Framework: React 18 + TypeScript
  Build Tool: Vite
  Editor Visual: React Flow (https://reactflow.dev/)
  UI Components: shadcn/ui + Tailwind CSS
  Estado Global: Zustand
  File System: File System Access API (browser nativo)

Despliegue:
  Host: Vercel/Netlify (archivos estáticos)
  Costo: GRATIS
```

---

## 🎯 Funcionalidades Principales

### 1. **Gestión de Archivos**
- ✅ Abrir `narrative_complete.json` desde el sistema local
- ✅ Guardar cambios directamente al archivo
- ✅ Auto-save opcional cada X minutos
- ✅ Validación JSON en tiempo real

### 2. **Canvas Visual (React Flow)**
- ✅ Nodos de fragmentos narrativos
- ✅ Nodos de productos de tienda
- ✅ Nodos de pistas (lore pieces)
- ✅ Conexiones visuales (decisiones)
- ✅ Drag & drop
- ✅ Zoom/Pan
- ✅ Mini-map de navegación

### 3. **Panel de Propiedades**
- ✅ Editar fragmento seleccionado
- ✅ Gestionar decisiones
- ✅ Configurar condiciones (besitos, rol)
- ✅ Vincular productos/pistas
- ✅ Preview del texto

### 4. **Validación y Análisis**
- ✅ Detectar fragmentos huérfanos
- ✅ Detectar referencias rotas
- ✅ Validar combinaciones de pistas
- ✅ Reportar estadísticas

---

## 📁 Estructura del Proyecto

```
narrative-editor/
├── public/
│   └── vite.svg
│
├── src/
│   ├── components/
│   │   ├── Editor/
│   │   │   ├── Canvas.tsx              # React Flow canvas principal
│   │   │   ├── FragmentNode.tsx        # Nodo de fragmento
│   │   │   ├── ShopNode.tsx            # Nodo de producto
│   │   │   ├── LoreNode.tsx            # Nodo de pista
│   │   │   ├── DecisionEdge.tsx        # Arista personalizada
│   │   │   └── Toolbar.tsx             # Barra de herramientas
│   │   │
│   │   ├── Panels/
│   │   │   ├── PropertiesPanel.tsx     # Inspector de propiedades
│   │   │   ├── ValidationPanel.tsx     # Panel de validación
│   │   │   └── StatsPanel.tsx          # Estadísticas
│   │   │
│   │   ├── Dialogs/
│   │   │   ├── FragmentDialog.tsx      # Crear/editar fragmento
│   │   │   ├── ShopItemDialog.tsx      # Crear/editar producto
│   │   │   └── LoreDialog.tsx          # Crear/editar pista
│   │   │
│   │   └── ui/                         # shadcn/ui components
│   │       ├── button.tsx
│   │       ├── input.tsx
│   │       ├── dialog.tsx
│   │       └── ...
│   │
│   ├── stores/
│   │   └── narrativeStore.ts           # Zustand store
│   │
│   ├── types/
│   │   └── narrative.ts                # TypeScript types
│   │
│   ├── utils/
│   │   ├── fileSystem.ts               # File System Access API
│   │   ├── validation.ts               # JSON validation
│   │   └── graphLayout.ts              # Auto-layout algorithms
│   │
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
│
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

---

## 🎨 Diseño de UI

### Layout Principal

```
┌───────────────────────────────────────────────────────────┐
│ Header: [Logo] [Abrir JSON] [Guardar] [Validar] [Stats] │
├─────────────────────────┬─────────────────────────────────┤
│                         │                                 │
│                         │                                 │
│                         │     Properties Panel            │
│                         │     ┌─────────────────────┐     │
│      Canvas             │     │ Fragment Details    │     │
│      (React Flow)       │     │ ├ Key: start        │     │
│                         │     │ ├ Text: ...         │     │
│      [Nodes & Edges]    │     │ ├ Character: Lucien │     │
│                         │     │ ├ Level: 1          │     │
│                         │     │ └ Choices: [+]      │     │
│                         │     └─────────────────────┘     │
│                         │                                 │
└─────────────────────────┴─────────────────────────────────┘
```

### Tipos de Nodos

#### **1. Fragment Node**
```typescript
{
  id: "start",
  type: "fragment",
  data: {
    key: "start",
    text: "🎩 **Lucien:** Bienvenido...",
    character: "Lucien",
    level: 1,
    conditions: ["0 besitos"],
    reward: "+5 besitos"
  },
  position: { x: 250, y: 0 },
  style: {
    background: character === "Lucien" ? "#1e3a8a" : "#ec4899",
    color: "white",
    borderRadius: "8px"
  }
}
```

#### **2. Shop Node**
```typescript
{
  id: "shop_diary",
  type: "shop",
  data: {
    name: "📓 Diario Íntimo",
    price: 30,
    unlocks_fragment: "diana_diary",
    unlocks_lore: null
  },
  position: { x: 500, y: 200 },
  style: {
    background: "#10b981",
    color: "white"
  }
}
```

#### **3. Lore Node**
```typescript
{
  id: "lore_jardin_1",
  type: "lore",
  data: {
    code_name: "pista_jardin_1",
    title: "El Secreto del Jardín",
    category: "jardin_secreto"
  },
  position: { x: 800, y: 300 },
  style: {
    background: "#f59e0b",
    color: "white"
  }
}
```

### Edges (Decisiones)

```typescript
{
  id: "e-start-intro_1",
  source: "start",
  target: "intro_1",
  label: "Estoy listo",
  type: "smoothstep",
  animated: false,
  style: {
    stroke: "#64748b",
    strokeWidth: 2
  },
  data: {
    required_besitos: 0,
    required_role: null
  }
}
```

---

## 💾 Gestión de Estado (Zustand)

```typescript
// stores/narrativeStore.ts
interface NarrativeStore {
  // Data
  narrative: NarrativeConfig | null;
  selectedNode: string | null;

  // File handling
  fileHandle: FileSystemFileHandle | null;
  isDirty: boolean;

  // Actions
  loadNarrative: (json: NarrativeConfig) => void;
  saveNarrative: () => Promise<void>;

  // Fragment operations
  addFragment: (fragment: StoryFragment) => void;
  updateFragment: (key: string, data: Partial<StoryFragment>) => void;
  deleteFragment: (key: string) => void;

  // Choice operations
  addChoice: (fragmentKey: string, choice: NarrativeChoice) => void;
  updateChoice: (fragmentKey: string, index: number, choice: NarrativeChoice) => void;
  deleteChoice: (fragmentKey: string, index: number) => void;

  // Shop operations
  addShopItem: (item: ShopItem) => void;
  updateShopItem: (name: string, item: Partial<ShopItem>) => void;
  deleteShopItem: (name: string) => void;

  // Lore operations
  addLorePiece: (lore: LorePiece) => void;
  updateLorePiece: (code: string, lore: Partial<LorePiece>) => void;
  deleteLorePiece: (code: string) => void;

  // Validation
  validate: () => ValidationResult;
}
```

---

## 🔧 File System Access API

```typescript
// utils/fileSystem.ts

export async function openFile(): Promise<{
  handle: FileSystemFileHandle;
  content: string;
}> {
  const [handle] = await window.showOpenFilePicker({
    types: [
      {
        description: 'JSON Files',
        accept: { 'application/json': ['.json'] }
      }
    ]
  });

  const file = await handle.getFile();
  const content = await file.text();

  return { handle, content };
}

export async function saveFile(
  handle: FileSystemFileHandle,
  content: string
): Promise<void> {
  const writable = await handle.createWritable();
  await writable.write(content);
  await writable.close();
}
```

---

## ✅ Validación

```typescript
// utils/validation.ts

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

export interface ValidationError {
  type: 'missing_fragment' | 'broken_reference' | 'duplicate_key';
  message: string;
  location: string;
}

export function validateNarrative(data: NarrativeConfig): ValidationResult {
  const errors: ValidationError[] = [];
  const warnings: ValidationWarning[] = [];

  // Check for orphaned fragments
  const referencedFragments = new Set<string>();
  data.fragments.forEach(f => {
    f.choices?.forEach(c => {
      referencedFragments.add(c.destination_fragment_key);
    });
  });

  const fragmentKeys = new Set(data.fragments.map(f => f.key));

  referencedFragments.forEach(ref => {
    if (!fragmentKeys.has(ref)) {
      errors.push({
        type: 'missing_fragment',
        message: `Referenced fragment "${ref}" does not exist`,
        location: 'fragments'
      });
    }
  });

  // Check shop item references
  data.shop_items?.forEach(item => {
    if (item.unlocks_fragment_key && !fragmentKeys.has(item.unlocks_fragment_key)) {
      errors.push({
        type: 'broken_reference',
        message: `Shop item "${item.name}" references non-existent fragment "${item.unlocks_fragment_key}"`,
        location: 'shop_items'
      });
    }
  });

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
}
```

---

## 🚀 Flujo de Trabajo

### 1. **Abrir Archivo**
```
Usuario → Click "Abrir JSON"
       → File System API
       → Parse JSON
       → Cargar en Zustand
       → Renderizar Canvas
```

### 2. **Editar Fragmento**
```
Usuario → Click en nodo
       → Abrir Properties Panel
       → Editar campos
       → Auto-update Zustand
       → Marcar como "dirty"
```

### 3. **Guardar Cambios**
```
Usuario → Click "Guardar"
       → Validar JSON
       → Si válido → File System API write
       → Marcar como "saved"
```

### 4. **Aplicar al Bot**
```
Admin → Guarda JSON
      → Git commit (opcional)
      → En servidor: /reload_narrative
      → Bot carga nueva narrativa
```

---

## 📊 Estadísticas y Análisis

El panel de estadísticas muestra:

- **Fragmentos totales**: X
- **Decisiones totales**: Y
- **Fragmentos huérfanos**: Z (sin conexiones entrantes)
- **Referencias rotas**: W
- **Productos de tienda**: A
- **Pistas**: B
- **Combinaciones**: C
- **Fragmentos por personaje**:
  - Lucien: X
  - Diana: Y
- **Fragmentos por nivel**:
  - Nivel 1: X
  - Nivel 2: Y
  - etc.

---

## 🎯 Próximos Pasos

1. ✅ Setup inicial del proyecto React + Vite
2. ✅ Configurar Tailwind + shadcn/ui
3. ✅ Implementar File System Access API
4. ✅ Crear tipos TypeScript desde el schema
5. ✅ Implementar Zustand store
6. ✅ Crear Canvas con React Flow
7. ✅ Crear tipos de nodos personalizados
8. ✅ Implementar Properties Panel
9. ✅ Implementar sistema de validación
10. ✅ Deploy en Vercel

---

## 🔗 Referencias

- [React Flow Docs](https://reactflow.dev/learn)
- [File System Access API](https://developer.mozilla.org/en-US/docs/Web/API/File_System_Access_API)
- [Zustand Docs](https://zustand-demo.pmnd.rs/)
- [shadcn/ui](https://ui.shadcn.com/)
