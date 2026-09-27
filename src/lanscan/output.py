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


def free_addresses(network, hosts, leases=None):
    net = ipaddress.ip_network(network, strict=False)
    occupied = set(hosts)

    if leases:
        occupied.update(leases)

    return [ip for ip in net.hosts() if ip not in occupied]


def build_summary(network, hosts, leases=None):
    net = ipaddress.ip_network(network, strict=False)
    host_addresses = set(net.hosts())
    arp_hosts = {
        ip: devices
        for ip, devices in hosts.items()
        if ip in host_addresses
    }
    lease_rows = {
        ip: lease
        for ip, lease in (leases or {}).items()
        if ip in host_addresses and ip not in arp_hosts
    }

    conflicts = sum(
        1 for devices in arp_hosts.values()
        if len(devices) > 1
    )
    used = len(arp_hosts) - conflicts
    reserved = sum(
        1 for lease in lease_rows.values()
        if lease.is_static
    )
    leased = len(lease_rows) - reserved
    occupied = used + conflicts + leased + reserved
    total = len(host_addresses)

    return {
        "network": str(net),
        "total": total,
        "occupied": occupied,
        "used": used,
        "conflicts": conflicts,
        "leased": leased,
        "reserved": reserved,
        "free": total - occupied,
    }


def print_summary(network, hosts, leases=None):
    summary = build_summary(network, hosts, leases)

    print(f"Network:   {summary['network']}")
    print(f"Total:     {summary['total']}")
    print(f"Occupied:  {summary['occupied']}")
    print(f"USED:      {summary['used']}")
    print(f"CONFLICT:  {summary['conflicts']}")
    print(f"LEASED:    {summary['leased']}")
    print(f"RESERVED:  {summary['reserved']}")
    print(f"FREE:      {summary['free']}")


def print_summary_json(network, hosts, leases=None):
    print(json.dumps(build_summary(network, hosts, leases), indent=2))


def _hostname(ip, hostnames, leases):
    hostname = hostnames.get(ip)
    if hostname:
        return hostname

    if leases and ip in leases:
        return leases[ip].hostname or "-"

    return "-"


def _lease_status(lease):
    return "RESERVED" if lease.is_static else "LEASED"


def _lease_vendor(lease):
    if lease.manufacturer:
        return lease.manufacturer

    return "OPNsense DHCP"


def _print_lease_row(ip, lease, hostname):
    print(
        f"{str(ip):15}  "
        f"{_lease_status(lease):8}  "
        f"{hostname:32}  "
        f"{(lease.mac or '-'):17}  "
        f"{_lease_vendor(lease)}"
    )


def print_devices(hosts, hostnames, leases=None):
    _print_header()

    addresses = set(hosts)
    if leases:
        addresses.update(leases)

    for ip in sorted(addresses):
        if ip not in hosts:
            lease = leases[ip]
            _print_lease_row(
                ip,
                lease,
                _hostname(ip, hostnames, leases),
            )
            continue

        devices = hosts[ip]
        status = host_status(devices)
        hostname = _hostname(ip, hostnames, leases)

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


def print_all(network, hosts, hostnames, leases=None):
    net = ipaddress.ip_network(network, strict=False)
    _print_header()

    for ip in net.hosts():
        if ip not in hosts:
            if leases and ip in leases:
                lease = leases[ip]
                _print_lease_row(
                    ip,
                    lease,
                    _hostname(ip, hostnames, leases),
                )
            else:
                print(
                    f"{str(ip):15}  "
                    f"{'FREE':8}  "
                    f"{'-':32}"
                )
            continue

        devices = hosts[ip]
        status = host_status(devices)
        hostname = _hostname(ip, hostnames, leases)

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


def print_free(network, hosts, leases=None):
    _print_header()

    for ip in free_addresses(network, hosts, leases):
        print(
            f"{str(ip):15}  "
            f"{'FREE':8}  "
            f"{'-':32}"
        )


def _json_host(ip, devices, hostname, lease=None):
    row = {
        "ip": str(ip),
        "status": host_status(devices).lower(),
        "hostname": hostname,
        "devices": [device.as_dict() for device in devices],
    }

    if lease is not None:
        row["lease"] = lease.as_dict()

    return row


def _json_leased(ip, lease, hostname):
    return {
        "ip": str(ip),
        "status": "reserved" if lease.is_static else "leased",
        "hostname": hostname,
        "devices": [],
        "lease": lease.as_dict(),
    }


def _json_free(ip, include_lease_field=False):
    row = {
        "ip": str(ip),
        "status": "free",
        "hostname": None,
        "devices": [],
    }

    if include_lease_field:
        row["lease"] = None

    return row


def _json_address(ip, hosts, hostnames, leases, include_lease_field):
    lease = leases.get(ip) if leases else None

    if ip in hosts:
        hostname = hostnames.get(ip) or (lease.hostname if lease else None)
        return _json_host(ip, hosts[ip], hostname, lease)

    if lease is not None:
        hostname = hostnames.get(ip) or lease.hostname
        return _json_leased(ip, lease, hostname)

    return _json_free(ip, include_lease_field=include_lease_field)


def build_json_data(
    hosts,
    hostnames,
    network=None,
    include_free=False,
    free_only=False,
    leases=None,
):
    include_lease_field = leases is not None

    if free_only:
        return [
            _json_free(ip, include_lease_field=include_lease_field)
            for ip in free_addresses(network, hosts, leases)
        ]

    if include_free:
        net = ipaddress.ip_network(network, strict=False)
        return [
            _json_address(
                ip,
                hosts,
                hostnames,
                leases,
                include_lease_field,
            )
            for ip in net.hosts()
        ]

    addresses = set(hosts)
    if leases:
        addresses.update(leases)

    return [
        _json_address(
            ip,
            hosts,
            hostnames,
            leases,
            include_lease_field,
        )
        for ip in sorted(addresses)
    ]


def print_json(
    hosts,
    hostnames,
    network=None,
    include_free=False,
    free_only=False,
    leases=None,
):
    print(
        json.dumps(
            build_json_data(
                hosts,
                hostnames,
                network=network,
                include_free=include_free,
                free_only=free_only,
                leases=leases,
            ),
            indent=2,
        )
    )
