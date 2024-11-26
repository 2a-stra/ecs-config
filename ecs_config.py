#!/usr/bin/python3
import sys

from sw_config import *

# Untagged ports
def untagged_ports(vlans):

    out = ""
    for v in vlans:
        for p in vlans[v]:
            interface = '''!
interface ethernet 1/{port}
    switchport allowed vlan add {vlan} untagged
    switchport mode access
    switchport native vlan {vlan}
    switchport allowed vlan remove 1\n'''.format(port=p, vlan=v)
            out += interface

    return out

# ports 43..46 - native vlan 1
#print("!\ninterface ethernet 1/46")


# EPSR

## Interface
def ring_interface(number):

    out = ""
    for ring in SW[number]["epsr"]:
        ring_main = EPSR[ring]

        if number in ring_main["members"]:

            vlans_list = []
            for v in ring_main["vlan-groups"]:
                vlans_list += GROUPS[v]
            vlans = ",".join(vlans_list)

            if ring_main["sub-ring"]:
                if number in ring_main["owner"]:
                    interface = '''!
interface ethernet 1/{west}
    no loopback-detection
    switchport allowed vlan add {vlans} tagged
    switchport allowed vlan remove 1
    spanning-tree spanning-disabled\n'''.format(vlans=vlans, west=ring_main["west"])
                elif number in ring_main["far-end"]:
                    interface = '''!
interface ethernet 1/{east}
    no loopback-detection
    switchport allowed vlan add {vlans} tagged
    switchport allowed vlan remove 1
    spanning-tree spanning-disabled\n'''.format(vlans=vlans, east=ring_main["east"])
                else:
                    interface = '''!
interface ethernet 1/{east}
    no loopback-detection
    switchport allowed vlan add {vlans} tagged
    switchport allowed vlan remove 1
    spanning-tree spanning-disabled
!
interface ethernet 1/{west}
    no loopback-detection
    switchport allowed vlan add {vlans} tagged
    switchport allowed vlan remove 1
    spanning-tree spanning-disabled\n'''.format(vlans=vlans, east=ring_main["east"], west=ring_main["west"])

            else:
                interface = '''!
interface ethernet 1/{east}
    no loopback-detection
    switchport allowed vlan add {vlans} tagged
    switchport allowed vlan remove 1
    spanning-tree spanning-disabled
!
interface ethernet 1/{west}
    no loopback-detection
    switchport allowed vlan add {vlans} tagged
    switchport allowed vlan remove 1
    spanning-tree spanning-disabled\n'''.format(vlans=vlans, east=ring_main["east"], west=ring_main["west"])

            out += interface

    return(out)

## VLAN groups
def vlan_groups(number):

    out = "!\nerps\n" # enable ERPS

    group_names = set()
    for ring in SW[number]["epsr"]:
        ring_main = EPSR[ring]

        if number in ring_main["members"]:
            group_names.update(ring_main["vlan-groups"])

    for name in group_names:
        vlans1 = ",".join(GROUPS[name])
        group = '''!
erps vlan-group {name}-group add {vlans}\n'''.format(name=name, vlans=vlans1)

        out += group

    return out


## Ring (east/west ports)
def ring_ports(number):

    out = ""
    for ring in SW[number]["epsr"]:
        ring_main = EPSR[ring]

        if number in ring_main["members"]:
            if ring_main["sub-ring"]:
                if number in ring_main["owner"]:
                    erps = '''!
erps ring {name}-ring
    ring-port west interface ethernet 1/{west}
    enable\n'''.format(**ring_main)
                elif number in ring_main["far-end"]:
                    erps = '''!
erps ring {name}-ring
    ring-port east interface ethernet 1/{east}
    enable\n'''.format(**ring_main)
                else:
                    erps = '''!
erps ring {name}-ring
    ring-port east interface ethernet 1/{east}
    ring-port west interface ethernet 1/{west}
    enable\n'''.format(**ring_main)
            else:
                erps = '''!
erps ring {name}-ring
    ring-port east interface ethernet 1/{east}
    ring-port west interface ethernet 1/{west}
    enable\n'''.format(**ring_main)

            out += erps

    return out

## Instance
def ring_instance(number):

    out = ""
    for ring in SW[number]["epsr"]:
        ring_main = EPSR[ring]

        if number in ring_main["members"]:

            rpl = ""
            if number == ring_main["owner"]:
                rpl = "\n    rpl owner"
            elif number == ring_main["neighbor"]:
                rpl = "\n    rpl neighbor"

            major = ""
            if ring_main["sub-ring"]:
                if (number in ring_main["owner"]) or \
                   (number in ring_main["far-end"]):
                    major = "\n    major-ring %s-inst" % ring_main["major-ring"]

            inclusion = ""
            for grp in ring_main["vlan-groups"]:
                inclusion += "\n    inclusion-vlan %s-group" % grp

            erps_inst = '''!
erps instance {name}-inst id {id}
    control-vlan {control}{rpl}
    physical-ring {name}-ring{major}{inclusion}
    enable\n'''.format(name=ring_main["name"],
                     id=ring_main["id"],
                     control=GROUPS[ring_main["control"]][0],
                     rpl=rpl,
                     major=major,
                     inclusion=inclusion
                     )

            out += erps_inst

    return out


if __name__ == '__main__':

    NUMBER = sys.argv[1]

    print(HEAD.format(name="switch", number=NUMBER, network=NETWORK, database=DB))

    vlans = SW[NUMBER]["vlans"]
    print(untagged_ports(vlans))
    print(ring_interface(NUMBER))
    print(vlan_groups(NUMBER))
    print(ring_ports(NUMBER))
    print(ring_instance(NUMBER))

    print(BOTTOM.format(number=NUMBER, network=NETWORK, mask=MASK, mngt_vid=MNGT_VLAN))
