from result import Result, Ok, Err, is_ok
from VirtualMachine import VirtualMachine

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
    _uid: uid = 0
    bandwidth_avail: float
    latency: float
    transfer_rate: float

    def __init__(self, bandwidth_avail: float, latency: float, transfer_rate: float) -> None:
        self.uid = uid
        self.bandwidth_avail = bandwidth_avail
        self.latency = latency
        self.transfer_rate = transfer_rate

    def allocate_resources(self, bandwidth: float) -> Result[uid, str]:
        """
        decrease available bandwidth of the Link, return uid or error message if resources not available
        """
        if self.bandwidth_avail < bandwidth:
            return Err(f'resources not available on link {self._uid}')

        self.bandwidth_avail -= bandwidth

        return Ok(self._uid)


# maybe have like a substrate factory that can make substrates with networkX?
class Substrate:
    nodes: dict[int, Host] = {}
    edges: dict[int, Link] = {}

    uid_counter = 0

    def _get_uid(self) -> int:
        self.uid_counter += 1
        return self.uid_counter

    def add_host(self, host: Host) -> uid:
        """
        add a host (node) to the substrate network and return host uid
        """
        uid = self._get_uid()
        host.uid = uid
        self.nodes[uid] = host

        return uid

    def _get_host_by_id(self, host_uid: int) -> Result[Host, str]:
        """
        get a host by id, return Host object or error message if host not found
        """
        if self.nodes.get(host_uid) is None:
            return Err(f'host {host_uid} not found')

        return Ok(self.nodes.get(host_uid))

    def add_link(self, link: Link) -> uid:
        """
        add a link (edge) to the substrate network and return link id
        """
        uid = self._get_uid()
        link.uid = uid
        self.edges[uid] = link

        return uid

    def _get_link_by_id(self, link_uid: int) -> Result[Link, str]:
        """
        get a link by uid, return Link object or error message if link not found
        """
        if self.edges.get(link_uid) is None:
            return Err(f'link {link_uid} not found')

        return Ok(self.edges.get(link_uid))

    def insert_virtual_machine(self, target_host: uid, vm: VirtualMachine) -> Result[None, str]:
        """
        allocate the resources on a host for a virtual machine and return None or fail with an error message
        """

        host = self._get_host_by_id(target_host)  # Host or error message
        if is_ok(host):
            match host.ok_value.allocate_resources(
                vm.cpu_usage,
                vm.mem_usage,
                vm.storage_usage
            ):
                case Ok():
                    return Ok(None)
                case Err(e):
                    return Err(e)

        return Err(host.err_value)

    # this too might lead to users freeing more resources than were initially available on the host
    def remove_virtual_machine(self, target_host: uid, vm: VirtualMachine) -> None:
        """
        free the resources on a host for a virtual machine
        """

        host = self._get_host_by_id(target_host)
        if is_ok(host):
            host.ok_value.free_resources(
                vm.cpu_usage,
                vm.mem_usage,
                vm.storage_usage
            )

    def insert_virtual_link(self, target_edge: uid, bandwidth_usage: float) -> Result[None, str]:
        """
        allocate the resources on a link for a virtual link and return None or fail with an error message
        """

        link = self._get_link_by_id(target_edge)
        if is_ok(link):
            match link.ok_value.allocate_resources(bandwidth_usage):
                case Ok():
                    return Ok(None)
                case Err(e):
                    return Err(e)

        return Err(link.err_value)

    # this too might lead to users freeing more resources than were initially available on the link
    def remove_virtual_link(self, target_edge: uid, bandwidth_usage: float) -> None:
        """
        free the resources on a link for a virtual link
        """

        link = self._get_link_by_id(target_edge)
        if is_ok(link):
            link.ok_value.free_resources(bandwidth_usage)

    def __str__(self):
        return f"hosts in network: {len(self.nodes)}, links in network: {len(self.edges)}"


if __name__ == '__main__':
    S = Substrate()
    host_id = S.add_host(Host(cpu_avail=4.5, mem_avail=16000, storage_avail=20000))

    S.insert_virtual_machine(target_host=host_id,
                             vm=VirtualMachine(cpu_usage=3.5, mem_usage=500, storage_usage=2000)).unwrap()

    print(S)
