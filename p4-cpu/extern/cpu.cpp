#include <bm/bm_sim/extern.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>

#include <thread>

bool started = false;
int  cpu_sw[1];

int get_cpu_sw(int id) {
    char cmd[256];
    sprintf(cmd, "top -bcn1 -d 0 -w512 | awk '/simple_switch/' | awk '/s%d/ {print $9}'", id);

    auto *pipe = popen((char *) cmd, "r");
    if (pipe == nullptr) {
        return 250;
    }

    char        buff[1024];
    std::string result;
    while (!feof(pipe)) {
        if (fgets(buff, 1024, pipe) != nullptr) {
            result.append(buff);
            break;
        }
    }
    pclose(pipe);

    return std::atoi(result.c_str());
}

int get_cpu_usage(int id) {
    if (!started) {
        started = true;
        std::thread([id]() -> void {
            cpu_sw[0] = 0;
            while (true) {
                cpu_sw[0] = get_cpu_sw(id);
                std::this_thread::sleep_for(std::chrono::nanoseconds(100));
            }
        }).detach();
    }

    return id >= 0 && id <= 5 ? cpu_sw[0] : 0;
}

void set_cpu(bm::Data &hdr, const bm::Data &sw) {
    int id  = sw.get_int();
    int cpu = get_cpu_usage(id);
    hdr.set(bm::Data { cpu });
}

BM_REGISTER_EXTERN_FUNCTION(set_cpu, bm::Data &, const bm::Data &);
