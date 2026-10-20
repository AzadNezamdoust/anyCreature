"""BPT's HF checkpoint pickles deepspeed objects (LossScaler, ZeroStageEnum, ...)
next to the weights; torch>=2.6 refuses them under weights_only=True. Load with
weights_only=True, allow-listing inert stand-in classes for exactly the
non-tensor globals it names (no code from the checkpoint runs), keep only
tensors/'model'/'version', re-save.
Usage: python bpt_convert_ckpt.py <in.pt> <out.pt>"""
import re, sys, types, torch

stubs = []

def stub(qual):
    mod, name = qual.rsplit('.', 1)
    parts = mod.split('.')
    for i in range(1, len(parts) + 1):
        sys.modules.setdefault('.'.join(parts[:i]), types.ModuleType('.'.join(parts[:i])))
    cls = type(name, (), {'__new__': lambda c, *a, **k: object.__new__(c),
                          '__init__': lambda s, *a, **k: None,
                          '__setstate__': lambda s, st: None,
                          '__module__': mod})
    setattr(sys.modules[mod], name, cls)
    stubs.append(cls)
    torch.serialization.add_safe_globals([cls])

for _ in range(30):
    try:
        pkg = torch.load(sys.argv[1], map_location='cpu', weights_only=True)
        break
    except Exception as e:
        m = re.search(r'Unsupported global: GLOBAL ([\w\.]+)', str(e))
        if not m or not m.group(1).startswith('deepspeed.'):
            raise
        print('stub', m.group(1)); stub(m.group(1))
print('keys', list(pkg.keys()))
out = {'model': pkg['model'], 'version': pkg.get('version')}
assert all(torch.is_tensor(v) for v in out['model'].values())
torch.save(out, sys.argv[2])
print('saved', len(out['model']), 'tensors')
