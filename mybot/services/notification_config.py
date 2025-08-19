from dataclasses import dataclass
from typing import Dict, Optional
import json
import os

@dataclass
class NotificationConfig:
    """Configuración del sistema de notificaciones."""
    
    # Delays de agregación por prioridad (en segundos)
    aggregation_delays: Dict[int, float] = None
    
    # Tamaño máximo de cola antes de forzar envío
    max_queue_size: int = 10
    
    # Tiempo para mantener hashes de duplicados (segundos)
    duplicate_window: int = 60
    
    # Habilitar/deshabilitar agregación
    enable_aggregation: bool = True
    
    # Tiempo máximo de espera para cualquier notificación
    max_wait_time: float = 2.0
    
    # Configuración de formato de mensajes
    message_format: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.aggregation_delays is None:
            self.aggregation_delays = {
                0: 0.1,   # CRITICAL
                1: 0.5,   # HIGH
                2: 1.0,   # MEDIUM
                3: 1.5    # LOW
            }
        
        if self.message_format is None:
            self.message_format = {
                "use_emojis": True,
                "use_markdown": True,
                "show_totals": True,
                "show_progress_bars": False,
                "group_similar": True,
                "diana_personality": True
            }
    
    @classmethod
    def from_file(cls, filepath: str) -> 'NotificationConfig':
        """Carga configuración desde archivo JSON."""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return cls(**data)
        return cls()
    
    def save_to_file(self, filepath: str) -> None:
        """Guarda configuración en archivo JSON."""
        data = {
            'aggregation_delays': self.aggregation_delays,
            'max_queue_size': self.max_queue_size,
            'duplicate_window': self.duplicate_window,
            'enable_aggregation': self.enable_aggregation,
            'max_wait_time': self.max_wait_time,
            'message_format': self.message_format
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

# Configuración global
_config: Optional[NotificationConfig] = None

def get_notification_config() -> NotificationConfig:
    """Obtiene la configuración global de notificaciones."""
    global _config
    if _config is None:
        config_path = os.environ.get(
            'NOTIFICATION_CONFIG_PATH', 
            'config/notifications.json'
        )
        _config = NotificationConfig.from_file(config_path)
    return _config

def set_notification_config(config: NotificationConfig) -> None:
    """Establece la configuración global de notificaciones."""
    global _config
    _config = config