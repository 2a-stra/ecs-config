# Generate Edge-Core Switch Configuration Files with VLANs and ERPS

Automate the configuration of Edge-Core ECS4100 series switches with these scripts. The generated configuration files can be quickly uploaded to switches via TFTP, significantly accelerating network deployment times. The configuration includes settings for IP networks, VLAN port assignments (tagged or untagged), and Ethernet Protection Rings (ERPS) for enhanced network reliability. All configuration settings are stored in the `sw_config.py` file.

## Configuration

Customize your settings by editing the `sw_config.py` file. Specify your preferred IP network settings, VLANs, port ranges, and ERPS rings.

### Network config

```python
NETWORK = "192.168.5"
MASK = "255.255.255.0"
MNGT_VLAN = "5"
```

VLAN access ports config per switch number:

```python
SW = {
"101": {
    "vlans": {                              # VLAN access ports
        "20": list(range(1,  13)),          # from 1 to 12          - VoIP
        "30": list(range(13, 25)),          # VID 30                - Lab test
        "10": list(range(25, 37)) + [52],   # from 25 to 36 and 52  - Core
        "5":  list(range(37, 43)),          # from 37 to 42         - Management
        },
    "epsr": {
        "Main": {
            "west": 47,  # UTP
            "east": 48   # UTP
            },
        "Core": {
            "east": 50,  # SFP (Far-end)
            }
        },
    "port-sec": list(range(1, 3)) + [52],  # port security (access ports)
    "source-guard": [
            {
            "port":  52,                   # external server
            "mode": "acl",
            "vlan":  10,
            "ip":    "192.168.0.123",
            "mac":   "XX-XX-XX-XX-XX-XX",
            },
        ],
    "dhcp-vlans": ["20"],           # dhcp snooping vlans
    "dhcp-trust": [11, 50],         # dhcp snooping trusted ports
    "dhcp-filter": [47, 48, 50],    # dhcp filter-only
    }
} # Add new SW to ESPR members list!
```

In the example configuration, Switch 101 is configured with ports 1 to 12 assigned as untagged VLAN 20 ports. The switch is a member of the ERPS ring named 'Main', with west port 47 and east port 48. Additionally, Switch 101 is part of the sub-ring 'Core', with port 50 assigned to this sub-ring.

Further configuration details include:

- Port Security: Enabled on ports 1, 2, and 52.
- IP Source Guard: Applied to port 52 with an Access Control List (ACL) to filter traffic.
- DHCP Snooping: Enabled on VLAN 20. Ports 11 and 50 are configured as trusted for DHCP servers.
- Trunk Port Filtering: Ports 47, 48, and 50 are configured as filter-only trunks with unlimited DHCP clients allowed on them.

### VLAN groups names with VLAN IDs

```python
GROUPS = {
    "Main": [5, 20],
    "Core": [10],
    "c-Main": [1002],
    "c-Core": [1001],
    "c-A": [1003],
    "c-B": [1004],
    "c-C": [1005]
}
```

### Ethernet Ring Protection switching (ERPS)

The EPRS configuration defines multiple rings. Each switch in the Major ring has two interface ports, `west` and `east`, along with the Ring Protection Link (RPL) owner and a control VLAN. The major ring also includes the control VLANs of all sub-rings.

![ERPS multiple rings](erps_rings_scheme.webp "Network connection scheme with multiple ERPS rings")

The sub-rings are connected to the Major ring at one end, where they link to the RPL owner switch through the `west` interface, and at the other end, they connect to the `far-end` switch via the `east` port. These two termination switches in the sub-ring each have only one interface port participating in the sub-ring. The sub-ring is configured to specify the `major-ring` for sending control packets.

```python
EPSR = {
    "Main": {
        "sub-ring": False,
        "name": "Main",
        "id": "2",
        "owner": "101",
        "neighbor": "105",
        "members": ["101", "102", "103", "104", "105"],
        "vlan-groups": ["Main", "Core", "c-Core", "c-Main", "c-A", "c-B", "c-C"],
        "control": "c-Main",
    },
    "Core": {
        "sub-ring": True,
        "major-ring": "Main",
        "name": "Core",
        "id": "1",
        "members": ["100", "101", "102"],
        "owner": "101",
        "neighbor": "100",
        "far-end": "102",
        "vlan-groups": ["Main", "Core", "c-Core"],
        "control": "c-Core",
    },
}
```

## Config generation

### Generate configs for all switches

Generate config files for all configured switches at once:
```sh
python3 gen_config_all.py
```

### Generate config for particular switch

Generate config for switch number `100`:
```sh
python3 ecs_config.py 100
```

As a result, an output file named `sw100.cfg` will be generated in the local directory. By default, the switch will be named 'switch-100' with a management IP address of '192.168.5.100.'

## Switch ERPS instance status

In normal operation, switches are set to the `Idle` state, and no Signal Fail (SL) messages are received. The RPL owner blocks the `west` interface, while the RPL neighbor blocks the `east` interface accordingly.

Core ring RPL owner `switch-101` settings:

![ERPS Core sub-rings owner](erps_sw101.webp "Core sub-ring owner settings")

Core ring RPL neighbor `switch-100` settings:

![ERPS Core sub-rings neighbor](erps_sw100.webp "Core sub-ring neighbor settings")

These scripts automate Edge-Core ECS4100 switch configurations, enabling fast upload of generated config files and accelerating network deployment with IP settings, VLANs, and ERPS for enhanced reliability.
