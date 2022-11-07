include(ExternalProject)

set(DOWNLOAD_URL https://git.ie.hann.wang/pub/oneDNN/-/archive/v2.7.1/oneDNN-v2.7.1.zip)
set(ROOT ${CMAKE_CURRENT_LIST_DIR}/../3rd_party/)
set(ONEDNN_DIR ${ROOT}/oneDNN/)
set(MNN_BUILD_DIR ${PROJECT_BINARY_DIR})

set(CONFIGURE_CMD cd ${ONEDNN_DIR} && cmake -DCMAKE_INSTALL_PREFIX=${MNN_BUILD_DIR} -DONEDNN_BUILD_EXAMPLES=OFF -DONEDNN_BUILD_TESTS=OFF -DONEDNN_LIBRARY_TYPE=STATIC -DONEDNN_CPU_RUNTIME=SEQ)
set(BUILD_CMD cd ${ONEDNN_DIR} && make -j$(nproc))
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

add_whole_archive_flag(dnnl_LIBS ${dnnl_LIBS})
