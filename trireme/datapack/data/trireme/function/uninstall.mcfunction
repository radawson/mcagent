# Remove ALL ship rigs of every type -- rideable, parked, and moored.
# Generic tags first; the legacy trireme_* tags are still killed so anything spawned by an older
# version of this pack is cleaned up too.
kill @e[type=item_display,tag=ship_disp]
kill @e[type=item_display,tag=ship_parked]
kill @e[type=item_display,tag=ship_moored]
kill @e[type=item_display,tag=trireme_disp]
kill @e[type=item_display,tag=trireme_parked]
kill @e[type=minecraft:oak_boat,tag=ship_boat]
kill @e[type=minecraft:oak_boat,tag=trireme_boat]
tellraw @a {"text":"All ships cleared.","color":"gray"}
