```js
121|     wheels: { r: k.wheelR + 0.03, width: k.wheelWidth + 0.04, z: [k.wheelFrontZ + 0.015, k.wheelRearZ - 0.025], hub: { r: k.hubR, ring: k.hubRing, cap: k.hubCap } },
```

```js
144|   parts.push(...K.assemble.mirror({ body: parts, side: KNOBS.rc_mirrors1.v, centreY: KNOBS.rc_mirrors2.v, z: KNOBS.rc_mirrors3.v + 0.084, head: { w: KNOBS.rc_mirrors4.v, h: KNOBS.rc_mirrors5.v, round: KNOBS.rc_mirrors6.v }, arm: KNOBS.rc_mirrors7.v }));
```

CHANGE: Enlarge and widen the wheels, nudge their centers toward the reported deficits, and move the mirror heads forward.
