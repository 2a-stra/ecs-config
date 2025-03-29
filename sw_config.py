NETWORK = "192.168.5"
MASK = "255.255.255.0"
MNGT_VLAN = "5"

DB = '''VLAN 1 name DefaultVlan media ethernet
    VLAN %s name mngt media ethernet
    VLAN 10 name core media ethernet
    VLAN 20 name voip media ethernet
    VLAN 30 name test-lab media ethernet
    VLAN 1001 name core-subring media ethernet
    VLAN 1002 name main-ring media ethernet
    VLAN 1003 name a-subring media ethernet
    VLAN 1004 name b-subring media ethernet
    VLAN 1005 name c-subring media ethernet''' % MNGT_VLAN

# Change passwords below to appropriate hash!
HEAD = '''!
clock timezone Armenia hours 4 minute 0
!
ntp client
ntp server {network}.1
!
prompt {name}-{number}
hostname {name}-{number}
!
banner configure company Company
banner configure department "Tech. dep."
banner configure equipment-location "Building 1"
banner configure equipment-info manufacturer-id ECS floor 1 row 1 rack 1 shelf-rack 1 manufacturer Edge-Core
banner configure lp-number {number}
banner configure ip-lan {network}.{number}
banner configure note "Switch #{number}"
!
snmp-server community public ro
snmp-server community private rw
!
username ecs access-level 15
username ecs password 7 xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
!no username admin
!no username guest
username user access-level 0
username user password 7 xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
enable password 7 xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
!
vlan database
    {database}
'''

BOTTOM = '''!
!
interface vlan 1
    ip address dhcp
    no ip dhcp client hostname
!
interface vlan {mngt_vid}
    ip address {network}.{number} {mask}
    no ip dhcp client hostname
!
no ip http server
!
no ip telnet server
!
line console
!
line vty
!
end
!
!'''

GROUPS = {
    "Main": ["5", "20"],
    "Core": ["10"],
    "c-Main": ["1002"],
    "c-Core": ["1001"],
    "c-A": ["1003"],
    "c-B": ["1004"],
    "c-C": ["1005"]
}

EPSR = {
    "Main": {
        "sub-ring": False,
        "name": "Main",
        "id": "2",
        "owner": "105",
        "neighbor": "106",
        "members": ["101", "102", "103", "104", "105"],
        "vlan-groups": ["Main", "Core", "c-Core", "c-Main", "c-A", "c-B", "c-C"],
        "control": "c-Main",
    },
    "Core": {
        "sub-ring": True,
        "major-ring": "Main",
        "name": "Core",
        "id": "1",
        "members": ["100", "101", "102", "110", "111"],
        "owner": "102",
        "neighbor": "111",
        "far-end": "101",
        "vlan-groups": ["Main", "Core", "c-Core"],
        "control": "c-Core",
    },
     "A": {
        "sub-ring": True,
        "major-ring": "Main",
        "name": "A",
        "id": "3",
        "members": ["103", "104", "120"],
        "owner": "103",
        "neighbor": "120",
        "far-end": "104",
        "vlan-groups": ["Main", "c-A"],
        "control": "c-A",
    },
}

SW = {                      # VLAN access ports
"100": {
    "vlans": {
        "20": list(range(1,  13)),  # from 1 to 12  - VoIP
        "30": list(range(13, 25)),  # VID 30        - Lab test
        "10": list(range(25, 37)),  # from 25 to 36 - Core
        "5":  list(range(37, 43)),  # from 37 to 42 - Management
    },
    "epsr": {  # Add the member to EPSR as well
        "Core": {
            "west": 49,  # SFP
            "east": 50,  # SFP
            }
        }
    },
"101": {
    "vlans": {
        "20": list(range(1,  25)),   # from 1 to 24
        "10": list(range(25, 37)),
        "5":  list(range(37, 43)),
    },
    "epsr": {
        "Main": {
            "west": 47,  # UTP
            "east": 48   # UTP
            },
        "Core": {
            "east": 50,  # SFP
            }
        }
    },
"102": {
    "vlans": {
        "20": list(range(1,  25)),  # VoIP
        "10": list(range(25, 37)),  # Core
        "5":  list(range(37, 43)),  # Mngt
    },
    "epsr": {
        "Main": {
            "west": 47, # UTP
            "east": 52  # SFP
            },
        "Core": {
            "west": 49, # SFP
            }
        }
    },
"103": {
    "vlans": {
        "20": list(range(1,  45)),  # form 1 to 44 VoIP
        "5":  list(range(45, 46)),  # only 45 Mngt (46 - native vlan 1)
    },
    "epsr": {
        "Main": {
            "west": 51,
            "east": 48   # UTP
            },
        "A": {
            "west": 49,
            }
        }
    },
"104": {
    "vlans": {
        "20": list(range(1,  45)),  # form 1 to 44 VoIP
        "5":  list(range(45, 46)),  # only 45 Mngt (46 - native vlan 1)
    },
    "epsr": {
        "Main": {
            "west": 47,  # UTP
            "east": 52
            },
        "A": {
            "east": 50,
            }
        }
    },
"105": {
    "vlans": {
        "20": list(range(1,  45)),  # form 1 to 44 VoIP
        "5":  list(range(45, 46)),  # only 45 Mngt (46 - native vlan 1)
    },
    "epsr": {
        "Main": {
            "west": 51,
            "east": 48  # UTP
            },
        }
    },
"120": {
    "vlans": {
        "20": list(range(1,  45)),  # form 1 to 44 VoIP
        "5":  list(range(45, 46)),  # only 45 Mngt (46 - native vlan 1)
    },
    "epsr": {
        "A": {
            "west": 49,
            "east": 50
            },
        },
    }
}

