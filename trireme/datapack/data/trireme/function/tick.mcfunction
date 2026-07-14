# Runs every tick (registered via minecraft:tick tag).
# Passenger position is intrinsic; we only copy YAW so the hull turns with its boat.
# Generic over SHIP TYPE: any rideable ship tags its display "ship_disp" and its boat "ship_boat",
# so one line covers triremes, merchantmen, and anything we add later. The nearest ship_boat to a
# display is its own vehicle (distance ~0), so the pairing stays correct with mixed fleets.
# Static ships (ship_parked / ship_moored) are deliberately NOT in here -- they have no vehicle,
# their rotation is set once at summon, and ticking them would be pure waste.
execute as @e[type=item_display,tag=ship_disp] run data modify entity @s Rotation set from entity @e[type=oak_boat,tag=ship_boat,limit=1,sort=nearest] Rotation
