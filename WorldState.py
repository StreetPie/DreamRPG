# -*- coding: utf-8 -*-
import os
import json # ПЕРЕНЕСТИ В ПАПКУ globalEvents
import io

class WorldState:
    def __init__(self, file_path, parent):
        self.file_path = file_path
        self.parent = parent
        self.data = {
            "active_event": None,
            "event_progress": 0,
            "completed_events": [],
            "world_buffs": {}
        }
        self.load()

    def load(self):
        if os.path.isfile(self.file_path):
            try:
                with io.open(self.file_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception as e:
                self.parent.Log("WorldState", "Ошибка загрузки: " + str(e))
                self.save()
        else:
            self.save()

    def save(self):
        try:
            with io.open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.parent.Log("WorldState", "Ошибка сохранения: " + str(e))

    def start_event(self, event_id):
        self.data["active_event"] = event_id
        self.data["event_progress"] = 0
        self.save()

    def end_event(self):
        if self.data["active_event"]:
            if self.data["active_event"] not in self.data["completed_events"]:
                self.data["completed_events"].append(self.data["active_event"])
            self.data["active_event"] = None
            self.data["event_progress"] = 0
            self.save()

    def add_progress(self, amount):
        if self.data["active_event"]:
            self.data["event_progress"] += amount
            self.save()
            return True
        return False

    def is_event_active(self, event_id=None):
        if event_id:
            return self.data["active_event"] == event_id
        return self.data["active_event"] is not None


    # --- Подкроватный монстр ---
    def get_monster(self):
        if "monster" not in self.data:
            self.data["monster"] = {
                "active": False,
                "location": None,
                "strength": 0,
                "last_move_time": 0,
                "defeated_by": [],       # список uid
                "total_encounters": 0,
                "total_defeats": 0
            }
            self.save()
        return self.data["monster"]

    def start_monster(self, locations, start_strength=0):
        import random, time
        m = self.get_monster()
        m["active"] = True
        m["location"] = random.SystemRandom().choice(locations)
        m["strength"] = start_strength 
        m["last_move_time"] = time.time()
        m["defeated_by"] = []
        m["total_encounters"] = 0
        m["total_defeats"] = 0
        self.save()
        return m

    def stop_monster(self):
        m = self.get_monster()
        m["active"] = False
        m["location"] = None
        m["strength"] = 0
        m["defeated_by"] = []
        self.save()

    def move_monster(self, locations):
        import random, time
        m = self.get_monster()
        if not m["active"]:
            return
        old = m["location"]
        choices = [l for l in locations if l != old]
        if not choices:
            choices = locations
        m["location"] = random.SystemRandom().choice(choices)
        m["last_move_time"] = time.time()
        self.save()

    def weaken_monster(self, amount=1):
        m = self.get_monster()
        m["strength"] = max(0, m["strength"] - amount)
        self.save()

    def strengthen_monster(self, amount=1, max_strength=None):
        m = self.get_monster()
        new_str = m["strength"] + amount
        if max_strength is not None:
            new_str = min(max_strength, new_str)
        m["strength"] = new_str
        self.save()

    def add_monster_contributor(self, user_id):
        m = self.get_monster()
        if user_id not in m["defeated_by"]:
            m["defeated_by"].append(user_id)
        m["total_encounters"] = m.get("total_encounters", 0) + 1
        self.save()

    def monster_is_here(self, command):
        m = self.get_monster()
        return m["active"] and m["location"] == command