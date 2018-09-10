#!/usr/bin/env python

import os
import re
import sys
import argparse

try:
    from terminaltables import AsciiTable
except ImportError:
    print('Missing dependency, please run:\n'
          '\n'
          '    pip install terminaltables'
          '\n')
    sys.exit(1)


ROOT_PATH = os.path.realpath(os.path.join(__file__, '../../../../../'))
sys.path.append(ROOT_PATH)

from w3af.core.controllers.core_helpers.status import CoreStatus, Adjustment
from scan_log_analysis import (get_first_timestamp,
                               get_line_epoch,
                               CRAWL_INFRA_FINISHED,
                               JOIN_TIMES)


HELP = '''\
Usage: ./calculate_eta_adjustments.py <scan.log>

This is a command line tool that calculates the ETA adjustments required to
achieve "100% accuracy" when calculating the ETA.

The tool takes a scan log as input, and calculates the ETA adjustment that should
have been used on each call to get_eta() to obtain the correct ETA for that point
in time.

This tool requires a scan log for a finished scan!
'''


CALCULATED_ETA = re.compile('Calculated (.*?) ETA: (.*?) seconds. \(input speed:(.*?),'
                            ' output speed:(.*?), queue size: (.*?), adjustment known: (.*?),'
                            ' adjustment unknown: (.*?), average: (.*?), run time: .*?\)')

CRAWL = 'crawl'
AUDIT = 'audit'
GREP = 'grep'

TABLE_HEADER = ['Timestamp',
                'Phase end',
                'Real ETA',
                'Calculated ETA',
                'Delta',
                'Q(input speed)',
                'Q(output speed)',
                'Q(size)',
                'Adj (known)',
                'Adj (unknown)',
                'Adj (avg)',
                'New adj (known)',
                'New adj (unknown)',
                'Perfect ETA']


class CalculatedETA(object):
    def __init__(self, phase, eta, input_speed, output_speed, queue_size,
                 adjustment_known, adjustment_unknown, adjustment_average,
                 timestamp, phase_end_timestamp):
        self.phase = phase
        self.eta = eta
        self.input_speed = input_speed
        self.output_speed = output_speed
        self.output_speed = output_speed
        self.queue_size = queue_size
        self.adjustment_known = adjustment_known
        self.adjustment_unknown = adjustment_unknown
        self.adjustment_average = adjustment_average
        self.timestamp = timestamp
        self.phase_end_timestamp = phase_end_timestamp

    def calculate_perfect_adjustments(self):
        """
        Calculate the perfect adjustment ratio for this point in time

        :return: Tuple with two floats:
                    * Perfect known adjustment
                    * Perfect unknown adjustment
        """
        perfect_known = 1.0
        perfect_unknown = 1.0

        if self.input_speed >= self.output_speed:
            perfect_unknown = self._calculate_perfect_unknown()
        else:
            perfect_known = self._calculate_perfect_known()

        return perfect_known, perfect_unknown

    def get_delta(self):
        """
        The difference between the ETA calculated during the w3af scan and the
        real one we get from the scan log.

        :return: float
        """
        estimated_phase_end_timestamp = self.timestamp + self.eta
        return self.phase_end_timestamp - estimated_phase_end_timestamp

    def _calculate_perfect_unknown(self):
        # To calculate the perfect adjustment ratio for the unknown scenario
        # We'll have to assume that the known adjustment ratio is 1
        if self.output_speed == 0:
            return 0.33

        t_queued = self.queue_size / self.output_speed * self.adjustment_known
        perfect_eta = self.phase_end_timestamp - self.timestamp

        perfect_ratio = perfect_eta - t_queued / ((self.input_speed * t_queued) / self.output_speed)
        return perfect_ratio

    def _calculate_perfect_known(self):
        # First we calculate the ETA without the adjustment ratio
        eta_no_ratio = self.eta / self.adjustment_known

        #
        # Normally we would multiply like this to calculate the ETA:
        #
        # eta_minutes = eta_minutes * adjustment.known
        #
        # But we do know the exact ETA, so we can use it to calculate the
        # known adjustment:
        #
        perfect_eta = self.phase_end_timestamp - self.timestamp
        perfect_ratio = perfect_eta / eta_no_ratio
        return perfect_ratio


