# Runs every tick (registered via minecraft:tick tag).
# Passenger position is intrinsic; we only copy YAW so the hull turns with the boat.
# The nearest trireme_boat to a display is its own vehicle, so this pairing is correct per-trireme.
execute as @e[type=item_display,tag=trireme_disp] run data modify entity @s Rotation set from entity @e[type=oak_boat,tag=trireme_boat,limit=1,sort=nearest] Rotation
