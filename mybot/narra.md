DianaBot Game & Narrative Framework (Python) — v1.0

-----------------------------------------------------------------------------

Este paquete define un motor de juego modular y un framework de narrativa

ramificada para integrarse en un bot de Telegram (DianaBot) vía Naboto.

Incluye:

- Persistencia (SQLite por defecto) con SQLAlchemy.

- Máquina de estados por usuario / por chat.

- DSL sencilla en YAML para narrativa (nodos, decisiones, condiciones, efectos).

- Sistema de gamificación: XP, niveles, logros, economía, inventario, cooldowns.

- Adaptador de Telegram (python-telegram-bot v20) desacoplado del core.

- Hooks y Eventos para extensión (misiones, narrativa dinámica, NPCs).

- Ejemplo de historia y ejemplo de ejecución del bot.

-----------------------------------------------------------------------------

┌───────────────────────────────────────────────────────────────────────────┐

│  ESTRUCTURA PROPUESTA DEL PROYECTO                                        │

└───────────────────────────────────────────────────────────────────────────┘



dianabot_engine/

init.py

config.py

storage.py

models.py

fsm.py

dsl.py

narrative.py

gameplay.py

economy.py

inventory.py

cooldowns.py

scheduler.py

telemetry.py

events.py

adapters/

telegram_adapter.py

examples/

stories/intro.yml

run_bot.py



NOTA: Este archivo consolida todos los módulos en un solo bloque para fácil

revisión. En producción, separa cada sección en su archivo correspondiente.

─────────────────────────────────────────────────────────────────────────────

init.py

─────────────────────────────────────────────────────────────────────────────

from future import annotations

all = [ "EngineConfig", "db_session", "Base", "User", "UserInventory", "Item", "Achievement", "UserAchievement", "EconomyTransaction", "Cooldown", "GameState", "FiniteStateMachine", "DSL", "Story", "StoryRunner", "Gameplay", "Economy", "Inventory", "Cooldowns", "EventBus", ]

─────────────────────────────────────────────────────────────────────────────

config.py

─────────────────────────────────────────────────────────────────────────────

import os from dataclasses import dataclass

@dataclass class EngineConfig: db_url: str = os.getenv("DIANABOT_DB_URL", "sqlite:///dianabot.db") echo_sql: bool = bool(int(os.getenv("DIANABOT_DB_ECHO", "0"))) # Telegram telegram_bot_token: str | None = os.getenv("TELEGRAM_BOT_TOKEN") # Economía / XP base_xp_per_choice: int = 5 level_curve_k: float = 1.7  # curva de niveles # Cooldowns default_cooldown_seconds: int = 30 # Narrativa autosave_on_step: bool = True

CFG = EngineConfig()

─────────────────────────────────────────────────────────────────────────────

storage.py + models.py

─────────────────────────────────────────────────────────────────────────────

from datetime import datetime from typing import Optional, Dict, Any from contextlib import contextmanager

from sqlalchemy import ( create_engine, Integer, String, DateTime, Boolean, ForeignKey, Float, JSON ) from sqlalchemy.orm import ( sessionmaker, DeclarativeBase, Mapped, mapped_column, relationship )

engine = create_engine(CFG.db_url, echo=CFG.echo_sql, future=True) Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase): pass

@contextmanager def db_session(): session = Session() try: yield session session.commit() except Exception: session.rollback() raise finally: session.close()

class User(Base): tablename = "users" id: Mapped[int] = mapped_column(Integer, primary_key=True) telegram_id: Mapped[str] = mapped_column(String, unique=True, index=True) username: Mapped[Optional[str]] = mapped_column(String, nullable=True) created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow) xp: Mapped[int] = mapped_column(Integer, default=0) level: Mapped[int] = mapped_column(Integer, default=1) coins: Mapped[int] = mapped_column(Integer, default=0) flags: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

inventory: Mapped[list["UserInventory"]] = relationship(back_populates="user")
achievements: Mapped[list["UserAchievement"]] = relationship(back_populates="user")
states: Mapped[list["GameState"]] = relationship(back_populates="user")

class Item(Base): tablename = "items" id: Mapped[int] = mapped_column(Integer, primary_key=True) key: Mapped[str] = mapped_column(String, unique=True) name: Mapped[str] = mapped_column(String) description: Mapped[Optional[str]] = mapped_column(String) base_price: Mapped[int] = mapped_column(Integer, default=0)

