# L2 replica refs - Logitech G502 HERO (wired)

Images saved in `refs/L2/` (git-ignored). Downloaded 2026-10-22.

| file | source URL | shows |
|---|---|---|
| top-angle-gallery-1.png | https://resource.logitechg.com/w_1088,c_pad,q_auto,f_png,dpr_1.0/d_transparent.gif/content/dam/gaming/en/non-braid/hyjal-g502-hero/2025/g502-hero-mouse-top-angle-gallery-1.png | official top view, near-orthographic, nose up. Plan outline, button split lines, wheel slot, G7/G8, G9, mode button, thumb rest flare |
| profile-right-angle-gallery-6.png | .../g502-hero-mouse-profile-right-angle-gallery-6.png (same base) | right profile, slightly elevated camera. Crest line, underside lift, right grip panel break |
| profile-left-angle-gallery-2.png | .../g502-hero-mouse-profile-left-angle-gallery-2.png | left profile (elevated). G4/G5/G6 thumb buttons, DPI LED bar, thumb rest |
| high-back-angle-gallery-4.png | .../g502-hero-mouse-high-back-angle-gallery-4.png | rear 3/4. Palm cover break, thumb-rest part break, rear notch |
| bottom-angle-gallery-3.png | .../g502-hero-mouse-bottom-angle-gallery-3.png | underside 3/4 (weights door; not modelled) |
| registered.npz | derived (replica/L2/ref_extract.py) | top + side silhouettes on a 0.25 mm grid, registered by spec length/height |

Product page the gallery came from: https://www.logitechg.com/en-us/products/gaming-mice/g502-hero-gaming-mouse.910-005469.html

Spec (dimensions): Logitech support article 360023303534 "Specification G502 HERO Gaming Mouse"
https://support.logi.com/hc/en-gb/articles/360023303534-Specification-G502-HERO-Gaming-Mouse - length 132 mm, width 75 mm,
height 40 mm, weight 121 g (mouse only). Same figures on https://www.ifixit.com/Device/Logitech_G502_Hero and
https://ple.com.au/products/633789/logitech-g502-hero-optical-gaming-mouse (7.5 x 13.2 x 4 cm).

No manufacturer dimension drawing / true orthographic blueprint was found; the product shots are the best public refs.
Registration: top 0.179 mm/px (length), width then reads 76.5 mm vs 75 spec (+2 %, perspective). Side shots are elevated,
so side heights are registered pad->crest = 40 mm with their own vertical scale (0.117 vs 0.152 mm/px horizontal).
