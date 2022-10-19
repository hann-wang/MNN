set (EXTRA_LIBS "")
if(MNN_CUDA_PROFILE)
    set(EXTRA_LIBS  -lnvToolsExt)
endif()

if(1)
    set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -D_FORCE_INLINES -Wno-deprecated-gpu-targets -w ${EXTRA_LIBS} ${ADDITIONAL_PLATFORM_LIB_FLAGS}")

    if(CMAKE_BUILD_TYPE MATCHES Debug)
        set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -O0")
    else()
        set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -O3")
    endif()
    if (WIN32)
        set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -Xcompiler /FS")
    endif ()

    message(STATUS "Enabling CUDA support (version: ${CMAKE_CUDA_COMPILER_VERSION},"
                    " archs: ${CMAKE_CUDA_ARCHITECTURES})")
else()
    message(FATAL_ERROR "CUDA not found >= ${CUDA_MIN_VERSION} required)")
endif()

file(GLOB_RECURSE MNN_CUDA_SRC ${CMAKE_CURRENT_LIST_DIR}/core/* ${CMAKE_CURRENT_SOURCE_DIR}/execution/*)
message(STATUS "message ${CMAKE_CUDA_FLAGS} !!!!!!!!!!!")

if(WIN32)
    add_library(MNN_CUDA STATIC Register.cpp ${MNN_CUDA_SRC})
    set(MNN_CUDA_LIBS MNN_CUDA ${CUDA_LIBRARIES} PARENT_SCOPE)
else()
    if(MNN_BUILD_SHARED_LIBS)
        add_library(MNN_Cuda_Main SHARED ${MNN_CUDA_SRC})
        set(MNN_CUDA_LIBS MNN_Cuda_Main PARENT_SCOPE)
        if(MNN_CUDA_PROFILE)
            target_compile_options(MNN_Cuda_Main PRIVATE -DMNN_CUDA_PROFILE)
            target_link_libraries(MNN_Cuda_Main  ${CUDA_INCLUDE_DIRS}/../lib/libnvToolsExt.so)
        endif()
        add_library(MNN_CUDA OBJECT Register.cpp)
    else()
        add_library(MNN_CUDA OBJECT Register.cpp ${MNN_CUDA_SRC})
        if(MNN_CUDA_PROFILE)
            target_compile_options(MNN_CUDA PRIVATE -DMNN_CUDA_PROFILE)
            target_link_libraries(MNN_CUDA ${CUDA_INCLUDE_DIRS}/../lib/libnvToolsExt.so)
        endif()
        set(MNN_CUDA_LIBS MNN_CUDA ${CUDA_LIBRARIES} PARENT_SCOPE)
    endif()
endif()

include_directories(
    ${CMAKE_CURRENT_LIST_DIR}/
    ${CUDA_INCLUDE_DIRS}
    ${CMAKE_SOURCE_DIR}/include/
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../3rd_party/cutlass/include
)
