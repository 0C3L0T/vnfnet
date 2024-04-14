# VNFnet Simulator v10.0.1
# VNF Simulation Laboratory | Fork of VNFnet2018
# Dr. Anestis Dalgkitsis ✖️ | VNFnet2020 started 29 March 2020 | Last update of VNFnet2020: 23 Jan 2022

# Python Modules
import os
import warnings
from enum import Enum

import networkx as nx
import matplotlib.pyplot as plt
import logging

# Apple ARM Fix
# import matplotlib  
# matplotlib.use('Qt5Agg')
# from matplotlib import pyplot as plt

# Suppress Warnings
warnings.filterwarnings("ignore")

# create a log directory if it does not exist
if not os.path.isdir('logs'):
    os.mkdir('logs')

logger = logging.getLogger(__name__)
logging.basicConfig(filename='./logs/VNFnetLog.log', level=logging.INFO, format='%(asctime)s - %(message)s')

logger.info(" >>>> New VNFnet Session >>>>")


# Simulation Classes

class TrafficPattern(Enum):
    RESERVED = 1
    SQUARE = 2
    SAW = 3


class Chain:
    def __init__(self, uid: int, title: str, chain_list, sla) -> None:
        self.uid = uid
        self.title = title
        self.sla = sla
        self.chain = chain_list  # DATA FLOW -> FROM FIRST TO LAST VM!

    def destination(self) -> str:
        return self.chain[len(self.chain) - 1].host.uid

    def __str__(self) -> str:
        text = ""

        for vm in self.chain:
            text += str(vm.uid)
            text += ">"

        text = text[:-1]
        return text


class Service:
    def __init__(self, uid: int, title="Untitled_Service", cpu_cores=1, ram=1, storage=1, bandwidth=0.22) -> None:
        self.name = title
        self.uid = uid
        self.CPU_requirements = cpu_cores
        self.RAM_requirements = ram
        self.storage_requirements = storage
        self.bandwidth_requirements = bandwidth


class Host:
    def __init__(self, uid: int, name="Untitled_host", cpu_cores=4, ram=8, storage=128, cpu_frequency=2.6,
                 cpu_cycles_per_sample_data=(10 ** 4)) -> None:

        # Host Attributes
        self.name = name
        self.uid = uid

        self.CPUcap = cpu_cores
        self.RAMcap = ram
        self.StorageCap = storage

        self.cpuFrequency = cpu_frequency ** 9  # GHz to Hz
        self.cpuCyclesPerSampleData = cpu_cycles_per_sample_data  # CPU Cycles Number
        self.architectureEffectiveSwitchedCapacitance = 10 ** (-28)
        self.bitsOverhead = 8440000  # 1.055 MB

        # Host Simulation Variables
        self.CPUUtil = 0
        self.RAMUtil = 0
        self.StorageUtil = 0

        self.runningServices = []

    def instantiate_service(self, service_object: Service) -> int:
        """ return 0 means hosted ok, return 1 means that it can not be hosted """

        if self.CPUcap < (self.CPUUtil + service_object.CPU_requirements):
            logger.info("[Host Alert] Full CPU on host: " + str(self.uid))  # + " | Top: " + str(self.top()))
            return 1
        if self.RAMcap < (self.RAMUtil + service_object.RAM_requirements):
            logger.info("[Host Alert] Full RAM on host: " + str(self.uid))  # + " | Top: " + str(self.top()))
            return 1
        if self.StorageCap < (self.StorageUtil + service_object.storage_requirements):
            logger.info("[Host Alert] Full Storage on host: " + str(self.uid))  # + " | Top: " + str(self.top()))
            return 1

        self.CPUUtil += service_object.CPU_requirements
        self.RAMUtil += service_object.RAM_requirements
        self.StorageUtil += service_object.storage_requirements

        self.runningServices.append(service_object)

        return 0

    def kill_service(self, service_object: Service) -> int:
        """ return 0 means killed ok, return 1 means that the service does not run in this host """

        for service in range(len(self.runningServices)):
            if service_object.uid == self.runningServices[service].uid:
                self.CPUUtil -= self.runningServices[service].CPUrequirements
                self.RAMUtil -= self.runningServices[service].RAMrequirements
                self.StorageUtil -= self.runningServices[service].StorageRequirements

                del self.runningServices[service]

                return 0
        logger.info("[Host Alert] Service to terminate does not exist: ")
        return 1

    def sample_energy_consumption(self) -> float:
        server_consumption = self.CPUUtil * self.architectureEffectiveSwitchedCapacitance * self.cpuCyclesPerSampleData * self.bitsOverhead * (self.cpuFrequency ** 2)
        return server_consumption


