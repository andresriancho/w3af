import sys

from data.file_sizes import show_file_sizes
from data.crawl_graph import generate_crawl_graph
from data.errors import show_errors
from data.consumer_join_times import show_consumer_join_times
from data.scan_finished_in import show_scan_finished_in
from data.crawling_stats import show_crawling_stats
from data.http_requests import show_total_http_requests
from data.http_errors import show_http_errors
from data.grep_plugin_performance import show_grep_plugin_performance
from data.known_problems import show_known_problems
from data.freeze_locations import show_freeze_locations
from data.wall_time import (show_audit_time,
                            show_discovery_time,
                            show_grep_time,
                            show_output_time,
                            show_plugin_time)

from graphs.urllib_error_rate import show_extended_urllib_error_rate
from graphs.parser_memory_limit import show_parser_process_memory_limit
from graphs.parser_errors import show_parser_errors
from graphs.active_threads import show_active_threads
from graphs.consumer_pool_size import show_consumer_pool_size
from graphs.worker_pool_size import show_worker_pool_size
from graphs.timeout import show_timeout
from graphs.rtt_histogram import show_rtt_histo
from graphs.progress_delta import show_progress_delta
from graphs.crawl_queue_size import show_queue_size_crawl
from graphs.grep_queue_size import show_queue_size_grep
from graphs.audit_queue_size import show_queue_size_audit
from graphs.connection_pool_wait import show_connection_pool_wait
from graphs.http_requests_over_time import show_http_requests_over_time


def get_console_functions():
    return [
        #show_scan_finished_in,
        show_file_sizes,
        show_errors,
        #show_discovery_time,
        #show_audit_time,
        #show_grep_time,
        #show_output_time,
        #show_plugin_time,
        #show_http_errors,
        #show_total_http_requests,
        #show_rtt_histo,
        #show_timeout,
        #show_extended_urllib_error_rate,
        #show_connection_pool_wait,
        #show_http_requests_over_time,
        show_crawling_stats,
        #generate_crawl_graph,
        #show_queue_size_grep,
        #show_queue_size_audit,
        #show_queue_size_crawl,
        #show_progress_delta,
        #show_grep_plugin_performance,
        #show_parser_errors,
        #show_parser_process_memory_limit,
        #show_worker_pool_size,
        #show_active_threads,
        #show_consumer_pool_size,
        show_consumer_join_times,
        #show_freeze_locations,
        #show_known_problems,
    ]


def generate_console_output(scan_log_filename, scan):
    for _function in get_console_functions():

        output = _function(scan_log_filename, scan)

        if output is None:
            print('%s returned None' % _function.__name__)
            sys.exit(1)

        output.to_console()
