import logging
import select
import tempfile
import subprocess
import shlex

from w3af.core.controllers.ci.nosetests_wrapper.constants import (NOISE,
                                                                  ARTIFACT_DIR,
                                                                  NOSE_TIMEOUT,
                                                                  NOSE_OUTPUT_PREFIX,
                                                                  NOSE_XUNIT_EXT)


def clean_noise(output_string):
    '''
    Removes useless noise from the output
    
    :param output_string: The output string, stdout.
    :return: A sanitized output string
    '''
    for noise in NOISE:
        output_string = output_string.replace(noise + '\n', '')
        output_string = output_string.replace(noise, '')
    
    return output_string

def open_nosetests_output(suffix='.log'):
    prefix = NOSE_OUTPUT_PREFIX
    fhandler = tempfile.NamedTemporaryFile(prefix=prefix,
                                           suffix=suffix,
                                           dir=ARTIFACT_DIR,
                                           delete=False)
    
    logging.debug('nosetests output file: "%s"' % fhandler.name)
    
    return fhandler

def run_nosetests(nose_cmd):
    '''
    Run nosetests and return the output
    
    :param nose_cmd: The nosetests command, with all parameters.
    :return: (stdout, stderr, exit code) 
    '''
    # Init the outputs
    stdout = stderr = ''
    output_file = open_nosetests_output('.log')
    xunit_output = open_nosetests_output(NOSE_XUNIT_EXT)
    
    # Configure the xunit output before running the command
    nose_cmd = nose_cmd % xunit_output.name
    
    cmd_args = shlex.split(nose_cmd)
    
    logging.debug('Starting: "%s"' % nose_cmd)
    
    p = subprocess.Popen(
        cmd_args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        universal_newlines=True
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
            
            # Write the output to the strings
            if r is p.stdout:
                stdout += out
            else:
                stderr += out
        else:
            idle_time += select_timeout
            if idle_time > NOSE_TIMEOUT:
                # Log everywhere I can:
                output_file.write('TIMEOUT\n')
                stdout += 'TIMEOUT\n'
                logging.warning('"%s" timeout waiting for output.' % nose_cmd)
                
                # Kill the nosetests command
                p.terminate()
                p.returncode = -1
                break
    
    # Make sure all the output is read, there were cases when the process ended
    # and there were still bytes in stdout/stderr.
    '''
    out = p.stdout.read()
    stdout += out
    output_file.write(out)
    
    out = p.stderr.read()
    stderr += out
    output_file.write(out)
    '''
    # Close the output   
    output_file.close()
    
    logging.debug('Finished: "%s" with code "%s"' % (nose_cmd, p.returncode))
    
    return nose_cmd, stdout, stderr, p.returncode, output_file.name