class UserInventory(Base): tablename = "user_inventory" id: Mapped[int] = mapped_column(Integer, primary_key=True) user_id: Mapped[int] = mapped_column(ForeignKey("users.id")) item_id: Mapped[int] = mapped_column(ForeignKey("items.id")) qty: Mapped[int] = mapped_column(Integer, default=1)

user: Mapped[User] = relationship(back_populates="inventory")
item: Mapped[Item] = relationship()

class Achievement(Base): tablename = "achievements" id: Mapped[int] = mapped_column(Integer, primary_key=True) key: Mapped[str] = mapped_column(String, unique=True) name: Mapped[str] = mapped_column(String) description: Mapped[Optional[str]] = mapped_column(String) points: Mapped[int] = mapped_column(Integer, default=10)

class UserAchievement(Base): tablename = "user_achievements" id: Mapped[int] = mapped_column(Integer, primary_key=True) user_id: Mapped[int] = mapped_column(ForeignKey("users.id")) achievement_id: Mapped[int] = mapped_column(ForeignKey("achievements.id")) unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

user: Mapped[User] = relationship(back_populates="achievements")
achievement: Mapped[Achievement] = relationship()

class EconomyTransaction(Base): tablename = "economy_tx" id: Mapped[int] = mapped_column(Integer, primary_key=True) user_id: Mapped[int] = mapped_column(ForeignKey("users.id")) amount: Mapped[int] = mapped_column(Integer) reason: Mapped[str] = mapped_column(String) created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Cooldown(Base): tablename = "cooldowns" id: Mapped[int] = mapped_column(Integer, primary_key=True) user_id: Mapped[int] = mapped_column(ForeignKey("users.id")) key: Mapped[str] = mapped_column(String, index=True) until: Mapped[datetime] = mapped_column(DateTime, index=True)

class GameState(Base): tablename = "game_states" id: Mapped[int] = mapped_column(Integer, primary_key=True) user_id: Mapped[int] = mapped_column(ForeignKey("users.id")) chat_id: Mapped[str] = mapped_column(String, index=True) scope: Mapped[str] = mapped_column(String, default="main")  # p.ej. "main", "quest:xxx" node: Mapped[str] = mapped_column(String, default="start") memory: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)  # variables de historia updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

user: Mapped[User] = relationship(back_populates="states")

Inicializa tablas

Base.metadata.create_all(engine)

─────────────────────────────────────────────────────────────────────────────

events.py — EventBus simple para hooks

─────────────────────────────────────────────────────────────────────────────

from collections import defaultdict from typing import Callable

class EventBus: def init(self): self._listeners: dict[str, list[Callable[..., None]]] = defaultdict(list)

def on(self, event: str, fn: Callable[..., None]):
    self._listeners[event].append(fn)

def emit(self, event: str, **payload):
    for fn in self._listeners.get(event, []):
        try:
            fn(**payload)
        except Exception:
            # Logging real en telemetry.py si se desea
            pass

EVENTS = EventBus()

─────────────────────────────────────────────────────────────────────────────

fsm.py — Máquina de estados ligera

─────────────────────────────────────────────────────────────────────────────

from dataclasses import dataclass

@dataclass class Transition: source: str dest: str condition: Callable[[dict], bool] | None = None action: Callable[[dict], None] | None = None

class FiniteStateMachine: def init(self, initial: str): self.state = initial self.transitions: list[Transition] = []

def add(self, t: Transition):
    self.transitions.append(t)

def step(self, context: dict) -> str:
    for t in self.transitions:
        if t.source == self.state and (t.condition is None or t.condition(context)):
            if t.action:
                t.action(context)
            self.state = t.dest
            return self.state
    return self.state

─────────────────────────────────────────────────────────────────────────────

dsl.py — DSL en YAML para narrativa

─────────────────────────────────────────────────────────────────────────────

import yaml from typing import List

class DSL: """ Formato YAML esperado:

meta:
  id: "intro"
  title: "Bienvenida"

variables:
  karma: 0

nodes:
  - id: start
    text: |
      Te despiertas en el canal de Diana. Lucien te observa.
    choices:
      - label: "¿Quién eres?"
        next: ask_lucien
      - label: "Seguir a Diana"
        effects:
          coins: +10
          xp: +5
        next: follow

  - id: ask_lucien
    text: "Soy Lucien. Te guiaré."
    choices:
      - label: "Ok"
        next: follow

  - id: follow
    text: "Gracias por seguir a Diana."
    end: true

Reglas:
  - Condiciones opcionales en choices: `if: "memory.karma > 0"`
  - effects soporta: coins, xp, flags.{clave}=valor, items.{key}=+N/-N
"""

