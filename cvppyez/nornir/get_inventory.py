import os

from nornir import InitNornir

__all__ = ['get_inventory']


def get_inventory(filter_func=None):
    """
    This function will use the Nornir to gather the device inventory from CVP.
    The User can provide a hostname based filter to apply to the complete
    inventory so that they can limit the scope of the scan. As a result of this
    processing the `ctx.obj.nr` will be set to the filtered list of devices to
    scan.  The `ctx.obj.nr_all` is the complete CVP inventory.

    Parameters
    ----------
    filter_func : callable
        If provided, the inventory items will be filtered
    """

    nr = InitNornir(
        core={
            'num_workers': 100
        },
        inventory={
            'plugin': 'cvppyez.nornir.CVPInventory'
        },
        logging={
            'enabled': False
        }
    )

    nr.inventory.defaults.username = os.environ['CVP_USER']
    nr.inventory.defaults.password = os.environ['CVP_PASSWORD']

    return nr if not filter_func else nr.filter(filter_func=filter_func)
