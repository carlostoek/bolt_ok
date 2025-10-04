from utils.config import ADMIN_IDS

async def is_admin(user_id: int, session=None) -> bool:
    """Verifica si un usuario es administrador basado en ADMIN_IDS del config"""
    return user_id in ADMIN_IDS
