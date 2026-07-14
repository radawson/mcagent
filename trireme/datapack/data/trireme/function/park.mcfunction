# Park a STATIC trireme -- no boat, no physics. For ships drawn up in the naval sheds (neosoikoi),
# and as a platform you can climb on. Stand at the HEAD of the slipway, face DOWN the shed toward
# the water, and run this. The display inherits your yaw, so the hull lies along the slot.
#
# SCALE FIX (was 4.0 -> now 12.0). 4.0 rendered a 12 m trireme, and we then built 40 m ship sheds
# off the Zea excavation: we would have been parking a toy in a boathouse. The model is 3.0 blocks
# long, so TRUE SCALE is 37/3.0 = 12.3. At 12.0 the ship is 36 m long with a 4.5 m beam, which
# fits the 40 m shed with clearance and leaves ~0.75 m either side in the 6 m slot. That the model's
# own proportions land inside the real shed dimensions is a good sign we got the hull right.
#
# Ships were hauled out DRY (trireme draught was only ~1 m), so no sink offset -- she sits on the
# slipway, not in the water. Summon her standing on the slip surface.
execute at @s run summon minecraft:item_display ~ ~ ~ {Tags:["ship_parked","ship_new"],billboard:"fixed",item:{id:"minecraft:paper",count:1,components:{"minecraft:item_model":"trireme:trireme"}},transformation:{translation:[0f,0.0f,0f],scale:[12.0f,12.0f,12.0f],left_rotation:[0f,0.70710677f,0f,0.70710677f],right_rotation:[0f,0f,0f,1f]}}
execute as @e[type=item_display,tag=ship_new] run data modify entity @s Rotation set from entity @p Rotation
tag @e[type=item_display,tag=ship_new] remove ship_new
tellraw @s {"text":"Trireme parked (36 m, true scale). Remove with: /kill @e[tag=ship_parked,distance=..48]","color":"aqua"}
