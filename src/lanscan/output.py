import ipaddress
import json


def host_status(devices):
    return "CONFLICT" if len(devices) > 1 else "USED"


def _print_header():
    print(
        f"{'IP':15}  "
        f"{'STATUS':8}  "
        f"{'HOSTNAME':32}  "
        f"{'MAC':17}  "
        f"VENDOR"
    )


def print_devices(hosts, hostnames):
    _print_header()

    for ip in sorted(hosts):
        devices = hosts[ip]
        status = host_status(devices)
        hostname = hostnames.get(ip) or "-"

        for index, device in enumerate(devices):
            ip_text = str(ip) if index == 0 else ""
            status_text = status if index == 0 else ""
            hostname_text = hostname if index == 0 else ""

            print(
                f"{ip_text:15}  "
                f"{status_text:8}  "
                f"{hostname_text:32}  "
                f"{device.mac:17}  "
                f"{device.vendor}"
            )


def print_all(network, hosts, hostnames):
    net = ipaddress.ip_network(network, strict=False)
    _print_header()

    for ip in net.hosts():
        if ip not in hosts:
            print(
                f"{str(ip):15}  "
                f"{'FREE':8}  "
                f"{'-':32}"
            )
            continue

        devices = hosts[ip]
        status = host_status(devices)
        hostname = hostnames.get(ip) or "-"

        for index, device in enumerate(devices):
            ip_text = str(ip) if index == 0 else ""
            status_text = status if index == 0 else ""
            hostname_text = hostname if index == 0 else ""

            print(
                f"{ip_text:15}  "
                f"{status_text:8}  "
                f"{hostname_text:32}  "
                f"{device.mac:17}  "
                f"{device.vendor}"
            )


def build_json_data(hosts, hostnames):
    data = []

    for ip in sorted(hosts):
        devices = hosts[ip]

        data.append(
            {
                "ip": str(ip),
                "status": host_status(devices).lower(),
                "hostname": hostnames.get(ip),
                "devices": [device.as_dict() for device in devices],
            }
        )

    return data


def print_json(hosts, hostnames):
    print(json.dumps(build_json_data(hosts, hostnames), indent=2))
