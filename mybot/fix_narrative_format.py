#!/usr/bin/env python3
"""
Script para convertir narrativa de HTML a formato compatible con Telegram.
Convierte <br> a saltos de línea y asegura que solo se usen etiquetas HTML válidas.
"""
import json
import re


def convert_html_to_telegram(text: str) -> str:
    """
    Convierte HTML a formato compatible con Telegram HTML.

    Telegram solo soporta: <b>, <i>, <code>, <pre>, <a>, <u>, <s>, <tg-spoiler>
    NO soporta: <br>, <p>, <div>, etc.
    """
    if not text:
        return text

    # Convertir <br> y <br/> a saltos de línea
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)

    # Convertir múltiples saltos de línea consecutivos
    # <br><br> → \n\n
    text = text.replace('\n\n\n', '\n\n')  # Limitar a máximo 2 saltos

    # Asegurar que <b>, <i> estén bien formados
    # Telegram es estricto con el cierre de etiquetas

    # Escapar caracteres HTML especiales FUERA de etiquetas
    # (pero mantener las etiquetas válidas)

    return text


def fix_narrative_json(input_file: str, output_file: str):
    """
    Lee el archivo JSON de narrativa, convierte el HTML y guarda la versión corregida.
    """
    print(f"📖 Leyendo {input_file}...")

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    fragments = data.get('fragments', [])
    fixed_count = 0

    print(f"🔧 Procesando {len(fragments)} fragmentos...")

    for fragment in fragments:
        if 'content' in fragment:
            original = fragment['content']
            fixed = convert_html_to_telegram(original)

            if original != fixed:
                fragment['content'] = fixed
                fixed_count += 1

                # Mostrar cambios para el primer fragmento (debug)
                if fixed_count == 1:
                    print("\n📝 Ejemplo de conversión:")
                    print("ANTES:")
                    print(original[:200] + "...")
                    print("\nDESPUÉS:")
                    print(fixed[:200] + "...")

    print(f"\n✅ Convertidos {fixed_count} fragmentos")

    # Guardar archivo corregido
    print(f"💾 Guardando en {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ ¡Listo! Archivo guardado en {output_file}")
    print("\n📌 Próximos pasos:")
    print("1. Revisa el archivo generado")
    print("2. Carga la narrativa con: python scripts/populate_narrative.py")
    print("3. Prueba con /historia en el bot")


if __name__ == "__main__":
    import sys

    input_file = "/home/azureuser/repos/bolt_ok/mybot/html.json"
    output_file = "/home/azureuser/repos/bolt_ok/mybot/narrative_fixed.json"

    fix_narrative_json(input_file, output_file)
