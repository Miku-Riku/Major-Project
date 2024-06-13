#pragma once

static uint32_t sum(const uint8_t* buf, int len) {
    uint32_t       sum = 0;
    const uint8_t* p   = buf;
    for (; len > 1; len -= 2) {
        sum += (*p << 8) + *(p + 1);
        p += 2;
    }
    if (len == 1) {
        sum += *p << 8;
    }
    return sum;
}

static uint32_t pseudoHeadSum(const iphdr* ip_header) {
    struct pseudo {
        uint8_t  zero;
        uint8_t  type;
        uint16_t len;
        uint32_t src_ip;
        uint32_t dst_ip;
    };

    pseudo head {
        .zero   = 0,
        .type   = IPPROTO_TCP,
        .len    = htons(static_cast<uint16_t>(ntohs(ip_header->tot_len) - ip_header->ihl * 4)),
        .src_ip = ip_header->saddr,
        .dst_ip = ip_header->daddr,
    };
    return sum((uint8_t*) &head, sizeof(pseudo));
}

uint16_t update_ip_checksum(iphdr* ip_header) {
    ip_header->check = 0;
    uint32_t check   = sum((uint8_t*) ip_header, ip_header->ihl * 4);
    check            = (check >> 16) + (check & 0xffff);
    check += check >> 16;
    return htons((uint16_t) ~check);
}

uint16_t update_tcp_checksum(iphdr* ip_header, tcphdr* tcp_header) {
    tcp_header->check = 0;
    uint32_t check    = pseudoHeadSum(ip_header);
    check += sum((uint8_t*) tcp_header, ntohs(ip_header->tot_len) - ip_header->ihl * 4);
    check = (check >> 16) + (check & 0xffff);
    check += check >> 16;
    return htons((uint16_t) ~check);
}
