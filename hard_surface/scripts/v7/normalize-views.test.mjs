// normalize-views.mjs sheet split (2026-09-29): the white-gutter split and its quadrant fallback for a drawing that
// crosses a gutter (a helicopter's rotor blade over the column gutter of a 2 x 2 turnaround sheet). Synthetic sheets.
import { test } from "node:test";
import assert from "node:assert/strict";

import { splitSheet, splitQuadrants } from "./normalize-views.mjs";

const W = 200; const H = 200;
/** A white RGB sheet + its 0/1 mask with the given filled rects [x0, y0, x1, y1] (inclusive) drawn dark. */
function sheet(rects) {
  const data = Buffer.alloc(W * H * 3, 255);
  const mask = new Uint8Array(W * H);
  for (const [x0, y0, x1, y1] of rects) {
    for (let y = y0; y <= y1; y += 1) for (let x = x0; x <= x1; x += 1) { mask[y * W + x] = 1; data.fill(40, (y * W + x) * 3, (y * W + x) * 3 + 3); }
  }
  return { img: { data, width: W, height: H }, mask };
}

// four views; the bottom-left view's "rotor" (a thin bar) reaches past x = 100 (under the bottom-right view's span)
const VIEWS = [[10, 10, 90, 60], [120, 10, 180, 60], [30, 130, 80, 180], [110, 128, 190, 190]];
const ROTOR = [5, 124, 115, 125];   // the bottom-left view's rotor bar, joined to it by BRIDGE
const BRIDGE = [50, 126, 52, 129];

test("a drawing across the column gutter: the gutter split throws, the quadrant split keeps each drawing in its quarter", () => {
  const { img, mask } = sheet([...VIEWS, ROTOR, BRIDGE]);
  assert.throws(() => splitSheet(img, mask, 2, 2), /found 0 white gutter\(s\), need 1/);
  const q = splitQuadrants(img, mask, 2, 2);
  assert.deepEqual(q.panels.map((p) => [p.x, p.y, p.x + p.w - 1, p.y + p.h - 1]), [[6, 6, 94, 64], [116, 6, 184, 64], [1, 120, 119, 184], [106, 124, 194, 194]]);
  // the bottom-left panel (x 1..119) overlaps the bottom-right view (x 110..190): that drawing is painted white in it
  const bl = q.images[2];
  const at = (im, x, y) => im.data[((y - q.panels[2].y) * im.width + (x - q.panels[2].x)) * 3];
  assert.equal(at(bl, 112, 150), 255);   // bottom-right view's pixel, removed
  assert.equal(at(bl, 112, 124), 40);    // its own rotor bar, kept
  assert.deepEqual(q.cells.map((c) => c.components), [1, 1, 1, 1]);
});

test("the quadrant split still refuses a sheet off the 2 x 2 layout (an empty quarter)", () => {
  const { img, mask } = sheet([[10, 10, 90, 60], [120, 10, 180, 60], [120, 70, 180, 95], [110, 120, 190, 190]]);
  assert.throws(() => splitQuadrants(img, mask, 2, 2), /cell\(s\) 2 \(row-major\) hold no drawing/);
});

test("a clean 2 x 2 sheet splits on its gutters unchanged", () => {
  const { img, mask } = sheet(VIEWS);
  const s = splitSheet(img, mask, 2, 2);
  assert.equal(s.panels.length, 4);
  assert.equal(s.gutters.rows.length, 1);
});
