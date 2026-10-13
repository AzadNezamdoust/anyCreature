# download official NVIDIA PyPI wheels (newest cu13 with win_amd64), verify sha256, extract include/ + lib/ only
import json, sys, urllib.request, hashlib, zipfile, io
dst = sys.argv[1]
for p in sys.argv[2:]:
    d = json.load(urllib.request.urlopen(f"https://pypi.org/pypi/{p}/json"))
    best = None
    for v, files in d['releases'].items():
        for f in files:
            if f['filename'].endswith('win_amd64.whl'): best = (v, f) if best is None or [int(x) for x in v.split('.') if x.isdigit()] > [int(x) for x in best[0].split('.') if x.isdigit()] else best
    v, f = best
    data = urllib.request.urlopen(f['url']).read()
    assert hashlib.sha256(data).hexdigest() == f['digests']['sha256'], p
    z = zipfile.ZipFile(io.BytesIO(data)); n = 0
    for m in z.namelist():
        if '/include/' in m or m.endswith('.lib'): z.extract(m, dst); n += 1
    print(p, v, f['filename'], 'files', n, flush=True)
