import socket
import pickle
from TCP_Packet import TCP_Packet, ColorUtils
import random
from threading import Thread
import time
import random
import sys

class Server:
    ACK_DELAY = 0.2
    DROP_PROBABILITY = 0

    def __init__(self, server_port=20001, receiving_window=10000, buffer_size=1024):
        self.IP = "10.0.0.2"
        self.port = server_port
        self.receiving_window = receiving_window
        self.UDP_serverSocket = self.UDP_establish_connection()
        self.buffer_size = buffer_size
        self.connection_duration = 40

    def UDP_establish_connection(self):
        UDP_serverSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        UDP_serverSocket.bind((self.IP, self.port))
        return UDP_serverSocket

    def UDP_send(self, TCP_packet, IP, port):
        serialized_packet = pickle.dumps(TCP_packet)
        self.UDP_serverSocket.sendto(serialized_packet, (IP, port))

    def UDP_receive(self):
        received_packet = self.UDP_serverSocket.recvfrom(self.buffer_size)
        TCP_received_packet = pickle.loads(received_packet[0])
        client_IP = received_packet[1][0]
        client_port = received_packet[1][1]
        print("Following Package Received:")
        print("\t Sequence Number: ", TCP_received_packet.sequence_number)
        print("\t Acknowledgment Number: ", TCP_received_packet.ack_number)
        print("\n")
        return TCP_received_packet, client_IP, client_port

    def TCP_establish_connection(self):
        ColorUtils.print_debug("Waiting for Client to Request Connection!", mode="Server")

        syn_received = False
        while not syn_received:
            received_packet, client_IP, client_port = self.UDP_receive()
            if received_packet.checksum_isValid() and received_packet.SYN == 1:
                syn_received = True

        sequence_number = random.randint(1, self.receiving_window)
        sending_packet = TCP_Packet(self.port, client_port, sequence_number, received_packet.sequence_number, 1, 1, 0)
        self.UDP_send(sending_packet, client_IP, client_port)

        ColorUtils.print_debug("Waiting for Client to Acknowledge Connection Approval!", mode="Server")
        syn_ack_received = False
        while not syn_ack_received:
            received_packet, client_IP, client_port = self.UDP_receive()
            if received_packet.checksum_isValid() and received_packet.ACK == 1:
                syn_ack_received = True

        ColorUtils.print_log("Connection Established!", mode="Server")
        return sequence_number, client_IP, client_port

    def start_receiving(self, sequence_number):
        def receiving_thread_target():
            while True:
                received_packet, client_IP, client_port = self.UDP_receive()
                handle_received_thread = Thread(target=self.handle_received_packet(received_packet,
                                                                                   client_IP,
                                                                                   client_port,
                                                                                   sequence_number))
                handle_received_thread.daemon = True
                handle_received_thread.start()

        receiving_thread = Thread(target=receiving_thread_target)
        receiving_thread.daemon = True
        receiving_thread.start()
        ColorUtils.print_debug("Receiving Threads are set up!", mode="Server")

    def handle_received_packet(self, received_packet, client_IP, client_port, sequence_number):
        if received_packet.checksum_isValid() and received_packet.FIN == 1:
            ColorUtils.print_debug("Connection Closing Request with Packet " + str(received_packet.sequence_number)
                                 + " Successfully Received!", mode="Server")
            self.close_connection(client_IP, client_port, sequence_number)

        time.sleep(Server.ACK_DELAY)
        if received_packet.checksum_isValid() and not server.flip_coin(server.DROP_PROBABILITY):
            ColorUtils.print_log("Packet " + str(received_packet.sequence_number) + " Successfully Received!", mode="Server")
            sending_packet = TCP_Packet(self.port, client_port, sequence_number, received_packet.sequence_number, 1,
                                        1, 0)
            self.UDP_send(sending_packet, client_IP, client_port)
        else:
            ColorUtils.print_debug("Packet " + str(received_packet.sequence_number) + " Dropped!", mode="Server")


    @staticmethod
    def flip_coin(one_probability):
        return random.uniform(0, 1) < one_probability

    def close_connection(self, client_IP, client_port, sequence_number):
        sending_packet = TCP_Packet(self.port, client_port, sequence_number, 0, 1, 0, 1)
        self.UDP_send(sending_packet, client_IP, client_port)
        ColorUtils.print_log("Connection Closed!", mode="Server")
        ColorUtils.save_to_file_server()
        sys.exit()

    def connect(self):
        sequence_number, client_IP, client_port = self.TCP_establish_connection()
        self.start_receiving(sequence_number)
        time.sleep(self.connection_duration)


server = Server()
server.connect()

