class VirtualLink:
    bandwidth_usage: float
    latency: float  # inherit from link
    transfer_rate: float

    def __init__(self, bandwidth_usage: float, latency: float, transfer_rate: float) -> None:
        self.bandwidth_usage = bandwidth_usage
        self.latency = latency
        self.transfer_rate = transfer_rate
