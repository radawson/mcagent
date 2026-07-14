# MACRO. Moor a STATIC merchantman alongside a quay -- no boat, no physics, just a hull in the water.
# Call with:  /function trireme:moor_at {scale:"7.5",sink:"-4.5"}
# Or use the zero-arg wrappers:  trireme:moor  (coaster)  /  trireme:moor_large  (deep-sea trader)
#
# HOW TO USE: stand on the quay deck and look ALONG the quay (not out to sea). The hull inherits
# your yaw, so it will lie parallel to the wall -- moored alongside, which is how a trader unloads.
# Looking out to sea would berth it bow-on, into the stone.
#
# scale -- model is 1.8125 blocks long, so rendered length = scale * 1.8125 m.
#          7.5  -> 13.6 m x 4.7 m beam   (Kyrenia: 14 m x 4.4 m)
#          14.0 -> 25.4 m x 8.8 m beam   (a big Phoenician/grain trader)
# sink  -- blocks to drop the display below your feet, so the waterline crosses the belly rather
#          than the keel. Our quay deck sits 2 m above the sea, and the hull needs ~1.3 m of
#          draught under it, hence -4.5 at scale 7.5. TUNE THIS ONE NUMBER IN-GAME: if the ship
#          rides high and shows keel, sink it further; if the deck is awash, raise it.
$execute at @s run summon minecraft:item_display ~ ~$(sink) ~ {Tags:["ship_moored","ship_new"],billboard:"fixed",item:{id:"minecraft:paper",count:1,components:{"minecraft:item_model":"trireme:merchantman"}},transformation:{translation:[0f,0f,0f],scale:[$(scale)f,$(scale)f,$(scale)f],left_rotation:[0f,0.70710677f,0f,0.70710677f],right_rotation:[0f,0f,0f,1f]}}
# Give it the player's yaw, then drop the marker tag so the NEXT moor doesn't re-rotate this one.
execute as @e[type=item_display,tag=ship_new] run data modify entity @s Rotation set from entity @p Rotation
tag @e[type=item_display,tag=ship_new] remove ship_new
tellraw @s {"text":"Merchantman moored. Clear nearby with: /kill @e[tag=ship_moored,distance=..16]","color":"gold"}
