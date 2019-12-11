import json
from pathlib import Path
from io import BytesIO

import paramiko
import jsonlines

from cvppyez.apish.common import APISH


class RemoteApish(APISH):

    def __init__(self, hostname, port=22, user=None, password=None, ssh_config=None, log=None):
        super(RemoteApish, self).__init__(log)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        client.load_system_host_keys()

        fp_ssh_config = None

        if not ssh_config:
            default_ssh_config = Path('~/.ssh/config').expanduser()
            if default_ssh_config.exists():
                fp_ssh_config = default_ssh_config
        else:
            fp_ssh_config = Path(ssh_config)
            if not fp_ssh_config.exists():
                raise RuntimeError(f'Given ssh-config file {ssh_config} does not exist')

        if fp_ssh_config:
            ssh_config = paramiko.SSHConfig()
            ssh_config.parse(fp_ssh_config.open())
            found = ssh_config.lookup(hostname)
            user = found.get('user') or user
            hostname = found.get('hostname') or hostname
            port = found.get('port') or port

        connect_args = {}
        if password:
            connect_args['password'] = password

        if port:
            connect_args['port'] = port

        try:
            client.connect(hostname, username=user, **connect_args)

        except Exception as exc:
            raise RuntimeError(f"Unable to connect to {hostname}: {str(exc)}")

        self.client = client

    @staticmethod
    def path_str(path):
        return f"'{json.dumps(path)}'"

    def execute(self, command_options):
        cmd = [APISH.BIN] + command_options
        cmd_str = ' '.join(cmd)
        self.log.info(f"APISH CALL: {cmd_str}")

        c_in, c_out, c_err = self.client.exec_command(cmd_str)

        rc = c_out.channel.recv_exit_status()
        if rc != 0:
            raise RuntimeError(f'command rc={rc}', cmd_str, rc, c_err.read().decode())

        return list(jsonlines.Reader(BytesIO(c_out.read())))
