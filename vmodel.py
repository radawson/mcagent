#!/usr/bin/env python3
"""
Shared vertical model + radii -- the SINGLE SOURCE OF TRUTH for Atlantis geometry.

WHY THIS EXISTS: atlantis_cmds.py, temple_gen.py, city_radial.py and dock_gen.py each independently
duplicated the vertical math. Rebasing sea level (scratchpad void -> whirled's y=63) would mean
changing it in four places, and missing one buries the temple. Derive everything from here instead.

ANCHOR IS SEA LEVEL, not the build floor. Every other elevation hangs off it.

    SCRATCHPAD (void test dimension): SEA = -30   (floor pinned near the -61 platform)
    WHIRLED    (real overworld):      SEA =  63   (vanilla sea level)

================================================================================================
v2 -- THE CRAMPED-RINGS REVISION.  Rick, flying it: "the land rings feel VERY cramped... having
water passages BEHIND the quay with no access is odd... at scale, how WIDE should the grand canal
be?  Given the scale and grandeur of the temple, this feels sandwiched in."

Every one of those was a symptom of the SAME root cause: I took Plato's PLAN dimensions literally
and then eyeballed the THIRD DIMENSION. Three errors, all found by going back to the text:

1. THE CANAL WAS 6x TOO NARROW.  `canal_w = 7` was a hardcoded half-width -- a magic number set for
   the S=30 smoke test that never scaled with S while every other dimension went through m2b().
   §B: "a canal of THREE HUNDRED FEET IN WIDTH and ONE HUNDRED FEET IN DEPTH." A stade is 600 feet,
   so 300 ft = HALF A STADE = 92 m. We built 15 m. The canal was DEEPER (31 m) THAN IT WAS WIDE --
   a mineshaft, not a waterway.  ==> ft2b() now exists so Plato's foot-measures are exact.

2. THE BANKS WERE A CURB, NOT A BANK.  y_land was sea+8 and tunnel headroom was sea+6, which left
   a TWO-METRE rock roof over a ship tunnel with a road on top. §B: "they covered over the channels
   so as to leave a way underneath for the ships; FOR THE BANKS WERE RAISED CONSIDERABLY ABOVE THE
   WATER." The height is not decoration -- it is what makes the roofed channels possible at all.
   And it is what makes §B's "they HOLLOWED OUT DOUBLE DOCKS, having roofs formed out of the native
   rock" physically possible: you cannot quarry a dock into an 8 m cliff.
   ==> Rings now STEP UP toward the centre: L2 +24, L1 +36, citadel +55. Ship headroom 14 m, so a
       merchantman passes through the tunnels WITH ITS MAST UP (Rick's call).

3. THE MERCHANTS WERE IN THE WRONG RINGS.  The big one, and Rick found it by reasoning about
   DEFENCE, not about Plato: "it doesn't make sense to put docks with access up to the city in the
   OUTER walls - a massive vulnerability... merchant cargo would want protection from raiders,
   pirates, and the sea itself."  Going back to the text, he is exactly right and the text says so:
       §B: the canal "they carried through to THE OUTERMOST ZONE, making a passage from the sea up
           to this, WHICH BECAME A HARBOUR"
       §E: "THE CANAL AND THE LARGEST OF THE HARBOURS were full of vessels and merchants coming
           from all parts... din and clatter of all sorts night and day"
   The commercial harbour is W3, the OUTERMOST water ring -- walled in brass, entered only through
   the gated canal mouth. Protected exactly as Rick argued.
   And the clincher, which I had quoted and never read: §B says the inter-ring passages leave
       "room for a SINGLE TRIREME to pass out of one zone into another."
   YOU CANNOT RUN A CARGO ECONOMY THROUGH A ONE-SHIP-AT-A-TIME ROOFED TUNNEL. That is not a trade
   route, it is a NAVAL SALLY PORT. So W2 and W1 are the ARSENAL, and the 44 m flooded gallery
   Rick found dead behind the quay was never wrong -- it was the arsenal with the wrong tenant.
   ==> TRADE lives on W3. THE NAVY lives on the inner faces of L1/L2, facing W1/W2. (Piraeus.)

"DOUBLE DOCKS" (§B) -- Rick reads it HORIZONTALLY, not as stacked levels: sheds two ships deep,
nose to tail. That is also the standard reading of double neosoikoi. ==> dock_depth 44 -> 88 m.
================================================================================================
"""
import math

