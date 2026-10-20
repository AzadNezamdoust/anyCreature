@echo off
rem pip-wheel CUDA 13.4 toolkit (no system install) + VS 18 MSVC
set "PATH=C:\Program Files (x86)\Microsoft Visual Studio\Installer;C:\Windows\System32;%PATH%"
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
set CUDA_HOME=E:\gen3d\cuda134\nvidia\cu13
set CUDA_PATH=%CUDA_HOME%
set PATH=%CUDA_HOME%\bin;%CUDA_HOME%\bin\x86_64;%CUDA_HOME%\nvvm\bin;%PATH%
set INCLUDE=%CUDA_HOME%\include;%INCLUDE%
set LIB=%CUDA_HOME%\lib\x64;%LIB%
set TORCH_CUDA_ARCH_LIST=12.0
set DISTUTILS_USE_SDK=1
set NVCC_APPEND_FLAGS=-Xcompiler /Zc:preprocessor
