"""
Script de prueba solo para JWT (sin bcrypt).
"""
from app.core.security import (
    create_admin_token,
    verify_token,
    validate_admin_role
)


def test_jwt_tokens():
    """Prueba la creación y verificación de tokens JWT."""
    print("🔑 Probando tokens JWT...")
    
    # Crear token
    token = create_admin_token(
        user_id="100000000",
        username="superadmin",
        email="superadmin@example.com",
        role="super_admin"
    )
    
    print(f"Token creado: {token[:50]}...")
    
    # Verificar token
    try:
        token_data = verify_token(token)
        print(f"Token verificado exitosamente:")
        print(f"  - User ID: {token_data['user_id']}")
        print(f"  - Role: {token_data['role']}")
        print(f"  - Username: {token_data['username']}")
        print(f"  - Email: {token_data['email']}")
    except Exception as e:
        print(f"Error verificando token: {e}")
    
    print()


def test_role_validation():
    """Prueba la validación de roles."""
    print("👥 Probando validación de roles...")
    
    # Casos de prueba
    test_cases = [
        ("super_admin", ["super_admin"], True),
        ("super_admin", ["admin"], True),
        ("super_admin", ["user"], True),
        ("admin", ["super_admin"], False),
        ("admin", ["admin"], True),
        ("admin", ["user"], True),
        ("user", ["super_admin"], False),
        ("user", ["admin"], False),
        ("user", ["user"], True),
    ]
    
    for current_role, required_roles, expected in test_cases:
        result = validate_admin_role(current_role, required_roles)
        status = "✅" if result == expected else "❌"
        print(f"{status} {current_role} -> {required_roles}: {result} (esperado: {expected})")
    
    print()


def main():
    """Función principal."""
    print("="*60)
    print("🔒 PRUEBA DEL SISTEMA JWT")
    print("="*60)
    print()
    
    test_jwt_tokens()
    test_role_validation()
    
    print("="*60)
    print("✅ Pruebas completadas")
    print("="*60)


if __name__ == "__main__":
    main()