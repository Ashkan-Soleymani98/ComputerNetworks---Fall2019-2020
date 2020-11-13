from typing import Dict, Set, List


class Packet:

    def __init__(self, dest) -> None:
        super().__init__()
        self.dest = dest
        self.ttl = 15


class TableEntry:

    def __init__(self, distance, nextHop):
        super().__init__()
        self.distance = distance
        self.nextHop = nextHop
        self.hold_timer = 0
        self.flush_timer = 0
        self.holded = False
        self.shouldBeFlushed = False

    def get_distance(self):
        return self.distance

    def set_distance(self, dist):
        if dist == 16:
            self.holded = True
            self.shouldBeFlushed = False
        else:
            self.holded = False
            self.shouldBeFlushed = False
            self.hold_timer = 0
            self.flush_timer = 0
        self.distance = dist

    def next_time(self):
        if self.distance != 16:
            return
        self.hold_timer += 1
        self.flush_timer += 1

        if self.hold_timer >= 60:
            self.hold_timer = 0
            self.holded = False

        if self.flush_timer >= 120:
            self.flush_timer = 0
            self.shouldBeFlushed = True


    def __repr__(self):
        return str(self)

    def __str__(self) -> str:
        return "Distance: " + str(self.distance) + " NextHop" + str(self.nextHop.id if self.nextHop is not None else "None") + " HT: " + str(
            self.hold_timer) + " FT: " + str(self.flush_timer)


class Router:

    def __init__(self, id) :
        super().__init__()
        self.id = id
        self.advertiseTimer = 0
        self.table = {}
        self.clients = set()
        self.neighbours = set()
        self.invalidTimer = {}

    def advertise(self):
        # print("Router" + str(self.id) + " Advertising...")
        for n in self.neighbours:
            adv = {}
            for client, entry in self.table.items():
                # Sending Invalids
                dist = entry.distance if (entry.nextHop is not n) else 16
                adv[client] = dist
            send_adv(self, n, adv)

    def next_time(self):
        self.advertiseTimer += 1
        if self.advertiseTimer is 30:
            self.advertise()
            self.advertiseTimer = 0

        to_pop = []
        for client, entry in self.table.items():
            entry.next_time()
            if entry.shouldBeFlushed:
                to_pop.append(client)
        for client in to_pop:
            self.table.pop(client)

        toInvalidate = set()
        for n in self.invalidTimer.keys():
            self.invalidTimer[n] += 1
            if self.invalidTimer[n] >= 180:
                # print(time, "Invalidating ", n.id)
                toInvalidate.add(n)
        for n in toInvalidate:
                self.invalidate(n)

    def get_advertisement(self, source, advertisement):
        # print("Router" + str(self.id) + " Received Advertisment " + str(source.id))
        self.invalidTimer[source] = 0
        for client, dist in advertisement.items():
            if client not in self.table.keys():
                self.table[client] = TableEntry(min(dist + 1, 16), source)
            entry = self.table[client]
            if not entry.holded and dist + 1 < entry.distance:
                entry.set_distance(dist + 1)
                entry.nextHop = source
            if not entry.holded and entry.nextHop is source:
                entry.set_distance(dist + 1 if dist != 16 else 16)

    def send(self, pckt):
        # print("Sending to ", pckt.dest, "via ", self.id, "clients: ", self.clients)
        dest = pckt.dest
        print(self.id, end=" ")
        if dest not in self.table.keys():
            print("INVALID")
            return
        entry = self.table[dest]
        if entry.distance == 16:
            print("INVALID")
            return
        if pckt.ttl == 0:
            print("TTL")
            return
        if dest in self.clients:
            print(dest)
        else:
            pckt.ttl -= 1
            send_pckt(self, entry.nextHop, pckt)

    def add_neighbour(self, router):
        self.neighbours.add(router)
        self.invalidTimer[router] = 0

    def add_client(self, client):
        self.table[client] = TableEntry(0, None)
        self.clients.add(client)

    def __str__(self) -> str:
        return "Router" + str(self.id) + ":\n" + str(self.table)

    def invalidate(self, n):
        for client, entry in self.table.items():
            if entry.nextHop is n:
                entry.set_distance(16)
        self.invalidTimer.pop(n)
        self.neighbours.remove(n)
        pass


clients_router = {}
routers = {}
network = {}
time = 0


def next_time():
    global time
    time = time + 1
    for router in network.keys():
        router.next_time()


def create_router(value):
    router = Router(value)
    network[router] = set()
    routers[value] = router


def connect_router(id1, id2):
    router1, router2 = routers[id1], routers[id2]
    network[router1].add(router2)
    network[router2].add(router1)
    router1.add_neighbour(router2)
    router2.add_neighbour(router1)


def disconnect_router(id1, id2):
    router1, router2 = routers[id1], routers[id2]
    network[router1].remove(router2)
    network[router2].remove(router1)


def delete_router(id):
    router = routers[id]
    for n in network[router]:
        network[n].remove(router)
    network.pop(router)


def create_client(client, id):
    router = routers[id]
    router.add_client(client)
    clients_router[client] = router


def ping(client1, client2):
    source = clients_router[client1]
    pckt = Packet(client2)
    print(client1, end=" ")
    source.send(pckt)


def send_adv(source, dest, adv):
    if dest in network[source]:
        dest.get_advertisement(source, adv)


def send_pckt(source:Router, nextHop, pckt):
    if nextHop in network[source]:
        nextHop.send(pckt)
    else:
        print("UNREACHABLE")


while True:
    inputline = input()
    command = inputline.split()[0]
    if command == "time":
        value = int(inputline.split()[1])
        for i in range(value):
            next_time()
        # for router in routers.values():
        #     print(router)
        # print("--------------------\n\n")

    elif command == "create_router":
        value = int(inputline.split()[1])
        create_router(value)

    elif command == "connect":
        id1 = int(inputline.split()[1])
        id2 = int(inputline.split()[2])
        connect_router(id1, id2)

    elif command == "disconnect":
        id1 = int(inputline.split()[1])
        id2 = int(inputline.split()[2])
        disconnect_router(id1, id2)

    elif command == "delete_router":
        value = int(inputline.split()[1])
        delete_router(value)

    elif command == "create_client":
        address = inputline.split()[1]
        router = int(inputline.split()[2])
        create_client(address, router)

    elif command == "ping":
        client1 = inputline.split()[1]
        client2 = inputline.split()[2]
        ping(client1, client2)

    elif command == "END":
        break

    else:
        print("Invalid Command!")
