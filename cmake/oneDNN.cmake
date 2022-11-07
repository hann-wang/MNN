include(ExternalProject)

set(DOWNLOAD_URL https://git.ie.hann.wang/pub/oneDNN/-/archive/v2.7.1/oneDNN-v2.7.1.zip)
set(ROOT ${CMAKE_CURRENT_LIST_DIR}/../3rd_party/)
set(ONEDNN_DIR ${ROOT}/oneDNN/)
set(MNN_BUILD_DIR ${CMAKE_CURRENT_LIST_DIR}/../build/)

set(CONFIGURE_CMD cd ${ONEDNN_DIR} && cmake -DCMAKE_INSTALL_PREFIX=${MNN_BUILD_DIR} -DONEDNN_BUILD_EXAMPLES=OFF -DONEDNN_BUILD_TESTS=OFF -DONEDNN_LIBRARY_TYPE=STATIC -DONEDNN_CPU_RUNTIME=SEQ)
set(BUILD_CMD cd ${ONEDNN_DIR} && make -j8)
set(INSTALL_CMD cd ${ONEDNN_DIR} && make install)

ExternalProject_Add(oneDNN
    PREFIX              oneDNN
    URL                 ${DOWNLOAD_URL}
    DOWNLOAD_DIR        ${ROOT}
    SOURCE_DIR          ${ONEDNN_DIR}
    CONFIGURE_COMMAND   ${CONFIGURE_CMD}
    BUILD_COMMAND       ${BUILD_CMD}
    INSTALL_COMMAND     ${INSTALL_CMD}
)

ExternalProject_Get_Property(oneDNN install_dir)
include_directories(${ONEDNN_DIR}/include)
set(dnnl_LIBS ${PROJECT_BINARY_DIR}/lib/libdnnl.a)

function(add_whole_archive_flag lib output_var)
  if(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    set(${output_var} -Wl,-force_load,$<TARGET_FILE:${lib}> PARENT_SCOPE)
  elseif(MSVC)
    # In MSVC, we will add whole archive in default.
    set(${output_var} -WHOLEARCHIVE:${lib} PARENT_SCOPE)
  else()
    # Assume everything else is like gcc
    set(${output_var} "-Wl,--whole-archive ${lib} -Wl,--no-whole-archive" PARENT_SCOPE)
  endif()
endfunction()

add_whole_archive_flag(dnnl_LIBS ${dnnl_LIBS})
