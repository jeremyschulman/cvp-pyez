from first import first


class PluginDevices(object):
    name = 'devices'

    class URLs:
        ACTIVE_DEVICES = '$a/DatasetInfo/Devices'

    def __init__(self, cvp):
        self.cvp = cvp

    def get_active_devices(self):
        got = self.cvp.get(self.URLs.ACTIVE_DEVICES)
        got.raise_for_status()
        body = got.json()['notifications']
        res = dict()
        for item in body:
            upd = item['updates']
            sn_key = first(upd)
            res[sn_key] = upd[sn_key]['value']

        return res
