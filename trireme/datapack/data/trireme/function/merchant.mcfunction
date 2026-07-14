# Spawn a RIDEABLE merchantman = an oak boat carrying a merchantman item_display as its passenger.
# Same rig as trireme:summon -- boat gives the water physics, display gives the shape.
#
# SCALE: 3.0, not the trireme's 4.0, and that is deliberate. The merchantman model is 1.81 blocks
# long where the trireme model is 3.0. Rendering both at 4.0 would make the trader 60% of the
# warship's length, when the real ratio (Kyrenia 14 m vs trireme 37 m) is 38%. Scale 3.0 gives a
# 5.4-block ship that reads correctly as a fat little coaster next to a 12-block trireme.
# This is the one number worth eyeballing in-game.
execute at @s run summon minecraft:oak_boat ~ ~ ~ {Tags:["ship_boat","merchant_boat"],Passengers:[{id:"minecraft:item_display",Tags:["ship_disp","merchant_disp"],billboard:"fixed",item:{id:"minecraft:paper",count:1,components:{"minecraft:item_model":"trireme:merchantman"}},transformation:{translation:[0f,0.2f,0f],scale:[3.0f,3.0f,3.0f],left_rotation:[0f,0.70710677f,0f,0.70710677f],right_rotation:[0f,0f,0f,1f]}}]}
tellraw @s {"text":"Merchantman spawned — board it and sail. Clear with /function trireme:uninstall","color":"gold"}
