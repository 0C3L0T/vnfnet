from result import Result
from simulation import Substrate

import NetworkFunction
import ServiceChain


class Simulation:
    """
    The simulation class is used to interact with the Substrate object
    """
    substrate: list[Substrate]  # allow for parallel embedding
    service_chains: dict[int, ServiceChain] = {}
    current_time: float = 0  # used to check if chains should be deleted

    def _allocate_function(self, target_vm_id: int, function: NetworkFunction) -> Result[None, str]:
        pass

    def _free_function(self, target_function_id: int) -> None:
        pass

    def _free_chain(self, chain: ServiceChain):
        pass

    def _check_chain_time_to_live(self):
        """
        check if there are allocated service chains that should be
        freed and free them
        :return:
        """
        for chain in self.service_chains.values():
            if chain.time_to_live < self.current_time:
                self._free_function(chain)

    def get_state(self) -> Substrate:
        """
        return the state of the substrate
        TODO: return serialized data
        :return:
        """
        return self.substrate

    def step(self, time_elapsed: float) -> None:
        self.current_time += time_elapsed

    def allocate_chain(self, chain: ServiceChain) -> Result[None, str]:
        pass
