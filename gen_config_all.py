#!/usr/bin/python3
from sw_config import *
from ecs_config import *

switches = SW.keys()

for num in switches:

    file_path = "sw%s.cfg" % num
    with open(file_path, "w") as file:

        out = create_config(num)
        file.write(out)
        print("Generated %s" % file_path)

