# -*- coding: utf-8 -*-
from systems import progression
from social import titles

MONSTER_EVENT_NAME = "подкроватный_монстр"

def handle_event_command(data, world, Parent, users_data, save_data, cfg):
    """Роутинг !ивент. Вызывается из главного скрипта только для модераторов."""
    param = data.GetParam(1).lower() if data.GetParam(1) else ""
    name = data.GetParam(2).lower() if data.GetParam(2) else ""

    if param == "старт":
        if name in (MONSTER_EVENT_NAME, "подкроватный монстр", "монстр"):
            _start_monster(world, Parent, cfg)
        else:
            Parent.SendStreamMessage(cfg.messages["unknown_event"].format(name=name))
        return

    if param == "конец" or param == "стоп":
        if name in (MONSTER_EVENT_NAME, "подкроватный монстр", "монстр"):
            _stop_monster(world, Parent)
        else:
            Parent.SendStreamMessage(cfg.messages["unknown_event"].format(name=name))
        return

    if param == "статус":
        event_name = " ".join([data.GetParam(i) for i in range(2, data.GetParamCount())]).lower()
        
        if event_name in (MONSTER_EVENT_NAME, "подкроватный монстр", "монстр"):
            m = world.get_monster()
            if m["active"]:
                Parent.SendStreamMessage(cfg.messages["monster_status_active"].format(strength=m["strength"]))                
            else:
                Parent.SendStreamMessage(cfg.messages["monster_status_inactive"])
        else:
            Parent.SendStreamMessage("Уточните название ивента: !ивент статус <название ивента>")
        return

    Parent.SendStreamMessage("Использование: !ивент старт|конец|статус <название>")


def _start_monster(world, Parent, cfg):
    locations = cfg.get_monster_locations()
    start_str = cfg.config.get("monster_start_strength", 5)
    m = world.start_monster(locations, start_str)
    Parent.SendStreamMessage(cfg.messages["monster_start"].format(strength=start_str))
    Parent.Log("DreamRPG", "Monster started at {0}".format(m["location"]))


def _stop_monster(world, Parent, cfg):
    world.stop_monster()
    Parent.SendStreamMessage(cfg.messages["monster_stop"])


def has_danger_here(command, world, cfg):
    """Быстрая проверка для рейдов, чтобы не писать лишний текст."""
    return world.monster_is_here(command)


def handle_danger_encounter(user, user_id, user_name, command, world, cfg, Parent, users_data, save_data, file_path, crit_s, crit_f, success):
    """Универсальная проверка на опасности в локации."""
    
    monster_here = world.monster_is_here(command)
    
    # (В будущем здесь можно добавить: event_here = world.event_is_here(command) и т.д.)
    event_here = False 
    
    # 2. Если опасностей нет — выходим
    if not monster_here and not event_here:
        return False
        
    # 3. Если есть и монстр, и ивент — выбираем одно случайное
    if monster_here and event_here:
        import random
        if random.SystemRandom().randint(1, 2) == 1:
            event_here = False # Выбираем монстра
        else:
            monster_here = False # Выбираем ивент
            
    # 4. Запускаем нужное событие
    if monster_here:
        return _handle_monster_fight(user, user_id, user_name, world, cfg, Parent, users_data, save_data, file_path, crit_s, crit_f, success)
        
    if event_here:
        # Заглушка для будущих ивентов
        pass
        
    return False


