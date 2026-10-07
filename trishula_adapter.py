from memory_engine import SovereignMemory

def get_shared_memory():
    return SovereignMemory(db_path=r"D:\Trishula-Infra\Netra\swarm_memory.db")
