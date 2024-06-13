#include <libnetfilter_queue/libnetfilter_queue.h>
#include <linux/ip.h>
#include <linux/netfilter.h>
#include <linux/tcp.h>
#include <linux/udp.h>

#include <atomic>

#include "checksum.hpp"

#define MAX_PAYLOAD_SIZE 4096
#define NFQ_TAG          "[NFQ] "

namespace tcp_nfq {

    class Handler {
    private:
        Handler() = default;

        static std::atomic<bool>  udp_req_called;
        static std::atomic<short> packets_transferred;
        static std::atomic<short> packet_drops;

        static in_addr      *source_ip;
        static in_addr_t     local_addr;
        static csm::Manager *csm_manager;

        static void init(in_addr *src, in_addr *dg) {
            udp_req_called      = false;
            packets_transferred = 0;
            packet_drops        = 0;

            source_ip   = src;
            local_addr  = inet_addr("127.0.0.1");
            csm_manager = new csm::Manager(dg);
        }

        static int packet_callback(nfq_q_handle *qh, nfgenmsg *, nfq_data *nfad, void *) {
            nfqnl_msg_packet_hdr *ph;
            uint32_t              packet_id;
            unsigned char        *packet;
            int                   packet_len;

            ph         = nfq_get_msg_packet_hdr(nfad);
            packet_id  = ntohl(ph->packet_id);
            packet_len = nfq_get_payload(nfad, &packet);

            // Manipulate the packet here if needed
            // For example, modify TCP destination port
            auto *ip_header = (iphdr *) packet;
            if (ip_header->saddr == local_addr || ip_header->daddr == local_addr) {
                // Skip local_addr
                return nfq_set_verdict(qh, packet_id, NF_ACCEPT, 0, nullptr);
            }

            if (ip_header->protocol == IPPROTO_UDP) {
                if (ip_header->saddr == source_ip->s_addr) {
                    return nfq_set_verdict(qh, packet_id, NF_ACCEPT, 0, nullptr);
                }

                // Capture only those with immediate hop
                if (ip_header->ttl - 1 != 0) {
                    return nfq_set_verdict(qh, packet_id, NF_ACCEPT, 0, nullptr);
                }

                auto *udp_header = (udphdr *) (packet + (ip_header->ihl << 2));
                if (ntohs(udp_header->dest) != CONGESTION_STATE_PORT) {
                    return nfq_set_verdict(qh, packet_id, NF_ACCEPT, 0, nullptr);
                }

                std::cout << NFQ_TAG << "[UDP] CS response\n";

                const u_char *payload = packet + (ip_header->ihl << 2) + sizeof(udphdr);
                //            int           payload_len = htons(udp_header->len) - sizeof(udphdr);

                csm_manager->update_state((csm::congestion_state *) payload);
            }

            if (ip_header->protocol == IPPROTO_TCP) {
                if (ip_header->saddr != source_ip->s_addr) {
                    return nfq_set_verdict(qh, packet_id, NF_ACCEPT, 0, nullptr);
                }

                if (csm_manager->has_state_ttl_expired()) {
                    if (packet_drops == MAX_CS_REQ_DROP) {
                        packet_drops   = 0;
                        udp_req_called = false;
                    }

                    if (udp_req_called) {
                        packet_drops++;
                        // Do not let any packet pass if we don't have congestion state
                        return nfq_set_verdict(qh, packet_id, NF_DROP, 0, nullptr);
                    }

                    std::cout << NFQ_TAG << "[CS] TTL expired. Renewing" << std::endl;
                    udp_req_called = csm_manager->cs_req_state() == 0;
                    return nfq_set_verdict(qh, packet_id, NF_DROP, 0, nullptr);
                }
                udp_req_called = false;
                packet_drops   = 0;

                auto *tcp_header = (tcphdr *) (packet + (ip_header->ihl << 2));

                if (!csm_manager->send()) {
                    tcp_header->cwr    = 1;
                    tcp_header->window = htons(csm_manager->value());

                    ip_header->check  = update_ip_checksum(ip_header);
                    tcp_header->check = update_tcp_checksum(ip_header, tcp_header);

                    if (packets_transferred == csm_manager->value()) {
                        if (csm_manager->delay() > 0) {
                            std::cout << NFQ_TAG << "[CS] Delaying for " << csm_manager->delay() << "us" << std::endl;
                            std::this_thread::sleep_for(std::chrono::microseconds(csm_manager->delay()));
                        }
                        packets_transferred = 0;
                    }
                    packets_transferred++;

                    return nfq_set_verdict(qh, ntohl(ph->packet_id), NF_ACCEPT, packet_len, packet);
                }
            }

            // Accept the modified packet
            // return nfq_set_verdict(qh, ntohl(ph->packet_id), NF_ACCEPT, payload_len, payload);
            return nfq_set_verdict(qh, packet_id, NF_ACCEPT, 0, nullptr);
        };

    public:
        static int start(in_addr *src, in_addr *dg) {
            init(src, dg);

            nfq_handle   *handle;
            nfq_q_handle *queue_handle;

            int  fd, rv;
            char buf[MAX_PAYLOAD_SIZE];

            handle = nfq_open();
            if (!handle) {
                std::cerr << NFQ_TAG << "Error during nfq_open()" << std::endl;
                return 1;
            }

            if (nfq_unbind_pf(handle, AF_INET) < 0) {
                std::cerr << NFQ_TAG << "Error during nfq_bind_pf()" << std::endl;
                return 1;
            }

            queue_handle = nfq_create_queue(handle, 0, &packet_callback, nullptr);
            if (!queue_handle) {
                std::cerr << NFQ_TAG << "Error during nfq_create_queue()" << std::endl;
                return 1;
            }

            if (nfq_set_mode(queue_handle, NFQNL_COPY_PACKET, 0xFFFF) < 0) {
                std::cerr << NFQ_TAG << "Can't set packet_copy mode" << std::endl;
                return 1;
            }

            std::cout << NFQ_TAG << "Starting handle" << std::endl;

            fd = nfq_fd(handle);
            while ((rv = recv(fd, buf, sizeof(buf), 0)) && rv >= 0) {
                nfq_handle_packet(handle, buf, rv);
            }

            nfq_destroy_queue(queue_handle);
            nfq_close(handle);

            std::cout << NFQ_TAG << "Stopped handle" << std::endl;

            return 0;
        }
    };

    std::atomic<bool>  Handler::udp_req_called      = false;
    std::atomic<short> Handler::packets_transferred = 0;
    std::atomic<short> Handler::packet_drops        = 0;

    in_addr      *Handler::source_ip   = nullptr;
    in_addr_t     Handler::local_addr  = 0;
    csm::Manager *Handler::csm_manager = nullptr;

}    // namespace tcp_nfq
