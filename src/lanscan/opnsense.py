import base64
import json
import ssl
from ipaddress import IPv4Address, ip_network
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import OpnsenseConfig
from .models import DhcpLease


class OpnsenseError(Exception):
    """Failure while reading data from the OPNsense API."""


INACTIVE_STATES = {
    "abandoned",
    "backup",
    "declined",
    "expired",
    "free",
    "inactive",
    "released",
}


def _api_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/api"):
        path = f"{base}/dhcpv4/leases/search_lease"
    else:
        path = f"{base}/api/dhcpv4/leases/search_lease"

    query = urlencode(
        {
            "current": 1,
            "rowCount": 10000,
            "searchPhrase": "",
        }
    )
    return f"{path}?{query}"


def _text(value):
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def _lease_is_active(row: dict) -> bool:
    state = _text(row.get("state"))
    if state and state.lower() in INACTIVE_STATES:
        return False

    return True


def parse_dhcp_leases(payload) -> dict[IPv4Address, DhcpLease]:
    if not isinstance(payload, dict):
        raise OpnsenseError("unexpected DHCP lease response")

    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise OpnsenseError("DHCP lease response does not contain a rows list")

    leases = {}

    for row in rows:
        if not isinstance(row, dict) or not _lease_is_active(row):
            continue

        address = _text(row.get("address") or row.get("ip"))
        if not address:
            continue

        try:
            ip = IPv4Address(address)
        except ValueError:
            continue

        mac = _text(row.get("hwaddr") or row.get("mac"))
        if mac:
            mac = mac.lower()

        lease = DhcpLease(
            ip=ip,
            mac=mac,
            hostname=_text(
                row.get("hostname")
                or row.get("client-hostname")
                or row.get("client_hostname")
            ),
            interface=_text(
                row.get("if_descr")
                or row.get("if_name")
                or row.get("if")
                or row.get("interface")
            ),
            state=_text(row.get("state")),
            starts=_text(row.get("starts") or row.get("start")),
            ends=_text(row.get("ends") or row.get("end")),
            lease_type=_text(row.get("type")),
            status=_text(row.get("status")),
            description=_text(row.get("descr") or row.get("description")),
            manufacturer=_text(row.get("man") or row.get("manufacturer")),
        )

        existing = leases.get(ip)
        if existing is None or lease.is_static or not existing.is_static:
            leases[ip] = lease

    return leases


def fetch_dhcp_leases(config: OpnsenseConfig):
    credentials = f"{config.api_key}:{config.api_secret}".encode("utf-8")
    token = base64.b64encode(credentials).decode("ascii")

    request = Request(
        _api_url(config.url),
        headers={
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
        },
        method="GET",
    )

    context = None
    if not config.verify_tls:
        context = ssl._create_unverified_context()

    try:
        with urlopen(
            request,
            timeout=config.timeout,
            context=context,
        ) as response:
            payload = json.load(response)
    except HTTPError as exc:
        raise OpnsenseError(
            f"OPNsense API returned HTTP {exc.code}"
        ) from exc
    except URLError as exc:
        raise OpnsenseError(
            f"could not connect to OPNsense API: {exc.reason}"
        ) from exc
    except (TimeoutError, json.JSONDecodeError, OSError) as exc:
        raise OpnsenseError(
            f"could not read OPNsense DHCP leases: {exc}"
        ) from exc

    return parse_dhcp_leases(payload)


def leases_in_network(network: str, leases):
    net = ip_network(network, strict=False)
    return {
        ip: lease
        for ip, lease in leases.items()
        if ip in net
    }
