"""
Implementing a microprocessor architecture based on ARM ISA.

This is based on the ARM sample script.
"""

import m5
from m5.objects import *

# Define L1 Caches for instruction and data
class L1Cache(Cache):
    """L1 Cache with default values"""

    # Parameters other than cache size for both L1 I and D caches
    assoc = 2
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    tgts_per_mshr = 20

    def connectCPU(self, cpu):
        """Connect to a CPU-side port"""
        raise NotImplementedError

    def connectBus(self, bus):
        """Connect cache to memory-side bus"""
        self.mem_side = bus.cpu_side_ports

class L1ICache(L1Cache):
    """L1 instruction cache"""

    # Set the size to architecture definition
    size = '16KiB'

    def connectCPU(self, cpu):
        """Connect cache's CPU icache"""
        self.cpu_side = cpu.icache_port

class L1DCache(L1Cache):
    """L1 data cache"""

    # Set the size to architecture definition
    size = '16KiB'

    def connectCPU(self, cpu):
        """Connect cache's CPU dcache"""
        self.cpu_side = cpu.dcache_port

class L2Cache(Cache):
    """L2 Cache"""

    # Default parameters
    size = '128KiB'
    assoc = 8
    tag_latency = 20
    data_latency = 20
    response_latency = 20
    mshrs = 20
    tgts_per_mshr = 12

    def connectCPUSideBus(self, bus):
        """"Connect cache to cpu"""
        self.cpu_side = bus.master

    def connectMemSideBus(self, bus):
        """"Connect cache to memory"""
        self.mem_side = bus.cpu_side_ports

system = System()

# system.clk_domain = SrcClockDomain()
# system.clk_domain.clock = "1GHz"
# system.clk_domain.voltage_domain = VoltageDomain()

# Define Clock Domain, Voltage Domain
# Define the frequency to voltage mappings
op_points = [
    ('1.0GHz', '1.0V'),
    ('750MHz', '0.9V'),
    ('500MHz', '0.8V')
]
frequencies = [op[0] for op in op_points]
voltages = [op[1] for op in op_points]

# Create a voltage domain with our list of voltages
# This allows the domain to switch between these voltage levels
system.voltage_domain = VoltageDomain(voltage=voltages)

# Create a source clock domain with our list of frequencies
system.clk_domain = SrcClockDomain(
    clock=frequencies,
    voltage_domain=system.voltage_domain,
)

# Create the DVFS handler
# This object manages switching between the operating points
system.dvfs_handler = DVFSHandler(
    sys_clk_domain=system.clk_domain,
#    domains=[system.clk_domain],
    enable=True
)


system.mem_mode = "timing"
# system.mem_mode = "functional"
system.mem_ranges = [AddrRange("512MiB")]
system.cpu = MinorCPU()

system.membus = SystemXBar()

# Connect caches to the CPU
system.cpu.icache = L1ICache()
system.cpu.dcache = L1DCache()

system.cpu.icache.connectCPU(system.cpu)
system.cpu.dcache.connectCPU(system.cpu)

# Connect L1 caches to memory bus
system.cpu.icache.connectBus(system.membus)
system.cpu.dcache.connectBus(system.membus)

system.cpu.createInterruptController()

system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

system.system_port = system.membus.cpu_side_ports

thispath = os.path.dirname(os.path.realpath(__file__))
binary = os.path.join(
    thispath,
    "../../gem5/",
    "tests/test-progs/hello/bin/arm/linux/hello",
)

system.workload = SEWorkload.init_compatible(binary)

process = Process()
process.cmd = [binary]
system.cpu.workload = process
system.cpu.createThreads()

root = Root(full_system=False, system=system)
m5.instantiate()

print(f"Beginning simulation!")
exit_event = m5.simulate()
print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")
