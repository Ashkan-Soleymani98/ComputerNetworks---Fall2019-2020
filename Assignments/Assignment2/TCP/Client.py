import socket
import pickle
from TCP_Packet import TCP_Packet, ColorUtils
import random
from threading import Thread
import threading
import sys
import datetime, time

class Client:
    MAX_CONGESTION_WINDOW_SIZE = 20
    ALPHA = 0.125
    BETA = 0.25

    def __init__(self, client_port=20002, receiving_window=10000, buffer_size=1024):
        self.IP = "10.0.0.1"
        self.port = client_port
        self.receiving_window = receiving_window
        self.UDP_clientSocket = self.UDP_establish_connection()
        self.buffer_size = buffer_size
        self.pending = {}
        self.pending_semaphore = threading.Semaphore()
        self.is_connected = False
        self.congestion_window_size = 5
        self.sequence_number = random.randint(1, self.receiving_window)
        self.sequence_number_semaphore = threading.Semaphore()
        self.connection_duration = 40
        self.connection_close_wait = 10
        self.sent_times = {}
        self.DevRTT = 0
        self.EstimatedRTT = 1
        self.time_out_duration = self.EstimatedRTT + 4 * self.DevRTT

    def UDP_establish_connection(self):
        UDP_clientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        UDP_clientSocket.bind((self.IP, self.port))
        return UDP_clientSocket

    def UDP_send(self, TCP_packet, IP, port):
        self.sent_times[TCP_packet.sequence_number] = datetime.datetime.now()
        serialized_packet = pickle.dumps(TCP_packet)
        self.UDP_clientSocket.sendto(serialized_packet, (IP, port))

    def UDP_receive(self):
        received_packet = self.UDP_clientSocket.recvfrom(self.buffer_size)
        TCP_received_packet = pickle.loads(received_packet[0])
        server_IP = received_packet[1][0]
        server_port = received_packet[1][1]
        print("Following Package Received:")
        print("\t Sequence Number: ", TCP_received_packet.sequence_number)
        print("\t Acknowledgment Number: ", TCP_received_packet.ack_number)
        print("\n")
        return TCP_received_packet, server_IP, server_port

    def add_sequence_number(self):
        self.sequence_number_semaphore.acquire()
        self.sequence_number += 1
        self.sequence_number_semaphore.release()

    def add_pending(self, sequence_number, ack_check_thread):
        self.pending_semaphore.acquire()
        self.pending[sequence_number] = ack_check_thread
        self.pending_semaphore.release()

    def remove_pending(self, sequence_number):
        self.pending_semaphore.acquire()
        if sequence_number in self.pending.keys():
            del self.pending[sequence_number]
        self.pending_semaphore.release()

    def isPending(self, sequence_number):
        return sequence_number in self.pending.keys()

    def TCP_establish_connection(self, server_IP, server_port):
        sending_packet = TCP_Packet(self.port, server_port, self.sequence_number, 0, 0, 1, 0)
        self.UDP_send(sending_packet, server_IP, server_port)

        ColorUtils.print_debug("Waiting for Server to Approve Connection!")

        syn_received = False
        while not syn_received:
            received_packet, server_IP, server_port = self.UDP_receive()
            if received_packet.checksum_isValid() and received_packet.SYN == 1:
                syn_received = True

        ColorUtils.print_log("Connection Established!")

        self.add_sequence_number()
        sending_packet = TCP_Packet(self.port, server_port, self.sequence_number, received_packet.sequence_number, 1, 0, 0)
        self.UDP_send(sending_packet, server_IP, server_port)
        self.add_sequence_number()
        self.is_connected = True

        return server_IP, server_port


    def start_receiving(self, server_IP, server_port):
        def receiving_thread_target():
            while True:
                received_packet, server_IP, server_port = self.UDP_receive()
                handle_received_thread = Thread(target=self.handle_received_packet(received_packet,
                                                                                   server_IP,
                                                                                   server_port))
                handle_received_thread.daemon = True
                handle_received_thread.start()

        receiving_thread = Thread(target=receiving_thread_target)
        receiving_thread.daemon = True
        receiving_thread.start()
        ColorUtils.print_debug("Receiving Threads are set up!")

    def handle_received_packet(self, received_packet, server_IP, server_port):
        if received_packet.checksum_isValid() and received_packet.FIN == 1 and received_packet.ACK == 1:
            ColorUtils.print_log("Connection Closed!")
            ColorUtils.save_to_file_client()
            sys.exit()

        if received_packet.checksum_isValid() and received_packet.ACK == 1:
            ColorUtils.print_log("Packet " + str(received_packet.ack_number)
                                 + (" Successfully Acknowledged!" if received_packet.ack_number in self.pending.keys()
                                        else " Double Acknowledged!"))
            self.remove_pending(received_packet.ack_number)
            self.update_congestion_window("ACK Received")
            self.update_time_out_duration(received_packet.ack_number) # TODO
            self.start_sending(server_IP, server_port)

    def start_sending(self, server_IP, server_port):
        while self.is_connected and self.sequence_number < self.get_first_pending() + self.congestion_window_size:
            time.sleep(0.1)
            sending_packet = TCP_Packet(self.port, server_port, self.sequence_number, 0, 0, 0, 0)
            self.add_sequence_number()

            def check_ack(sequence_number):
                time.sleep(self.time_out_duration)
                if self.isPending(sequence_number):
                    self.handle_packet_lost(server_IP, server_port, sequence_number)

            ack_checker_thread = Thread(target=check_ack, args=(sending_packet.sequence_number, ))
            ack_checker_thread.daemon = True
            ack_checker_thread.start()
            self.add_pending(sending_packet.sequence_number, ack_checker_thread)
            self.UDP_send(sending_packet, server_IP, server_port)
            ColorUtils.print_debug("Timer for package " + str(sending_packet.sequence_number) + " is set up!")

    def handle_packet_lost(self, server_IP, server_port, sequence_number):
        ColorUtils.print_log("Packet " + str(sequence_number) + " Lost!")
        self.update_congestion_window("Packet Lost")
        sending_packet = TCP_Packet(self.port, server_port, sequence_number, 0, 0, 0, 0)

        def check_ack(sequence_number):
            time.sleep(self.time_out_duration)
            if self.isPending(sequence_number):
                self.handle_packet_lost(server_IP, server_port, sequence_number)

        ack_checker_thread = Thread(target=check_ack, args=(sequence_number,))
        ack_checker_thread.daemon = True
        ack_checker_thread.start()
        self.add_pending(sequence_number, ack_checker_thread)
        self.UDP_send(sending_packet, server_IP, server_port)
        ColorUtils.print_debug("Timer for package " + str(sending_packet.sequence_number) + " is set up!")

    def update_congestion_window(self, type):
        if type == "ACK Received":
            self.congestion_window_size = min(self.congestion_window_size + 1, Client.MAX_CONGESTION_WINDOW_SIZE)
        elif type == "Packet Lost":
            self.congestion_window_size = max(self.congestion_window_size // 2, 1)
        ColorUtils.print_statistics("Congestion Window size: " + str(self.congestion_window_size))

    def update_time_out_duration(self, sequence_number):
        sampleRTT = (datetime.datetime.now() - self.sent_times[sequence_number]).total_seconds()
        self.DevRTT = (1 - Client.BETA) * self.DevRTT + Client.BETA * (sampleRTT - self.time_out_duration)
        self.EstimatedRTT = (1 - Client.ALPHA) * self.EstimatedRTT + Client.ALPHA * (sampleRTT)
        self.time_out_duration = self.EstimatedRTT + 4 * self.EstimatedRTT
        ColorUtils.print_time_statistics("Round Trip Time: " + str(sampleRTT))

    def get_first_pending(self):
        if self.pending:
            return min(self.pending.keys())
        else:
            return float('+inf')

    def close_connection(self, server_IP, server_port):
        self.is_connected = False
        sending_packet = TCP_Packet(self.port, server_port, self.sequence_number, 0, 0, 0, 1)
        self.UDP_send(sending_packet, server_IP, server_port)

    def connect(self, server_IP, server_port):
        self.TCP_establish_connection(server_IP, server_port)
        self.start_receiving(server_IP, server_port)
        self.start_sending(server_IP, server_port)
        time.sleep(self.connection_duration)
        self.close_connection(server_IP, server_port)
        time.sleep(self.connection_close_wait)


client = Client()
client.connect("10.0.0.2", 20001)



