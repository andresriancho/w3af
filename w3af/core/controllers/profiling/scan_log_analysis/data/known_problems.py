def show_known_problems(scan_log_filename, scan):
    """
    This will query the log for some known issues and if those appear show
    alerts in the output.

    :param scan: The file handler for the scan log
    :return: None, all printed to the output
    """
    scan.seek(0)

    #
    #   Identify a problem I rarely see: grep plugin finishes and other plugins
    #   are still running. This seems to be an issue in the teardown process.
    #
    found_grep_teardown = None

    grep_teardown = 'Finished Grep consumer _teardown'
    discover_call = '.discover(uri='

    for line in scan:
        if grep_teardown in line:
            found_grep_teardown = line
            continue

        if discover_call in line and found_grep_teardown:
            print('Known issue found!')
            print('')
            print('The grep consumer was finished at:')
            print('    %s' % found_grep_teardown)
            print('But calls to discover were found after:')
            print('    %s' % line)
            break
