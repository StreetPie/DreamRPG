# -*- coding: utf-8 -*-
import random
import time

def get_entity(world, entity_type):
    """Возвращает словарь сущности из global_state."""
    if "entities" not in world.data:
        world.data["entities"] = {}
    
    if entity_type not in world.data["entities"]:
        world.data["entities"][entity_type] = {
            "active": False,
            "location": None,
            "hidden_until": 0,
            "last_move": 0,
            "data": {} # Сюда можно класть owner_id для душ и т.д.
        }
        world.save()
    return world.data["entities"][entity_type]

def spawn_entity(world, entity_type, locations, extra_data=None):
    """Спавнит сущность в случайной локации."""
    ent = get_entity(world, entity_type)
    ent["active"] = True
    ent["location"] = random.SystemRandom().choice(locations)
    ent["hidden_until"] = 0
    ent["last_move"] = time.time()
    ent["data"] = extra_data or {}
    world.save()
    return ent

def despawn_entity(world, entity_type):
    """Удаляет сущность (после встречи или изгнания)."""
    ent = get_entity(world, entity_type)
    ent["active"] = False
    ent["location"] = None
    ent["data"] = {}
    world.save()

def move_entity(world, entity_type, locations, hide_chance=0.0, hide_duration=300):
    """Двигает сущность. Иногда может затаиться."""
    ent = get_entity(world, entity_type)
    if not ent["active"]:
        return
        
    now = time.time()
    
    # Проверяем, не спряталась ли она
    if now < ent["hidden_until"]:
        return
        
    # Шанс затаиться
    if hide_chance > 0 and random.SystemRandom().random() < hide_chance:
        ent["hidden_until"] = now + hide_duration
        world.save()
        return
        
    # Иначе двигаем в новую локацию
    old = ent["location"]
    choices = [l for l in locations if l != old]
    if not choices:
        choices = locations
    ent["location"] = random.SystemRandom().choice(choices)
    ent["last_move"] = now
    world.save()

def is_here(world, entity_type, command):
    """Проверяет, находится ли сущность в этой локации и не спряталась ли."""
    ent = get_entity(world, entity_type)
    if not ent["active"]:
        return False
    if time.time() < ent["hidden_until"]:
        return False
    return ent["location"] == command