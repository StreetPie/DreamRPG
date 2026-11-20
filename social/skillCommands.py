# -*- coding: utf-8 -*-
from systems import progression
from social import titles

def handle_rescue(user, user_name, users_data, data, Parent, save_data_func, cfg, file_path):
    """Команда !помочь"""
    if titles.has_title(user, "Мертв Внутри"):
        Parent.SendStreamMessage(cfg.messages["rescue_dead_error"].format(user=user_name))
        return
    target_name = data.GetParam(1)
    if not target_name:
        Parent.SendStreamMessage(cfg.messages["rescue_no_target"].format(user=user_name))
        return

    target_name = target_name.replace("@", "").lower()
    target_id = next((uid for uid, u in users_data.items() if u["name"].lower() == target_name), None)

    if not target_id:
        Parent.SendStreamMessage(cfg.messages["error_not_found"].format(user=user_name, target=target_name))
        return

    target = users_data[target_id]
    if not target.get("is_down", False):
        Parent.SendStreamMessage(cfg.messages["error_no_need_help"].format(user=user_name, target=target_name))
        return

    if titles.has_title(target, "Мертв Внутри"):
        Parent.SendStreamMessage(cfg.messages["rescue_ghoul"].format(user=user_name))
        return

    if target_id == user_name:
        Parent.SendStreamMessage(cfg.messages["rescue_self_error"].format(user=user_name))
        return
    target["is_down"] = False
    user["rescues_count"] += 1
    
    msgs, actual_exp = progression.add_exp(user, 50, file_path)
    gained_dreams = progression.add_dreams(user, 10) 
    user["reputation"] += 2

    Parent.SendStreamMessage(cfg.messages["rescue_success"].format(user=user_name, target=target["name"], exp=actual_exp, dreams=gained_dreams))

    for msg in msgs:
        Parent.SendStreamMessage(msg)

    titles.check_savior_title(user, Parent)
    titles.check_savior_evolution(user, Parent)

    save_data_func()


def handle_blessing(user, user_name, users_data, data, Parent, save_data_func, cfg):
    """Команда !благословить"""
    # 1. Проверка прав (Спаситель, Миссия, АнПал)
    if not titles.has_title(user, "Спаситель") and not titles.has_title(user, "Миссия") and not titles.has_title(user, "АнПал"):
        Parent.SendStreamMessage(cfg.messages["blessing_no_title"].format(user=user_name))
        return
        
    target_name = data.GetParam(1)
    
    # 2. Логика массового благословения (АнПал)
    if not target_name:
        if titles.has_title(user, "АнПал"):
            count = 0
            source_id = "anpal_" + user["name"] # Уникальный ID источника
            for uid, u in users_data.items():
                if "blessings" not in u: u["blessings"] = {}
                # Накладываем, только если этого источника еще нет
                if source_id not in u["blessings"]:
                    u["blessings"][source_id] = 1
                    _recalculate_dice_bonus(u) # Функция пересчета
                    count += 1
            Parent.SendStreamMessage(cfg.messages["blessing_anpal"].format(user=user_name, count=count))
            save_data_func()
            return
        else:
            Parent.SendStreamMessage(cfg.messages["blessing_no_target"].format(user=user_name))
            return

    target_name = target_name.replace("@", "").lower()
    target_id = next((uid for uid, u in users_data.items() if u["name"].lower() == target_name), None)

    if not target_id:
        Parent.SendStreamMessage("{0}, пользователь {1} не найден.".format(user_name, target_name))
        return

    target = users_data[target_id]

    if titles.has_title(target, "Мертв Внутри") and titles.has_title(user, "Миссия"):
        if not titles.has_title(target, "АнПал"):
            target["titles"].append("АнПал")
            target["title"] = "АнПал"
            Parent.SendStreamMessage(cfg.messages["blessing_give_anpal"].format(user=target["name"]))
            save_data_func()
            return

    # 5. Обычное благословение (Спаситель или Миссия)
    # АнПал тоже может кидать обычное, но он не должен спамить.
    # Проверяем, не кинул ли он уже бафф на кого-то (в этом случае он должен снять с прошлого).
    if titles.has_title(user, "АнПал"):
        Parent.SendStreamMessage(cfg.messages["blessing_anpal_no_target"].format(user=user_name))
        return

    blessing_power = 1
    blessing_name = "Спаситель"
    if titles.has_title(user, "Миссия"):
        blessing_power = 2
        blessing_name = "Миссия"
        
    source_id = "caster_" + user["name"] # Уникальный ID для этого благословляющего

    # Если у игрока уже была цель - снимаем ЕГО бафф с прошлой цели
    if user.get("blessing_target") and user["blessing_target"] in users_data:
        old_target = users_data[user["blessing_target"]]
        if "blessings" in old_target and source_id in old_target["blessings"]:
            del old_target["blessings"][source_id]
            _recalculate_dice_bonus(old_target)

    # Накладываем бафф на новую цель
    user["blessing_target"] = target_id
    if "blessings" not in target: target["blessings"] = {}
    target["blessings"][source_id] = blessing_power
    _recalculate_dice_bonus(target)
    Parent.SendStreamMessage(cfg.messages["blessing_success"].format(user=user_name, target=target["name"], power=blessing_power, name=blessing_name))
    save_data_func()


def _recalculate_dice_bonus(user):
    """Пересчитывает кеш dice_bonus на основе всех активных благословений."""
    if "blessings" not in user:
        user["blessings"] = {}
    total = sum(user["blessings"].values())
    user["dice_bonus"] = total

def handle_passive_choice(user, user_name, data, cfg, file_path, Parent, save_data_func):
    """Команда !пассивка"""
    level, _, _ = progression.get_level_by_total_exp(user.get("total_exp", 0), file_path)
    
    available = []
    if level >= 20 and "20" not in user.get("levelup_choices", []):
        available = progression.LEVEL_BONUSES[20]
    elif level >= 30 and "30" not in user.get("levelup_choices", []):
        available = progression.LEVEL_BONUSES[30]
        
    if not available:
        Parent.SendStreamMessage("{0}, у тебя сейчас нет доступных пассивок.".format(user_name))
        return
        
    param = data.GetParam(1)
    if not param:
        msg = "Доступные пассивки (напиши !пассивка + <номер навыка>): "
        for i, b in enumerate(available):
            msg += "{0}. {1} ({2}) | ".format(i + 1, b["name"], b["desc"])
        Parent.SendStreamMessage(msg)
        return
        
    try:
        idx = int(param) - 1
        chosen = available[idx]
    except:
        chosen = next((b for b in available if b["id"] == param), None)
        
    if chosen:
        choice_level = 20 if chosen["id"] in ["greed", "resilience"] else 30
        user["levelup_choices"].append(str(choice_level))
        user["bonus_" + chosen["id"]] = True
        Parent.SendStreamMessage("✅ {0} выбрал пассивку: {1}! ({2})".format(user_name, chosen["name"], chosen["desc"]))
        save_data_func()