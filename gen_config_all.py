#!/usr/bin/python3
from sw_config import *
from ecs_config import *

switches = SW.keys()

for num in switches:

    file_path = "sw%s.cfg" % num
    with open(file_path, "w") as file:

        vlans = SW[num]["vlans"]
        out = HEAD.format(name="switch", number=num, network=NETWORK, database=DB)
        out += untagged_ports(vlans)
        out += ring_interface(num)
        out += vlan_groups(num)
        out += ring_ports(num)
        out += ring_instance(num)
        out += BOTTOM.format(number=num, network=NETWORK, mask=MASK, mngt_vid=MNGT_VLAN)
        file.write(out)
        print("Generated %s" % file_path)