class VM:
    def __init__(self, uid: int, name: str, service_image, host_object: Host) -> None:
        self.uid = uid
        self.name = name

        self.service = service_image
        self.host = host_object


class Link:
    def __init__(self, uid: int, source_object, destination_object, bandwidth=1, latency=1,
                 optical_power_tx=-2) -> None:

        # Link Attributes
        self.uid = uid

        self.bandwidthCap = bandwidth  # Gbps
        self.latency = latency  # ms

        self.source = source_object
        self.destination = destination_object

        self.opticalPowerTX = optical_power_tx  # dBm

        # Link Simulation Variables
        self.bandwidthUtil = bandwidth
        self.runningConnections = []

    def establish_connection(self, service_object: Service) -> int:
        """return 0 means ok, 1 means can not be hosted"""

        if self.bandwidthCap < (self.bandwidthUtil + service_object.bandwidth_requirements):
            logger.info("[linkALERT] full capacity reached on: " + str(self.uid))  # + " | Top: " + str(self.top()))
            return 1

        self.bandwidthUtil += service_object.bandwidth_requirements
        self.runningConnections.append(service_object)

        return 0

    def close_connection(self, service_object: Service) -> int:
        """ return 0 means closed, 1 means the connection does not exist """

        for service in range(len(self.runningConnections)):
            if service_object.uid == self.runningConnections[service].id:
                self.bandwidthUtil -= self.runningConnections[service].bandwidthRequirements
                del self.runningConnections[service]
                return 0

        logger.warning("Connection to kill does not exist")  #: " + str(self.top()))
        return 1

    def top(self) -> list[int]:
        """returns a list with the IDs of all running connections"""

        topConnectionsID = []
        for connection in range(len(self.runningConnections)):
            topConnectionsID.append(self.runningConnections[connection].id)
        return topConnectionsID

    def sample_energy_consumption(self, datasize: float) -> float:  # bits
        link_consumption = -self.opticalPowerTX * (datasize / self.bandwidthUtil * (10 ** -9))
        return link_consumption


class Domain:
    def __init__(self, uid: int, name: str, host_list: list[Host], link_list: list[Link]) -> None:
        self.uid = uid
        self.name = name
        self.hostList = host_list
        self.linkList = link_list


class User:
    def __init__(self, uid: int, name: str, vm_chain: Chain, data_rate: float, traffic_pattern: TrafficPattern) -> None:

        # User Attributes
        self.uid = uid
        self.name = name

        self.bitsOverhead = 8440000  # 1.055 MB
        self.userChain = vm_chain  # One Chain for every user
        self.bandwidth = data_rate  # Gbps. Casual mmWave 5G 0.1 Gbps
        self.traffic_pattern = traffic_pattern  # Default: Reserved, otherwise: Square or Saw

        # Simulation Variables
        self.runtime_user_data_rate = self.bandwidth
        self.counter = 0

    def traffic_pattern_generator(self) -> float:

        if self.traffic_pattern == TrafficPattern.SQUARE:
            if self.counter % 2 == 0:
                self.runtime_user_data_rate = 0.3 * self.bandwidth
            else:
                self.runtime_user_data_rate = self.bandwidth

        if self.traffic_pattern == TrafficPattern.SAW:
            self.runtime_user_data_rate = abs(self.counter) % 10 * 0.1 * self.bandwidth

        self.counter += 1

        return self.runtime_user_data_rate


