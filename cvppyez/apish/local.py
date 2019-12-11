import subprocess
import json
from io import BytesIO

import jsonlines
from cvppyez.apish.common import APISH


__all__ = ['LocalApish']


class LocalApish(APISH):
    DEFAULT_TIMEOUT = 15

    def __init__(self, log=None, timeout=None):
        super(LocalApish, self).__init__(
            log, opts_driver=dict(
                timeout=timeout or self.DEFAULT_TIMEOUT
            ))

    @staticmethod
    def path_str(path):
        return json.dumps(path)

    def execute(self, cmdopts):
        cmd = [APISH.BIN] + cmdopts
        self.log.info("APISH CALL: %s" % ' '.join(cmd))

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            c_out, c_err = proc.communicate(timeout=self.opts_driver['timeout'])

        except subprocess.TimeoutExpired:
            proc.kill()
            c_out, c_err = proc.communicate()

        if proc.returncode:
            raise RuntimeError('FAIL: %s' % ' '.join(cmd), c_out, c_err)

        return list(jsonlines.Reader(BytesIO(c_out)))

