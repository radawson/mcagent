# Spawn a RIDEABLE trireme = an oak boat carrying a trireme item_display as its passenger.
# The boat gives real water physics; the display gives the trireme shape.
# Board the boat and row. Position auto-follows (passenger); tick.mcfunction syncs the yaw.
# TUNE: transformation translation/scale below to sit the hull at the waterline and centre it.
#
# Tags: the generic "ship_boat"/"ship_disp" pair is what tick.mcfunction and uninstall key on, so
# every ship type shares one tick line. The old trireme_* tags are kept alongside them so anything
# already parked or scripted against them still resolves.
execute at @s run summon minecraft:oak_boat ~ ~ ~ {Tags:["ship_boat","trireme_boat"],Passengers:[{id:"minecraft:item_display",Tags:["ship_disp","trireme_disp"],billboard:"fixed",item:{id:"minecraft:paper",count:1,components:{"minecraft:item_model":"trireme:trireme"}},transformation:{translation:[0f,0.2f,0f],scale:[3.0f,3.0f,3.0f],left_rotation:[0f,0.70710677f,0f,0.70710677f],right_rotation:[0f,0f,0f,1f]}}]}
tellraw @s {"text":"Trireme spawned — board it and row. Clear with /function trireme:uninstall","color":"aqua"}
