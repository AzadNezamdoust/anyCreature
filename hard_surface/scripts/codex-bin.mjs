// codex-bin.mjs — locate the Codex CLI. The desktop app installs it under a hash folder that changes on
// every update, so a hard-coded path goes stale; CODEX_BIN wins, else the newest codex.exe under the bin root.
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

export function codexBin(env = process.env) {
  if (env.CODEX_BIN) return env.CODEX_BIN;
  const root = path.join(env.LOCALAPPDATA || path.join(os.homedir(), "AppData", "Local"), "OpenAI", "Codex", "bin");
  let best = null;
  try {
    for (const dir of fs.readdirSync(root)) {
      const exe = path.join(root, dir, "codex.exe");
      if (!fs.existsSync(exe)) continue;
      const t = fs.statSync(exe).mtimeMs;
      if (!best || t > best.t) best = { exe, t };
    }
  } catch { /* no desktop install */ }
  return best ? best.exe : "codex";
}