def _handle_monster_fight(user, user_id, user_name, world, cfg, Parent, users_data, save_data, file_path, crit_s, crit_f, success):
    # Внутри уже не нужно проверять world.monster_is_here, так как это сделал диспетчер

    pen_dreams = cfg.config.get("monster_penalty_dreams", 30)
    is_witcher = titles.has_title(user, "Ведьмак")
    
    damage = 2 if is_witcher else 1 

    if crit_s and cfg.config.get("monster_crit_instant_win", True):
        _defeat_monster(world, cfg, Parent, users_data, save_data, file_path, user, user_id, user_name)
        return True

    if success or is_witcher:
        world.weaken_monster(damage)
        world.add_monster_contributor(user_id)
        
        if world.get_monster()["strength"] <= 0:
            _defeat_monster(world, cfg, Parent, users_data, save_data, file_path, user, user_id, user_name)
        else:
            Parent.SendStreamMessage(cfg.messages["monster_encounter_weaken"].format(user=user_name, strength=world.get_monster()["strength"]))
        return True

    # 3. Провал 
    world.strengthen_monster(1) 
    
    if not crit_f:
        # Обычный провал (не смерть)
        lost = progression.remove_dreams(user, pen_dreams)
        Parent.SendStreamMessage(cfg.messages["monster_encounter_fail"].format(user=user_name, strength=world.get_monster()["strength"], lost=lost))
    else:
        
        # Если игрок уже мертв (is_down=True) ИЛИ у него титул "Мертв Внутри"
        if user.get("is_down", False) or titles.has_title(user, "Мертв Внутри"):
            user["death_count"] = user.get("death_count", 0) + 1
            titles.check_walking_dead_title(user, Parent, cfg)
            if titles.has_title(user, "Ходячий Мертвец"):
                # Функция сама начислит опыт, грезы и напишет сообщение
                progression.give_walking_dead_reward(user, file_path, Parent)
            else:
                # Обычный Мертв Внутри (без бонуса)
                Parent.SendStreamMessage("👾 Монстр утащил 💀 {0} под кровать. Но ему уже всё равно.".format(user_name))
                if not titles.has_title(user, "Мертв Внутри"):
                    titles.check_dead_inside_title(user, Parent)
                    
        else:
            # Игрок ЖИВ (например, щит спас его в данже, или это был рейд)
            # Монстр пытается его убить
            if not titles.consume_babysitter_shield(user):
                # Щита нет 
                user["is_down"] = True
                user["death_count"] = 0 
                Parent.SendStreamMessage(cfg.messages["monster_kill"].format(user=user_name))
            else:
                # Щит сработал 
                Parent.SendStreamMessage(cfg.messages["monster_shield"].format(user=user_name))                
    return True


def _defeat_monster(world, cfg, Parent, users_data, save_data, file_path, killer_user, killer_user_id, killer_name):
    """Изгнание монстра. Награда всем, кто внёс вклад."""
    m = world.get_monster()
    contributors = list(m["defeated_by"])
    if killer_user_id not in contributors:
        contributors.append(killer_user_id)

    base_exp = cfg.config.get("monster_reward_exp", 500)
    base_dreams = cfg.config.get("monster_reward_dreams", 300)
    base_rep = cfg.config.get("monster_reward_rep", 10)

    valid_contributors = [uid for uid in contributors if uid in users_data]
    num_players = len(valid_contributors)
    
    if num_players == 0:
        return

    # --- БЛОК СОЛО / ГРУППА ---
    if num_players == 1:
        u = users_data[killer_user_id]
        progression.add_exp(u, base_exp, file_path)
        progression.add_dreams(u, base_dreams)
        u["reputation"] += base_rep
        u["solo_kills"] = u.get("solo_kills", 0) + 1
        titles.check_witcher_title(u, Parent, cfg)
        Parent.SendStreamMessage(cfg.messages["monster_encounter_win"].format(user=killer_name, exp=base_exp, dreams=base_dreams, rep=base_rep))
        
    else:
        shared_exp = int(base_exp / num_players)
        shared_dreams = int(base_dreams / num_players)
        names_list = []

        for uid in valid_contributors:
            u = users_data[uid]
            names_list.append("@{0}".format(u["name"]))
            progression.add_exp(u, shared_exp, file_path)
            progression.add_dreams(u, shared_dreams)
            if uid == killer_user_id:
                u["reputation"] += base_rep
                Parent.SendStreamMessage(cfg.messages["monster_encounter_group"].format(exp=shared_exp, dreams=shared_dreams, names=", ".join(names_list), killer=killer_name, rep=base_rep))
    
    cfg.config["monster_event_active"] = False
    cfg.save()

    world.stop_monster()
    save_data()


def tick(world, cfg, Parent, script_name="DreamRPG"):
    if not world:
        return
    try:
        m = world.get_monster()
        if m.get("active"):
            interval = cfg.config.get("monster_move_interval", 600)
            import time
            now = time.time()
            if now - m.get("last_move_time", 0) > interval:
                world.move_monster(cfg.get_monster_locations())
                Parent.Log(script_name, "Monster moved to {0}".format(world.get_monster()["location"]))
    except Exception as e:
        Parent.Log(script_name, "Tick error: " + str(e))


def ui_start_monster(world, cfg, Parent):
    try:
        _start_monster(world, Parent, cfg)
    except Exception as e:
        Parent.Log("DreamRPG", "ui_start_monster error: " + str(e))


def ui_stop_monster(world, Parent):
    try:
        _stop_monster(world, Parent)
    except Exception as e:
        Parent.Log("DreamRPG", "ui_stop_monster error: " + str(e))