import functools
import logging
import time
import sys

logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s - %(levelname)s - %(message)s",
                    handlers=[logging.FileHandler("system_kernel.log"),
                              logging.StreamHandler()])

KERNEL_ERRORS = {
    'PROCESS_FAIL': '0xF1',
    'MEMORY_OVERFLOW': '0xF2'
}

class Process:
    def __init__(self, name, memory_block, priority=1):
        self.name = name
        self.memory_block = memory_block
        self.priority = priority
        self.pid = id(self)

class Memory:
    def __init__(self):
        self.storage = {}

    def alloc(self, size):
        block = bytearray(size)
        self.storage[id(block)] = block
        return block

    def free(self, block):
        block_id = id(block)
        if block_id in self.storage:
            del self.storage[block_id]

class Kernel:
    def __init__(self):
        self.memory = Memory()
        self.process_list = []
        self.max_processes = 1000

    def spawn(self, name, priority=1, mem_size=1024):
        if len(self.process_list) >= self.max_processes:
            self.panic('Memory overflow', KERNEL_ERRORS['MEMORY_OVERFLOW'])
        block = self.memory.alloc(mem_size)
        proc = Process(name, block, priority)
        self.process_list.append(proc)
        logging.info(f"Spawned process {proc.name} with PID {proc.pid}")
        return proc.pid

    def destroy(self, pid):
        proc = next((p for p in self.process_list if p.pid == pid), None)
        if not proc:
            logging.warning(f"No such process with PID {pid}")
            return
        self.memory.free(proc.memory_block)
        self.process_list.remove(proc)
        logging.info(f"Killed process {proc.name} with PID {proc.pid}")

    def panic(self, msg, code):
        logging.critical(f"KERNEL PANIC: {msg}, Code: {code}")
        sys.exit(1)

kernel = Kernel()

def process_management(priority=1):
    def wrap(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            pid = None
            try:
                pid = kernel.spawn(func.__name__, priority)
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                logging.error(f"Error during process: {e}")
                kernel.panic('Process fail', KERNEL_ERRORS['PROCESS_FAIL'])
            finally:
                if pid:
                    kernel.destroy(pid)
        return inner
    return wrap
