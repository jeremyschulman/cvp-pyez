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
    np_dev = task.host.get_connection("napalm", task.nornir.config)

    cmd_res = np_dev.device.run_commands(
        commands=[
            f'show mac address-table address {macaddr}'
        ]
    )

    mac_entries = cmd_res[0]['unicastTable']['tableEntries']

    if progress:
        progress()

    if not len(mac_entries):
        return None

    r_items = [
        (entry['vlanId'], entry['interface'])
        for entry in mac_entries
        if entry['interface'].startswith('Eth')
    ]

    return r_items if len(r_items) else None


def test(inv, macaddr=, progress=None):
    res = inv.run(task=find_mac, macaddr=macaddr, progress=progress)

    return [
        dict(hostname=found.host.name, vlan=item[0], interface=item[1])
        for found in filter(attrgetter('result'), res.values())
        for item in found.result
    ]




