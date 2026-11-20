# -*- coding: utf-8 -*-
import random
from systems import progression
from social import titles, states
from globalEvents import events


def handle_sleepwalker(user, user_name, cfg, file_path, cooldowns, user_id, now, Parent, save_data_func, world):
                
    # 1. Проверка включения
    if not cfg.config.get("enable_sleepwalker", True):
        return
        
    user_level, _, _ = progression.get_level_by_total_exp(user.get("total_exp", 0), file_path)
    if user_level < 15:
        Parent.SendStreamMessage(cfg.messages["sleepwalker_level_error"].format(user=user_name))
        return
    # Защита от бага со старыми данными
    if user_id not in cooldowns:
        cooldowns[user_id] = {"last_raid_time": 0, "last_dungeon_time": 0}
    elif not isinstance(cooldowns[user_id], dict):
        cooldowns[user_id] = {"last_raid_time": 0, "last_dungeon_time": 0}

    global_cd = cfg.config.get("global_raid_cooldown", 60) 
    
    last_raid_time = cooldowns[user_id].get("last_raid_time", 0)
    if now - last_raid_time < global_cd:
        remaining = int(global_cd - (now - last_raid_time))
        Parent.SendStreamMessage(cfg.messages["sleepwalker_cooldown"].format(user=user_name, sec=remaining, total=global_cd))
        return

    # Бросок кубика (только чистый d20, без бонусов и Pity)
    base_roll = random.SystemRandom().randint(1, 20)
    total_roll = base_roll
    
    if total_roll >= 10:
        dice_msg = "🎲 {0} выбросил ??".format(user_name)
    else:
        dice_msg = "🎲 {0} выбросил ???".format(user_name)        

   
    if total_roll == 1: outcome_id = 1
    elif total_roll in [2, 3]: outcome_id = 2
    elif total_roll in [4, 5, 6, 7, 8]: outcome_id = 3
    elif total_roll in [9, 10, 11]: outcome_id = 4
    elif total_roll in [12, 13]: outcome_id = 5
    elif total_roll in [14, 15, 16, 17]: outcome_id = 6
    elif total_roll in [18, 19]: outcome_id = 7
    else: outcome_id = 8 # К

    # --- СЧЕТЧИК УНИКАЛЬНЫХ ИСХОДОВ ---
    if "sleepwalker_seen" not in user:
        user["sleepwalker_seen"] = []
    
    if outcome_id not in user["sleepwalker_seen"]:
        user["sleepwalker_seen"].append(outcome_id)
        user["sleepwalker_count"] = user.get("sleepwalker_count", 0) + 1

    # 5. Логика исходов
    level_up_msgs = []
    
    if total_roll >= 20:
        msgs, actual_exp = progression.add_exp(user, 100, file_path)
        level_up_msgs.extend(msgs)
        gained = progression.add_dreams(user, 100)
        Parent.SendStreamMessage("{0} | 🌟 Тебе снится сон, в которым ты можешь управлять своим временем как только захочешь! +{1} опыта, +{2} грез, КД рейдов откатилось!".format(dice_msg, actual_exp, gained))
        cooldowns[user_id]["last_raid_time"] = 0 
        
    elif total_roll == 1:
        is_dead_inside = titles.has_title(user, "Мертв Внутри")
        is_walking_dead = titles.has_title(user, "Ходячий Мертвец")

        shielded = False
        if not is_dead_inside:
            shielded = titles.consume_babysitter_shield(user)

        if shielded:
            Parent.SendStreamMessage(cfg.messages["shield_block"].format(dice_msg=dice_msg, user=user_name))
        else:
            if is_dead_inside or is_walking_dead:
                # Андеды
                user["death_count"] = user.get("death_count", 0) + 1
                titles.check_walking_dead_title(user, Parent)
                if is_walking_dead:
                    Parent.SendStreamMessage("{0} | 💥 КРИТ ПРОВАЛ! {1} засыпает мертвым сном. Как глупо было верить в свет...".format(dice_msg, user_name))
                    progression.give_walking_dead_reward(user, file_path, Parent)

                else:
                    cfg.messages["sleepwalker_crit_dead"].format(dice_msg=dice_msg, user=user_name)
                    titles.check_dead_inside_title(user, Parent)
            else:
                # Обычные игроки без щита
                user["is_down"] = True
                user["death_count"] = 0
                Parent.SendStreamMessage(cfg.messages["sleepwalker_crit_lose"].format(dice_msg=dice_msg, user=user_name))
            
    elif total_roll in [2, 3]:
        lost = progression.remove_dreams(user, 100)
        Parent.SendStreamMessage(cfg.messages["sleepwalker_mara"].format(dice_msg=dice_msg, user=user_name, lost=lost))

    elif total_roll in [4, 5, 6, 7, 8]:
        msgs, actual_exp = progression.add_exp(user, 25, file_path)
        level_up_msgs.extend(msgs)
        Parent.SendStreamMessage(cfg.messages["sleepwalker_circles"].format(dice_msg=dice_msg, user=user_name, exp=actual_exp))

    elif total_roll in [9, 10, 11]:
        user["reputation"] = max(0, user["reputation"] - 1)
        user["dirty_count"] = user.get("dirty_count", 0) + 1
        Parent.SendStreamMessage(cfg.messages["sleepwalker_dirt"].format(dice_msg=dice_msg))
        titles.check_dirty_title(user, Parent)   
            
    elif total_roll in [12, 13]:
        lost = progression.remove_dreams(user, 30)
        Parent.SendStreamMessage(cfg.messages["sleepwalker_yama"].format(dice_msg=dice_msg, user=user_name, lost=lost))
        
    elif total_roll in [14, 15, 16, 17]:
        user["mouse_count"] = user.get("mouse_count", 0) + 1
        
        if user["mouse_count"] <= 5:
            msgs, actual_exp = progression.add_exp(user, 75, file_path)
            level_up_msgs.extend(msgs)
            gained = progression.add_dreams(user, 150)
            Parent.SendStreamMessage(cfg.messages["sleepwalker_mouse"].format(dice_msg=dice_msg, user=user_name, exp=actual_exp, dreams=gained))
        else:
            msgs, actual_exp = progression.add_exp(user, 300, file_path)
            level_up_msgs.extend(msgs)
            gained = progression.add_dreams(user, 300)
            Parent.SendStreamMessage("{0} | 🐭 {1} снится, что он мышка Соня. Но спать совсем не хочется. {1} успешно добрался до сокровищ! 💰 +{2} опыта, +{3} грез.".format(dice_msg, user_name, actual_exp, gained))
            user["mouse_count"] = 0 

    elif total_roll in [18, 19]:
        moon_count = user.get("moon_bonus_count", 0)
        bonus_exp = 110 + (moon_count * 5)
        bonus_dreams = 20 + (moon_count * 10)
        
        msgs, actual_exp = progression.add_exp(user, bonus_exp, file_path)
        level_up_msgs.extend(msgs)
        gained = progression.add_dreams(user, bonus_dreams)
        
        Parent.SendStreamMessage(cfg.messages["sleepwalker_moon"].format(dice_msg=dice_msg, exp=actual_exp, dreams=gained, user=user_name))

        user["moon_bonus_count"] = moon_count + 1
        
        if user["moon_bonus_count"] >= 18:
            Parent.SendStreamMessage("🌕 ВНИМАНИЕ! Событие 'Лунный Король' активировано! (Заглушка)")
            user["moon_bonus_count"] = 0 

    # 6. Вывод повышения уровня
    for msg in level_up_msgs:
        Parent.SendStreamMessage(msg)

    # Проверка на титул Лунатик
    titles.check_sleepwalker_title(user, Parent, cfg)

    # 7. Записываем КД
    if total_roll < 20: 
        cooldowns[user_id]["last_raid_time"] = now
        
    save_data_func() 


# 8. пассивка лунатика
def try_cooldown_reset(user, user_name, cooldowns, user_id, Parent):
    if not titles.has_title(user, "Лунатик"):
        return False
    if random.SystemRandom().randint(1, 100) <= 7:
        cooldowns[user_id]["last_raid_time"] = 0
        cooldowns[user_id]["last_dungeon_time"] = 0
        Parent.SendStreamMessage(
            "🌙 Благодаря лунатизму {0} спал наяву во время вылазки и совсем не устал! КД сброшено!".format(user_name)
        )
        return True
    return False