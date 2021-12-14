# Targomiko

A wrapper for paramiko, focused on easy remote command handling of IO, waiting, abortion and exit-code retrieval.

It also brings along sane defaults for zero-user-interaction automation.

## Installing

```commandline
pip install targomiko
```

## Examples

```python
import time
import targomiko

with targomiko.SSHConnection("127.0.0.1", "user", password="password") as ssh:
    ssh.upload_recursive(".", "/opt/targomiko")

    # Do something with the underlying paramiko client
    with ssh.client.open_sftp() as sftp:
        sftp.mkdir("/opt/somedir")

    # Execute command and wait for exit.
    with ssh.exec('/opt/targomiko/entrypoint.sh arg1 "long arg 2"') as cmd:
        cmd.wait()
    print(f"Exit code: {cmd.exit_code}")  # Will output something along the lines of "Exit code: 0"

    # Execute command and abort after 1.5 seconds
    with ssh.exec('/opt/targomiko/entrypoint.sh arg1 "long arg 2"') as cmd:
        try:
            cmd.wait(1.5)
        except TimeoutError:
            print("command timed out")
    # Upon exit of the with, the command is aborted
    print(f"Exit code: {cmd.exit_code}")  # If the timeout was reached, will output "Exit code: -1"

    # Execute command and abort after 1.5 seconds
    with ssh.exec('/opt/targomiko/entrypoint.sh arg1 "long arg 2"') as cmd:
        cmd.stdin.write("helo")
        time.sleep(1)
        # Preliminary output
        print(f"STDOUT: {cmd.stdout}")
        print(f"STDERR: {cmd.stderr}")
        cmd.wait()
    # Final, complete output
    print(f"STDOUT: {cmd.stdout}")
    print(f"STDERR: {cmd.stderr}")
    print(f"Exit code: {cmd.exit_code}")

    # You don't *have to* use a with-statement, but then remember to call close!
    cmd = ssh.exec('/opt/targomiko/entrypoint.sh arg1 "long arg 2"')
    try:
        cmd.wait(1.5)
    except TimeoutError:
        print("command timed out")
    finally:
        cmd.close()
```
