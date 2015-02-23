import subprocess
import json
import time
import sys
import os

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
DOCKER_RUN = 'docker run -d -v ~/.w3af:/root/.w3af ' \
             '-v ~/w3af-shared:/root/w3af-shared andresriancho/w3af'


def start_container(tag):
    """
    Start a new w3af container so we can connect using SSH and run w3af

    :return: The container id we just started
    """

    if tag is not None:
        docker_run = DOCKER_RUN + ':%s' % tag
    else:
        docker_run = DOCKER_RUN

    try:
        container_id = subprocess.check_output(docker_run, shell=True)
    except subprocess.CalledProcessError, cpe:
        print('w3af container failed to start: "%s"' % cpe)
        sys.exit(1)
    else:
        # Let the container start the ssh daemon
        time.sleep(1)
        return container_id.strip()


def stop_container(container_id):
    """
    Stop a running w3af container
    """
    try:
        subprocess.check_output('docker stop %s' % container_id, shell=True)
    except subprocess.CalledProcessError, cpe:
        print('w3af container failed to stop: "%s"' % cpe)
        sys.exit(1)


def create_volumes():
    """
    Create the directories if they don't exist
    """
    w3af_home = os.path.expanduser('~/.w3af')
    w3af_shared = os.path.expanduser('~/w3af-shared')

    if not os.path.exists(w3af_home):
        os.mkdir(w3af_home)

    if not os.path.exists(w3af_shared):
        os.mkdir(w3af_shared)


def connect_to_container(container_id, cmd, extra_ssh_flags=()):
    """
    Connect to a running container, start one if not running.
    """
    try:
        cont_data = subprocess.check_output('docker inspect %s' % container_id, shell=True)
    except subprocess.CalledProcessError:
        print('Failed to inspect container with id %s' % container_id)
        sys.exit(1)

    try:
        ip_address = json.loads(cont_data)[0]['NetworkSettings']['IPAddress']
    except:
        print('Invalid JSON output from inspect command')
        sys.exit(1)

    ssh_key = os.path.join(ROOT_PATH, 'w3af-docker.prv')

    # Create the SSH connection command
    ssh_cmd = ['ssh', '-i', ssh_key, '-t', '-t', '-oStrictHostKeyChecking=no',
               '-o UserKnownHostsFile=/dev/null',
               '-o LogLevel=quiet']

    # Add the extra ssh flags
    for extra_ssh_flag in extra_ssh_flags:
        ssh_cmd.append(extra_ssh_flag)

    ssh_cmd.append('root@' + ip_address)
    ssh_cmd.append(cmd)

    subprocess.call(ssh_cmd)


def check_root():
    # if not root...kick out
    if not os.geteuid() == 0:
        sys.exit('Only root can run this script')

