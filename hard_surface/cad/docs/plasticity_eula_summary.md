# Plasticity EULA / terms summary (NOT legal advice)

Sources: https://www.plasticity.xyz/eula , https://www.plasticity.xyz/terms (fetched 2026-10-21 via WebFetch summariser, so quotes are secondhand; re-read the originals before relying on them). /pricing returned 404.
Local install: C:\Program Files\Plasticity does not exist on this machine; no local licence file read.

| Topic | Finding |
|---|---|
| Reverse engineering / decompiling | EULA 3.2: no modifying, derivative works of the Application, no "reverse engineer, or otherwise attempt to access the source code". Also no removing notices, circumventing security. Breach = material breach (3.3), immediate termination. |
| Competing products | No clause found in fetched text. |
| Derivative works | Barred only for the Application itself (3.2), not for user output. |
| Benchmarking | No clause found. |
| Automation / scripting / bots | No explicit clause. Sec 8 covers Third-Party Services/APIs only. Bridge not mentioned. |
| Trial | 3.1: free, time-limited, "for evaluation only"; "Any commercial use during the Free Trial period is strictly prohibited". Expires automatically, does not convert to paid. Length and export limits not stated in EULA; company may limit repeat trials. |
| Paid licence | Perpetual, personal, non-transferable, not shareable. Maintenance expiry keeps right to last eligible version. Academic/Non-Commercial licence needs commercial licence for commercial use. |
| Output ownership | 4.1: "You retain full ownership of any designs, models, files". Company claims none. |
| Terms of Service | Licence per EULA; EULA breach allows suspension/termination; feedback becomes Company property. No scraping/competing clauses. |
| Law | Delaware (sec 16); US export control (sec 14). |

## Black-box trial use to document behaviour for a separate product
No clause expressly forbids observing behaviour, nor building a competing product. But: (1) trial is evaluation-only and commercial use prohibited, so using it to build a commercial product is risky grey area; (2) any reverse engineering or source access (asar, bytecode, protocol sniffing of binaries) is expressly barred. Safe line: use only documented UI/file-format/behaviour, no unpacking. Ask Plasticity (Nick Kallen) in writing if unsure.
