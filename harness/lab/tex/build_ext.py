# run setup.py with torch's CUDA major-version check disabled (pip CUDA 13.4 nvcc vs torch cu12x/13.0)
import sys, os, runpy, torch.utils.cpp_extension as ce
ce._check_cuda_version = lambda *a, **k: None
os.chdir(sys.argv[1]); sys.argv = ['setup.py'] + sys.argv[2:]
sys.path.insert(0, os.getcwd())
runpy.run_path('setup.py', run_name='__main__')
