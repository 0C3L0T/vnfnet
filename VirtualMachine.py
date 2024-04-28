class VirtualMachine:
    cpu_usage: float
    mem_usage: float
    storage_usage: float

    def __init__(self, cpu_usage: float, mem_usage: float, storage_usage: float) -> None:
        self.cpu_usage = cpu_usage
        self.mem_usage = mem_usage
        self.storage_usage = storage_usage
