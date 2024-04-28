from result import Result

import NetworkFunction
import ServiceChain
import VirtualLink
import VirtualMachine


class Simulation:
    virtual_machines: dict[int, VirtualMachine] = {}
    virtual_links: dict[int, VirtualLink] = {}
    service_chains: dict[int, ServiceChain] = {}

    def allocate_function(self, target_vm_id: int, function: NetworkFunction) -> Result[None, str]:
        pass

    def free_function(self, target_function_id: int) -> None:
        pass

    def allocate_chain(self, chain: ServiceChain) -> Result[None, str]:
        pass