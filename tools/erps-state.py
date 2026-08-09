#!/usr/bin/python3
#
# Connect over SSH and check ERPS status per switch
#
# Source:
# https://github.com/2a-stra/ecs-config

import re
import os
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

import logging
logging.basicConfig(filename='netmiko_output.log', level=logging.DEBUG)
logger = logging.getLogger("netmiko")

# Configuration
CONFIG_FILE = "~/.ssh/include/sw.config"
KEY_FILE = "~/.ssh/ecs"
SWITCHES = ["sw100", "sw110", "sw120", "sw130"]
COMMAND = "sh erps instance"

# Regex pattern to match "Idle", "Pending", or "Protected" (case-insensitive)
STATUS_PATTERN = re.compile(r"\b(Idle|Pending|Protected)\b", re.IGNORECASE)

def main():
    for switch in SWITCHES:
        print(f"\n{'='*10} Connecting to {switch} {'='*10}")

        # Netmiko device configuration
        device = {
            'device_type': 'cisco_ios', # Try 'generic_term' or 'edgecore_nos'  if this hangs
            'host': switch,
            'ssh_config_file': os.path.expanduser(CONFIG_FILE), # Explicitly point to your config
            'key_file': os.path.expanduser(KEY_FILE),
            'use_keys': True,
            'fast_cli': False, # Recommended for older/slower switch CPUs
            'conn_timeout': 10,
        }

        try:
            # Establish connection and send command
            with ConnectHandler(**device) as net_connect:
                output = net_connect.send_command(COMMAND)

            found_any = False
            
            # Process output line by line and print matches immediately
            for line in output.splitlines():
                if STATUS_PATTERN.search(line):
                    print(line)
                    found_any = True

            if not found_any:
                print(f"[-] No target status (Idle/Pending/Protected) found on {switch}.")
                
        except NetmikoTimeoutException:
            print(f"[ERROR] Connection timed out while communicating with {switch}")
        except NetmikoAuthenticationException:
            print(f"[ERROR] Authentication failed for {switch}")
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred on {switch}: {e}")

if __name__ == "__main__":
    main()