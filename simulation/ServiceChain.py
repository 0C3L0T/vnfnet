from __future__ import annotations  # used for forward reference

from simulation.NetworkFunction import NetworkFunction


class ServiceChain:
    """
    A service chain consists of multiple Network Functions in an ordered list.
    When the chain gets embedded it will be in the order of the functions list.
    """
    functions: list[NetworkFunction] = []

    # by defining a next chain, we make it possible to support
    # traffic splitting and bifurcated paths
    next_chain: list[ServiceChain] = []

    time_to_live: float = 0  # time until which this chain should be available

    def add_function(self, function: NetworkFunction) -> None:
        self.functions.append(function)

    def calculate_latency(self) -> float:
        pass
