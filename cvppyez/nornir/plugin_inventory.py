from collections import defaultdict

from cvppyez.rest import CVPRestClient

from nornir.core.deserializer.inventory import Inventory

__all__ = ['CVPInventory']


def _get_tags(cvp, tag_list):
    r_dev_tags = defaultdict(list)
    r_tags = list()

    for tag_name in tag_list:
        res = cvp.api.get('/label/getLabels.do', params=dict(
            module='cvp',
            type=tag_name
        ))
        res.raise_for_status()

        for record in res.json()['labels']:
            tag_count = record['netElementCount']
            if not tag_count:
                continue

            tag_key = record['key']
            r_tags.append(tag_key)

            res = cvp.api.get('/label/getAppliedDevices.do', params=dict(
                labelId=tag_key, startIndex=0, endIndex=0
            ))
            res.raise_for_status()
            for dev_rec in res.json()['data']:
                hostname = dev_rec['hostName']
                r_dev_tags[hostname].append(tag_key)

    return r_tags, r_dev_tags


class CVPInventory(Inventory):

    def __init__(self, config, **kwargs):

        cvp = CVPRestClient()
        res = cvp.api.get('/inventory/devices')
        res.raise_for_status()
        body = res.json()

        hosts = {
            dev['fqdn']: dict(hostname=dev['ipAddress'])
            for dev in body
        }

        sn_to_hn = {dev['serialNumber']: dev['fqdn'] for dev in body}
        host_sn_keys = set(sn_to_hn)

        # now obtain the device status information for two reason:
        # (1) remove any hosts that are not active
        # (2) remove any hosts that are not _present_ in the status area

        # TODO: should probably log these inactive hosts somewhere.

        res = cvp.api.get('$a/DatasetInfo/Devices')
        res.raise_for_status()
        host_status = cvp.extracto_notifications(res.json())
        host_status_sn_keys = set(host_status)

        # (1) - remove any hosts that are not active
        for host_ds in host_status.values():
            hostname = host_ds['hostname']
            if host_ds['status'] != 'active':
                print(f"WARNING: removing inactive host: {hostname}")
                del hosts[hostname]

        # (2) remove any hosts that are not _present_ in the status area
        for nonexist_sn in host_sn_keys - host_status_sn_keys:
            hostname = sn_to_hn[nonexist_sn]
            print(f"WARNING: removing 'zombie' host: {hostname}")
            del hosts[hostname]

        groups = {}
        groupby_tags = kwargs.get('groupby_tags')
        if groupby_tags:
            tags, dev_tags = _get_tags(cvp, tag_list=groupby_tags)
            for dev_name, tag_list in dev_tags.items():
                hosts[dev_name]['groups'] = tag_list

            for tag_name in tags:
                groups[tag_name] = dict()

        defaults = {
            'platform': 'eos'
        }

        super().__init__(hosts=hosts, groups=groups, defaults=defaults, **kwargs)
