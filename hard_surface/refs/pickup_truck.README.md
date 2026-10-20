# pickup_truck — structural inventory (TEXT target, no image)

M5's generality subject. There is **no reference image**: this text IS the frozen
target, the same way `refs/README.md`'s written inventory stood in for the
tenement photo in M3. Feed it to the LISTER with
`node scripts/gen.mjs pickup_truck --runner file --inventory refs/pickup_truck.README.md`.

Camera: `refs/pickup_truck.camera.json`, copied from the tenement one and still
flagged `provisional` (30 deg elevation / 45 deg azimuth, unmeasured).

## The subject

A cartoon low-poly pickup truck — chunky, flat cel colours, no texture, the same
family as the tenement block. **Left/right is X, length is Z, y is up**: that is
the vehicle convention the `wheel` composite and V9 both assume.

Roughly **4.8 m long (z), 1.9 m wide (x), 1.8 m tall (y)**, wheels on the
ground.

## Parts

1. **Chassis** — a slab running the whole length, the ground part everything else
   hangs off. Role `chassis`.
2. **Cab** — a box on the front half of the chassis, with a **windshield** and
   **two side windows** as inset boxes (sockets, one per side, a mirror pair).
   Role `cab`.
3. **Hood** — a lower box ahead of the cab, on the chassis.
4. **Bed** — open, behind the cab: a floor plus **three low walls** (two sides
   and the front bulkhead) and a **tailgate** at the back.
5. **Four wheels** — two mirror pairs, radius **0.38 m**, under the chassis at
   the four corners. Role `wheel`.
6. **Two headlights** — a mirror pair on the front face of the hood. Role
   `headlight`.
7. **Two mirrors** — a mirror pair on the cab's sides, at window height. Role
   `mirror`.
8. **Front bumper** and **rear bumper** — full-width bars across the nose and
   the tail.
9. **Roof rack** — optional; a light frame on the cab roof. Leave it out if the
   triangle budget (vehicle: 4000) is tight.

Every part touches the chassis, the cab or the bed. Nothing floats. Minimum
feature: a mirror arm, about 1/40 of the truck's length.

## Open number (owner ruling needed before the blind run)

The V7 vehicle row `wheel_diameter_frac_of_length` is provisional and is currently
read literally as **radius / length**. The inventory above (radius 0.38 m on a
4.8 m truck) gives 0.079, outside the provisional 0.1–0.2 band; measured as
DIAMETER / length it gives 0.158, dead centre. See `src/validate/limits.json`
(`v7._note`). Whichever way it is ratified, the target numbers above do not move
— the limit does.
