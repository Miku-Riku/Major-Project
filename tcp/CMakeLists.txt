cmake_minimum_required(VERSION 3.22)
project(tcp)

set(CMAKE_CXX_STANDARD 17)

if (MSVC)
    add_compile_options("$<$<CONFIG:RELEASE>:/O2>" "/arch:AVX512" "/Oi" "/fp:precise" "/sdl" "/GL")
else ()
    add_compile_options("-Wall" "-Wextra" "-Werror" "$<$<CONFIG:RELEASE>:-O3>")

    if ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang")
        add_compile_options("-stdlib=libc++")
    else ()
        # nothing special for gcc at the moment
    endif ()
endif ()

add_executable(tcp src/main.cpp
        src/csm.hpp
        src/tcp.hpp
        src/checksum.hpp
)

set_target_properties(tcp PROPERTIES OUTPUT_NAME tcp-shank)

target_link_libraries(tcp -lnfnetlink -lnetfilter_queue)

install(TARGETS tcp DESTINATION bin)
if (WIN32)
    install(FILES README.md DESTINATION .)
endif ()
