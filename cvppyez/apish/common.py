from cvppyez.log import setup_log


class APISH(object):
    BIN = "/cvpi/tools/apish"

    PATH = {
        'events': '/events/activeEvents',
        'devices': '/DatasetInfo/Devices',
        'events-ack': '/events/userInteractions'
    }

    def __init__(self, log=None, opts_driver=None):
        self.opts_driver = opts_driver or {}
        self.log = log or setup_log('/dev/null')

    @staticmethod
    def extract_notifications(apish_output):
        for each in apish_output:
            for notif in each.get('Notifications'):
                yield notif

    def execute(self, cmdopts):
        raise NotImplementedError()

    @staticmethod
    def path_str(path):
        raise NotImplementedError()

    def get(self, dataset_name, **cmdopts):
        apish_cmdopts = ['get']
        cmdopts['dataset_name'] = dataset_name

        path = cmdopts.get('path')
        if path and isinstance(path, list):
            # convert list path to json string
            cmdopts['path'] = self.path_str(path)

        for key, value in cmdopts.items():
            apish_cmdopts.append(f'--{key.replace("_", "-")}={value}')

        return self.execute(apish_cmdopts)

    def get_devices(self):
        lines = self.get(dataset_name='analytics', path=self.PATH['devices'])
        devices = dict()

        for notif in self.extract_notifications(lines):
            for sn, sn_val in notif.get('updates', {}).items():
                devices[sn] = sn_val['value']

        return devices

    def get_events(self, **cmdopts):
        lines = self.get(dataset_name='analytics', path=self.PATH['events'],
                         **cmdopts)

        return self.extract_notifications(lines)
