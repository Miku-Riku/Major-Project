#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <cstring>
#include <iostream>

#define CONGESTION_STATE_PORT 16

struct congestion_state {
    bool           send;
    unsigned short value;
    unsigned short delay;

    void convert(char buff[6]) {
        buff[0] = send;
        buff[1] = 0; /* padding */
        buff[2] = value & 0xFF;
        buff[3] = (value >> 8) & 0xFF;
        buff[4] = delay & 0xFF;
        buff[5] = (delay >> 8) & 0xFF;
    }
};

int main(int argc, char *argv[]) {
    int                udpSocket;
    struct sockaddr_in serverAddr, clientAddr;
    char               buffer[1024];
    int                ttlValue = 2;

    if (argc <= 3) {
        std::cerr << "Usage: udp <send> <value> <delay>" << std::endl;
        return 1;
    }

    // Create UDP socket
    udpSocket = socket(AF_INET, SOCK_DGRAM, 0);
    if (udpSocket < 0) {
        std::cerr << "Error creating socket" << std::endl;
        return 1;
    }

    // Server address and port
    memset((char *) &serverAddr, 0, sizeof(serverAddr));
    serverAddr.sin_family      = AF_INET;
    serverAddr.sin_port        = htons(CONGESTION_STATE_PORT);    // Port number to listen on
    serverAddr.sin_addr.s_addr = INADDR_ANY;                      // Accept packets on any available local IP address

    // Bind socket to server address
    if (bind(udpSocket, (struct sockaddr *) &serverAddr, sizeof(serverAddr)) < 0) {
        std::cerr << "Error binding socket to server address" << std::endl;
        close(udpSocket);
        return 1;
    }

    while (true) {
        socklen_t clientLen = sizeof(clientAddr);

        // Receive message from client
        int recvBytes = recvfrom(udpSocket, buffer, sizeof(buffer), 0, (struct sockaddr *) &clientAddr, &clientLen);
        if (recvBytes < 0) {
            std::cerr << "Error receiving message" << std::endl;
            break;
        }

        // Display received message
        buffer[recvBytes] = '\0';
        std::cout << "Received message from client: " << buffer << std::endl;

        // Set TTL value
        if (setsockopt(udpSocket, IPPROTO_IP, IP_TTL, &ttlValue, sizeof(ttlValue)) < 0) {
            std::cerr << "Error setting TTL" << std::endl;
            break;
        }

        // Set source address and port
        struct sockaddr_in sourceAddr;
        memset((char *) &sourceAddr, 0, sizeof(sourceAddr));
        sourceAddr.sin_family      = AF_INET;
        sourceAddr.sin_port        = htons(CONGESTION_STATE_PORT);    // Source port 16
        sourceAddr.sin_addr.s_addr = INADDR_ANY;                      // Use any available local IP address

        // Message to send
        congestion_state state {
            strcmp(argv[1], "1") == 0,
            (unsigned short) (atoi(argv[2]) & 0xFFFF),
            (unsigned short) (atoi(argv[3]) & 0xFFFF)
        };
        state.convert(buffer);

        // Send the UDP packet back to the sender
        if (sendto(udpSocket, buffer, 6, 0, (struct sockaddr *) &clientAddr, clientLen) < 0) {
            std::cerr << "Error sending message" << std::endl;
            break;
        }

        std::cout << "Sent response UDP packet to client" << std::endl;
    }

    // Close socket
    close(udpSocket);

    return 0;
}
