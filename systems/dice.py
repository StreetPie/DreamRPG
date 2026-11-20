# -*- coding: utf-8 -*-
import random
from social import titles

def roll_dice(user, threshold, is_abyss, cfg, Parent=None):
    pity_key = "pity_dungeon" if is_abyss else "pity_raid"
    
    base_roll = random.SystemRandom().randint(1, 20)
    dice_bonus = user.get("dice_bonus", 0)
    
    if cfg.config["enable_pity"]:
        pity_bonus = user.get(pity_key, 0)
    else:
        pity_bonus = 0

    total_roll = base_roll + pity_bonus + dice_bonus

    #ЛОГИКА ПАНДОЧКИ
    is_panda = titles.has_title(user, "Пандочка")
    
    if cfg.config["enable_crit"]:
        if is_panda:
            is_crit_success = (total_roll == 1)  
            is_crit_fail = (total_roll >= 20)    
        else:
            is_crit_success = (total_roll >= 20) # либо base_roll == 20 НЕ МОГУ ОПРЕДЕЛИТЬСЯ
            is_crit_fail = (base_roll == 1)
    else:
        is_crit_success = False
        is_crit_fail = False

    success = ((total_roll >= threshold) or is_crit_success) and not is_crit_fail
    
    display_roll = min(20, base_roll + pity_bonus)
    display_total = display_roll + dice_bonus

    if is_crit_fail:
        display_roll = base_roll
        display_total = base_roll + dice_bonus #логично. если играл в ДнД

    if dice_bonus > 0:
        dice_msg = "🎲 {0} выбросил {1}+{2} = {3}".format(user["name"], display_roll, dice_bonus, display_total)
    else:
        dice_msg = "🎲 {0} выбросил {1}".format(user["name"], display_roll)

    if not success and titles.has_title(user, "Шулер"): #шулер
        reroll = random.SystemRandom().randint(1, 20)
        reroll_total = reroll + pity_bonus + dice_bonus
        
        if cfg.config["enable_crit"]:
            if is_panda:
                re_crit_success = (reroll_total == 1)
                re_crit_fail = (reroll_total >= 20)
            else:
                re_crit_success = (reroll_total >= 20)
                re_crit_fail = (reroll_total == 1)
        else:
            re_crit_success = False
            re_crit_fail = False
            
        re_success = ((reroll_total >= threshold) or re_crit_success) and not re_crit_fail
        
        dice_msg += " | переброс 🎲: {0}".format(reroll)
        
        success = re_success
        is_crit_success = re_crit_success
        is_crit_fail = re_crit_fail
        total_roll = reroll_total

    if cfg.config["enable_pity"]:
        if not success:
            user[pity_key] = user.get(pity_key, 0) + 1
        else:
            user[pity_key] = 0

    return success, dice_msg, is_crit_success, is_crit_fail