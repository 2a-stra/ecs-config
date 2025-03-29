#!/usr/bin/python3
import sys

from sw_config import *

# Untagged ports
def untagged_ports(vlans, dhcp, sec, guard):

    out = ""
    for v in vlans:
        for p in vlans[v]:
            interface = '''!
interface ethernet 1/{port}\n'''.format(port=p)

            if p in sec:
                interface += '''    port security max-mac-count 1
    port security
    port security action trap-and-shutdown\n'''
    
            interface += '''    switchport allowed vlan add {vlan} untagged
    switchport mode access
    switchport native vlan {vlan}
    switchport allowed vlan remove 1\n'''.format(vlan=v)

            if p in dhcp:
                interface += "    ip dhcp snooping trust\n"

            if guard:
                if p == guard[0]["port"]:
                    interface += '''    ip source-guard sip
    ip source-guard mode acl max-binding 1\n'''

            out += interface

    return out

# Tagged ports
def trunk_ports(trunks, dhcp):

    out = ""
    for p in trunks:

        vlans_list = []
        for v in trunks[p]:
            vlans_list += GROUPS[v]

        vlans_list.sort()   # sort digits
        vlans_str = [str(x) for x in vlans_list]
        vlans = ",".join(vlans_str)

        interface = '''!
interface ethernet 1/{port}
    switchport allowed vlan add {vlan} tagged
    switchport mode trunk
    switchport allowed vlan remove 1\n'''.format(port=p, vlan=vlans)

        if int(p) in dhcp:
            interface += "    ip dhcp snooping trust\n"

        out += interface

    return out

# ports 43..46 - native vlan 1
#print("!\ninterface ethernet 1/46")


# EPSR

def east_west(port, vlans, dhcp, dhcp_filter):

    interface = '''!
interface ethernet 1/{port}
    no loopback-detection
    switchport allowed vlan add {vlans} tagged
    switchport allowed vlan remove 1
    spanning-tree spanning-disabled\n'''.format(vlans=vlans, port=port)

    if int(port) in dhcp:
        interface += "    ip dhcp snooping trust\n"

    if int(port) in dhcp_filter:
        interface += "    ip dhcp snooping max-number filter-only\n"

    return interface

## Interface
def ring_interface(number, dhcp, dhcp_filter):

    out = ""
    epsr_rings = SW[number]["epsr"]
    for ring in epsr_rings.keys():
        ring_main = EPSR[ring]

        if number in ring_main["members"]:

            vlans_list = []
            for v in ring_main["vlan-groups"]:
                vlans_list += GROUPS[v]
            vlans_list.sort()   # sort digits
            vlans_str = [str(x) for x in vlans_list]
            vlans = ",".join(vlans_str)

            if ring_main["sub-ring"]:

                if number in ring_main["owner"]:
                    west = epsr_rings[ring]["west"]
                    interface = east_west(west, vlans, dhcp, dhcp_filter)

                elif number in ring_main["far-end"]:
                    east = epsr_rings[ring]["east"]
                    interface = east_west(east, vlans, dhcp, dhcp_filter)

                else:
                    east = epsr_rings[ring]["east"]
                    west = epsr_rings[ring]["west"]
                    interface = east_west(east, vlans, dhcp, dhcp_filter)
                    interface += east_west(west, vlans, dhcp, dhcp_filter)

            else:
                east = epsr_rings[ring]["east"]
                west = epsr_rings[ring]["west"]
                interface = east_west(east, vlans, dhcp, dhcp_filter)
                interface += east_west(west, vlans, dhcp, dhcp_filter)

            out += interface

    return(out)

