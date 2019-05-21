import os
import shlex
import signal
import select
import logging

import subprocess32 as subprocess

from w3af.core.controllers.ci.nosetests_wrapper.utils.output import get_run_id
from w3af.core.controllers.ci.nosetests_wrapper.constants import (ARTIFACT_DIR,
                                                                  NOSE_TIMEOUT,
                                                                  NOSE_OUTPUT_PREFIX,
                                                                  NOSE_XUNIT_EXT)


def open_nosetests_output(suffix, first, last):
    name = '%s_%s-%s.%s' % (NOSE_OUTPUT_PREFIX, first, last, suffix)
    path_name = os.path.join(ARTIFACT_DIR, name)
    
    fhandler = file(path_name, 'wb')
    logging.debug('nosetests output file: "%s"' % path_name)
    
    return fhandler


def add_message(message, output_file, stdout):
    output_file.write('%s\n' % message)
    output_file.flush()

    logging.debug(message)

    stdout += '%s\n' % message
    return stdout


def run_nosetests(nose_cmd, first, last):
    """
    Run nosetests and return the output
    
    :param nose_cmd: The nosetests command, with all parameters.
    :return: (stdout, stderr, exit code) 
    """
    logging.debug('Called run_nosetests for %s' % get_run_id(first, last))

    try:
        # Init the outputs
        console = stdout = stderr = ''
        output_file = open_nosetests_output('log', first, last)
        xunit_output = open_nosetests_output(NOSE_XUNIT_EXT, first, last)
    
        # Configure the xunit output before running the command
        nose_cmd %= xunit_output.name
    except Exception as e:
        logging.warning('Failed to initialize run_nosetests: "%s"' % e)
        return

    logging.debug('Starting (%s): "%s"' % (get_run_id(first, last), nose_cmd))

    # Start the nosetests process
    cmd_args = shlex.split(nose_cmd)

    p = subprocess.Popen(
        cmd_args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        universal_newlines=True,
        preexec_fn=os.setsid
    )
    
    # Read output while the process is alive
    idle_time = 0
    select_timeout = 1
    
    while p.poll() is None:
        reads, _, _ = select.select([p.stdout, p.stderr], [], [], select_timeout)
        for r in reads:
            idle_time = 0
            # Write to the output file
            out = r.read(1)
            output_file.write(out)
            output_file.flush()
            console += out
            
            # Write the output to the strings
            if r is p.stdout:
                stdout += out
            else:
                stderr += out
        else:
            idle_time += select_timeout
            if idle_time > NOSE_TIMEOUT:
                # There is a special case which happens with the first call to
                # nose where the tests finish successfully (OK shown) but the
                # nosetests process doesn't end. Handle that case here:
                if console.strip().split('\n')[-1].startswith('OK') and 'Ran ' in console:
                    msg = 'TIMEOUT after success at wrapper (%s)'
                    stdout = add_message(msg % get_run_id(first, last),
                                         output_file,
                                         stdout)

                    # Send the signal to all the process groups
                    os.killpg(p.pid, signal.SIGTERM)
                    p.returncode = 0

                    logging.debug('Process %s killed' % get_run_id(first, last))

                    break

                # Log everywhere I can:
                msg = 'TIMEOUT after error at wrapper (%s)'
                stdout = add_message(msg % get_run_id(first, last),
                                     output_file,
                                     stdout)

                args = (nose_cmd, get_run_id(first, last))
                logging.warning('"%s" (%s) timeout waiting for output.' % args)
                
                # Kill the nosetests command
                # Send the signal to all the process groups
                os.killpg(p.pid, signal.SIGTERM)
                p.returncode = -1

                logging.debug('Process %s killed' % get_run_id(first, last))

                break

    logging.debug('Cleanup for %s' % get_run_id(first, last))

    # Make sure all the output is read, there were cases when the process ended
    # and there were still bytes in stdout/stderr.
    c_stdout, c_stderr = p.communicate()
    stdout += c_stdout
    output_file.write(c_stdout)
    
    stderr += c_stderr
    output_file.write(c_stderr)
    
    # Close the output   
    output_file.close()
    
    logging.debug('Finished (%s): "%s" with code "%s"' % (get_run_id(first, last),
                                                          nose_cmd,
                                                          p.returncode))
    
    return nose_cmd, stdout, stderr, p.returncode, output_file.name