def create_eta_table(scan):
    """
    For each ETA log entry we find in the log we need to add a row to the
    output table which has:

        * Timestamp
        * Phase
        * Queue input speed
        * Queue output speed
        * Queue size
        * Used adjustment known
        * Used adjustment unknown
        * Proposed adjustment known
        * Proposed adjustment unknown

    :param scan: A file pointer to the scan log
    :return: None, the table is printed to the console
    """
    first_timestamp = get_first_timestamp(scan)

    #
    # Find the end times for crawl, audit, grep
    #
    scan.seek(0)

    phase_end_timestamps = {}

    for line in scan:
        if CRAWL_INFRA_FINISHED in line:
            phase_end_timestamps[CRAWL] = get_line_epoch(line) - first_timestamp

        if 'seconds to join' not in line:
            continue

        match = JOIN_TIMES.search(line)
        if match:
            if AUDIT in line.lower():
                phase_end_timestamps[AUDIT] = get_line_epoch(line) - first_timestamp
            if GREP in line.lower():
                phase_end_timestamps[GREP] = get_line_epoch(line) - first_timestamp

    #
    # Find the crawl, audit and grep progress estimations
    #
    scan.seek(0)

    calculated_etas = []

    for line in scan:
        match = CALCULATED_ETA.search(line)
        if not match:
            continue

        timestamp = get_line_epoch(line) - first_timestamp

        eta = match.group(2)
        if eta == 'None':
            eta = '0.0'

        eta = float(eta)

        phase = match.group(1).strip().lower()
        input_speed = float(match.group(3))
        output_speed = float(match.group(4))
        queue_size = int(match.group(5))
        adjustment_known = float(match.group(6))
        adjustment_unknown = float(match.group(7))
        adjustment_average = 'true' in match.group(8).lower()

        if phase not in phase_end_timestamps:
            continue

        phase_end_timestamp = phase_end_timestamps[phase]

        calculated_eta = CalculatedETA(phase,
                                       eta,
                                       input_speed,
                                       output_speed,
                                       queue_size,
                                       adjustment_known,
                                       adjustment_unknown,
                                       adjustment_average,
                                       timestamp,
                                       phase_end_timestamp)

        calculated_etas.append(calculated_eta)

    status = CoreStatus(None, None)
    status.start()

    # Print the tables!
    for phase in (GREP, AUDIT, CRAWL):
        print(phase)
        print('=' * len(phase))
        print('')

        table_data = [TABLE_HEADER]

        for calculated_eta in calculated_etas:
            if calculated_eta.phase != phase:
                continue

            adj_known, adj_unknown = calculated_eta.calculate_perfect_adjustments()

            adjustment = Adjustment(known=adj_known, unknown=adj_unknown)

            recalculated_eta = status.calculate_eta(calculated_eta.input_speed,
                                                    calculated_eta.output_speed,
                                                    calculated_eta.queue_size,
                                                    _type=phase,
                                                    adjustment=adjustment)

            data = [calculated_eta.timestamp,
                    calculated_eta.phase_end_timestamp,
                    calculated_eta.phase_end_timestamp - calculated_eta.timestamp,
                    calculated_eta.eta,
                    calculated_eta.get_delta(),
                    calculated_eta.input_speed,
                    calculated_eta.output_speed,
                    calculated_eta.queue_size,
                    calculated_eta.adjustment_known,
                    calculated_eta.adjustment_unknown,
                    calculated_eta.adjustment_average,
                    #'%.2f' % adj_known,
                    #'%.2f' % adj_unknown,
                    #'%.2f' % recalculated_eta,
                    'TBD',
                    'TBD',
                    'TBD']

            table_data.append(data)

        table = AsciiTable(table_data)
        print(table.table)
        print('')
        print('')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='w3af ETA adjustment calculator', usage=HELP)

    parser.add_argument('scan_log', action='store')
    parsed_args = parser.parse_args()

    try:
        scan = file(parsed_args.scan_log)
    except:
        print('The scan log file does not exist!')
        sys.exit(2)

    create_eta_table(scan)
