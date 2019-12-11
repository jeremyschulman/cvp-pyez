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

nr.inventory.defaults.username = os.environ['USER']
nr.inventory.defaults.password = os.environ['PASSWORD']


def test_task(task):
    np_dev = task.host.get_connection("napalm", task.nornir.config)
    return np_dev.device.run_commands(commands=[
        'show version',
        'show interfaces description',
        'show ip interface'
    ])


def find_mac(task, macaddr):
    np_dev = task.host.get_connection("napalm", task.nornir.config)
    cmd_res = np_dev.device.run_commands(commands=[
        f'show mac address-table address {macaddr}'
    ])[0]

    mac_entry = first(cmd_res['unicastTable']['tableEntries'])
    if not mac_entry:
        return None

    if_name = mac_entry['interface']
    return if_name if if_name.startswith('Eth') else None


def test(inv, seek_macaddr='08:00:0f:df:2a:67'):
    res = inv.run(task=find_mac, macaddr=seek_macaddr)
    found = first(filter(attrgetter('result'), res.values()))
    return (found.host, found.result) if found else 'not found'


