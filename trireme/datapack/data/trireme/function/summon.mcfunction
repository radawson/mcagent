# Spawn a trireme = an oak boat carrying a trireme item_display as its passenger.
# The boat gives real water physics; the display gives the trireme shape.
# Board the boat and row. Position auto-follows (passenger); tick.mcfunction syncs the yaw.
# TUNE: transformation translation/scale below to sit the hull at the waterline and centre it.
execute at @s run summon minecraft:oak_boat ~ ~ ~ {Tags:["trireme_boat"],Passengers:[{id:"minecraft:item_display",Tags:["trireme_disp"],billboard:"fixed",item:{id:"minecraft:paper",count:1,components:{"minecraft:item_model":"trireme:trireme"}},transformation:{translation:[0f,-0.3f,0f],scale:[2.4f,2.4f,2.4f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}]}
tellraw @s {"text":"Trireme spawned — board it and row. Clear with /function trireme:uninstall","color":"aqua"}
