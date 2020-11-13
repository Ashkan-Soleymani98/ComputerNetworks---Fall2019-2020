import copy

MONITOR_ENABLE = False

class ColorUtils:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[2m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def print_error(string):
        print(ColorUtils.FAIL + string + ColorUtils.ENDC)

    @staticmethod
    def print_ping(string):
        print(ColorUtils.OKBLUE + "----------------")
        print(*string)
        print("----------------" + ColorUtils.ENDC)

    @staticmethod
    def print_monitor(string):
        if MONITOR_ENABLE:
            print(ColorUtils.WARNING + "**************")
            print(string)
            print("**************" + ColorUtils.ENDC)


class Packet:
    def __init__(self, message, sender_ID, receiver_ID, type):
        self.message = message
        self.sender_ID = sender_ID
        self.receiver_ID = receiver_ID
        self.type = type # hello, flood, ping, DBD


class Client:
    def __init__(self, IP):
        self.IP = IP
        self.link = None

    @staticmethod
    def check_valid_IP(IP):
        parts = IP.split(".")
        if len(parts) != 4:
            return False
        for part in parts:
            if not 0 <= int(part) <= 255:
                return False
        return True

    @staticmethod
    def check_uniqueness_IP(clients, IP):
        for client in clients:
            if client.IP == IP:
                return False
        return True

    def set_link(self, link):
        self.link = link

    def send_packet(self, packet):
        if not self.link is None:
            self.link.send_packet(packet, self.IP)

    def receive_packet(self, packet, link):
        ColorUtils.print_monitor(self.IP + ": \n" + "type: " + str(packet.type) + "\nbody: "  + "----------") #TODO + str(*packet.message)
        if packet.type == "ping":
            packet.message += [self.IP]
            ColorUtils.print_ping(packet.message)

    def ping(self, receiver_ID):
        packet = Packet([self.IP], self.IP, receiver_ID, "ping")
        if self.link is not None:
            if not self.link.send_packet(packet, self.IP):
                packet.message += ['invalid']
                ColorUtils.print_ping(packet.message)
        else:
            packet.message += ['unreachable']
            ColorUtils.print_ping(packet.message)



class Router:
    def __init__(self, ID):
        self.ID = ID
        self.num_of_interfaces = 10
        self.num_of_available_interfaces = self.num_of_interfaces
        self.topology_database = {self.ID: {}}
        self.routing_table = {}
        self.receive_timer = {}
        self.send_timer = {}

    @staticmethod
    def check_valid_ID(ID):
        return 1000 <= int(ID) <= 9999

    @staticmethod
    def check_uniqueness_ID(routers, ID):
        for router in routers:
            if router.ID == ID:
                return False
        return True

    def add_link_to_client(self, link, other_side):
        if self.num_of_available_interfaces > 0:
            self.num_of_available_interfaces -= 1
            self.topology_database[self.ID][other_side.IP] = link
            self.topology_database[other_side.IP] = {self.ID: link}
            self.route()
            self.send_advertisement(other_side.IP, "add")
        else:
            ColorUtils.print_error("Interface Limit Reached!")

    def is_link_to_client(self, link, other_side):
        if other_side.IP not in self.topology_database[self.ID].keys():
            ColorUtils.print_error("Such Link Does Not Exists!")

    def is_link_to_router(self, link, other_side):
        if other_side.ID not in self.topology_database[self.ID].keys():
            ColorUtils.print_error("Such Link Does Not Exists!")

    def update_topology_database(self, new_database, sender_ID, type="add"):
        temp_database = {}
        for node in self.topology_database.keys():
            temp_database[node] = copy.copy(self.topology_database[node])
        if type == "add":
            for id in new_database.keys():
                if id not in self.topology_database.keys():
                    self.topology_database[id] = {}
                self.topology_database[id].update(new_database[id])
        elif type == "remove":
            self.topology_database = {}
            for node in new_database.keys():
                self.topology_database[node] = copy.copy(new_database[node])
        if temp_database != self.topology_database:
            self.send_advertisement(sender_ID, type)
            self.route()

    def route(self):
        self.routing_table = {}
        D = {i: float("inf") if i != self.ID else 0 for i in self.topology_database.keys()}
        P = {i: [] if i != self.ID else [-1] for i in self.topology_database.keys()}
        N = [self.ID]
        for neighbor in self.topology_database[self.ID].keys():
            D[neighbor] = self.topology_database[self.ID][neighbor].cost
        num_of_nodes = len(D.keys())
        while len(N) != num_of_nodes:
            for i in N:
                D.pop(i, None)
            min_node = min(D, key=D.get)
            for neighbor in self.topology_database[min_node].keys():
                if neighbor not in N:
                    if D[min_node] + self.topology_database[min_node][neighbor].cost < D[neighbor]:
                        D[neighbor] = D[min_node] + self.topology_database[min_node][neighbor].cost
                        P[neighbor] = P[min_node] + [min_node]
            N.append(min_node)
        for neighbor in self.topology_database[self.ID].keys():
            P[neighbor] = P[neighbor] + [neighbor]
        for i in P.keys():
            if len(P[i]) > 0:
                self.routing_table[i] = P[i][0]

    def send_hello(self, link, first_time=False):
        packet = Packet(self.topology_database[self.ID].keys(), self.ID, None, "hello")
        if link.send_packet(packet, self.ID):
            if first_time:
                # link.states[self.ID] = "hello_sent"
                pass

    def send_database_description(self, link):
        packet = Packet(self.topology_database, self.ID, None, "DBD")
        link.send_packet(packet, self.ID)

    def receive_packet(self, packet, link):
        ColorUtils.print_monitor(self.ID + ": \n" + "type: " + packet.type + "\nbody: " + "----------") #TODO + packet.message
        if packet.type == "hello":
            if link.states[self.ID] == "down":
                if packet.sender_ID not in self.topology_database[self.ID].keys():
                    link.states[self.ID] = "init"
                    self.topology_database[self.ID][packet.sender_ID] = link
                    if packet.sender_ID not in self.topology_database.keys():
                        self.topology_database[packet.sender_ID] = {}
                    # self.topology_database[packet.sender_ID][self.ID] = link
                    self.send_hello(link, first_time=True)
                    self.route()
                else:
                    ColorUtils.print_error("Connection is Already Established!")
            elif link.states[self.ID] == "init":
                if self.ID in packet.message:
                    link.states[self.ID] = "2-way"
                    self.send_hello(link)
                    self.send_database_description(link)
                    self.add_to_timer(packet.sender_ID)
            elif link.states[self.ID] == "2-way":
                self.set_receive_timer(packet.sender_ID)

        elif packet.type == "DBD":
            self.update_topology_database(packet.message, packet.sender_ID, type="add")

        elif packet.type == "flood":
            self.update_topology_database(packet.message, packet.sender_ID, type="remove")

        elif packet.type == "ping":
            packet.message += [self.ID]
            try:
                link = get_link(self.ID, self.routing_table[packet.receiver_ID])
                if link is None:
                    packet.message += ['unreachable']
                    ColorUtils.print_ping(packet.message)
                elif not link.send_packet(packet, self.ID):
                    packet.message += ['invalid']
                    print(self.routing_table)
                    ColorUtils.print_ping(packet.message)
            except KeyError:
                packet.message += ['unreachable']
                ColorUtils.print_ping(packet.message)

    def send_advertisement(self, sender_ID, type):
        if type == "add":
            packet = Packet(self.topology_database, self.ID, None, "DBD")
            for neighbor in self.topology_database[self.ID].keys():
                if neighbor != sender_ID:
                    self.topology_database[self.ID][neighbor].send_packet(packet, self.ID)
        elif type == "remove":
            packet = Packet(self.topology_database, self.ID, None, "flood")
            for neighbor in self.topology_database[self.ID].keys():
                if neighbor != sender_ID:
                    self.topology_database[self.ID][neighbor].send_packet(packet, self.ID)

    def add_to_timer(self, neighbor_ID):
        self.receive_timer[neighbor_ID] = 30
        self.send_timer[neighbor_ID] = 10

    def set_receive_timer(self, neighbor_ID):
        self.receive_timer[neighbor_ID] = 30

    def remove_neighbor(self, neighbor_IDs):
        for neighbor_ID in neighbor_IDs:
            del self.topology_database[self.ID][neighbor_ID]
            del self.receive_timer[neighbor_ID]
            del self.send_timer[neighbor_ID]
        if len(neighbor_IDs) > 0:
            self.send_advertisement(None, "remove")
            # print(neighbor_ID)
            self.route()

    def next_time(self):
        removing_neighbors = list()
        for neighbor in self.receive_timer.keys():
            self.receive_timer[neighbor] -= 1
            # print(self.receive_timer[neighbor])
            if self.receive_timer[neighbor] == 0:
                removing_neighbors.append(neighbor)
        self.remove_neighbor(removing_neighbors)

        for neighbor in self.send_timer.keys():
            self.send_timer[neighbor] -= 1
            if self.send_timer[neighbor] == 0:
                self.send_hello(self.topology_database[self.ID][neighbor])
                self.send_timer[neighbor] = 10



class Link:
    def __init__(self, first_side, second_side, cost):  #state = down init, 2-way, full
        self.first_side = first_side
        self.second_side = second_side
        self.cost = cost
        self.state = "intact"
        self.sides = {
            self.first_side.IP if type(self.first_side) is Client else self.first_side.ID: self.second_side,
            self.second_side.IP if type(self.second_side) is Client else self.second_side.ID: self.first_side
        }
        self.states = {
            self.first_side.IP if type(self.first_side) is Client else self.first_side.ID: "down",
            self.second_side.IP if type(self.second_side) is Client else self.second_side.ID: "down"
        }

    def establish_connection(self):
        self.state = "intact"
        if type(self.first_side) is Client and type(self.second_side) is Client:
            ColorUtils.print_error("Impossible Connection Between Two Clients!")
        elif type(self.first_side) is Client and type(self.second_side) is Router:
            self.second_side.add_link_to_client(self, self.first_side)
            self.first_side.set_link(self)
        elif type(self.first_side) is Router and type(self.second_side) is Client:
            self.first_side.add_link_to_client(self, self.second_side)
            self.second_side.set_link(self)
        elif type(self.first_side) is Router and type(self.second_side) is Router:
            self.first_side.send_hello(self, first_time=True)

    def disable_connection(self):
        self.state = "broken"
        for side in self.states:
            self.states[side] = "down"
        if type(self.first_side) is Client and type(self.second_side) is Client:
            ColorUtils.print_error("Impossible Connection Between Two Clients!")
        elif type(self.first_side) is Client and type(self.second_side) is Router:
            self.second_side.is_link_to_client(self, self.first_side)
        elif type(self.first_side) is Router and type(self.second_side) is Client:
            self.first_side.is_link_to_client(self, self.second_side)
        elif type(self.first_side) is Router and type(self.second_side) is Router:
            self.first_side.is_link_to_router(self, self.second_side)

    def send_packet(self, packet, last_hop_ID):
        if self.state == "intact":
            self.sides[last_hop_ID].receive_packet(packet, self)
            return True
        else:
            ColorUtils.print_error("Link Not Available!")
            return False



clients = list()
routers = list()
links = list()

def add_client(IP):
    if Client.check_valid_IP(IP):
        if Client.check_uniqueness_IP(clients, IP):
            new_client = Client(IP)
            clients.append(new_client)
        else:
            ColorUtils.print_error("Repeated IP!")
    else:
        ColorUtils.print_error("Invalid IP!")

def add_router(ID):
    if Router.check_valid_ID(ID):
        if Router.check_uniqueness_ID(routers, ID):
            new_router = Router(ID)
            routers.append(new_router)
        else:
            ColorUtils.print_error("Repeated ID!")
    else:
        ColorUtils.print_error("Invalid ID!")

def is_client(ID):
    return Client.check_valid_IP(ID)

def is_router(ID):
    return Router.check_valid_ID(ID)

def get_entity(ID):
    if is_client(ID):
        return get_client(ID)
    elif is_router(ID):
        return get_router(ID)

def get_client(IP):
    for client in clients:
        if client.IP == IP:
            return client
    ColorUtils.print_error("IP " + str(IP) + "Not Found!")

def get_router(ID):
    for router in routers:
        if router.ID == ID:
            return router
    ColorUtils.print_error("IP " + str(ID) + "Not Found!")

def get_link(id1, id2):
    for link in links:
        if link.first_side == get_entity(id1) and link.second_side == get_entity(id2) \
                or link.second_side == get_entity(id1) and link.first_side == get_entity(id2):
            return link
    ColorUtils.print_error("Link Not Found!")
    return None


while True:
    inputline = input()
    command = inputline.split()[0]
    if command == "sec":
        value = int(inputline.split()[1])
        for i in range(value):
            for router in routers:
                router.next_time()

    elif command == "add":
        typo = inputline.split()[1]
        id = inputline.split()[2]
        if typo == "router":
            add_router(id)
        elif typo == "client":
            add_client(id)

    elif command == "connect":
        id1 = inputline.split()[1]
        id2 = inputline.split()[2]
        cost = int(inputline.split()[3])
        new_link = Link(get_entity(id1), get_entity(id2), cost)
        new_link.establish_connection()
        links.append(new_link)

    elif command == "link":
        id1 = inputline.split()[1]
        id2 = inputline.split()[2]
        typo = inputline.split()[3]
        link = get_link(id1, id2)
        if typo == "e":
            link.establish_connection()
        elif typo == "d":
            link.disable_connection()

    elif command == "ping":
        id1 = inputline.split()[1]
        id2 = inputline.split()[2]
        client = get_client(id1)
        if is_client(id2):
            client.ping(id2)
        else:
            ColorUtils.print_error("Invalid IP!")

    elif command == "monitor":
        typo = inputline.split()[1]
        if typo == "e":
            MONITOR_ENABLE = True
        elif typo == "d":
            MONITOR_ENABLE = False

    elif command == "end":
        break

    else:
        ColorUtils.print_error("Invalid Command!")