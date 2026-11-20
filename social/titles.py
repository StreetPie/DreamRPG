# -*- coding: utf-8 -*-

def list_titles(user, user_name, Parent):
    """Выводит список титулов игрока."""
    if not user.get("titles"):
        Parent.SendStreamMessage(cfg.messages["title_list_empty"].format(user=user_name))
    else:
        Parent.SendStreamMessage(cfg.messages["title_list"].format(user=user_name, titles=", ".join(user["titles"])))

def has_title(user, title_name):
    return title_name in user.get("titles", [])

   
    
def check_sleep_title(user, cfg, Parent):
    """Проверяет, не заслужил ли игрок титул Воспитательницы."""
    required = cfg.config.get("sleep_titles_required", 100)
    count = user.get("sleep_count", 0)
    
    if count >= required and "Воспитательница" not in user.get("titles", []):
        user["titles"].append("Воспитательница")
        user["title"] = "Воспитательница" 
        Parent.SendStreamMessage(cfg.messages["title_babysitter"].format(user=user["name"]))
        return True
    return False

def give_babysitter_shield(user):
    """Выдает щит от потери грез (защита от is_down)."""
    user["babysitter_shield"] = True

def consume_babysitter_shield(user):
    """Проверяет и потребляет щит. Возвращает True, если щит был."""
    if user.get("babysitter_shield", False):
        user["babysitter_shield"] = False
        return True
    return False

def check_sleepwalker_title(user, Parent, cfg):
    """Проверяет, не заслужил ли игрок титул Лунатика."""
    required = 8  
    count = user.get("sleepwalker_count", 0)
    
    if count >= required and "Лунатик" not in user.get("titles", []):
        user["titles"].append("Лунатик")
        user["title"] = "Лунатик" 
        Parent.SendStreamMessage(cfg.messages["title_sleepwalker"].format(user=user["name"])) 
        return True
    return False
    
def check_savior_title(user, Parent, cfg):
    """Выдает титул Спаситель при N спасениях."""
    if user.get("rescues_count", 0) >= 5 and not has_title(user, "Спаситель"):
        user["titles"].append("Спаситель")
        user["title"] = "Спаситель"
        Parent.SendStreamMessage(cfg.messages["title_savior"].format(user=user["name"]))
        return True
    return False

def check_savior_evolution(user, Parent, cfg):
    """Эволюция титула Спаситель в Миссию при N+ спасениях."""
    if user.get("rescues_count", 0) >= 30 and has_title(user, "Спаситель") and not has_title(user, "Миссия"):
        user["titles"].append("Миссия")
        user["title"] = "Миссия"
        Parent.SendStreamMessage(cfg.messages["title_mission"].format(user=user["name"]))
        return True
    return False

def check_shuler_title(user, Parent, cfg):
    """Выдает титул Шулер за N критов подряд."""
    if user.get("crit_streak", 0) >= 3 and not has_title(user, "Шулер"):
        set_active_title(user, "Шулер")
        Parent.SendStreamMessage(cfg.messages["title_shuler"].format(user=user["name"]))
        return True
    return False

def check_panda_title(user, Parent, cfg):
    """Выдает титул Пандочка (если понадобится условие)."""
    # Пока просто заготовка
    pass

def check_dirty_title(user, Parent, cfg):
    """Выдает титул Грязнуля при N попаданиях в липкое."""
    if user.get("dirty_count", 0) >= 5 and not has_title(user, "Грязнуля"):
        set_active_title(user, "Грязнуля")
        Parent.SendStreamMessage(cfg.messages["title_dirty"].format(user=user["name"]))
        return True
    return False

def check_moderator_title(user, Parent, cfg, is_mod=False, is_broadcaster=False):
    """Выдает титул Модератор стримеру и модераторам (при первом обращении)."""
    if (is_mod or is_broadcaster) and not has_title(user, "Модератор"):
        user["titles"].append("Модератор")
        #без
        Parent.SendStreamMessage(cfg.messages["title_moderator"].format(user=user["name"]))
        return True
    return False

def check_witcher_title(user, Parent, cfg):
    """Выдает титул Ведьмак за 10 соло-убийств монстров."""
    if user.get("solo_kills", 0) >= 10 and not has_title(user, "Ведьмак"):
        user["titles"].append("Ведьмак")
        user["title"] = "Ведьмак"
        Parent.SendStreamMessage(cfg.messages["title_witcher"].format(user=user["name"]))
        return True
    return False

def check_dead_inside_title(user, Parent, cfg):
    if user.get("death_count", 0) >= 1 and not has_title(user, "Мертв Внутри"):
        user["titles"].append("Мертв Внутри")
        user["title"] = "Мертв Внутри"

        CURSED_SAVIOR = u"̶С̶п̶а̶с̶и̶т̶е̶л̶ь̶"
        CURSED_MISSION = u"М҉̕͜и̵̧҇с̷̧̕с̷͜͞и̶̡҇я̸͢͠"
        
        for i, t in enumerate(user["titles"]):
            if t == "Спаситель":
                user["titles"][i] = CURSED_SAVIOR
            elif t == "Миссия":
                user["titles"][i] = CURSED_MISSION
                
        user["blessing_target"] = ""
        Parent.SendStreamMessage(cfg.messages["title_dead_inside"].format(user=user["name"]))
        return True
    return False

def check_walking_dead_title(user, Parent, cfg):
    """Выдает титул Ходячий Мертвец при N+ смертях."""
    if user.get("death_count", 0) >= 10 and not has_title(user, "Ходячий Мертвец"):
        user["titles"].append("Ходячий Мертвец")
        user["title"] = "Ходячий Мертвец"
        Parent.SendStreamMessage(cfg.messages["title_walking_dead"].format(user=user["name"]))
        return True
    return False

def give_first_explorer(user, Parent, cfg):
    if not has_title(user, "Первооткрыватель"):
        user["titles"].append("Первооткрыватель")
        user["title"] = "Первооткрыватель"
        Parent.SendStreamMessage("🏆 {0} становится Первооткрывателем! (Заглушка: награда за первое завершение события)".format(user["name"]))

def give_altered_mind_title(user, Parent, cfg):
    """Выдается за 3 возврата своей души."""
    if user.get("soul_returns", 0) >= 3 and not has_title(user, "Измененное сознание"):
        user["titles"].append("Измененное сознание")
        user["title"] = "Измененное сознание"
        Parent.SendStreamMessage("🏆🧠 {0} получает титул 'Измененное сознание'! Собрав частички своей души, ты стал кем-то большим. (Эффект: Заглушка)".format(user["name"]))
        return True
    return False

def give_exorcist_title(user, Parent, cfg):
    """Выдается за 10 изгнаний духов."""
    if user.get("soul_banishes", 0) >= 10 and not has_title(user, "Экзорцист"):
        user["titles"].append("Экзорцист")
        user["title"] = "Экзорцист"
        Parent.SendStreamMessage("🏆🕊️ {0} получает титул 'Экзорцист'! Ты проводишь духов на свет. (Эффект: Заглушка)".format(user["name"]))
        return True
    return False