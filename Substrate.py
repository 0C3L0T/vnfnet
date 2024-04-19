from result import Result, Ok, Err, is_ok

uid = int


class Host:
    uid: uid
    cpu_avail: float
    mem_avail: float
    storage_avail: float

    def __init__(self, uid: int, cpu_avail: float, mem_avail: float, storage_avail: float):
        self.uid = uid
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
    uid: uid
    bandwidth_avail: float
    latency: float
    transfer_rate: float

    def __init__(self, uid: int, bandwidth_avail: float, latency: float, transfer_rate: float) -> None:
        self.uid = uid
        self.bandwidth_avail = bandwidth_avail
        self.latency = latency
        self.transfer_rate = transfer_rate

    def allocate_resources(self, bandwidth: float) -> Result[uid, str]:
        """
        decrease available bandwidth of the Link, return uid or error message if resources not available
        """

        if self.bandwidth_avail < bandwidth:
            return Err(f'resources not available on link {self.uid}')

        self.bandwidth_avail -= bandwidth

        return Ok(self.uid)


# maybe have like a substrate factory that can make substrates with networkX?
class Substrate:
    nodes: dict[int, Host] = {}
    edges: dict[int, Link] = {}

    uid_counter = 0

    def _get_uid(self) -> int:
        self.uid_counter += 1
        return self.uid_counter

    def add_host(self, cpu_avail: float, mem_avail: float, storage_avail: float) -> None:
        """
        add a host (node) to the substrate network
        """

        uid = self._get_uid()
        host = Host(uid=uid, cpu_avail=cpu_avail, mem_avail=mem_avail, storage_avail=storage_avail)
        self.nodes[uid] = host

    def _get_host(self, uid: int) -> Result[Host, str]:
        """
        get a host by id, return Host object or error message if host not found
        """
        if self.nodes.get(uid) is None:
            return Err(f'host {uid} not found')

        return Ok(self.nodes.get(uid))

    def add_link(self, bandwidth_avail: float, latency: float, transfer_rate: float) -> None:
        """
        add a link (edge) to the substrate network
        """

        uid = self._get_uid()
        link = Link(uid=uid, bandwidth_avail=bandwidth_avail, latency=latency, transfer_rate=transfer_rate)
        self.edges[uid] = link

    def _get_link(self, uid: int) -> Result[Link, str]:
        """
        get a link by uid, return Link object or error message if link not found
        """
        if self.edges.get(uid) is None:
            return Err(f'link {uid} not found')

        return Ok(self.edges.get(uid))

    def insert_virtual_machine(self,
                               target_host: uid,
                               cpu_usage: float,
                               mem_usage: float,
                               storage_usage: float
                               ) -> Result[uid, str]:
        """
        allocate the resources on a host for a virtual machine or fail with an error message
        """

        host = self._get_host(target_host)
        if is_ok(host):
            match host.ok_value.allocate_resources(cpu_usage, mem_usage, storage_usage):
                case Ok():
                    return Ok(target_host)
                case Err(e):
                    return Err(e)

        return Err(host.err_value)

    # this too might lead to users freeing more resources than were initially available on the host
    def remove_virtual_machine(self,
                               target_host: uid,
                               cpu_usage: float,
                               mem_usage: float,
                               storage_usage: float
                               ) -> None:
        """
        free the resources on a host for a virtual machine
        """

        host = self._get_host(target_host)
        if is_ok(host):
            host.ok_value.free_resources(cpu_usage, mem_usage, storage_usage)

    def insert_virtual_link(self, target_edge: uid, bandwidth_usage: float) -> Result[uid, str]:
        """
        allocate the resources on a link for a virtual link or fail with an error message
        """

        link = self._get_link(target_edge)
        if is_ok(link):
            match link.ok_value.allocate_resources(bandwidth_usage):
                case Ok():
                    return Ok(target_edge)
                case Err(e):
                    return Err(e)

        return Err(link.err_value)

    # this too might lead to users freeing more resources than were initially available on the link
    def remove_virtual_link(self, target_edge: uid, bandwidth_usage: float) -> None:
        """
        free the resources on a link for a virtual link
        """

        link = self._get_link(target_edge)
        if is_ok(link):
            link.ok_value.free_resources(bandwidth_usage)
