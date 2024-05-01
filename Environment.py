"""
The environment class is used by the remote agent to interact with
the simulation and the traffic generator.
"""
from typing import Callable

from result import Result

from TrafficGenerator import TrafficGenerator
from simulation import ServiceChain, Substrate
from simulation.Simulation import Simulation


class Environment:
    simulation: Simulation = None
    traffic_generator: TrafficGenerator = None

    def __init__(self):
        self.simulation = Simulation()
        self.traffic_generator = TrafficGenerator()

    def poll(self) -> (Substrate, ServiceChain):
        """
        return the current state of the substrate and a service request
        :return:
        """

        state: Substrate = self.simulation.get_state()
        request: ServiceChain = self.traffic_generator.create_request_chain()

        return state, request

    def embed(self, embedding: ServiceChain) -> Result[None, str]:
        """
        given a service chain containing a proposed embedding, try to
        embed the chain on the network.
        :param embedding:
        :return:
        """
        return self.simulation.allocate_chain(embedding)

    def step(self, time_elapsed: float) -> None:
        """
        update the simulation time
        :return:
        """
        self.simulation.step(time_elapsed)