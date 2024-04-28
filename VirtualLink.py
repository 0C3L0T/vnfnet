class VirtualLink:
    uid: int = 0
    bandwidth_usage: float
    latency: float = 0  # inherit from Link
    transfer_rate: float = 0  # inherit from Link

    def __init__(self, bandwidth_usage: float) -> None:
        self.bandwidth_usage = bandwidth_usage
