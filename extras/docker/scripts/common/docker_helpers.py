import subprocess
import json
import time
import sys
import os

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
DOCKER_RUN = ('docker run'
              ' -d'
              ' -v ~/.w3af:/root/.w3af'
              ' -v ~/w3af-shared:/root/w3af-shared'
              ' -p 44444:44444'
              ' andresriancho/w3af')


def start_container(tag, command=DOCKER_RUN):
    """
    Start a new w3af container so we can connect using SSH and run w3af

    :return: The container id we just started
    """

    if tag is not None:
        docker_run = command + ':%s' % tag
    else:
        docker_run = command + ':latest'

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
        cont_data = subprocess.check_output('docker inspect %s' % container_id,
                                            shell=True)
    except subprocess.CalledProcessError:
        print('Failed to inspect container with id %s' % container_id)
        sys.exit(1)

    try:
        ip_address = json.loads(cont_data)[0]['NetworkSettings']['IPAddress']
    except ValueError:
        print('Invalid JSON output from inspect command')
        sys.exit(1)

    ssh_key = os.path.join(ROOT_PATH, 'w3af-docker.prv')

    # git can't store this
    # https://stackoverflow.com/questions/11230171
    os.chmod(ssh_key, 600)

    # Create the SSH connection command
    ssh_cmd = ['ssh', '-i', ssh_key, '-t', '-t', '-oStrictHostKeyChecking=no',
               '-o UserKnownHostsFile=/dev/null',
               '-o LogLevel=quiet']

    # Add the extra ssh flags
    for extra_ssh_flag in extra_ssh_flags:
        ssh_cmd.append(extra_ssh_flag)

    ssh_cmd.append('root@' + ip_address)
    ssh_cmd.append(cmd)

    try:
        subprocess.call(ssh_cmd)
    finally:
        # revert previous chmod to avoid annoying git change
        os.chmod(ssh_key, 436)


def check_root():
    # if not root...kick out
    if not os.geteuid() == 0:
        sys.exit('Only root can run this script')


def restore_file_ownership():
    """
    There are some issues with "sudo w3af_api_docker" (and any other *_docker)
    where we write to the ~/.w3af/ file but we're doing it as root, and then
    the user wants to execute ./w3af_api and this message appears:

    Either the w3af home directory "/home/user/.w3af" or its contents are not
    writable or readable. Please set the correct permissions and ownership.
    This usually happens when running w3af as root using "sudo"

    So we restore the file ownership of all files inside ~/.w3af/ before exit

    :return: True if we were able to apply the changes
    """
    path = os.path.join(os.path.expanduser('~/'), '.w3af')
    if not os.path.exists(path):
        return False

    try:
        # These two are set by sudo, which is the most common way our users
        # will run w3af inside docker: sudo w3af_console_docker
        uid = int(os.getenv('SUDO_UID'))
        gid = int(os.getenv('SUDO_GID'))
    except ValueError:
        # TODO: More things to be implemented here
        return False

    try:
        _chown(path, uid, gid)
    except:
        return False

    return True


def _chown(path, uid, gid):
    """
    Change permissions recursively

    :param path: The path to apply changes to
    :param uid: User id
    :param gid: Group id
    :return: None
    """
    os.chown(path, uid, gid)

    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if os.path.isfile(item_path):
            os.chown(item_path, uid, gid)
        elif os.path.isdir(item_path):
            os.chown(item_path, uid, gid)
            _chown(item_path, uid, gid)
