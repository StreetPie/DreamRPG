# -*- coding: utf-8 -*-
from systems import dice, progression
from social import titles, states
from activities import sleepwalker
from globalEvents import events
#from social.states import _process_death удален

def handle_dungeon(command, user, user_name, users_data, cfg, file_path, cooldowns, user_id, now, Parent, save_data_func, world):

    sleepwalker.try_cooldown_reset(user, user_name, cooldowns, user_id, Parent)

    # 1
    dungeon_id = None
    if command == "!бездна":
        dungeon_id = "abyss"
    elif command == "!пещера":
        dungeon_id = "goblin_cave"
        
    if not dungeon_id:
        return

    # 2. Включен ли 
    if not cfg.config.get("enable_" + dungeon_id, True):
        return

    if user_id not in cooldowns:
        cooldowns[user_id] = {"last_raid_time": 0, "last_dungeon_time": 0}
    elif not isinstance(cooldowns[user_id], dict):
        cooldowns[user_id] = {"last_raid_time": 0, "last_dungeon_time": 0}

    # 3. Проверка КД 
    global_cd = cfg.config.get("global_dungeon_cooldown", 300)
    last_dungeon_time = cooldowns[user_id].get("last_dungeon_time", 0)
    
    if now - last_dungeon_time < global_cd:
        remaining = int(global_cd - (now - last_dungeon_time))
        Parent.SendStreamMessage(cfg.messages["dungeon_cooldown"].format(user=user_name, sec=remaining))
        return

    # 4. Специфичные проверки и стоимость
    cost = cfg.config.get(dungeon_id + "_cost", 0)
    if cost > 0 and user["dreams"] < cost:
        Parent.SendStreamMessage(cfg.messages["dungeon_no_dreams"].format(user=user_name, cost=cost))
        return
        
    if cost > 0:
        user["dreams"] -= cost

    # 5. Запуск Данжа
    threshold = cfg.get_threshold(cfg.config[dungeon_id + "_success_chance"])
    success, dice_msg, crit_s, crit_f = dice.roll_dice(user, threshold, True, cfg, Parent)
    if crit_s:
        user["crit_streak"] = user.get("crit_streak", 0) + 1
        titles.check_shuler_title(user, Parent) # Проверка титула
    else:
        user["crit_streak"] = 0
    level_up_msgs = []

    if success:
        w_exp = cfg.config.get(dungeon_id + "_win_exp", 0)
        w_rep = cfg.config.get(dungeon_id + "_win_rep", 0)
        if crit_s:
            msgs, actual_exp = progression.add_exp(user, int(w_exp * 2), file_path) 
            level_up_msgs.extend(msgs)
            user["reputation"] += int(w_rep * 2)
            Parent.SendStreamMessage(cfg.messages["dungeon_crit_win"].format(dice_msg=dice_msg, exp=actual_exp, rep=w_rep*2))
        else:
            msgs, actual_exp = progression.add_exp(user, w_exp, file_path) 
            level_up_msgs.extend(msgs)
            user["reputation"] += w_rep
            Parent.SendStreamMessage(cfg.messages["dungeon_win"].format(dice_msg=dice_msg, exp=actual_exp, rep=w_rep))
    else: # Поражение в данже
        if crit_f:
            has_danger = events.has_danger_here(command, world, cfg)
            
            # Тратим щит ЗДЕСЬ (только для живых)
            shielded = False
            if not titles.has_title(user, "Мертв Внутри"):
                shielded = titles.consume_babysitter_shield(user)
            
            if shielded:
                Parent.SendStreamMessage(cfg.messages["shield_block"].format(dice_msg=dice_msg, user=user_name))
                # Игрок жив. Если есть монстр, он попытается его убить.
            else:
                if user.get("is_down", False) or titles.has_title(user, "Мертв Внутри"):
                    user["death_count"] = user.get("death_count", 0) + 1
                    titles.check_walking_dead_title(user, Parent)

                # Если он не был мертв до данжа, убиваем его здесь
                if not user.get("is_down", False):
                    user["is_down"] = True
                    user["death_count"] = 0
                
                if has_danger:
                    # ПИШЕМ КОРОТКОЕ СООБЩЕНИЕ О СМЕРТИ В ДАНЖЕ
                    cfg.messages["dungeon_crit_lose_danger"].format(dice_msg=dice_msg, user=user_name)
                else:
                    Parent.SendStreamMessage(cfg.messages["dungeon_crit_lose"].format(dice_msg=dice_msg, user=user_name))
        else:
            Parent.SendStreamMessage(cfg.messages["dungeon_lose"].format(dice_msg=dice_msg))

    # 6. Сохранение
    for msg in level_up_msgs:
        Parent.SendStreamMessage(msg)
    
    # Встреча с опасностью
    events.handle_danger_encounter(
        user, user_id, user_name, command, world, cfg, Parent, 
        users_data, save_data_func, file_path, crit_s, crit_f, success
    )
    
    cooldowns[user_id]["last_dungeon_time"] = now
    save_data_func()