class Connection:
    def __init__(self, uid: int, node_path, user_object: User) -> None:
        self.uid = uid
        self.nodePath = node_path
        self.userObject = user_object


class Network:
    def __init__(self, title: str) -> None:

        self.title = title
        # Network Graph
        self.topologyGraph = nx.Graph()

        # Network Entities
        self.networkHosts = []
        self.networkUsers = []
        self.networkLinks = []
        self.networkServices = []
        self.networkVMs = []
        self.networkChains = []
        self.networkDomains = []

        # Statistics (Used for ML regularization)
        self.maxNetCPU = -1
        self.maxNetRAM = -1
        self.maxNetStorage = -1
        self.maxNetLatency = -1
        self.maxNetBandwidth = -1
        self.maxNetSLA = -1

        # Internal Variables
        self.guidCounter = -1  # Graph Unique Identifier Counter

        self.suspendedLinks = []
        self.trafficActivityList = []

    # Internal Utilities

    def get_guid(self) -> int:
        self.guidCounter += 1
        return self.guidCounter

    # Network Building Commands

    def add_host(self, hostname: str, cpu_cores: int, ram: int, storage: int) -> Host:

        uid = self.get_guid()
        hostObject = Host(uid, hostname, cpu_cores, ram, storage)
        self.networkHosts.append(hostObject)

        self.topologyGraph.add_node(uid, label=hostname, shapes="o")
        logger.info("Host added with uid: " + str(uid) + ", hostname: " + str(hostname) + ".")

        if cpu_cores > self.maxNetCPU:
            self.maxNetCPU = cpu_cores
        if ram > self.maxNetRAM:
            self.maxNetRAM = ram
        if storage > self.maxNetStorage:
            self.maxNetStorage = storage

        return hostObject

    def add_user(self, name: str, vm_chain, data_rate=1, traffic_pattern=TrafficPattern.RESERVED) -> User:  # , sla=10

        uid = self.get_guid()
        userObject = User(uid, name, vm_chain, data_rate, traffic_pattern)  # , sla
        self.networkUsers.append(userObject)

        self.topologyGraph.add_node(uid, uid=uid, label=name, shapes="v")
        logger.info("User with uid: " + str(uid) + " added.")

        return userObject

    def remove_user(self, user_object: User) -> bool:

        self.topologyGraph.remove_node(user_object.uid)
        self.networkUsers.remove(user_object)
        del user_object

        return True

    def add_link(self, source_host_object: Host, destination_host_object: Host, bandwidth=10, delay=5, loss=0) -> Link:

        uid = self.get_guid()
        linkObject = Link(uid, source_host_object, destination_host_object, bandwidth=bandwidth, latency=delay)
        self.networkLinks.append(linkObject)

        if loss > 0:
            self.topologyGraph.add_edge(source_host_object.uid, destination_host_object.uid, uid=uid, color='m',
                                        style="dashed", weight=bandwidth / 12, length=delay, delay=delay,
                                        bandwidth=bandwidth, loss=loss)
        else:
            self.topologyGraph.add_edge(source_host_object.uid, destination_host_object.uid, uid=uid, color='skyblue',
                                        style="solid", weight=bandwidth / 12, length=delay, delay=delay,
                                        bandwidth=bandwidth, loss=loss)

        logger.info("Link " + "(" + str(source_host_object.uid) + ")<->(" + str(
            destination_host_object.uid) + ")" + " with bandwidth: " + str(bandwidth) + " added with uid: " + str(
            uid) + ".")

        if delay > self.maxNetLatency:
            self.maxNetLatency = delay
        if bandwidth > self.maxNetBandwidth:
            self.maxNetBandwidth = bandwidth

        return linkObject

    def remove_link(self, link_object: Link) -> bool:

        self.topologyGraph.remove_edge(link_object.source, link_object.destination)
        self.networkLinks.remove(link_object)
        del link_object

        return True

    def add_service(self, title: str, cpu_cores=2, ram=3, storage=8) -> Service:

        uid = self.get_guid()
        service_object = Service(uid, title, cpu_cores=cpu_cores, ram=ram, storage=storage)
        self.networkServices.append(service_object)

        logger.info("Service added with uid: " + str(uid) + ".")

        return service_object

    def add_chain(self, title: str, service_object_list: list[Service], sla: int) -> Chain:

        uid = self.get_guid()
        chainObject = Chain(uid=uid, title=title, chain_list=service_object_list, sla=sla)
        self.networkChains.append(chainObject)
        logger.info("Chain added with uid: " + str(uid) + ".")

        return chainObject

    def remove_chain(self, chain_object: Chain) -> bool:

        self.networkChains.remove(chain_object)
        del chain_object

        return True

    def add_domain(self, name: str, host_list: list[Host], link_list: list[Link]) -> Domain:

        uid = self.get_guid()
        domainObject = Domain(uid, name, host_list, link_list)
        self.networkDomains.append(domainObject)
        logger.info("Domain " + str(name) + " added with uid: " + str(uid) + ".")

        return domainObject

    # VM Orchestration Operations

    def instantiate_vm(self, service_object: Service, host_object: Host) -> VM:

        uid = self.get_guid()
        title2 = service_object.name + str(uid)
        VM_object = VM(uid, title2, service_object, host_object)
        self.networkVMs.append(VM_object)
        logger.info("Service VM Instantiated with uid: " + str(uid) + ".")

        error = host_object.instantiate_service(service_object)

        if error:
            logger.error("Error Instantiating Service VM in Host, check logfile. Err: " + str(error))

        self.topologyGraph.add_node(uid, uid=uid, label=title2, shapes="^")
        self.topologyGraph.add_edge(uid, host_object.uid, uid=uid, color='g', style="dashed", weight=1, length=12,
                                    delay=99999, bandwidth=0, loss=100)

        return VM_object

    def terminate_vm(self, vm_object: VM) -> bool:
        hostObject = vm_object.host
        error = hostObject.kill_service(vm_object.service)
        if error:
            logger.error("Error while terminating VM in host. Check the class code.")
            return False

        self.topologyGraph.remove_node(vm_object.uid)
        self.topologyGraph.remove_edge(vm_object.uid, hostObject.uid)

        return True

    def migrate_vm(self, vm: VM, source_host_object: Host, destination_host_object: Host) -> bool:

        connectionsWithThisHost = []

        # Discover connections to update

        if source_host_object == destination_host_object:
            logger.warning("Source and destination hosts are the same.")
            return True
        for connection in self.trafficActivityList:
            if vm.host in connection.nodePath:
                connectionsWithThisHost.append(connection)

        # Stop Traffic in old host (BM)

        for connection in connectionsWithThisHost:
            # self.stopTraffic(connection.userObject)
            er = self.stop_traffic(connection)
            if not er:
                logger.error("Error in vm.stop(): " + str(er))
                return False

        # Start traffic in new host (AM)

        for connection in connectionsWithThisHost:
            error = self.start_traffic(connection)
            if not error:
                logger.error("Error migrating, could not start connection in new host.")
                return False

        # Terminate VM instance in old host (BM)

        error = source_host_object.kill_service(vm.service)
        if error:
            logger.error("Error while terminating VM with uid " + str(vm.uid) + " in host with uid " + str(
                source_host_object.uid) + ". VM not found in host.")
            return False
        else:
            logger.info(
                "VM with uid " + str(vm.uid) + " in host " + str(source_host_object.uid) + " terminated successfully.")
            self.topologyGraph.remove_edge(vm.uid, source_host_object.uid)

        # Instantiate VM instance in new host (AM)

        # self.instantiateVM(vm.service, destinationHostObject)
        error = destination_host_object.instantiate_service(vm.service)
        if error:
            logger.error("Error Instantiating Service VM in Host, check logfile. Err: " + str(error))
        else:
            logger.info("Service VM Instantiated.")
            self.topologyGraph.add_edge(vm.uid, destination_host_object.uid, uid=vm.uid, color='g', style="dashed",
                                        weight=1, length=12, delay=99999, bandwidth=0, loss=100)

        # Log Action

        vm.host = destination_host_object
        logger.info("Migration successful. Info: " + str(vm.uid) + " (" + str(source_host_object.uid) + ")->-(" + str(
            destination_host_object.uid) + ").")
        return True

    # Traffic Flows Management

    def create_connection(self, user_object: User) -> bool | list[any]:

        # Calculate Available Route (Dijkstra)

        chainNodePath = []
        try:
            nodePath = nx.single_source_dijkstra(self.topologyGraph, user_object.uid,
                                                 user_object.userChain.chain[0].host.uid, weight='delay')
        except nx.NetworkXNoPath:
            logger.error("except NetworkXNoPath")
            return False
        chainNodePath.extend(nodePath[1])
        for n in range(len(user_object.userChain.chain) - 1):
            chainNodePath = chainNodePath[:-1]
            try:
                nodePath = nx.single_source_dijkstra(self.topologyGraph, user_object.userChain.chain[n].host.uid,
                                                     user_object.userChain.chain[n + 1].host.uid, weight='delay')
            except nx.NetworkXNoPath:
                return False
            chainNodePath.extend(nodePath[1])
        logger.info(
            "User uid " + str(user_object.uid) + " has this host chain path: " + str(chainNodePath) + " with this SC:")
        for h in range(len(user_object.userChain.chain)):
            logger.info(" |- VM [" + str(user_object.userChain.chain[h].uid) + "] in host (" + str(
                user_object.userChain.chain[h].host.uid) + ")")

        # Allocate bandwidth on Links

        for edge in range(len(chainNodePath) - 1):
            linkAttributesJSON = self.topologyGraph.get_edge_data(chainNodePath[edge], chainNodePath[edge + 1])
            linkbandwidth = linkAttributesJSON["bandwidth"]
            linkuid = linkAttributesJSON["uid"]
            bandwidthAfter = linkbandwidth - user_object.bandwidth
            logger.info(
                "Link uid: " + str(linkuid) + " bandwidth_after is " + str(bandwidthAfter) + " of connection (" + str(
                    chainNodePath[edge]) + ")-(" + str(chainNodePath[edge + 1]) + ").")
            if bandwidthAfter <= 0:
                logger.warning("Cannot create connection between nodes: " + str(chainNodePath[edge]) + " and " + str(
                    chainNodePath[
                        edge + 1]) + ". ZERO OR NEGATIVE bandwidth AFTER TRAFFIC ASSIGNMENT. Adding link to suspended.")
                self.suspendedLinks.append([chainNodePath[edge], chainNodePath[edge + 1],
                                            self.topologyGraph[chainNodePath[edge]][chainNodePath[edge + 1]]])
                self.topologyGraph.remove_edge(chainNodePath[edge], chainNodePath[edge + 1])
                return True
            self.topologyGraph[chainNodePath[edge]][chainNodePath[edge + 1]]['bandwidth'] = bandwidthAfter

            index = 0
            for link in self.networkLinks:
                if link.uid == linkuid:
                    break
                index += 1
            self.networkLinks[index].bandwidthUtil = bandwidthAfter

        return chainNodePath

    def unsuspend_links(self) -> None:
        if self.suspendedLinks:
            for link in self.suspendedLinks[:]:
                attributesList = link[2]
                self.topologyGraph.add_edge(link[0], link[1], uid=attributesList["uid"], color=attributesList["color"],
                                            style=attributesList["style"], weight=attributesList["weight"],
                                            length=attributesList["length"], delay=attributesList["delay"],
                                            bandwidth=attributesList["bandwidth"], loss=attributesList["loss"])
                self.suspendedLinks.remove(link)
        return

    def start_traffic(self, user_object: User) -> bool | Connection:

        while True:
            chainNodePath = self.create_connection(user_object)
            if isinstance(chainNodePath, list):
                logger.info("chainNodePath " + str(chainNodePath) + " defined successfully")
                break
            elif not chainNodePath:

                logger.info("suspended links <<ffXX>> dump: " + str(self.suspendedLinks))

                self.unsuspend_links()

                logger.info("suspended links <<rrXX>> dump: " + str(self.suspendedLinks))

                logger.warning("chainNodePath of user " + str(
                    user_object.uid) + "COULD NOT BE DEFINED. No links with available bandwidth are connected to the "
                                       "destination node.")

                return False  # Refuse service
            else:
                logger.info("Rerouting. Removed unavailable link from graph.")
                pass

        logger.info("suspended links <<ff>> dump: " + str(self.suspendedLinks))

        self.unsuspend_links()

        logger.info("suspended links <<rr>> dump: " + str(self.suspendedLinks))

        uid = len(self.trafficActivityList)
        connectionObject = Connection(uid, chainNodePath, user_object)
        self.trafficActivityList.append(connectionObject)

        return connectionObject

    def stop_traffic(self, connection_object: Connection) -> bool:
        if not connection_object:
            logger.warning("Connection does not exist. Service was denied during request.")
            return False
        logger.info("stopTraffic(@args) >> connectionObject.nodePath: " + str(connection_object.nodePath))
        for edge in range(len(connection_object.nodePath) - 1):
            linkAttributesJSON = self.topologyGraph.get_edge_data(connection_object.nodePath[edge],
                                                                  connection_object.nodePath[edge + 1])
            linkbandwidth = linkAttributesJSON["bandwidth"]
            linkuid = linkAttributesJSON["uid"]
            bandwidthAfter = linkbandwidth + connection_object.userObject.bandwidth
            self.topologyGraph[connection_object.nodePath[edge]][connection_object.nodePath[edge + 1]][
                'bandwidth'] = bandwidthAfter
            index = 0
            for link in self.networkLinks:

                if link.uid == linkuid:
                    break
                index += 1
            self.networkLinks[index].bandwidthUtil = bandwidthAfter
            logger.info("Traffic stopped in edge: " + str(connection_object.nodePath[edge]))
        self.trafficActivityList.remove(connection_object)
        logger.info("Traffic connection " + str(connection_object.nodePath) + " stopped successfully.")
        return True

    def service_ping(self, connection_object: Connection) -> int:
        if not connection_object:
            logger.error(
                "DURING SERVICEPING. THIS MESSAGE SHOULD NOT DISPLAY! Connection does not exist. Service was denied "
                "during request.")
            return 99999  # Denied flag
        logger.info("servicePing(@args) >> connectionObject.nodePath: " + str(connection_object.nodePath))
        rtt = 0
        for edge in range(len(connection_object.nodePath) - 1):
            linkAttributesJSON = self.topologyGraph.get_edge_data(connection_object.nodePath[edge],
                                                                  connection_object.nodePath[edge + 1])
            rtt += linkAttributesJSON["delay"]
        logger.info(
            "servicePing for chain " + str(connection_object.nodePath) + " done with result: " + str(rtt) + "ms.")
        return rtt

    def service_data(self, connection_object: Connection) -> int:
        if not connection_object:
            logger.error(
                "DURING SERVICEDATA. THIS MESSAGE SHOULD NOT DISPLAY! Connection does not exist. Service was denied "
                "during request.")
            return -1  # Denied flag
        logger.info("serviceData(@args) >> connectionObject.nodePath: " + str(connection_object.nodePath))

        linkEnergy = 0
        if len(connection_object.nodePath) - 2 != 0:  # is not
            for i in range(len(connection_object.nodePath) - 2):
                for link in self.networkLinks:
                    if link.source.uid == connection_object.nodePath[i] and link.destination.uid == \
                            connection_object.nodePath[i + 1]:
                        linkEnergy += link.sample_energy_consumption(link.source.bitsOverhead)
                        if linkEnergy == 0:
                            print(linkEnergy)
                            print(link.source.bitsOverhead)
                            print(connection_object.nodePath)
                            print(connection_object.nodePath[i])
                            print(connection_object.nodePath[i + 1])
                            exit()
        else:
            for link in self.networkLinks:
                if link.source.uid == connection_object.nodePath[0] and link.destination.uid == \
                        connection_object.nodePath[1]:
                    linkEnergy += link.sample_energy_consumption(link.source.bitsOverhead)
                    if linkEnergy == 0:
                        print(linkEnergy)
                        print(link.source.bitsOverhead)
                        print(connection_object.nodePath)
                        print(connection_object.nodePath[0])
                        print(connection_object.nodePath[1])
                        exit()
        if linkEnergy == 0:
            print("Zero Energy! ERROR! Dump info:")
            print(connection_object.nodePath)
            exit()

        logger.info("serviceData for chain " + str(connection_object.nodePath) + " done with result: " + str(
            linkEnergy) + " bits.")
        return linkEnergy

    @staticmethod
    def service_perf(connection_object: Connection) -> float:
        if not connection_object:
            logger.error(
                "DURING SERVICEPERF. THIS MESSAGE SHOULD NOT DISPLAY! Connection does not exist. Service was denied "
                "during request.")
            return 0  # Denied flag

        logger.info("Starting SERVICE PERF of user " + str(connection_object.userObject.uid))
        bw = connection_object.userObject.traffic_pattern_generator()
        logger.info("SERVICE PERF done with result: " + str(bw) + "Gbps.")
        return bw

    def service_performance_score(self, connection_object: Connection) -> float:
        rtt = self.service_ping(connection_object)
        bw = self.service_perf(connection_object)
        return bw / rtt

    # Interactive Terminal Commands

    def print_topology(self) -> None:

        plt.figure(1)
        plt.clf()

        # Positions for all nodes
        pos = nx.spring_layout(self.topologyGraph)

        # Fetch graph attributes / Calculate graph element attributes
        edges = self.topologyGraph.edges()
        colors = [self.topologyGraph[u][v]['color'] for u, v in edges]
        weights = [self.topologyGraph[u][v]['weight'] for u, v in edges]
        lengths = [self.topologyGraph[u][v]['length'] for u, v in edges]
        styles = [self.topologyGraph[u][v]['style'] for u, v in edges]

        nodes = self.topologyGraph.nodes()
        shapes = set((aShape[1]["shapes"] for aShape in nodes(data=True)))

        # Blue nodes: Servers, size = capacity
        # Magenta nodes: Users
        for aShape in shapes:
            nx.draw_networkx_nodes(self.topologyGraph, pos, node_size=700, node_shape=aShape,
                                   nodelist=[sNode[0] for sNode in filter(lambda x: x[1]["shapes"] == aShape,
                                                                          self.topologyGraph.nodes(data=True))])

        # Solid lines: optical links, size = free capacity
        # Magenta dashed lines: wireless links, size = free capacity.
        nx.draw_networkx_edges(self.topologyGraph, pos, edgelist=self.topologyGraph.edges, edge_color=colors,
                               style=styles, width=weights)  # length=lengths
        nx.draw_networkx_labels(self.topologyGraph, pos, font_size=20, font_family='sans-serif')

        plt.axis('off')
        plt.savefig("./figures/topology.png", format="PNG")
        plt.clf()

    def print_hosts(self) -> None:
        print("[Hosts in Network: " + str(len(self.networkHosts)) + "]")
        for h in range(len(self.networkHosts)):
            print(" |- uid: " + str(self.networkHosts[h].uid) + ", name: " + str(self.networkHosts[h].name))

    def print_links(self) -> None:
        print("[Links in Network: " + str(len(self.networkLinks)) + "]")
        for l in range(len(self.networkLinks)):
            print(" |- uid: " + str(self.networkLinks[l].uid) + ", src_uid: " + str(
                self.networkLinks[l].source.uid) + ", dst_uid: " + str(
                self.networkLinks[l].destination.uid) + ", bw_u/c: " + str(
                self.networkLinks[l].bandwidthUtil) + "/" + str(self.networkLinks[l].bandwidthCap) + ", lat: " + str(
                self.networkLinks[l].latency))

    def print_services(self) -> None:
        print("[Application Flavors Available: " + str(len(self.networkServices)) + "]")
        for s in range(len(self.networkServices)):
            print(" |- uid: " + str(self.networkServices[s].uid) + ", name: " + str(
                self.networkServices[s].name) + ", cpu: " + str(
                self.networkServices[s].CPUrequirements) + ", ram: " + str(
                self.networkServices[s].RAMrequirements) + ", storage: " + str(
                self.networkServices[s].StorageRequirements))

    def print_chains(self) -> None:
        print("[Defined Chains: " + str(len(self.networkChains)) + "]")
        for c in range(len(self.networkChains)):
            print(" |- uid: " + str(self.networkChains[c].uid) + ", flow: " + str(
                self.networkChains[c].strChain()) + ", sla: " + str(self.networkChains[c].sla))

    def print_vms(self) -> None:
        print("[VMs in Network: " + str(len(self.networkVMs)) + "]")
        for v in range(len(self.networkVMs)):
            print(" |- uid: " + str(self.networkVMs[v].uid) + ", app: " + str(
                self.networkVMs[v].name) + ", host_uid: " + str(self.networkVMs[v].host.uid))

    def print_users(self) -> None:
        print("[Users in Network: " + str(len(self.networkUsers)) + "]")
        for u in range(len(self.networkUsers)):
            print(" |- uid: " + str(self.networkUsers[u].uid) + ", name: " + str(
                self.networkUsers[u].name) + ", chain_uid: " + str(self.networkUsers[u].userChain.uid) + ", bw: " + str(
                self.networkUsers[u].bandwidth))

    def print_net_top(self) -> None:
        # for all hosts and links visualize the data
        print("[[NetTop]]")
        print("[Hosts]")
        for h in range(len(self.networkHosts)):
            print(" |- host_uid: " + str(self.networkHosts[h].uid) + ", name: " + str(self.networkHosts[h].name))
            print(" |   |- CPU: ", self.networkHosts[h].CPUUtil, "/", self.networkHosts[h].CPUcap)
            print(" |   |- RAM: ", self.networkHosts[h].RAMUtil, "/", self.networkHosts[h].RAMcap)
            print(" |   |- STR: ", self.networkHosts[h].StorageUtil, "/", self.networkHosts[h].StorageCap)
        print("[Links]")
        for l in range(len(self.networkLinks)):
            print(" |- link_uid: " + str(self.networkLinks[l].uid) + ", src_uid: " + str(
                self.networkLinks[l].source.uid) + ", dst_uid: " + str(self.networkLinks[l].destination.uid))
            print(" |   |- BWD: ", self.networkLinks[l].bandwidthUtil, "/", self.networkLinks[l].bandwidthCap)
            print(" |   |- LAT: ", self.networkLinks[l].latency)

    def print_flows(self):
        # print active data traffic flows
        pass

    @staticmethod
    def print_user_snap(user_object: User) -> str:
        chtext = ""

        for h in range(len(user_object.userChain.chain)):
            chtext += str(user_object.userChain.chain[h].host.uid) + ">"

        chtext = chtext[:-1]
        return "user_uid: " + str(
            user_object.uid) + " | SC: " + user_object.userChain.__str__() + " | SCHosts: " + chtext
