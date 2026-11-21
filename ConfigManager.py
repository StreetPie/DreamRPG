# -*- coding: utf-8 -*-
import os
import json
import codecs

class ConfigManager:
    def __init__(self, file_path, parent):
        self.file_path = file_path
        self.parent = parent
        self.config = self.get_defaults()
        self.load()

    def get_defaults(self):
        return {
            "enable_crit": True,
            "enable_pity": True,
            "global_raid_cooldown": 360,
            "enable_sleepwalker": True,
            "enable_raid": True,
            "raid_success_chance": 40,
            "raid_win_exp": 25, "raid_win_dreams": 10, "raid_lose_exp": 5, "raid_lose_dreams": 10,
            "enable_deep": True,
            "deep_success_chance": 45,
            "deep_win_exp": 50, "deep_win_dreams": 25, "deep_lose_exp": 25, "deep_lose_dreams": 10,
            "enable_distort": True,
            "distort_success_chance": 50,
            "distort_win_exp": 150, "distort_win_dreams": 50, "distort_lose_exp": 150, "distort_lose_dreams": 50,
            "global_dungeon_cooldown": 720,
            "enable_abyss": True,
            "abyss_success_chance": 30, "abyss_cost": 100, "abyss_win_exp": 500, "abyss_win_rep": 5,
            "enable_goblin_cave": True,
            "goblin_cave_success_chance": 60, "goblin_cave_cost": 50, "goblin_cave_win_exp": 200, "goblin_cave_win_rep": 2,
            "monster_move_interval": 600,
            "monster_start_strength": 5,
            "monster_penalty_dreams": 30,
            "monster_penalty_exp": 0,
            "monster_reward_exp": 50,
            "monster_reward_dreams": 30,
            "monster_reward_rep": 10,             
            "monster_crit_instant_win": True,
            "monster_locations": ["!рейд", "!погружение", "!искажение", "!бездна", "!пещера"],  #менять при создании новых лок
            "monster_event_active": False
        }

    def load(self):
        if os.path.isfile(self.file_path):
            try:
                with codecs.open(self.file_path, "r", encoding="utf-8-sig") as f:
                    loaded_data = json.load(f)
                    for key, value in loaded_data.items():
                        if key in self.config:
                            self.config[key] = value
                self.parent.Log("ConfigManager", "Настройки загружены.")
            except Exception as e:
                self.parent.Log("ConfigManager", "Ошибка загрузки: " + str(e))
        else:
            self.parent.Log("ConfigManager", "Файл конфига не найден, используются дефолты.")
        
    def save(self):
        try:
            with codecs.open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.parent.Log("ConfigManager", "Ошибка сохранения конфига: " + str(e))

    def get_threshold(self, chance_percent):
        """Переводит шанс в процентах в порог для кубика d20."""
        threshold = 21 - (chance_percent / 5)
        if threshold < 1: threshold = 1
        if threshold > 20: threshold = 20
        return int(threshold)

    def get_monster_locations(self):
        locs = self.config.get("monster_locations", ["!рейд"])
        if isinstance(locs, str):
            return [x.strip() for x in locs.split(",") if x.strip()]
        return locs

    def load_messages(self):
        """Загружает тексты из messages.json"""
        user_dir = os.path.dirname(os.path.dirname(self.file_path))
        msg_path = os.path.join(user_dir, "messages.json")

        
        if os.path.isfile(msg_path):
            try:
                with codecs.open(msg_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                self.parent.Log("ConfigManager", "Ошибка чтения messages.json: " + str(e))
        return default_messages