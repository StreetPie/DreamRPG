# -*- coding: utf-8 -*-
import os
import json
import codecs
from social import titles, states, skillCommands

def _load_levels(file_path):
    script_dir = os.path.dirname(os.path.abspath(file_path))
    levels_path = os.path.join(script_dir, "levels.json")

    if not os.path.isfile(levels_path):
        default_levels = {str(i): (i - 1) * 100 for i in range(1, 101)}
        try:
            with codecs.open(levels_path, "w", encoding="utf-8") as f:
                json.dump(default_levels, f, indent=4, ensure_ascii=False)
        except Exception:
            pass
        return {i: (i - 1) * 100 for i in range(1, 101)}

    try:
        with codecs.open(levels_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {int(k): int(v) for k, v in data.items()}
    except Exception as e:
        return {i: (i - 1) * 100 for i in range(1, 101)}

def get_level_by_total_exp(total_exp, file_path):
    if total_exp < 0:
        total_exp = 0
        
    levels = _load_levels(file_path)
    current_level = 1
    
    for lvl in range(1, max(levels.keys()) + 1):
        next_lvl = lvl + 1
        if next_lvl in levels:
            if total_exp >= levels[next_lvl]:
                current_level = next_lvl
            else:
                break
        else:
            break

    current_lvl_start = levels.get(current_level, 0)
    exp_inside = total_exp - current_lvl_start
    
    next_lvl = current_level + 1
    if next_lvl in levels:
        next_level_total = levels[next_lvl]
        needed = next_level_total - current_lvl_start
    else:
        needed = 100 
        
    return current_level, exp_inside, needed

def get_exp_for_level(level, file_path):
    levels = _load_levels(file_path)
    next_lvl = level + 1
    if level in levels and next_lvl in levels:
        return levels[next_lvl] - levels[level]
    return 0

       # ИСПРАВИТЬ БАЛАНС!!!
LEVEL_BONUSES = {
    25: [
        {"id": "greed", "name": "Жадность", "desc": "Получать на 25% больше опыта и грез"},
        {"id": "resilience", "name": "Стойкость", "desc": "Терять на 50% меньше грез и получать на 10% больше опыта"}
    ],
    35: [
        {"id": "sage", "name": "Мудрец", "desc": "Получать на 15% больше опыта от всех действий"},
        {"id": "hoarder", "name": "Скопидом", "desc": "Получать на 25% больше грез от всех действий"},
        {"id": "lucky", "name": "Счастливчик", "desc": "+2 к броску кубика во всех вылазках"}
    ]
}

def get_exp_multiplier(user):
    """Возвращает максимальный множитель для опыта (без перемножения)."""
    mult = 1.0
    if user.get("bonus_greed"): mult = max(mult, 1.25)
    if user.get("bonus_resilience"): mult = max(mult, 1.1)
    if user.get("bonus_sage"): mult = max(mult, 1.15)
    return mult

def get_dreams_multiplier(user):
    """Возвращает максимальный множитель для грез."""
    mult = 1.0
    if user.get("bonus_greed"): mult = max(mult, 1.25)
    if user.get("bonus_hoarder"): mult = max(mult, 1.25)
    return mult

def get_loss_multiplier(user):
    """Возвращает множитель потерь (0.5 = терять в 2 раза меньше)."""
    if user.get("bonus_resilience"): return 0.5
    return 1.0

def add_exp(user, amount, file_path):
    """Начисляет опыт с учетом множителя от пассивок."""
    final_amount = int(amount * get_exp_multiplier(user))
    old_level, _, _ = get_level_by_total_exp(user.get("total_exp", 0), file_path)
    user["total_exp"] = user.get("total_exp", 0) + final_amount
    if user["total_exp"] < 0: 
        user["total_exp"] = 0
        
    new_level, _, _ = get_level_by_total_exp(user["total_exp"], file_path)
    
    level_up_msgs = []
    if new_level > old_level:
        msg = "✨ {0} достигает {1} уровня!".format(user["name"], new_level)
        
        if old_level < 25 <= new_level:
            msg += " Доступна новая !пассивка."
        elif old_level < 35 <= new_level:
            msg += " Доступна новая !пассивка."
            
        level_up_msgs.append(msg)
        
        if old_level < 20 <= new_level:
            level_up_msgs.append("🌙 {0} научился бродить во сне 👣👣 Новый рейд !лунатик!".format(user["name"]))
            
    return level_up_msgs, final_amount

def add_dreams(user, amount):
    """Добавляет грезы с учетом множителя."""
    final_amount = int(amount * get_dreams_multiplier(user))
    user["dreams"] += final_amount
    return final_amount

def remove_dreams(user, amount):
    """Списывает грезы с учетом множителя потерь."""
    if titles.has_title(user, "Мертв Внутри"):
        return 0
        
    final_amount = int(amount * get_loss_multiplier(user))
    user["dreams"] = max(0, user["dreams"] - final_amount)
    return final_amount

def give_walking_dead_reward(user, file_path, Parent):
    """Выдает награду Ходячему Мертвецу за смерть."""
    # Базовые награды (можно вынести в конфиг)
    WALKING_DEAD_EXP = 100
    WALKING_DEAD_DREAMS = 50
    
    msgs, exp = add_exp(user, WALKING_DEAD_EXP, file_path)
    gained = add_dreams(user, WALKING_DEAD_DREAMS)
    for m in msgs:
        Parent.SendStreamMessage(m)
    Parent.SendStreamMessage(
        "💀 Но смерть лишь придала {0} сил! +{1} опыта, +{2} грез.".format(
            user["name"], exp, gained
        )
    )

