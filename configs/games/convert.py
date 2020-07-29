import re

from Qt import QtCore


config_txt = open("Team Fortress 2/bin/GameConfig.txt")
# Configs > Games > Half-Life 2 > GameDir
#                                 Hammer > GameData0 ... MapDir ...
# Configs > Games > Team Fortress 2 > ...
context = ""
depth = 0
prev_line = ""
for line in config_txt:
    if depth == 3:
        active_ini = QtCore.QSettings(f"{context}.ini", QtCore.QSettings.IniFormat)
    elif depth > 3:
        active_ini.beginGroup(context)
    if '{' in line:
        depth += 1  
    elif '}' in line:
        depth -= 1
    elif line.count('"') == 2: # e.g. "Games"
        context = re.search('^\ *"[^"]+"\ *$', line).group(0)
        # ^ contents of quotes
    elif line.count('"') == 4 and depth >= 3: # Key-Value pair
        key, value = re.findall('(?<=")[^"]+?(?=")')
        active_ini.setValue(key, value)
    prev_line = line
