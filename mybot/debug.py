import os
import json
from pathlib import Path

def debug_narrative_loading():
    # 1. Verificar acceso a los archivos
    fragments_dir = Path("mybot/narrative_fragments")
    print(f"\n📂 Contenido del directorio ({fragments_dir}):")
    for file in fragments_dir.glob("*.json"):
        print(f" - {file.name} (Última modificación: {file.stat().st_mtime})")

    # 2. Leer y comparar contenido de un archivo específico
    test_file = fragments_dir / "welcome.json"
    print(f"\n🔍 Contenido de {test_file.name}:")
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            content = json.load(f)
            print(json.dumps(content, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Error leyendo archivo: {e}")

    # 3. Verificar posibles fuentes alternativas
    print("\n🕵️ Posibles fuentes alternativas:")
    possible_sources = [
        "/tmp/narrative_cache",
        "~/.botmaestro/narrative",
        "./.cache/narrative"
    ]
    for source in possible_sources:
        expanded = Path(source).expanduser()
        if expanded.exists():
            print(f"⚠️ Se encontró fuente alternativa: {expanded}")

if __name__ == "__main__":
    debug_narrative_loading()
  
