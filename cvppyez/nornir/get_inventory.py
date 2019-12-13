import os
from datetime import datetime
import logging

from nornir import InitNornir

__all__ = ['get_inventory']


def get_inventory(log=None, match_hostname=None):
    """
    This function will use the Nornir to gather the device inventory from CVP.
    The User can provide a hostname based filter to apply to the complete
    inventory so that they can limit the scope of the scan. As a result of this
    processing the `ctx.obj.nr` will be set to the filtered list of devices to
    scan.  The `ctx.obj.nr_all` is the complete CVP inventory.

    Parameters
    ----------
    log : logger
        If provided, will log to this logger; otherwise will use the standard
        nornir logger.

    match_hostname : callable
        If provided, the inventory items will be filtered agaist hostnames that
        match using the provided callable.
    """

    if not log:
        log = logging.getLogger('nornir')

    log.info(f"Gathering CVP inventory from {os.environ['CVP_SERVER']}")
    start_ts = datetime.now()
    nr = InitNornir(
        core={
            'num_workers': 100
        },
        inventory={
            'plugin': 'cvppyez.nornir.CVPInventory'
        }
    )
    end_ts = datetime.now()
    collect_td = end_ts - start_ts

    log.info(f"CVP inventory gather took: {collect_td}")

    nr.inventory.defaults.username = os.environ['CVP_USER']
    nr.inventory.defaults.password = os.environ['CVP_PASSWORD']

    return (nr if not match_hostname
            else nr.filter(filter_func=lambda h: match_hostname(h.name)))
