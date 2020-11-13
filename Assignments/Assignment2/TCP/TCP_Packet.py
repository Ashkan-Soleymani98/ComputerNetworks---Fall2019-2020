class TCP_Packet:
    checksum_buffer_size = 16

    def __init__(self, source_port, destination_port, sequence_number, ack_number, ACK, SYN, FIN):
        self.source_port = source_port
        self.destination_port = destination_port
        self.sequence_number = sequence_number
        self.ack_number = ack_number
        self.ACK = ACK
        self.SYN = SYN
        self.FIN = FIN
        self.checksum = self.calculate_checksum()

    def calculate_checksum(self):
        output = TCP_Packet.checksum_add_all(self.source_port, self.destination_port, self.sequence_number,
                                             self.ack_number, self.merge_flags())
        return TCP_Packet.flip(output)

    def checksum_isValid(self):
        if self.checksum + TCP_Packet.flip(self.calculate_checksum()) == -1:
            return True
        return False

    def merge_flags(self):
        return int(str(self.ACK) + str(self.SYN) + str(self.FIN), 2)

    @staticmethod
    def checksum_add_all(arg1, *args):
        for arg in args:
            arg1 = TCP_Packet.checksum_add(arg1, arg)
        return arg1

    @staticmethod
    def checksum_add(a, b):
        out = bin(a + b)
        if len(out) > TCP_Packet.checksum_buffer_size + 2:
            out = bin(int(out[4:], 2) + 1)
        return int(out, 2)

    @staticmethod
    def flip(a):
        return ~a


class ColorUtils:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[2m'
    UNDERLINE = '\033[4m'

    # server_log = list()
    # client_log = list()
    # server_debug = list()
    # client_debug = list()
    # congestion_windows = list()
    # time_out_durations = list()


    @staticmethod
    def print_log(str, mode="Client"):
        if mode == "Client":
            with open('info/client_log.txt', 'a') as f:
                f.write(str + "\n")
        else:
            with open('info/server_log.txt', 'a') as f:
                f.write(str + "\n")
        print(ColorUtils.WARNING + str + "\n" + ColorUtils.ENDC)

    @staticmethod
    def print_debug(str, mode="Client"):
#         if mode == "Client":
#             with open('info/client_debug.txt', 'a') as f:
#                 f.write(str+ "\n")
#         else:
#             with open('info/server_debug.txt', 'a') as f:
#                 f.write(str+ "\n")
        print(ColorUtils.OKBLUE + str + "\n" + ColorUtils.ENDC)

    @staticmethod
    def print_statistics(str):
        with open('info/congestion_windows.txt', 'a') as f:
            f.write(str.split(" ")[3] + "\n")
        print(ColorUtils.HEADER + str + "\n" + ColorUtils.ENDC)

    @staticmethod
    def print_time_statistics(str):
        with open('info/sample_round_trip_time.txt', 'a') as f:
            f.write(str.split(" ")[3] + "\n")
        print(ColorUtils.FAIL + str + "\n" + ColorUtils.ENDC)