## VLAN groups
def vlan_groups(number):

    out = ""
    group_names = set()
    epsr_rings = SW[number]["epsr"]

    for ring in epsr_rings.keys():
        if number in EPSR[ring]["members"]:
            out = "!\nerps\n" # enable ERPS

    for ring in epsr_rings.keys():
        ring_main = EPSR[ring]

        if number in ring_main["members"]:
            group_names.update(ring_main["vlan-groups"])

    groups_list = sorted(group_names)
    for name in groups_list:
        vlans_str = [str(x) for x in GROUPS[name]]
        vlans1 = ",".join(vlans_str)
        group = '''!
erps vlan-group {name}-group add {vlans}\n'''.format(name=name, vlans=vlans1)

        out += group

    return out


## Ring (east/west ports)
def ring_ports(number):

    out = ""
    epsr_rings = SW[number]["epsr"]
    for ring in epsr_rings.keys():
        ring_main = EPSR[ring]

        if number in ring_main["members"]:
            if ring_main["sub-ring"]:
                if number in ring_main["owner"]:
                    erps = '''!
erps ring {name}-ring
    ring-port west interface ethernet 1/{west}
    enable\n'''.format(name=ring, west=epsr_rings[ring]["west"])
                elif number in ring_main["far-end"]:
                    erps = '''!
erps ring {name}-ring
    ring-port east interface ethernet 1/{east}
    enable\n'''.format(name=ring, east=epsr_rings[ring]["east"])
                else:
                    erps = '''!
erps ring {name}-ring
    ring-port east interface ethernet 1/{east}
    ring-port west interface ethernet 1/{west}
    enable\n'''.format(name=ring, west=epsr_rings[ring]["west"], east=epsr_rings[ring]["east"])
            else:
                erps = '''!
erps ring {name}-ring
    ring-port east interface ethernet 1/{east}
    ring-port west interface ethernet 1/{west}
    enable\n'''.format(name=ring, west=epsr_rings[ring]["west"], east=epsr_rings[ring]["east"])

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
            groups_list = sorted(ring_main["vlan-groups"])
            for grp in groups_list:
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


def src_guard(guard):

    out = ""

    for grd in guard:

        out += '''!
ip source-guard binding mode {mode} {mac} vlan {vlan} {ip} interface ethernet 1/{port}\n'''.format(**grd)

    return out


def dhcp_snooping(vlans):

    out = ""
    if vlans:
        out = "!\nip dhcp snooping\n"
        vlans_str = ",".join(vlans)
        out += "ip dhcp snooping vlan %s\n" % vlans_str

    return out


def get_data(num):

    vlans = SW[num]["vlans"]  # access ports

    try:
        trunks = SW[num]["trunk_ports"]
    except:
        trunks = []

    try:
        guard = SW[num]["source-guard"]
    except:
        guard = []

    try:
        dhcp_ports = SW[num]["dhcp-trust"]
    except:
        dhcp_ports = []

    try:
        dhcp_vlans = SW[num]["dhcp-vlans"]
    except:
        dhcp_vlans = []

    try:
        dhcp_filter = SW[num]["dhcp-filter"]
    except:
        dhcp_filter = []

    try:
        sec = SW[num]["port-sec"]
    except:
        sec = []

    return vlans, trunks, guard, dhcp_ports, dhcp_vlans, dhcp_filter, sec


def create_config(num):

    vlans, trunks, guard, dhcp_ports, dhcp_vlans, dhcp_filter, sec = get_data(num)

    out = HEAD.format(name="switch", number=num, network=NETWORK, database=DB)
    out += untagged_ports(vlans, dhcp_ports, sec, guard)
    out += trunk_ports(trunks, dhcp_ports)
    out += ring_interface(num, dhcp_ports, dhcp_filter)
    out += vlan_groups(num)
    out += ring_ports(num)
    out += ring_instance(num)
    out += dhcp_snooping(dhcp_vlans)
    out += src_guard(guard)
    out += BOTTOM.format(number=num, network=NETWORK, mask=MASK, mngt_vid=MNGT_VLAN)

    return out

if __name__ == '__main__':

    NUMBER = sys.argv[1]
    print(create_config(NUMBER))
