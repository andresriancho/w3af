from w3af.core.ui.api.db.master import SCANS
from w3af.core.controllers.w3afCore import w3afCore


def get_core_for_scan(scan_id):
    return SCANS.get(scan_id, None)


