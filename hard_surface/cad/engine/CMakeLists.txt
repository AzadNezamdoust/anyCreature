cmake_minimum_required(VERSION 3.24)
project(cadengine CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

# OpenCASCADE 8.0.x SDK (conda-forge occt 8.0.1 novtk, unpacked to E:/gen3d/occt/Library). LGPL-2.1 + exception: dynamic link.
set(OCCT_ROOT "E:/gen3d/occt/Library" CACHE PATH "OCCT install prefix (include/opencascade, lib, bin)")
set(DEPS_DIR "E:/gen3d/occt/thirdparty" CACHE PATH "nlohmann/json + stb headers")
set(OCPLIBS "E:/gen3d/venv_cad/Lib/site-packages/cadquery_ocp_novtk.libs" CACHE PATH "FreeImage/freetype runtime DLLs (TKService imports)")

set(OCCT_LIBS TKernel TKMath TKG2d TKG3d TKGeomBase TKGeomAlgo TKBRep TKTopAlgo TKPrim TKBO TKBool TKShHealing
              TKFillet TKOffset TKFeat TKMesh TKBin TKDE TKXSBase TKDESTEP)

add_executable(cadengine src/main.cpp src/model.cpp src/geomutil.cpp src/ops.cpp src/kernels.cpp src/isolate.cpp src/gpu.cpp)
target_include_directories(cadengine PRIVATE ${OCCT_ROOT}/include/opencascade ${DEPS_DIR})
target_link_directories(cadengine PRIVATE ${OCCT_ROOT}/lib)
target_link_libraries(cadengine PRIVATE ${OCCT_LIBS} opengl32 gdi32 user32)
target_compile_definitions(cadengine PRIVATE _USE_MATH_DEFINES WIN32_LEAN_AND_MEAN NOMINMAX)
target_compile_options(cadengine PRIVATE /MP /bigobj /EHsc /W1 /utf-8)
target_precompile_headers(cadengine PRIVATE src/common.hpp)
set_source_files_properties(src/gpu.cpp PROPERTIES SKIP_PRECOMPILE_HEADERS ON)
set_target_properties(cadengine PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/bin)

# copy the OCCT runtime DLLs next to the exe (dynamic linking; no system install / PATH change)
add_custom_command(TARGET cadengine POST_BUILD
  COMMAND ${CMAKE_COMMAND} -DSRC=${OCCT_ROOT}/bin -DDST=${CMAKE_SOURCE_DIR}/bin -DOCPLIBS=${OCPLIBS} -P ${CMAKE_SOURCE_DIR}/copy_dlls.cmake)