@staticmethod
def load(yaml_text: str) -> dict:
    data = yaml.safe_load(yaml_text)
    assert "nodes" in data, "El YAML debe contener 'nodes'"
    ids = [n["id"] for n in data["nodes"]]
    assert len(ids) == len(set(ids)), "IDs de nodos deben ser únicos"
    return data

─────────────────────────────────────────────────────────────────────────────

narrative.py — Story y StoryRunner

─────────────────────────────────────────────────────────────────────────────

from typing import Tuple import operator import re

class Story: def init(self, data: dict): self.data = data self.nodes_by_id = {n["id"]: n for n in data["nodes"]} self.meta = data.get("meta", {}) self.defaults = data.get("variables", {})

def start_node(self) -> str:
    return self.meta.get("start", "start")

def node(self, node_id: str) -> dict:
    return self.nodes_by_id[node_id]

class StoryRunner: def init(self, story: Story): self.story = story

@staticmethod
def _eval_condition(expr: str, memory: dict) -> bool:
    # Soporta expresiones simples: memory.karma > 0, flags.seguido == true
    # Muy simple y seguro: reemplaza memory.xxx por su valor literal y evalúa
    env = {"true": True, "false": False}
    def resolve(path: str):
        parts = path.split(".")
        cur = {"memory": memory}
        cur = cur[parts[0]]
        for p in parts[1:]:
            cur = cur.get(p)
        return cur
    # Reemplazar tokens tipo memory.xxxx por sus valores
    tokens = re.findall(r"([a-zA-Z_][a-zA-Z0-9_\.]+)", expr)
    expr_eval = expr
    for t in sorted(set(tokens), key=len, reverse=True):
        if t.startswith("memory."):
            val = resolve(t)
            expr_eval = expr_eval.replace(t, repr(val))
    try:
        return bool(eval(expr_eval, {"__builtins__": {}}, env))
    except Exception:
        return False

def get_choices(self, node: dict, memory: dict) -> list[dict]:
    out = []
    for ch in node.get("choices", []):
        cond = ch.get("if")
        if cond:
            if not self._eval_condition(cond, memory):
                continue
        out.append(ch)
    return out

def apply_effects(self, user: User, memory: dict, effects: dict):
    from datetime import datetime
    with db_session() as s:
        if effects.get("xp"):
            Gameplay.add_xp(s, user, int(str(effects["xp"]).replace("+", "")))
        if effects.get("coins"):
            Economy.add_coins(s, user, int(str(effects["coins"]).replace("+", "")), reason="story_effect")
        # flags.
        for k, v in (effects.items() if isinstance(effects, dict) else []):
            if isinstance(k, str) and k.startswith("flags."):
                key = k.split(".", 1)[1]
                user.flags[key] = v
        s.merge(user)
    # items.
    for k, v in (effects.items() if isinstance(effects, dict) else []):
        if isinstance(k, str) and k.startswith("items."):
            item_key = k.split(".", 1)[1]
            if str(v).startswith("+"):
                Inventory.add_item_by_key(user, item_key, int(str(v).replace("+", "")))
            elif str(v).startswith("-"):
                Inventory.remove_item_by_key(user, item_key, int(str(v).replace("-", "")))
    # memory direct
    for k, v in (effects.items() if isinstance(effects, dict) else []):
        if isinstance(k, str) and k.startswith("memory."):
            key = k.split(".", 1)[1]
            memory[key] = v

def step(self, user: User, chat_id: str, choice_index: int | None = None, scope: str = "main") -> Tuple[str, dict, list[dict]]:
    with db_session() as s:
        state = s.query(GameState).filter_by(user_id=user.id, chat_id=str(chat_id), scope=scope).one_or_none()
        if not state:
            state = GameState(user_id=user.id, chat_id=str(chat_id), scope=scope, node=self.story.start_node(), memory={**self.story.defaults})
            s.add(state)
            s.flush()

        node = self.story.node(state.node)
        memory = dict(state.memory or {})

        # Si recibimos una elección, procesar transición
        if choice_index is not None:
            choices = self.get_choices(node, memory)
            if 0 <= choice_index < len(choices):
                ch = choices[choice_index]
                # efectos
                effects = ch.get("effects", {})
                if effects:
                    self.apply_effects(user, memory, effects)
                # XP base por decisión
                with db_session() as s2:
                    Gameplay.add_xp(s2, user, CFG.base_xp_per_choice)
                # siguiente nodo
                next_node = ch.get("next")
                if next_node:
                    state.node = next_node
                    node = self.story.node(state.node)
                state.memory = memory
                state.updated_at = datetime.utcnow()
                s.merge(state)

        # Devolver contenido actual
        text = node.get("text", "")
        choices = self.get_choices(node, memory)
        end = node.get("end", False)
        if end:
            # Si es final, podemos limpiar o reiniciar según diseño.
            pass
        return text, memory, choices

