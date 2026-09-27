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


def free_addresses(network, hosts):
    net = ipaddress.ip_network(network, strict=False)
    return [ip for ip in net.hosts() if ip not in hosts]


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


def print_free(network, hosts):
    _print_header()

    for ip in free_addresses(network, hosts):
        print(
            f"{str(ip):15}  "
            f"{'FREE':8}  "
            f"{'-':32}"
        )


def _json_host(ip, devices, hostname):
    return {
        "ip": str(ip),
        "status": host_status(devices).lower(),
        "hostname": hostname,
        "devices": [device.as_dict() for device in devices],
    }


def _json_free(ip):
    return {
        "ip": str(ip),
        "status": "free",
        "hostname": None,
        "devices": [],
    }


def build_json_data(
    hosts,
    hostnames,
    network=None,
    include_free=False,
    free_only=False,
):
    if free_only:
        return [_json_free(ip) for ip in free_addresses(network, hosts)]

    if include_free:
        net = ipaddress.ip_network(network, strict=False)
        return [
            _json_host(ip, hosts[ip], hostnames.get(ip))
            if ip in hosts
            else _json_free(ip)
            for ip in net.hosts()
        ]

    return [
        _json_host(ip, hosts[ip], hostnames.get(ip))
        for ip in sorted(hosts)
    ]


def print_json(
    hosts,
    hostnames,
    network=None,
    include_free=False,
    free_only=False,
):
    print(
        json.dumps(
            build_json_data(
                hosts,
                hostnames,
                network=network,
                include_free=include_free,
                free_only=free_only,
            ),
            indent=2,
        )
    )
