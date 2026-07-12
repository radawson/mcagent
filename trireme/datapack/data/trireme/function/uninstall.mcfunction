# Remove all trireme rigs (displays + tagged boats).
kill @e[tag=trireme_disp]
kill @e[type=minecraft:oak_boat,tag=trireme_boat]
tellraw @a {"text":"Triremes cleared.","color":"gray"}
