import os
import json
import requests
import importlib
from first import first

__all__ = ['CVPRestClient']


class CvpClientURLs:
    SHORTCUTS = {
        None: '/web',
        '$a': '/api/v1/rest/analytics',
        '$r': '/api/v1/rest',
        '$c': '/cvpservice',
        '$n': '/api/v1/rest/analytics/network/v1'
    }

    LOGIN = '/login/authenticate.do'
    INVENTORY = '/inventory/devices'
    VERSION = '/cvpInfo/getCvpInfo.do'


class CvpSession(requests.Session):
    ENV = {
        'username': ['CVP_USER', 'USER'],
        'password': ['CVP_PASSWORD', 'PASSWORD'],
        'server': ['CVP_SERVER']
    }

    URLs = CvpClientURLs

    def __init__(self, server=None, username=None, password=None, quiet=True, login=True):

        super(CvpSession, self).__init__()
        self.host_url = "https://%s" % (self._required_var('server', server))
        self._auth = dict(userId=self._required_var('username', username),
                          password=self._required_var('password', password))
        self.headers['Content-Type'] = 'application/json'
        self.verify = False
        self.version = None

        if quiet:
            self.quiet()

        if login:
            self.login()

    def _required_var(self, name, provided_value):
        has_value = provided_value or first(map(os.getenv, self.ENV[name]))
        if not has_value:
            raise RuntimeError(f'Missing required value for parameter: {name}')

        return has_value

    def quiet(self):
        requests.urllib3.disable_warnings()
        return self

    def login(self):
        res = self.post(self.URLs.LOGIN, json=self._auth)
        res.raise_for_status()
        res = self.get(self.URLs.VERSION)
        res.raise_for_status()
        self.version = res.json()['version']
        return self

    def prepare_request(self, request):
        """
        This method overrides to produce the compelte URL based on the CvpClient
        host information.  If the `reuqest.url` begins with "$t", then the
        Telemetry base URI will be used rather than the standard CVP /web value.

        Parameters
        ----------
        request : Request instance
        """
        if request.url.startswith('$'):
            key, _, url = request.url.partition('/')
            api_base = self.URLs.SHORTCUTS[key]
            url = "/" + url
        else:
            api_base = self.URLs.SHORTCUTS[None]
            url = request.url

        request.url = f'{self.host_url}{api_base}{url}'

        return super(CvpSession, self).prepare_request(request)

    @property
    def about(self):
        return dict(version=self.version,
                    username=self._auth['userId'],
                    host=self.host_url)


class CVPRestClient(object):

    def __init__(self, server=None, username=None, password=None, quiet=True, login=True):
        self.api = CvpSession(server=server, username=username, password=password,
                              quiet=quiet, login=login)

    def add_plugin(self, name):
        """
        Used to extend the CVP instance object with more API functions.

        Parameters
        ----------
        name : str
            This method will import the file of this value, for example
            "devices", and then create an instance of the Plugin class, and then
            bind it to this CVP instance

        Returns
        -------
        self
        """
        if not isinstance(name, str):
            raise ValueError(f"Plugin `name` is not a string as expected")

        cls_name = "Plugin" + name.title()
        mod = importlib.import_module(f"{__package__}.{name}")
        cls = getattr(mod, cls_name)

        cls_inst = cls(self)
        setattr(self, name, cls_inst)
        return self

    @staticmethod
    def extracto_notifications(dataset, extract='value'):
        """
        This function extracts (flattens) the dataset notifications payload
        into a key-value dictionary.  The key will be each notification item
        dictionary key.  The value will be determined by the `extract` parameter.

        Parameters
        ----------
        dataset : dict
            API payload that has 'notifications' key

        extract : str ['value', 'key']
            Deteremins which part of the item payload is returned in the resulting dictionary

        Returns
        -------
        dict
        """
        notif_list = dataset['notifications']
        items = dict()
        for notif in notif_list:
            updates = notif['updates']
            for item_id, item_data in updates.items():
                items[item_id] = item_data[extract]

        return items

    def __repr__(self):
        return f"{self.__class__.__name__}: {json.dumps(self.api.about, indent=3)}"
