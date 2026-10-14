```js replace 125-125
    zones: { liner: "dark" },   // _profile.inlays.archLiner (the wheel-well tone)
```
```js replace 142-142
  parts.push(...K.assemble.grille({ body: parts, face: "nose", bounds: K.span({ x: [-KNOBS.rc_grille1.v, KNOBS.rc_grille1.v], y: [KNOBS.rc_grille2.v, KNOBS.rc_grille3.v] }), slots: 3 }));
```
CHANGE: Set arch liner zone to dark to resolve dark zone deficit and remove grille rear excess, and set grille slots to 3 to match target styling.
