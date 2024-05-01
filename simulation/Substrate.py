from result import Result, Ok, Err, is_ok

uid = int


class Host:
    uid: uid = 0
    cpu_avail: float
    mem_avail: float
    storage_avail: float

    def __init__(self, cpu_avail: float, mem_avail: float, storage_avail: float):
        self.cpu_avail = cpu_avail
        self.memory_avail = mem_avail
        self.storage_avail = storage_avail

    def _resources_are_available(self, cpu: float, mem: float, storage: float) -> bool:
        return not (
                self.cpu_avail < cpu or
                self.memory_avail < mem or
                self.storage_avail < storage
        )

    def _decrease_resources(self, cpu: float, mem: float, storage: float) -> None:
        self.cpu_avail -= cpu
        self.memory_avail -= mem
        self.storage_avail -= storage

    def allocate_resources(self, cpu: float, mem: float, storage: float) -> Result[uid, str]:
        """
        decrease available resources of the host, return uid of the host if success or an error message if fail
        """
        if not self._resources_are_available(cpu, mem, storage):
            return Err(f'resources not available on host {self.uid}')

        self._decrease_resources(cpu, mem, storage)

        return Ok(self.uid)

    # this could potentially lead to users adding more resources back to a host than was originally available
    def free_resources(self, cpu: float, mem: float, storage: float) -> None:
        """
        increase available resources of the host
        """
        self.cpu_avail += cpu
        self.mem_avail += mem
        self.storage_avail += storage


class Link:
    bandwidth_avail: float
    latency: float
    transfer_rate: float

    def __init__(self, bandwidth_avail: float, latency: float, transfer_rate: float) -> None:
        self.bandwidth_avail = bandwidth_avail
        self.latency = latency
        self.transfer_rate = transfer_rate

    def allocate_resources(self, bandwidth: float) -> Result[None, str]:
        """
        decrease available bandwidth of the Link, return uid or error message if resources not available
        """
        if self.bandwidth_avail < bandwidth:
            return Err(f'resources not available on link')

        self.bandwidth_avail -= bandwidth

        return Ok(None)

    def free_resources(self, bandwidth: float) -> None:
        """
        increase available resources on the link, return None
        :param bandwidth:
        :return:
        """
        self.bandwidth_avail += bandwidth


# maybe have like a substrate factory that can make substrates with networkX?
class Substrate:
    nodes: dict[uid, Host] = {}  # host uid links to Host object
    edges: dict[(uid, uid), Link] = {}  # tuple of host uid links to Link object

    uid_counter = 0

    def _get_uid(self) -> int:
        self.uid_counter += 1
        return self.uid_counter

    def add_host(self, host: Host) -> None:
        """
        add a host (node) to the substrate network
        """
        uid = self._get_uid()
        host.uid = uid
        self.nodes[uid] = host

    def _get_host_by_id(self, host_uid: int) -> Result[Host, str]:
        """
        get a host by id, return Host object or error message if host not found
        """
        if self.nodes.get(host_uid) is None:
            return Err(f'host {host_uid} not found')

        return Ok(self.nodes.get(host_uid))

    def add_link(self, source_host: uid, destination_host: uid, link: Link) -> None:
        """
        add a Link object between source_host and destination_host
        :param source_host:
        :param destination_host:
        :param link:
        :return:
        """
        self.edges[(source_host, destination_host)] = link

    def _get_link_by_ids(self, source_host: uid, destination_host: uid) -> Result[Link, str]:
        """
        return a Link object between source_host and destination_host,
        or an error message if the link is not found
        :param source_host:
        :param destination_host:
        :return:
        """
        link = self.edges.get((source_host, destination_host))

        if link:
            return Ok(link)

        Err(f'link not found')

    def __str__(self):
        return f"hosts in network: {len(self.nodes)}, links in network: {len(self.edges)}"
