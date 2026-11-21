# -*- coding: utf-8 -*-
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import json
import random
import time
import codecs
import Migrator
import WorldState
import ConfigManager
from activities import raids, dungeons, sleepwalker
from social import states, titles, skillCommands
from systems import dice, expSystem, progression
from globalEvents import challenges, events, treats

random.seed(time.time() * 1000) #чтобы рандом нормально рандомился правильно

ScriptName = "DreamRPG"
Website = None
Description = "Мини-RPG со сном"
Creator = "StreetPie"
Version = "0.5.0"

# ФАЙЛЫ ДАННЫХ
DATA_FILE = "rpg_data.json"
STATE_FILE = "global_state.json"

# ГЛОБАЛЬНЫЕ ПЕРЕМЕННые
users_data = {}
cooldowns = {}
file_path = ""
world = None
cfg = None 



def Init():
    Parent.Log(ScriptName, "-------------------=- Запуск DreamRPG -=-------------------")
    global file_path, users_data, world, cfg
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    user_dir = os.path.join(script_dir, "user_data")
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
        
    data_dir = os.path.join(user_dir, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Пути к файлам
    file_path = os.path.join(data_dir, DATA_FILE)           
    config_path = os.path.join(data_dir, "config.json")     
    
    state_path = os.path.join(user_dir, STATE_FILE)       

    world = WorldState.WorldState(state_path, Parent)
    cfg = ConfigManager.ConfigManager(config_path, Parent)
    cfg.messages = cfg.load_messages() 

    if os.path.isfile(file_path):
        try:
            with codecs.open(file_path, "r", encoding="utf-8") as f:
                users_data = json.load(f)

            # Миграция данных
            users_data, changes = Migrator.migrate_users(users_data)

            if changes > 0:
                Parent.Log(ScriptName, "Миграция: обновлено {0} профилей.".format(changes)) #самый главный лог
                save_data()
            else:
                Parent.Log(ScriptName, "Миграция не требуется.")

        except Exception as e:
            Parent.Log(ScriptName, "Ошибка загрузки/миграции: " + str(e))
            users_data = {}
    else:
        users_data = {}

def Execute(data):
    if not data.IsChatMessage():
        return

    command = data.GetParam(0).lower()
    user_id = data.User
    user_name = data.UserName


    if command == "!сброс":
        if user_id in users_data:
            del users_data[user_id]
            if user_id in cooldowns: del cooldowns[user_id]
            save_data()
            Parent.SendStreamMessage("{0}, прогресс профиля сброшен!".format(user_name))
        return

    if command != "!сон" and user_id not in users_data:
        Parent.SendStreamMessage("{0}, сначала погрузись в сон командой !сон".format(user_name))
        return

    if command == "!сон":
        if user_id in users_data:
            Parent.SendStreamMessage("{0}, ты уже являешься участником сна.".format(user_name))
            return

        users_data[user_id] = {
            "name": user_name, "total_exp": 0, "dreams": 100,
            "raids_total": 0, "raids_success": 0, "raids_fail": 0,
            "reputation": 0, "title": "", "titles": [],
            "dice_bonus": 0, "pity_raid": 0, "pity_dungeon": 0, 
            "is_down": False, "rescues_count": 0, "crit_streak":0, "blessing_target": "",
            "solo_kills": 0, "is_participating": False,  
            "sleep_count": 0, "babysitter_shield": False,
            "dirty_count": 0, "sleepwalker_count": 0, "sleepwalker_seen": [],
            "mouse_count": 0, "moon_bonus_count": 0, "blessings": [],
            "levelup_choices": []
        }
        cooldowns[user_id] = {"last_raid_time": 0, "last_dungeon_time": 0}
        Parent.SendStreamMessage("{0} погружается в сон...".format(user_name))
        save_data()
        return

        #registered users
    user = users_data[user_id]   
    
    if user_id not in cooldowns:
        cooldowns[user_id] = {"last_raid_time": 0, "last_dungeon_time": 0}
    now = time.time()

    if command == "!помочь":
        skillCommands.handle_rescue(user, user_name, users_data, data, Parent, save_data, cfg, file_path)
        return

    if command == "!благословить":
        skillCommands.handle_blessing(user, user_name, users_data, data, Parent, save_data, cfg)
        return

    if command == "!титулы":
        titles.list_titles(user, user_name, Parent, cfg)
        return

    if command == "!ивент":
        if not titles.has_title(user, "Модератор"):
            Parent.SendStreamMessage("{0}, команда доступна только модераторам и стримеру.".format(user_name))
            return
        events.handle_event_command(data, world, Parent, users_data, save_data, cfg)
        return

    if not states.check_player_state(user, user_name, command, Parent, cfg):
        return

    # Автовыдача титула модератора
    # Проверяем, является ли пользователь стримером (по нику) НАпомнить алинушке или себе поменять
    is_broadcaster = (user_name.lower() == "streetpie") 

    is_mod = Parent.HasPermission(user_name, "Moderator", "")
    
    titles.check_moderator_title(user, Parent, is_mod, is_broadcaster)


        #ПРОФИЛЬ
    if command == "!профиль" or command == "!profile":
        level, exp_inside, next_level_exp = progression.get_level_by_total_exp(user.get("total_exp", 0), file_path)
        
        levels = progression._load_levels(file_path)
        next_lvl = level + 1
        
        if next_lvl in levels:
            next_total_exp = levels[next_lvl]  #from levels.json
        else:
            next_total_exp = user.get("total_exp", 0) + next_level_exp
            
        title_display = user["title"] if user["title"] != "" else "Нет"
        
        if titles.has_title(user, "Мертв Внутри"):
            down_status = " | ПОВЕРЖЕН Навсегда 💀"
        elif user.get("is_down"):
            down_status = " | 🌑 ПОВЕРЖЕН"
        else:
            down_status = ""

        msg = (
            u"[Профиль] {} |"
            u"Ур: {}|"
            u"XP: {}/{}|"
            u"Грезы: {}|"
            u"Репутация: {}|"
            u"Титул: {}|"
            u"Вылазки: {} (win: {}, lose: {}){}"
        ).format(
            user["name"], level, user.get("total_exp", 0), next_total_exp,
            user["dreams"], user["reputation"], title_display,
            user["raids_total"], user["raids_success"], user["raids_fail"],
            down_status
        )

        Parent.SendStreamMessage(msg)
        return  
            #RAIDS
    elif command in ["!рейд", "!погружение", "!искажение", "!уложить", "!лунатик"]:
        raids.handle_raid(command, user, user_name, users_data, data, cfg, file_path, cooldowns, user_id, now, Parent, save_data, world)
            #Dungeons
    elif command in ["!бездна", "!пещера"]:
        dungeons.handle_dungeon(command, user, user_name, users_data, cfg, file_path, cooldowns, user_id, now, Parent, save_data, world)

    if command == "!пассивка":
        skillCommands.handle_passive_choice(user, user_name, data, cfg, file_path, Parent, save_data)
    return


def Tick():
    events.tick(world, cfg, Parent, ScriptName)

def start_monster_event():
    events.ui_start_monster(world, cfg, Parent)

def stop_monster_event():
    events.ui_stop_monster(world, Parent, cfg)

def open_levels_file():
    try:
        data_dir = os.path.dirname(file_path)
        levels_path = os.path.join(data_dir, "levels.json")
        
        if not os.path.isfile(levels_path):
            progression._load_levels(file_path)
            
        os.system('cmd /c start "" "{}"'.format(levels_path))
    except Exception as e:
        Parent.Log(ScriptName, "Ошибка в open_levels_file: " + str(e))

def open_messages_file():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        msg_path = os.path.join(script_dir, "user_data", "messages.json")
        
        if not os.path.isfile(msg_path):
            default_msgs = {
                "raid_win": "🎲 {dice_msg} | ⚔️ Успех! +{exp} опыта, +{dreams} грез.",
                #заглушка
            }
            with codecs.open(msg_path, "w", encoding="utf-8") as f:
                json.dump(default_msgs, f, indent=4, ensure_ascii=False)
                
        os.system('cmd /c start "" "{}"'.format(msg_path))
    except Exception as e:
        Parent.Log(ScriptName, "Ошибка в open_messages_file: " + str(e))


def save_data():  #потом вынести в отдельный файл
    try:
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))

        with codecs.open(file_path, "w", encoding="utf-8") as f:
            json.dump(users_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        Parent.Log(ScriptName, "ОШИБКА СОХРАНЕНИЯ: " + str(e))

def ReloadSettings(jsonData):
    try:
        cfg.load()
        
        want_active = cfg.config.get("monster_event_active", False)
        is_active = world.get_monster().get("active", False)
        
        if want_active and not is_active:
            from globalEvents import events
            events._start_monster(world, Parent, cfg)
        elif not want_active and is_active:
            from globalEvents import events
            events._stop_monster(world, Parent)
            
        Parent.Log(ScriptName, "Настройки обновлены.")
    except Exception as e:
        Parent.Log(ScriptName, "Ошибка при обновлении: " + str(e))