STADE_M = 185.0
FEET_PER_STADE = 600.0      # Plato gives the canal, the ditch and the bridge in FEET, not stades.

PRESETS = {"scratchpad": -30, "whirled": 63}


class VModel:
    def __init__(self, S, sea=-30, cx=-10000, cz=10000):
        self.S = S
        self.cx, self.cz = cx, cz
        self.sea = sea

        def m2b(m):
            return max(1, round(m * S / STADE_M))

        def ft2b(ft):
            """Greek feet -> blocks. 600 ft = 1 stade = S blocks. Keeps Plato's foot-measures EXACT
            instead of round-tripping them through metres and losing them (see canal, above)."""
            return max(1, round(ft * S / FEET_PER_STADE))
        self.m2b, self.ft2b = m2b, ft2b

        # ------------------------------------------------------------------ THE CANAL (§B, LITERAL)
        # "a canal of three hundred feet in width and one hundred feet in depth and fifty stadia in
        # length, which they carried through to the outermost zone... which became a harbour"
        self.canal_w     = ft2b(300)            # 300 ft = HALF A STADE = 92 m at S=185
        self.canal_hw    = self.canal_w // 2    # the generator works in half-widths
        self.canal_floor = sea - ft2b(100)      # 100 ft = 31 m deep
        self.canal_len   = 50 * S               # 50 stades out to the open sea

        # ------------------------------------------------- THE INTER-RING PASSAGES (§B, LITERAL)
        # "leaving room for a SINGLE TRIREME to pass out of one zone into another."
        # DECOUPLED from canal_w, which is the bug that hid the canal error: tun_hw was defined as
        # `canal_w - 1`, so ONE knob was doing TWO jobs and fixing the canal would have blown the
        # tunnels out to 91 m. They are different things and the text sizes them differently.
        # A trireme is 6 m in the beam; 15 m of channel is one ship with working clearance.
        self.tunnel_w    = m2b(15)
        self.tunnel_hw   = self.tunnel_w // 2
        self.bridge_w    = ft2b(100)            # "the bridge... the sixth part of a stadium" = 31 m
        self.bridge_hw   = self.bridge_w // 2

        # --------------------------------------------------------------------------- THE VERTICAL
        # Plato fixes ONE depth (the canal). Everything else below is ours, but DERIVED, not guessed:
        # each ring must be tall enough to bore a roofed ship channel through it AND carry a road
        # and a city on the roof.
        self.ring_floor = sea - m2b(10)         # water rings: 10 m. Deep water; a trireme draws 1-2.
        self.headroom   = m2b(14)               # ship clearance in the tunnels -- MAST UP (Rick)
        self.roof_min   = m2b(10)               # minimum native rock over a channel

        self.y_l2    = sea + m2b(24)            # OUTER land ring surface  (3 stades wide)
        self.y_l1    = sea + m2b(36)            # INNER land ring surface  (2 stades wide)
        self.y_isle  = sea + m2b(55)            # citadel plateau, cliff-sided
        self.y_belt  = sea + m2b(12)            # the outer city, 50 stades of it: low ground
        self.wall_h  = m2b(8)                   # every circuit wall stands 8 m above ITS OWN ring
        self.quay_y  = sea + m2b(2)             # working wharf: you unload ONTO this, not 24 m up
        self.clear_top = sea + m2b(140)         # in whirled, air out everything above the design

        # SANITY: the roof over each tunnel must actually exist. This is the check whose absence let
        # a 2 m roof ship. If it ever fails, the ring is too short for the headroom you asked for.
        for nm, y in (("L2", self.y_l2), ("L1", self.y_l1)):
            roof = (y - sea) - self.headroom
            if roof < self.roof_min:
                raise ValueError(
                    f"{nm} surface is sea+{y-sea} but headroom is {self.headroom} -> only {roof} "
                    f"blocks of rock roof over the ship channel (need >= {self.roof_min}). "
                    f"Raise the ring or lower the headroom.")

        # ---------------------------------------------------------- THE ARSENAL (W1/W2, inner faces)
        # Ship sheds to the EXCAVATED dimensions at Zea, the war harbour of Athens (Dragatsis/
        # Doerpfeld; corroborated by Vitruvius): shed ~40 m long, just 6 m WIDE, interior 4.026 m.
        # A trireme is just under 37 m, hull 2.15 m above water, DRAUGHT ~1 m -- so they were not
        # moored floating, they were HAULED OUT up a slipway and stored DRY. The shed is a SLOT.
        # DOUBLE DOCKS (§B), read horizontally (Rick): two ships nose-to-tail in one gallery.
        self.shed_len   = m2b(40)
        self.dock_depth = m2b(88)        # TWO 40 m sheds in line + the back wall = "double"
        self.shed_width = m2b(6)
        self.shed_pier  = m2b(3)         # masonry between sheds
        self.slip_mouth = sea - m2b(2)   # slipway floor at the sea end: the ship floats in
        self.slip_head  = sea + m2b(3)   # ...and is hauled UP to here, dry, at the back
        self.shed_roof  = sea + m2b(7)   # underside of the native-rock roof

        # ------------------------------------------------------- THE EMPORION (W3, the great harbour)
        # The commercial harbour. Merchantmen moor AFLOAT and ALONGSIDE (they draw too much to haul
        # out, and the point is to UNLOAD them). Quays on both shores of W3:
        #   OUTER shore (r_w3, the city side)  -- the working wharves + bonded warehouses. The din
        #     and clatter. Backed by 50 stades of dense city, NOT by an exposed outer wall: this is
        #     Rick's protection argument, and it is why the cargo lives on this shore.
        #   INNER shore (r_l2, L2's outer cliff) -- the official side. Customs, the deigma (the
        #     sample-market), grand stairs up into the royal rings, brass-crested wall above.
        self.quay_w      = m2b(20)       # the working wharf, built out into the harbour
        self.store_depth = m2b(40)       # bonded warehouse gallery cut back into the shore
        self.store_roof  = sea + m2b(14) # tall vaults -- these take cargo, not hulls

        # --------------------------- radii (literal Critias figures, PLATO_SOURCE §B/§E) -----------
        self.r_isl  = 2.5 * S                # citadel island, diameter 5 stades
        self.r_w1   = 3.5 * S                # water 1  (width 1)  -- ARSENAL
        self.r_l1   = 5.5 * S                # land  1  (width 2)
        self.r_w2   = 7.5 * S                # water 2  (width 2)  -- ARSENAL
        self.r_l2   = 10.5 * S               # land  2  (width 3)
        self.r_w3   = 13.5 * S               # water 3  (width 3)  -- THE EMPORION. core edge, d=27
        self.r_belt = 63.5 * S               # great wall: 50 stades past the core (diam 127)

    def zones(self):
        return [
            (0, self.r_isl, "island"), (self.r_isl, self.r_w1, "water"),
            (self.r_w1, self.r_l1, "land1"), (self.r_l1, self.r_w2, "water"),
            (self.r_w2, self.r_l2, "land2"), (self.r_l2, self.r_w3, "water"),
            (self.r_w3, self.r_belt, "belt"),
        ]

    def surface_of(self, kind):
        return {"island": self.y_isle, "land1": self.y_l1,
                "land2": self.y_l2, "belt": self.y_belt}[kind]

    def __repr__(self):
        s = self.sea
        return (f"VModel(S={self.S} sea={s})\n"
                f"    canal    {self.canal_w} wide x {s - self.canal_floor} deep "
                f"(Plato: 300ft x 100ft)\n"
                f"    tunnel   {self.tunnel_w} wide, {self.headroom} headroom (single trireme, mast up)\n"
                f"    bridge   {self.bridge_w} wide (Plato: 1/6 stade)\n"
                f"    rings    floor {self.ring_floor}  L2 {self.y_l2} (+{self.y_l2-s})  "
                f"L1 {self.y_l1} (+{self.y_l1-s})  citadel {self.y_isle} (+{self.y_isle-s})\n"
                f"    roofs    over L2 {(self.y_l2-s)-self.headroom}m rock | "
                f"over L1 {(self.y_l1-s)-self.headroom}m rock\n"
                f"    arsenal  gallery {self.dock_depth} deep (double sheds), quay {self.quay_y}\n"
                f"    emporion quay {self.quay_w} wide, stores {self.store_depth} deep")


if __name__ == "__main__":
    for name, sea in PRESETS.items():
        print(f"--- {name} ---")
        print(VModel(185, sea), "\n")