─────────────────────────────────────────────────────────────────────────────

gameplay.py — XP, niveles, logros

─────────────────────────────────────────────────────────────────────────────

import math

class Gameplay: @staticmethod def xp_to_level(xp: int) -> int: # Curva simple: nivel = floor((xp/25)^(1/k)) + 1 k = CFG.level_curve_k lvl = int(math.floor((max(xp,0)/25.0) ** (1.0/max(k,1e-6)))) + 1 return max(lvl, 1)

@staticmethod
def add_xp(s, user: User, amount: int):
    user = s.merge(user)
    user.xp += max(amount, 0)
    new_level = Gameplay.xp_to_level(user.xp)
    leveled_up = new_level > user.level
    user.level = new_level
    s.add(user)
    s.flush()
    if leveled_up:
        EVENTS.emit("level_up", user=user, level=new_level)

@staticmethod
def unlock_achievement(s, user: User, key: str):
    ach = s.query(Achievement).filter_by(key=key).one_or_none()
    if not ach:
        return False
    ua = UserAchievement(user_id=user.id, achievement_id=ach.id)
    s.add(ua)
    s.flush()
    EVENTS.emit("achievement_unlocked", user=user, achievement=ach)
    return True

─────────────────────────────────────────────────────────────────────────────

economy.py — Monedas y transacciones

─────────────────────────────────────────────────────────────────────────────

class Economy: @staticmethod def add_coins(s, user: User, amount: int, reason: str = ""): user = s.merge(user) user.coins += amount s.add(EconomyTransaction(user_id=user.id, amount=amount, reason=reason or "generic")) s.flush() EVENTS.emit("coins_changed", user=user, delta=amount, reason=reason)

─────────────────────────────────────────────────────────────────────────────

inventory.py — Inventario

─────────────────────────────────────────────────────────────────────────────

class Inventory: @staticmethod def add_item_by_key(user: User, key: str, qty: int = 1): with db_session() as s: item = s.query(Item).filter_by(key=key).one_or_none() if not item: item = Item(key=key, name=key) s.add(item) s.flush() inv = s.query(UserInventory).filter_by(user_id=user.id, item_id=item.id).one_or_none() if not inv: inv = UserInventory(user_id=user.id, item_id=item.id, qty=0) s.add(inv) inv.qty += max(qty, 0)

@staticmethod
def remove_item_by_key(user: User, key: str, qty: int = 1):
    with db_session() as s:
        item = s.query(Item).filter_by(key=key).one_or_none()
        if not item:
            return
        inv = s.query(UserInventory).filter_by(user_id=user.id, item_id=item.id).one_or_none()
        if not inv:
            return
        inv.qty = max(0, inv.qty - max(qty, 0))

─────────────────────────────────────────────────────────────────────────────

cooldowns.py — Control de cooldowns por acción/clave

─────────────────────────────────────────────────────────────────────────────

from datetime import timedelta

class Cooldowns: @staticmethod def set(user: User, key: str, seconds: int | None = None): from datetime import datetime until = datetime.utcnow() + timedelta(seconds=seconds or CFG.default_cooldown_seconds) with db_session() as s: cd = s.query(Cooldown).filter_by(user_id=user.id, key=key).one_or_none() if not cd: cd = Cooldown(user_id=user.id, key=key, until=until) s.add(cd) else: cd.until = until

@staticmethod
def ready(user: User, key: str) -> bool:
    from datetime import datetime
    with db_session() as s:
        cd = s.query(Cooldown).filter_by(user_id=user.id, key=key).one_or_none()
        return not cd or cd.until <= datetime.utcnow()

─────────────────────────────────────────────────────────────────────────────

telemetry.py — Log/Metric hooks (stub)

─────────────────────────────────────────────────────────────────────────────

import logging logger = logging.getLogger("dianabot") logging.basicConfig(level=logging.INFO)

─────────────────────────────────────────────────────────────────────────────

adapters/telegram_adapter.py — Integración con python-telegram-bot v20

─────────────────────────────────────────────────────────────────────────────

NOTA: Para ejecutar, instala: pip install python-telegram-bot==20.* pyyaml sqlalchemy

from typing import Callable as _Callable

