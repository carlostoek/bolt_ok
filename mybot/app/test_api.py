"""
Script de prueba rápida de la API.

Ejecutar desde la carpeta app/:
    python test_api.py

Nota: Requiere que el servidor FastAPI esté corriendo.
"""
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"


async def test_health_check():
    """Test del health check."""
    print("\n" + "="*70)
    print("TEST 1: Health Check")
    print("="*70)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200


async def test_create_fragment_nested():
    """Test de creación de fragmento con nested entities."""
    print("\n" + "="*70)
    print("TEST 2: Create Fragment with Nested Creation")
    print("="*70)

    payload = {
        "key": "CAP_FINAL_TEST",
        "text": "Entrada al castillo oscuro. Las puertas crujen mientras te adentras en la penumbra...",
        "min_besitos": 0,
        "reward_besitos": 50,

        "unlock_product": {
            "name": "Llave Maestra Test",
            "description": "Desbloquea el capítulo final",
            "price": 100,
            "is_vip_only": False
        },

        "choices": [
            {
                "text": "Entrar al salón del trono",
                "destination_fragment": {
                    "key": "SALON_TRONO_TEST",
                    "text": "El rey te espera sentado en su trono de hierro. Sus ojos brillan con una luz sobrenatural.",
                    "reward_besitos": 20
                },
                "required_besitos": 0
            }
        ]
    }

    print(f"\nPayload enviado:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/narrative/fragments",
            json=payload
        )

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 201:
            result = response.json()
            print("\n✅ ÉXITO - Fragmento creado:")
            print(f"  • Fragmento principal: {result['fragment']['key']} (ID: {result['fragment']['id']})")

            if result['created_product']:
                print(f"  • Producto creado: {result['created_product']['name']} (ID: {result['created_product']['id']})")

            print(f"  • Decisiones creadas: {len(result['created_choices'])}")
            for choice in result['created_choices']:
                print(f"    - '{choice['text']}' → {choice['destination']}")

            print(f"\nResumen:")
            print(f"  • Total fragmentos: {result['summary']['fragments_created']}")
            print(f"  • Total productos: {result['summary']['products_created']}")
            print(f"  • Total decisiones: {result['summary']['choices_created']}")

            return result['fragment']['key']
        else:
            print(f"❌ ERROR: {response.text}")
            return None


async def test_get_fragment(key: str):
    """Test de obtención de fragmento."""
    print("\n" + "="*70)
    print(f"TEST 3: Get Fragment by Key '{key}'")
    print("="*70)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/narrative/fragments/{key}"
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            fragment = response.json()
            print("\n✅ Fragmento encontrado:")
            print(f"  • ID: {fragment['id']}")
            print(f"  • Key: {fragment['key']}")
            print(f"  • Text: {fragment['text'][:50]}...")
            print(f"  • Reward: {fragment['reward_besitos']} besitos")
            print(f"  • Decisiones: {len(fragment['choices'])}")
        else:
            print(f"❌ ERROR: {response.text}")


async def test_list_fragments():
    """Test de listado de fragmentos."""
    print("\n" + "="*70)
    print("TEST 4: List All Fragments")
    print("="*70)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/narrative/fragments?limit=10"
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            fragments = response.json()
            print(f"\n✅ Encontrados {len(fragments)} fragmentos:")
            for fragment in fragments:
                print(f"  • {fragment['key']} (ID: {fragment['id']}) - {len(fragment['choices'])} decisiones")
        else:
            print(f"❌ ERROR: {response.text}")


async def test_delete_fragment(key: str):
    """Test de eliminación de fragmento."""
    print("\n" + "="*70)
    print(f"TEST 5: Delete Fragment '{key}'")
    print("="*70)

    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{BASE_URL}/api/v1/narrative/fragments/{key}"
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 204:
            print("✅ Fragmento eliminado exitosamente")
        else:
            print(f"❌ ERROR: {response.text}")


async def main():
    """Ejecutar todos los tests."""
    print("\n" + "="*70)
    print("SUITE DE TESTS - Bot Admin Panel API")
    print("="*70)
    print("\nAsegúrate de que el servidor esté corriendo en http://localhost:8000")

    try:
        # Test 1: Health check
        await test_health_check()

        # Test 2: Crear fragmento con nested creation
        fragment_key = await test_create_fragment_nested()

        if fragment_key:
            # Test 3: Obtener fragmento
            await test_get_fragment(fragment_key)

            # Test 4: Listar fragmentos
            await test_list_fragments()

            # Test 5: Eliminar fragmento
            await test_delete_fragment(fragment_key)

            # Test 6: Verificar que fragmento destino también fue creado
            await test_get_fragment("SALON_TRONO_TEST")

            # Clean up fragmento destino
            await test_delete_fragment("SALON_TRONO_TEST")

        print("\n" + "="*70)
        print("✅ TODOS LOS TESTS COMPLETADOS")
        print("="*70 + "\n")

    except httpx.ConnectError:
        print("\n❌ ERROR: No se pudo conectar al servidor.")
        print("Asegúrate de que FastAPI esté corriendo:")
        print("  cd app && python main.py")
        print("  o")
        print("  uvicorn app.main:app --reload")

    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
