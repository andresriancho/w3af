from utils.output import KeyValueOutput


SQLITE_MAX_REACHED = 'The SQLiteExecutor.in_queue length has reached its max'


def get_dbms_queue_size_exceeded(scan_log_filename, scan):
    scan.seek(0)
    error_count = 0

    for line in scan:
        if SQLITE_MAX_REACHED in line:
            error_count += 1

    return KeyValueOutput('sqlite_limit_reached',
                          'SQLite queue limit reached',
                          error_count)
