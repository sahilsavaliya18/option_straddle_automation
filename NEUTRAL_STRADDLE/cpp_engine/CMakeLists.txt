cmake_minimum_required(VERSION 3.14)
project(backtest_engine LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ── Find Python & pybind11 ──────────────────────────────────────────────
find_package(Python REQUIRED COMPONENTS Interpreter Development)
find_package(pybind11 REQUIRED)

# ── Source files ─────────────────────────────────────────────────────────
pybind11_add_module(backtest_engine
    backtest_engine.cpp
    csv_loader.cpp
    bindings.cpp
)

# ── Optimisation flags (Release) ─────────────────────────────────────────
if(MSVC)
    target_compile_options(backtest_engine PRIVATE /O2 /Oi /GL /DNDEBUG)
else()
    target_compile_options(backtest_engine PRIVATE -O3 -march=native -DNDEBUG)
endif()

# ── Output .pyd/.so directly into STRATEGY folder (no Release\ subfolder) ───────────────────
set_target_properties(backtest_engine PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY         "${CMAKE_CURRENT_SOURCE_DIR}/.."
    RUNTIME_OUTPUT_DIRECTORY         "${CMAKE_CURRENT_SOURCE_DIR}/.."
    LIBRARY_OUTPUT_DIRECTORY_RELEASE "${CMAKE_CURRENT_SOURCE_DIR}/.."
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_CURRENT_SOURCE_DIR}/.."
    LIBRARY_OUTPUT_DIRECTORY_DEBUG   "${CMAKE_CURRENT_SOURCE_DIR}/.."
    RUNTIME_OUTPUT_DIRECTORY_DEBUG   "${CMAKE_CURRENT_SOURCE_DIR}/.."
)
