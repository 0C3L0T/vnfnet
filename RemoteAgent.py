"""
dummy remote agent used for testing,
a RemoteAgent receives the state of the substrate network and
a service request and tries to map the request on the network.
"""

from Environment import Environment
from simulation import Substrate, ServiceChain

# init the environment
env = Environment()

(state, service_request) = env.poll()  # these could be serialized in the future


def generate_embedding(state: Substrate, request: ServiceChain) -> ServiceChain:
    """
    receives the state of the substrate network and an unembedded servicechain
    and returns a service chain with the proposed embedding
    :param state:
    :param request:
    :return:
    """
    print("Generating embedding..")


embedding = generate_embedding(state, service_request)

env.embed(embedding).unwrap()
env.step()
