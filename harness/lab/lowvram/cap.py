# import first: caps CUDA allocator to emulate an 8 GB card when CAP=1 (default)
import os, time, atexit, torch
CAP = os.environ.get('CAP', '1') == '1'
if CAP: torch.cuda.set_per_process_memory_fraction(7.5 / 95.6)
_t0 = time.time()
def peak(tag=''):
    a = torch.cuda.max_memory_allocated() / 2**30; r = torch.cuda.max_memory_reserved() / 2**30
    print(f'PEAK {tag} cap={int(CAP)} alloc {a:.2f} GiB reserved {r:.2f} GiB t {time.time()-_t0:.0f}s', flush=True)
atexit.register(peak, 'exit')
