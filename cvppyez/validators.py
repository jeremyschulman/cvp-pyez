import re
import ipaddress


__all__ = [
    'validate_macaddr',
    'validate_ipaddr'
]


_mac_char_re = re.compile(r'[0-9a-f]', re.I)
_mac_char_len = 12


def validate_macaddr(macaddr, chunk_len=2, chunk_sep=':'):

    if not (_mac_char_len / chunk_len).is_integer():
        raise ValueError('chunk_len invalid', chunk_len)

    mac_chars = ''.join(_mac_char_re.findall(macaddr))
    if len(mac_chars) != _mac_char_len:
        return None

    return chunk_sep.join((mac_chars[i:i + chunk_len]
                           for i in range(0, len(mac_chars), chunk_len)))


def validate_ipaddr(ipaddr):
    try:
        ipaddress.ip_address(ipaddr)
        return ipaddr

    except ValueError:
        return None
