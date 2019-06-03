import sys
import json

from data.file_sizes import get_file_sizes
from data.crawl_graph import generate_crawl_graph
from data.errors import get_errors
from data.consumer_join_times import get_consumer_join_times
from data.scan_finished_in import get_scan_finished_in
from data.crawling_stats import get_crawling_stats
from data.bruteforce import get_bruteforce_data
from data.http_requests import get_total_http_requests
from data.http_errors import get_http_errors
from data.not_found_requests import get_not_found_requests
from data.dbms_queue_size_exceeded import get_dbms_queue_size_exceeded
from data.known_problems import get_known_problems
from data.freeze_locations import get_freeze_locations
from data.wall_time import (get_audit_time,
                            get_discovery_time,
                            get_grep_time,
                            get_output_time,
                            get_plugin_time)

from graphs.urllib_error_rate import draw_extended_urllib_error_rate, get_error_rate_data, get_error_rate_summary
from graphs.parser_memory_limit import draw_parser_process_memory_limit, get_parser_process_memory_limit_summary, get_parser_process_memory_limit_data
from graphs.parser_errors import get_parser_errors_data, get_parser_errors_summary, draw_parser_errors
from graphs.active_threads import draw_active_threads, get_active_threads_data
from graphs.consumer_pool_size import draw_consumer_pool_size, get_consumer_pool_size_data
from graphs.worker_pool_size import draw_worker_pool_size, get_worker_pool_size_data
from graphs.timeout import draw_timeout, get_timeout_data
from graphs.rtt_histogram import draw_rtt_histogram, get_rtt_histogram_data
from graphs.rtt import draw_rtt, get_rtt_data
from graphs.should_grep_stats import draw_should_grep, get_should_grep_data
from graphs.not_found_requests import get_not_found_requests_over_time_data, draw_not_found_requests_over_time
from graphs.not_found_cache_rate import get_not_found_cache_rate_data, draw_not_found_cache_rate_over_time
from graphs.progress_delta import show_progress_delta
from graphs.crawl_queue_size import draw_queue_size_crawl, get_queue_size_crawl_data
from graphs.grep_queue_size import draw_queue_size_grep, get_queue_size_grep_data
from graphs.audit_queue_size import draw_queue_size_audit, get_queue_size_audit_data
from graphs.connection_pool_wait import draw_connection_pool_wait, get_time_waited_by_workers, get_connection_pool_wait_data
from graphs.http_requests_over_time import draw_http_requests_over_time, get_http_requests_over_time_data


def get_console_functions():
    return [
        get_scan_finished_in,
        get_file_sizes,
        get_errors,
        get_discovery_time,
        get_audit_time,
        get_grep_time,
        get_output_time,
        get_plugin_time,
        get_http_errors,
        get_total_http_requests,
        draw_rtt_histogram,
        draw_rtt,
        draw_timeout,
        draw_extended_urllib_error_rate,
        get_error_rate_summary,
        get_not_found_requests,
        draw_not_found_requests_over_time,
        draw_not_found_cache_rate_over_time,
        get_time_waited_by_workers,
        draw_connection_pool_wait,
        draw_http_requests_over_time,
        get_crawling_stats,
        #generate_crawl_graph,                  ######
        draw_should_grep,
        draw_queue_size_grep,
        draw_queue_size_audit,
        draw_queue_size_crawl,
        get_dbms_queue_size_exceeded,
        #show_progress_delta,                   ######
        get_bruteforce_data,
        get_parser_errors_summary,
        draw_parser_errors,
        get_parser_process_memory_limit_summary,
        draw_parser_process_memory_limit,
        draw_worker_pool_size,
        draw_active_threads,
        draw_consumer_pool_size,
        get_consumer_join_times,
        get_freeze_locations,
        get_known_problems,
    ]


def get_json_functions():
    return [
        get_scan_finished_in,
        get_file_sizes,
        get_errors,
        get_discovery_time,
        get_audit_time,
        get_grep_time,
        get_output_time,
        get_plugin_time,
        get_http_errors,
        get_total_http_requests,
        get_rtt_histogram_data,
        get_rtt_data,
        get_timeout_data,
        get_error_rate_data,
        get_error_rate_summary,
        get_not_found_requests,
        get_not_found_requests_over_time_data,
        get_not_found_cache_rate_data,
        get_connection_pool_wait_data,
        get_time_waited_by_workers,
        get_http_requests_over_time_data,
        get_crawling_stats,
        #generate_crawl_graph,      ######
        get_should_grep_data,
        get_queue_size_grep_data,
        get_queue_size_audit_data,
        get_queue_size_crawl_data,
        get_dbms_queue_size_exceeded,
        #show_progress_delta,       ######
        get_bruteforce_data,
        get_parser_errors_summary,
        get_parser_errors_data,
        get_parser_process_memory_limit_summary,
        get_parser_process_memory_limit_data,
        get_worker_pool_size_data,
        get_active_threads_data,
        get_consumer_pool_size_data,
        get_consumer_join_times,
        get_freeze_locations,
        get_known_problems,
    ]


def generate_console_output(scan_log_filename, scan):
    for _function in get_console_functions():
        scan.seek(0)

        output = _function(scan_log_filename, scan)

        if output is None:
            if not _function.__name__.startswith('draw_'):
                print('%s returned None' % _function.__name__)
                sys.exit(1)
        else:
            output.to_console()


def generate_json_output(scan_log_filename, scan, json_filename):
    try:
        output_fp = file(json_filename, 'w')
    except Exception, e:
        print('Failed to open %s for writing: "%s"' % e)
        sys.exit(1)

    output_data = dict()
    print('Generating JSON output...')

    for _function in get_json_functions():

        scan.seek(0)
        function_output = _function(scan_log_filename, scan)

        if function_output is None:
            print('%s returned None' % _function.__name__)
            sys.exit(2)

        if hasattr(function_output, 'to_json'):
            output_data.update(function_output.to_json())
        else:
            key = _function.__name__.replace('get_', '')
            output_data[key] = function_output

    json.dump(output_data, output_fp, indent=4, sort_keys=True)
