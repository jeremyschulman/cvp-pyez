import os
from nornir import InitNornir
from nornir.core.filter import F
from nornir.plugins.functions.text import print_result
from datetime import datetime
from first import first
from operator import attrgetter

print("Retrieving inventory from CVP ")

start_ts = datetime.now()
nr = InitNornir(
    core={
        'num_workers': 100
    },
    inventory={
        'plugin': 'cvppyez.nornir.CVPInventory',
        'options': dict(
            groupby_tags=['device-role'],
        ),
    }
)
end_ts = datetime.now()
collection_time = end_ts - start_ts
print("Detla time: %s" % str(collection_time))

nr.inventory.defaults.username = os.environ['CVP_USER']
nr.inventory.defaults.password = os.environ['CVP_PASSWORD']


def test_task(task):
    np_dev = task.host.get_connection("napalm", task.nornir.config)
    return np_dev.device.run_commands(commands=[
        'show version',
        'show interfaces description',
        'show ip interface'
    ])


def find_mac(task, macaddr, progress=None):
    """
    This Nornir task is used to locate the given `macaddr` on the device.  If
    the MACADDR is found on Eth interfaces, then this function will return a
    list of tuples (int: vlan-id, str: interface name).  If the MACADDR is not
    found then this function will return None.

    Notes
    -----
    There is a filter match on interface name starts with 'Eth' so we don't
    include Port-Channels.  This is for demo-purposes only; and your specific
    filtering criteria could vary.

    Parameters
    ----------
    task : Nornir.task
    macaddr : str - the MACADDR value to find
    progress : function to declare progress

    Returns
    -------
    list[tuple] or None as described.
    """

    # use NAPALM driver to execute the command

    np_dev = task.host.get_connection("napalm", task.nornir.config)

    # but use the direct pyEAPI device so we get back structured data and not
    # CLI text

    cmd_res = np_dev.device.run_commands(
        commands=[
            f'show mac address-table address {macaddr}'
        ]
    )

    mac_entries = cmd_res[0]['unicastTable']['tableEntries']

    if progress:
        progress()

    # if the MACADDR is not found, then return None

    if not len(mac_entries):
        return None

    # filter matching on ETh interfaces only

    r_items = [
        (entry['vlanId'], entry['interface'])
        for entry in mac_entries
        if entry['interface'].startswith('Eth')
    ]

    return r_items if len(r_items) else None


def test(inv, macaddr, progress=None):
    """
    This function will execute the find-mac function against all hosts in the
    `inv` Nornir object.  Any found item will be returned as a list of dict; where
    each dict contains the hostname, vlan, and interface where the MACADDR was found.

    Parameters
    ----------
    inv : Nornir instance
    macaddr : str - MACADDR to find
    progress : callable to indicate progress

    Returns
    -------
    list[dict] as described.
    """

    res = inv.run(task=find_mac, macaddr=macaddr, progress=progress)

    # there will be a result for each of the hosts in the `inv` instance. We
    # want to filter on only those results that are not None.  So the code
    # below uses the built-in filter() to obtain the host item result to
    # determine if it is None or not (as returned by the find_mac task.  If the
    # results are not None then we iterate through the list of found entries
    # for that device.

    return [
        dict(hostname=found.host.name, vlan=item[0], interface=item[1])
        for found in filter(attrgetter('result'), res.values())
        for item in found.result
    ]


