# -*- coding: utf-8 -*-
from social import titles

def check_player_state(user, user_name, command, Parent, cfg):
    if titles.has_title(user, "Мертв Внутри"):
        return True

    allowed_commands = ["!профиль", "!profile", "!титулы", "!сон", "!сброс"]

    if user.get("is_down", False) and command not in allowed_commands:
        msg = cfg.messages["is_down_warning"].format(user=user_name)
        Parent.SendStreamMessage(msg)
        return False
    return True

