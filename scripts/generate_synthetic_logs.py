import json
import random
from pathlib import Path


# --- Configuration for Enhanced Synthetic Data ---

# More realistic and varied entities
DEVICE_NAMES = [
    "S1",
    "D1",
    "R1",
    "core-switch-01",
    "access-gw-5",
    "dist-router-3",
    "leaf-101",
    "spine-01",
    "FW-01",
    "DC-BORDER-RTR",
]
INTERFACES = [
    "GigabitEthernet0/1",
    "Gi0/2",
    "FastEthernet0/24",
    "TenGigabitEthernet1/0/1",
    "Te1/1",
    "eth0/0",
    "Po1",
    "Port-channel10",
    "Vlan100",
    "Loopback0",
    "Fa0/1",
]
VLANS = ["10", "20", "100", "250", "999", "400", "501"]
PROTOCOLS = [
    "bgp",
    "ospf",
    "arp",
    "mac address-table",
    "vlan",
    "cdp neighbors",
    "lldp",
    "spanning-tree",
    "ip route",
]
KEYWORDS = [
    "status",
    "config",
    "running-config",
    "table",
    "neighbors",
    "uptime",
    "version",
    "brief",
    "errors",
    "flaps",
]
IPS = ["10.1.1.1", "192.168.100.5", "172.16.31.254", "8.8.8.8", "203.0.113.10"]
SUBNETS = ["10.1.1.0/24", "192.168.100.0 255.255.255.0", "0.0.0.0"]

# --- Weighted Query Templates ---
# We assign weights to make common queries appear more frequently.

# (Template, Weight)
WEIGHTED_TEMPLATES = {
    "get_status": [
        ("show ip interface brief on {device}", 10),
        ("show interface status on {device}", 8),
        ("show interface {interface} on {device}", 7),
        ("show vlan brief on {device}", 6),
        ("show ip route on {device}", 5),
        ("show cdp neighbors on {device}", 5),
        ("show lldp neighbors detail on {device}", 4),
        ("show mac address-table on {device}", 4),
        ("show version on {device}", 4),
        ("show inventory on {device}", 3),
        ("show ip arp {ip} on {device}", 3),
        ("show spanning-tree vlan {vlan} on {device}", 2),
        ("ping {ip} from {device}", 2),
        ("traceroute {ip} on {device}", 1),
        ("what is the uptime of {device}?", 5),
        ("are there any errors on {interface} on {device}?", 4),
        ("check cpu utilization on {device}", 3),
        ("display the arp table for {device}", 4),
        ("is {device} connected to {neighbor_device}?", 3),
    ],
    "get_config": [
        ("show running-config interface {interface} on {device}", 8),
        (
            "show running-config on {device}",
            3,
        ),  # Less common to ask for the whole thing
        ("show running-config | section router bgp on {device}", 4),
        ("show running-config | include {ip} on {device}", 3),
        ("what is the config for vlan {vlan} on {device}?", 5),
        ("get me the startup-config for {device}", 2),
        ("display the access-lists on {device}", 3),
    ],
    "find_device": [
        ("list all devices", 10),
        ("show inventory", 8),
        ("find devices with role 'access'", 5),
        ("where is ip {ip}?", 4),
        ("find the mac address for {ip}", 3),
    ],
    "ambiguous_and_general": [
        ("hello", 5),
        ("hi there", 5),
        ("thanks", 3),
        ("interface status", 4),  # Missing device
        ("bgp neighbors", 3),  # Missing device
        ("show me the config", 2),  # Ambiguous
        ("is it up?", 1),  # Needs context
        ("what can you do?", 2),
    ],
}


def introduce_noise(query: str) -> str:
    """Adds minor variations and typos to a query string."""
    if random.random() < 0.15:  # 15% chance to add noise
        # Simple typo: swap two adjacent characters
        if len(query) > 4:
            pos = random.randint(1, len(query) - 2)
            if query[pos].isalpha() and query[pos - 1].isalpha():
                query = (
                    query[: pos - 1] + query[pos] + query[pos - 1] + query[pos + 1 :]
                )

    if random.random() < 0.2:  # 20% chance to change phrasing
        phrases = [
            ("show", "get"),
            ("show", "display"),
            ("show", "what is"),
            ("on", "for"),
        ]
        find, replace = random.choice(phrases)
        if find in query:
            query = query.replace(find, replace, 1)

    if random.random() < 0.1:  # 10% chance of weird capitalization
        query = query.upper()

    return query


def generate_synthetic_logs(num_entries: int = 2000) -> None:
    """
    Generates a comprehensive synthetic log file with varied, realistic user queries.

    Args:
        num_entries (int): The number of log entries to generate.
    """
    print(f"🔥 Generating {num_entries} high-quality synthetic log entries...")
    logs = []

    # Unpack weighted templates for random selection
    all_templates = []
    for intent in WEIGHTED_TEMPLATES:
        for template, weight in WEIGHTED_TEMPLATES[intent]:
            all_templates.extend([(template, weight)])

    templates, weights = zip(*all_templates, strict=False)

    for _ in range(num_entries):
        template = random.choices(templates, weights=weights, k=1)[0]

        # Fill template with random entities
        query = template.format(
            device=random.choice(DEVICE_NAMES),
            neighbor_device=random.choice(DEVICE_NAMES),
            interface=random.choice(INTERFACES),
            vlan=random.choice(VLANS),
            protocol=random.choice(PROTOCOLS),
            keyword=random.choice(KEYWORDS),
            ip=random.choice(IPS),
            subnet=random.choice(SUBNETS),
        )

        # Add realistic variations
        query = introduce_noise(query)
        logs.append({"text": query})

    # Ensure the data directory exists
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    output_file = data_dir / "raw_queries.jsonl"
    with open(output_file, "w") as f:
        for log_entry in logs:
            f.write(json.dumps(log_entry) + "\n")

    print(
        f"✅ Successfully created synthetic log file with {len(logs)} entries at: {output_file}"
    )
    print("🎉 You can now proceed to Phase 2: Bootstrapping Labels.")


if __name__ == "__main__":
    generate_synthetic_logs(num_entries=2000)
