# Windows / Plasticity 26.2.1 port — status: BLOCKED

## Status
The upstream approach does not work on the Windows 26.2.1 build without modifying the binary.

- Upstream (macOS, 26.1.3) launches Plasticity with `--inspect-brk`, attaches to the Electron main process
  and puts back `--remote-debugging-port`, because Plasticity's main process removes that switch
  (`app.commandLine.removeSwitch`) itself.
- The Windows `Plasticity.exe` (app-26.2.1) has the Electron fuses **RunAsNode, NodeOptions and
  NodeCliInspectArguments switched OFF** (fuse wire read `000011011`). Because of that, `--inspect-brk`
  is ignored, and `--remote-debugging-port` (both `=` and space forms) is stripped. No CDP port opens.
- The only way through is flipping fuses or otherwise patching the signed exe/asar. That is binary
  patching. It was not done.

## Code changes made (`src/plasticity/launcher.ts`)
- On win32 it spawns `C:/Program Files/Plasticity/app-26.2.1/Plasticity.exe` directly (you can override
  this with the `PLASTICITY_APP` env var). It checks for a running instance with `tasklist` instead of `pgrep`.
- No version gate or tool fixes were added, because no live renderer was reachable to re-discover object paths.

## Auto-update
- This is an MSI machine install ("Plasticity (Machine - MSI)", product code {30E1C385-126D-4F59-AE9E-16B2B8CC5DF1}).
- There is **no Update.exe** in `C:\Program Files\Plasticity`, and nothing in LocalAppData or the Run keys.
  The Squirrel self-update path therefore cannot run, and there was nothing to rename.
- The update logic sits in V8 bytecode (`plasticity.jsc.pack`). No in-app setting was found. Updates
  most likely arrive as a notice plus a new MSI that you install by hand. Just don't install new MSIs.

## Upstream audit notes
- MIT licence (Aleksand Meshchriakov, 2026).
- No install scripts. The only `fetch` calls go to loopback CDP.
- At startup it spawns the `codex` CLI (OpenAI Codex app-server) for its "analysis" and "reference
  search" features. Those reach the network through Codex. Set `PLASTICITY_CODEX_EXECUTABLE` to a
  missing path to disable them.
- It also has STEP/reference download tools.
- The mac-only bits are `/usr/bin/sips`, `/bin/zsh` in `plugins/.../.mcp.json`, and the docker arm64 FEM build.

## EULA risk
Driving Plasticity internals through a debugger, and getting around its deliberate removal of the
debugging switch, is very likely outside what the Plasticity EULA permits. Weigh that before going further.
