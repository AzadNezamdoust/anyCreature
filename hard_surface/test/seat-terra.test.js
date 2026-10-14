import test from "node:test";
import assert from "node:assert/strict";
import { runSeat, terraArgs, TERRA_DEFAULT_MODEL } from "../scripts/seats/terra.mjs";
import { SEATS } from "../scripts/pass.mjs";

// Terra is a TEST seat (owner 2026-09-13): these pin the blind invocation without spawning codex.

test("terra is a registered seat and defaults to gpt-5.6-terra", () => {
  assert.ok(SEATS.includes("terra"));
  assert.equal(TERRA_DEFAULT_MODEL, "gpt-5.6-terra");
});

test("terra argv is blind: ephemeral, no user config, no rules, no MCP, read-only, private cwd", () => {
  const args = terraArgs({ dir: "C:/tmp/terra-x", model: "gpt-5.6-terra", effort: "high", images: ["C:/tmp/terra-x/image1.png"] });
  for (const flag of ["--ephemeral", "--ignore-user-config", "--ignore-rules", "--skip-git-repo-check"]) assert.ok(args.includes(flag), flag);
  assert.equal(args[args.indexOf("-s") + 1], "read-only");
  assert.equal(args[args.indexOf("-C") + 1], "C:/tmp/terra-x");
  assert.equal(args[args.indexOf("-m") + 1], "gpt-5.6-terra");
  assert.ok(args.includes("mcp_servers={}"));
  assert.ok(!args.some((a) => /resume|workspace-write|danger/.test(a)));
});

test("terra seat refuses agent mode as a contract failure, without spawning", async () => {
  const out = await runSeat({ prompt: "x", mode: "agent", env: {} });
  assert.equal(out.failureClass, "contract");
});
