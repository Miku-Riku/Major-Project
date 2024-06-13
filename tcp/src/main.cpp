#include <arpa/inet.h>
#include <ifaddrs.h>

#include <cstring>
#include <iostream>
#include <thread>
#include <vector>

#include "csm.hpp"
#include "tcp.hpp"

int setup_iptables_rules() {
    return system("sudo iptables -I OUTPUT -j NFQUEUE --queue-bypass && sudo iptables -I INPUT -j NFQUEUE --queue-bypass");
}

in_addr *get_interface_ip(char *interface) {
    ifaddrs *addrs = nullptr;
    int      code  = getifaddrs(&addrs);
    if (code != 0) {
        std::cerr << "[Main] Unable to fetch interfaces" << std::endl;
        return nullptr;
    }

    for (ifaddrs *curr = addrs; curr != nullptr; curr = curr->ifa_next) {
        if (curr->ifa_addr->sa_family != AF_INET) {
            continue;
        }

        // IPv4

        // Be aware that the `ifa_addr`, `ifa_netmask` and `ifa_data` fields might contain nullptr.
        // De-referencing nullptr causes "Undefined behavior" problems.
        // So it is needed to check these fields before de-referencing.
        if (curr->ifa_addr != nullptr && strcmp(curr->ifa_name, interface) == 0) {
            return &((sockaddr_in *) (curr->ifa_addr))->sin_addr;
        }
    }
    return nullptr;
}

int exec(const char *cmd, std::string *output) {
    char  buff[128];
    FILE *pipe = popen(cmd, "r");
    if (pipe == nullptr) {
        return -1;
    }

    try {
        while (fgets(buff, sizeof(buff), pipe) != nullptr) {
            output->append(buff);
        }
    } catch (std::exception &e) {
        std::cerr << "[MAIN] - " << e.what() << std::endl;
    }
    pclose(pipe);

    return 0;
}

void split(const std::string &delim, std::string &src, std::vector<std::string> *res) {
    size_t start = 0;
    for (size_t found = src.find(delim); found != std::string::npos; found = src.find(delim, start)) {
        res->emplace_back(src.begin() + start, src.begin() + found);
        start = found + delim.size();
    }
    if (start != src.size()) {
        res->emplace_back(src.begin() + start, src.end());
    }
}

in_addr_t get_gateway_ip(char *interface) {
    std::string inf(interface);

    std::string str;
    if (exec(R"(route -n | awk 'FNR > 2 {print $8 " " $1 " " $2}')", &str) == -1) {
        std::cerr << "[MAIN] Error executing cmd" << std::endl;
        return 0;
    }

    std::vector<std::string> routes;
    split("\n", str, &routes);

    for (auto &route : routes) {
        std::vector<std::string> tokens;
        split(" ", route, &tokens);
        if (tokens.size() != 3) continue;

        if (tokens[0] == inf && tokens[1] == "0.0.0.0" && tokens[2] != "0.0.0.0") {
            return inet_addr(tokens[2].c_str());
        }
    }
    return 0;
}

int main(int argc, char *argv[]) {
    if (argc <= 1) {
        std::cerr << "Usage: tcp-shank <interface>" << std::endl;
        return 1;
    }

    std::cout << "[Main] Interface: " << argv[1] << std::endl;

    in_addr *addr = get_interface_ip(argv[1]);
    if (addr == nullptr) {
        std::cerr << "[Main] Unable to get IP for interface " << argv[1] << std::endl;
        return 1;
    }
    std::cout << "[Main] IP: " << inet_ntoa(*addr) << std::endl;

    if (setup_iptables_rules() != 0) {
        std::cerr << "[Main] Unable to set iptables rule" << std::endl;
        return 1;
    }

    in_addr_t dg_ip = get_gateway_ip(argv[1]);
    if (dg_ip == 0) {
        std::cerr << "[MAIN] Unable to get default gateway for " << argv[1] << std::endl;
    }

    in_addr dg_addr { dg_ip };
    std::cout << "[MAIN] DG: " << inet_ntoa(dg_addr) << std::endl;

    std::thread([&addr, &dg_addr]() -> void { tcp_nfq::Handler::start(addr, &dg_addr); }).join();
    std::cout << "Terminated\n";

    return 0;
}
