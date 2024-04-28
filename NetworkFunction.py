class NetworkFunction:
    uid: int = 0
    vm_id: int = 0

    cpu_usage: float
    memory_usage: float
    storage_usage: float
    processing_time: float

    def __init__(self, cpu_usage: float, memory_usage: float, storage_usage: float, processing_time: float) -> None:
        self.cpu_usage = cpu_usage
        self.memory_usage = memory_usage
        self.storage_usage = storage_usage
        self.processing_time = processing_time
