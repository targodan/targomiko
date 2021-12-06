import os
from typing import Optional

import paramiko as paramiko
from paramiko.sftp_client import SFTPClient

from .command import RemoteCommand


class SSHConnection:
    """
    SSHConnection is a wrapper for a paramiko.SSHClient with sane defaults
    for zero-user-interaction automation.
    """

    def __init__(self, host: str,
                 username: Optional[str], password: Optional[str] = None, key_filename: Optional[str] = None,
                 timeout: Optional[float] = None, auto_add_host_key: bool = True, **kwargs):
        """
        Initializes and connects using paramiko and sane defaults for zero-user-interaction automation.

        :param host: Hostname or IP to connect to.
        :param username: Username used for login.
        :param password: Optional password used for login (if omitted, key_filename must be given).
        :param key_filename: Optional key filename used for login (if omitted, password must be given).
        :param timeout: Optional timeout in seconds for connection.
        :param auto_add_host_key: If True (default), the missing host key policy "AutoAdd" will be used.
        :param kwargs: Additional args passed to paramiko.SSHClient.connect.
        """
        if "allow_agent" not in kwargs:
            # Prevents interaction with the ssh-agent, which is safer.
            kwargs["allow_agent"] = False
        if "look_for_keys" not in kwargs:
            # Prevents looking for keys by default. This is useful in case of automation
            # alongside a fallback password. In this case you typically don't want paramiko
            # to go looking for any old key on your system, which might trigger a password
            # prompt.
            kwargs["look_for_keys"] = False
        if key_filename:
            kwargs["key_filename"] = key_filename
        if password:
            kwargs["password"] = password

        if not key_filename and not password:
            raise ValueError("at least one of key_filename or password must be given")

        self._ssh = paramiko.SSHClient()
        if auto_add_host_key:
            self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._ssh.connect(hostname=host, username=username, timeout=timeout, **kwargs)

    def exec(self, command: str) -> RemoteCommand:
        """
        Executes a command and returns the RemoteCommand object, which will handle IO.
        :param command: The command line to be executed. Note that escaping of arguments may depend on the shell used and is up to the user.
        :return: The RemoteCommand object to handle IO.
        """
        stdin, stdout, stderr = self._ssh.exec_command(command)
        return RemoteCommand(stdin, stdout, stderr)

    def upload_recursive(self, local_dir: str, remote_dir: str):
        """
        Recursively traverses the given local_dir and uploads the entire tree structure with all files
        to the remote_dir.
        :param local_dir: Local path to be uploaded.
        :param remote_dir: Remote path to be uploaded to.
        """
        local_dir = local_dir.rstrip("/")
        remote_dir = remote_dir.rstrip("/")

        with self._ssh.open_sftp() as sftp:
            sftp: SFTPClient
            for path, subdirs, files in os.walk(local_dir):
                subpath = path[len(local_dir):].lstrip("/")
                remotepath = f"{remote_dir}/{subpath}".rstrip("/")

                for subdir in subdirs:
                    try:
                        sftp.mkdir(f"{remotepath}/{subdir}")
                    except:
                        pass
                for file in files:
                    sftp.put(f"{path}/{file}", f"{remotepath}/{file}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """
        Closes the connection.
        """
        self._ssh.close()
