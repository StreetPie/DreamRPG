# -*- coding: utf-8 -*-
import random
from systems import dice, progression
from social import titles, states
from activities import sleepwalker
from globalEvents import events  


def handle_raid(command, user, user_name, users_data, data, cfg, file_path, cooldowns, user_id, now, Parent, save_data_func, world):    

    sleepwalker.try_cooldown_reset(user, user_name, cooldowns, user_id, Parent)

    if command == "!лунатик":
        sleepwalker.handle_sleepwalker(user, user_name, cfg, file_path, cooldowns, user_id, now, Parent, save_data_func, world)
        return                       

    if command == "!уложить":
        if not cfg.config.get("enable_sleep", True):
            return
        
        if user_id not in cooldowns:
            cooldowns[user_id] = {"last_raid_time": 0, "last_dungeon_time": 0}
        elif not isinstance(cooldowns[user_id], dict):
            cooldowns[user_id] = {"last_raid_time": 0, "last_dungeon_time": 0}

        # Проверка общего КД
        global_cd = cfg.config.get("global_raid_cooldown", 60)
        last_raid_time = cooldowns[user_id].get("last_raid_time", 0)
        if now - last_raid_time < global_cd:
            remaining = int(global_cd - (now - last_raid_time))
            Parent.SendStreamMessage(cfg.messages["cooldown_wait"].format(user=user_name, sec=remaining))
            return

        target_name = data.GetParam(2)
        
              # ЛОГИКА СОН-ЧаСА
        if not target_name:
            if "Воспитательница" in user.get("titles", []):
                exp_reward = cfg.config.get("sleep_win_exp", 40)
                dreams_reward = cfg.config.get("sleep_win_dreams", 20)
                
                count = 0
                for uid, u in users_data.items():
                    if "total_exp" in u: 
                        msgs, _ = progression.add_exp(u, exp_reward, file_path)
                        progression.add_dreams(u, dreams_reward)
                        
                        titles.give_babysitter_shield(u) 
                        
                        count += 1
                        for msg in msgs:
                            Parent.SendStreamMessage(msg)
                
                user["reputation"] += cfg.config.get("sleep_rep_giver", 1)
                user["sleep_count"] = user.get("sleep_count", 0) + 1
                titles.check_sleep_title(user, cfg, Parent)
                
                Parent.SendStreamMessage(cfg.messages["sleep_hour"].format(user=user_name, exp=exp_reward, dreams=dreams_reward, count=count))
                
                cooldowns[user_id]["last_raid_time"] = now
                save_data_func()
                return
            else:
                Parent.SendStreamMessage(cfg.messages["sleep_no_target"].format(user=user_name))
                return

        # ЛОГИКА ДЛЯ ОДНОГО ИГРОКА
        target_name = target_name.replace("@", "").lower()
        target_id = next((uid for uid, u in users_data.items() if u["name"].lower() == target_name), None)

        if not target_id:
            Parent.SendStreamMessage("{0}, пользователь {1} не найден.".format(user_name, target_name))
            return
            
        if target_id == user_id:
            Parent.SendStreamMessage("{0}, себя уложить спать нельзя!".format(user_name))
            return

        target = users_data[target_id]
        exp_reward = cfg.config.get("sleep_win_exp", 15)
        dreams_reward = cfg.config.get("sleep_win_dreams", 5)
        
        msgs, actual_exp = progression.add_exp(target, exp_reward, file_path)
        actual_dreams = progression.add_dreams(target, dreams_reward)
        
        for msg in msgs:
            Parent.SendStreamMessage(msg)
            
        user["reputation"] += cfg.config.get("sleep_rep_giver", 1)
        user["sleep_count"] = user.get("sleep_count", 0) + 1
        titles.check_sleep_title(user, cfg, Parent)
        titles.give_babysitter_shield(user)
        
        Parent.SendStreamMessage("💤 {0} уложил {1} спать! {1} получает +{2} опыта и +{3} грез.".format(
            user_name, target_name, actual_exp, actual_dreams
        ))
        
        cooldowns[user_id]["last_raid_time"] = now
        save_data_func()
        return

    if command == "!рейд" and not cfg.config.get("enable_raid", True):
        return
    if command == "!погружение" and not cfg.config.get("enable_deep", True):
        return
    if command == "!искажение" and not cfg.config.get("enable_distort", True):
        return

    # 1. Проверка уровня
    user_level, _, _ = progression.get_level_by_total_exp(user.get("total_exp", 0), file_path)
    if command == "!погружение" and user_level < 5:
        Parent.SendStreamMessage(cfg.messages["level_need_5"].format(user=user_name))
        return
    if command == "!искажение" and user_level < 10:
        Parent.SendStreamMessage(cfg.messages["level_need_10"].format(user=user_name))
        return

    # 2. Получаем настройки
    if command == "!рейд":
        threshold = cfg.get_threshold(cfg.config["raid_success_chance"])
        w_exp, w_dr = cfg.config["raid_win_exp"], cfg.config["raid_win_dreams"]
        l_exp, l_dr = cfg.config["raid_lose_exp"], cfg.config["raid_lose_dreams"]
    elif command == "!погружение":
        threshold = cfg.get_threshold(cfg.config["deep_success_chance"])
        w_exp, w_dr = cfg.config["deep_win_exp"], cfg.config["deep_win_dreams"]
        l_exp, l_dr = cfg.config["deep_lose_exp"], cfg.config["deep_lose_dreams"]
    elif command == "!искажение":
        threshold = cfg.get_threshold(cfg.config["distort_success_chance"])
        w_exp, w_dr = cfg.config["distort_win_exp"], cfg.config["distort_win_dreams"]
        l_exp, l_dr = cfg.config["distort_lose_exp"], cfg.config["distort_lose_dreams"]

    # 3. Проверка КД
    global_cd = cfg.config.get("global_raid_cooldown", 60)
    last_raid_time = cooldowns[user_id].get("last_raid_time", 0)
    if now - last_raid_time < global_cd:
        remaining = int(global_cd - (now - last_raid_time))
        cfg.messages["raid_cooldown"].format(user=user_name, sec=remaining, total=global_cd)
        return

    # 4. Запуск рейда
    user["raids_total"] += 1
    success, dice_msg, crit_s, crit_f = dice.roll_dice(user, threshold, False, cfg, Parent)
    
    if crit_s:
        user["crit_streak"] = user.get("crit_streak", 0) + 1
        titles.check_shuler_title(user, Parent, cfg) # Проверка титула
    else:
        user["crit_streak"] = 0
    level_up_msgs = []

    if success:
        user["raids_success"] += 1
        if crit_s:
            msgs, actual_exp = progression.add_exp(user, int(w_exp * 2), file_path)
            level_up_msgs.extend(msgs)
            gained_dreams = progression.add_dreams(user, int(w_dr * 2)) 
            Parent.SendStreamMessage(cfg.messages["raid_crit_win"].format(dice_msg=dice_msg, exp=actual_exp, dreams=gained_dreams))
        else:
            msgs, actual_exp = progression.add_exp(user, w_exp, file_path)
            level_up_msgs.extend(msgs)
            gained_dreams = progression.add_dreams(user, w_dr) 
            Parent.SendStreamMessage(cfg.messages["raid_win"].format(dice_msg=dice_msg, exp=actual_exp, dreams=gained_dreams))
    else:
        if crit_f:
            user["raids_fail"] += 1
            has_danger = events.has_danger_here(command, world, cfg)
            
            if has_danger:
                Parent.SendStreamMessage("{0} | 💥 КРИТ ПРОВАЛ!".format(dice_msg))
            else:
                lost_dreams = progression.remove_dreams(user, int(l_dr * 1.5))
                Parent.SendStreamMessage(cfg.messages["raid_crit_lose"].format(dice_msg=dice_msg, dreams=lost_dreams))
        else:
            user["raids_fail"] += 1
            msgs, actual_exp = progression.add_exp(user, l_exp, file_path)
            level_up_msgs.extend(msgs)
            lost_dreams = progression.remove_dreams(user, l_dr)
            Parent.SendStreamMessage(cfg.messages["raid_lose"].format(dice_msg=dice_msg, exp=actual_exp, dreams=lost_dreams))
            
    # 5. Вывод повышения уровня и сохранение
    for msg in level_up_msgs:
        Parent.SendStreamMessage(msg)
    
 
    events.handle_danger_encounter(
        user, user_id, user_name, command, world, cfg, Parent, 
        users_data, save_data_func, file_path, crit_s, crit_f, success
    )
    
    cooldowns[user_id]["last_raid_time"] = now
    save_data_func()