try: from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes except Exception: Update = object  # type: ignore Application = object  # type: ignore InlineKeyboardButton = InlineKeyboardMarkup = object  # type: ignore CommandHandler = CallbackQueryHandler = ContextTypes = object  # type: ignore

class TelegramAdapter: def init(self, token: str, story_runner: StoryRunner): self.app = Application.builder().token(token).build() self.story_runner = story_runner # Handlers self.app.add_handler(CommandHandler("start", self.cmd_start)) self.app.add_handler(CallbackQueryHandler(self.on_choice, pattern=r"^choice:(\d+)$"))

async def cmd_start(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = self._ensure_user(update)
    text, memory, choices = self.story_runner.step(user, str(update.effective_chat.id), None)
    await self._send_node(update, text, choices)

async def on_choice(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = self._ensure_user(update)
    idx = int(update.callback_query.data.split(":")[1])
    text, memory, choices = self.story_runner.step(user, str(update.effective_chat.id), idx)
    await update.callback_query.answer()
    await self._send_node(update, text, choices, edit=True)

def _ensure_user(self, update: Update) -> User:
    tg_id = str(update.effective_user.id)
    with db_session() as s:
        u = s.query(User).filter_by(telegram_id=tg_id).one_or_none()
        if not u:
            u = User(telegram_id=tg_id, username=update.effective_user.username)
            s.add(u)
            s.flush()
        return u

async def _send_node(self, update: Update, text: str, choices: list[dict], edit: bool=False):
    kb = [
        [InlineKeyboardButton(ch.get("label", f"Opción {i+1}"), callback_data=f"choice:{i}")]
        for i, ch in enumerate(choices)
    ]
    markup = InlineKeyboardMarkup(kb) if kb else None
    if edit and update.callback_query and update.callback_query.message:
        await update.callback_query.message.edit_text(text, reply_markup=markup)
    else:
        await update.effective_chat.send_message(text, reply_markup=markup)

def run(self):
    self.app.run_polling()

─────────────────────────────────────────────────────────────────────────────

examples/stories/intro.yml — Historia de ejemplo

─────────────────────────────────────────────────────────────────────────────

EXAMPLE_STORY_YAML = """ meta: id: "intro" title: "Bienvenida a DianaBot" start: "start"

variables: karma: 0

nodes:

id: start text: | Te despiertas en el canal. Una voz susurra: "Sigue a Diana." Lucien aparece a tu lado. choices:

label: "¿Quién eres, Lucien?" next: ask_lucien

label: "Seguir a Diana ahora" effects: coins: "+10" xp: "+5" flags.followed: true next: follow


id: ask_lucien text: | "Soy Lucien. No temas: cada decisión te acerca o te aleja de ella." choices:

label: "Estoy listo" effects: memory.karma: 1 next: follow


id: follow text: | Has dado el primer paso. +10 coins, +5 XP. Tu karma actual es {{memory.karma}}. end: true """


─────────────────────────────────────────────────────────────────────────────

examples/run_bot.py — Runner de ejemplo

─────────────────────────────────────────────────────────────────────────────

if name == "main": # Preparar historia data = DSL.load(EXAMPLE_STORY_YAML) story = Story(data) runner = StoryRunner(story)

# Suscribirse a eventos clave (ejemplo)
def on_level_up(user: User, level: int, **_):
    logger.info(f"User {user.telegram_id} subió a nivel {level}")
EVENTS.on("level_up", on_level_up)

# Lanzar Telegram si hay token en variables de entorno
if CFG.telegram_bot_token:
    adapter = TelegramAdapter(CFG.telegram_bot_token, runner)
    print("DianaBot Engine — Telegram adapter running… /start")
    adapter.run()
else:
    # Modo CLI mínimo para probar sin Telegram
    print("DianaBot Engine — modo CLI. Escribe '0' o '1' para elegir.")
    # Crear/obtener usuario de prueba
    with db_session() as s:
        u = s.query(User).filter_by(telegram_id="cli").one_or_none()
        if not u:
            u = User(telegram_id="cli", username="cli")
            s.add(u)
            s.flush()
    current_text, memory, choices = runner.step(u, chat_id="cli")
    print(current_text)
    for i, ch in enumerate(choices):
        print(f"[{i}] {ch.get('label')}")
    while True:
        sel = input("> ").strip()
        if not sel.isdigit():
            continue
        current_text, memory, choices = runner.step(u, chat_id="cli", choice_index=int(sel))
        print(current_text)
        if not choices:
            print("(Fin)")
            break
        for i, ch in enumerate(choices):
            print(f"[{i}] {ch.get('label')}")

