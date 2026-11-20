# -*- coding: utf-8 -*-

def migrate_users(users_data):
    updated_count = 0

    for user_id, user in users_data.items():
        if "is_participating" not in user:
            user["is_participating"] = False
            updated_count += 1
        
        if "sleepwalker_count" not in user:
            user["sleepwalker_count"] = 0
            updated_count += 1

        if "mouse_count" not in user:
            user["mouse_count"] = 0
            updated_count += 1

        if "dirty_count" not in user:
            user["dirty_count"] = 0
            updated_count += 1
            
        if "moon_bonus_count" not in user:
            user["moon_bonus_count"] = 0
            updated_count += 1

        if "sleep_count" not in user:
            user["sleep_count"] = 0
            updated_count += 1

        if "solo_kills" not in user:
            user["solo_kills"] = 0
            updated_count += 1

        if "babysitter_shield" not in user:
            user["blessing_shield"] = False
            updated_count += 1
            
        if "blessings" not in user:
            user["blessings"] = {}

        if "titles" not in user:
            if user.get("title"):
                user["titles"] = [user["title"]]
            else:
                user["titles"] = []
            updated_count += 1

        if "levelup_choices" not in user:
            user["levelup_choices"] = []
            updated_count += 1

        if "crit_streak" not in user:
            user["crit_streak"] = 0
            updated_count += 1

        if "is_down" not in user:
            user["is_down"] = user.get("is_trapped", False)
            updated_count += 1

        if "dice_bonus" not in user:
            user["dice_bonus"] = 0
            updated_count += 1

        if "pity_raid" not in user:
            user["pity_raid"] = 0
            updated_count += 1

        if "pity_dungeon" not in user:
            user["pity_dungeon"] = user.get("pity_abyss", 0)
            if "pity_abyss" in user:
                del user["pity_abyss"] 
            updated_count += 1

        if "rescues_count" not in user:
            user["rescues_count"] = 0
            updated_count += 1

        if "blessing_target" not in user:
            user["blessing_target"] = ""
            updated_count += 1

        if "reputation" not in user:
            user["reputation"] = 0
            updated_count += 1

    return users_data, updated_count

def migrate_global_state(state_data):
    if not isinstance(state_data, dict):
        state_data = {}

    if "active_event" not in state_data:
        state_data["active_event"] = None
    if "event_progress" not in state_data:
        state_data["event_progress"] = 0
    if "completed_events" not in state_data:
        state_data["completed_events"] = []
    if "world_buffs" not in state_data:
        state_data["world_buffs"] = {}

    return state_data