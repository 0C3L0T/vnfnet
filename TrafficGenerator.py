from simulation import ServiceChain
from simulation import NetworkFunction

"""
This is a dummy implementation of a Traffic generator,
we could change this into an interface to allow for multiple 
implementations.
"""

class TrafficGenerator:
    """
    This class generates random function chain requests consisting of random network functions
    """

    def __init__(self):
        pass

    def create_request_chain(self):
        chain = ServiceChain()

        chain.add_function(NetworkFunction(
            cpu_usage=500,
            memory_usage=200,
            storage_usage=512,
            processing_time=5
        ))

        chain.add_function(NetworkFunction(
            cpu_usage=500,
            memory_usage=200,
            storage_usage=512,
            processing_time=5
        ))

        return chain
