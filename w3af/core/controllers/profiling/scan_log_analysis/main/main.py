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


def show_scan_stats(scan_log_filename, scan):
    show_scan_finished_in(scan)

    show_file_sizes(scan_log_filename, scan)

    print('')

    show_errors(scan)

    print('')

    print('Wall time used by threads:')
    show_discovery_time(scan)
    show_audit_time(scan)
    show_grep_time(scan)
    show_output_time(scan)

    show_plugin_time(scan)

    print('')

    show_http_errors(scan)
    show_total_http_requests(scan)
    show_rtt_histo(scan)
    show_timeout(scan)
    show_extended_urllib_error_rate(scan)
    show_connection_pool_wait(scan)
    show_http_requests_over_time(scan)

    print('')

    show_crawling_stats(scan)
    generate_crawl_graph(scan)

    print('')

    show_queue_size_grep(scan)
    show_queue_size_audit(scan)
    show_queue_size_crawl(scan)

    print('')

    show_progress_delta(scan)

    print('')

    show_grep_plugin_performance(scan)

    print('')

    show_parser_errors(scan)
    show_parser_process_memory_limit(scan)

    print('')

    show_worker_pool_size(scan)
    show_active_threads(scan)
    show_consumer_pool_size(scan)

    print('')

    show_consumer_join_times(scan)

    print('')

    show_freeze_locations(scan)

    print('')

    show_known_problems(scan)
