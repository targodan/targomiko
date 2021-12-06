import threading
from typing import Optional

from paramiko.channel import ChannelStdinFile, ChannelFile, ChannelStderrFile


class RemoteCommand:
    """
    RemoteCommand wraps the IO pipes of a paramiko command. It is with-able and
    uses threads to guarantee easy IO. Note that upon exit of the with-statement,
    the RemoteCommand will be aborted if it has not already exit. Use the RemoteCommand.wait
    function to wait for the command exit. Note that if you do not catch the TimeoutError
    within the with-statement, the __exit__ call will cause an abortion of the command.
    """
    def __init__(self, stdin: ChannelStdinFile, stdout: ChannelFile, stderr: ChannelStderrFile):
        self.stdin = stdin
        self._stdout = stdout
        self._stderr = stderr

        self._stdout_buff_lock = threading.Lock()
        self._stdout_buff = ""
        self._stderr_buff_lock = threading.Lock()
        self._stderr_buff = ""

        self._stdout_consumer_ready = threading.Event()
        self._stderr_consumer_ready = threading.Event()

        self._stdout_consumer = threading.Thread(target=self._consume_stdout)
        self._stderr_consumer = threading.Thread(target=self._consume_stderr)
        self._stdout_consumer.start()
        self._stderr_consumer.start()

        self._stdout_consumer_ready.wait()
        self._stderr_consumer_ready.wait()

        self._exit_code: Optional[int] = None
        self._has_exit = threading.Event()
        self._exit_listener = threading.Thread(target=self._wait)
        self._exit_listener.start()

    def _consume_stdout(self):
        try:
            self._stdout_consumer_ready.set()
            while True:
                line = self._stdout.readline()
                if not line:
                    break
                with self._stdout_buff_lock:
                    self._stdout_buff += line
        except:
            return

    def _consume_stderr(self):
        try:
            self._stderr_consumer_ready.set()
            while True:
                line = self._stderr.readline()
                if not line:
                    break
                with self._stderr_buff_lock:
                    self._stderr_buff += line
        except:
            return

    def _wait(self):
        self._exit_code = self._stdout.channel.recv_exit_status()
        self._has_exit.set()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def exit_code(self) -> Optional[int]:
        """
        Returns the exit_code of the command or None if the command is still running.
        In case of a failure or an aborted command, -1 will be returned as paramiko does via
        recv_exit_status.
        :return: Exit code of the command or None if the command is still running.
        """
        if not self._has_exit.is_set():
            return None
        return self._exit_code

    def wait(self, timeout: Optional[float] = None) -> int:
        """
        Waits for the command to exit. Raises a TimeoutError if the timeout is reached
        before the command has exit. The command will not be aborted automatically if this happens.
        :param timeout: Timeout in (fractions of) seconds. Infinity if None.
        :return: The exit code of the process.
        """
        self._has_exit.wait(timeout)
        if self.exit_code is None:
            raise TimeoutError("waiting for command exit timed out")
        return self.exit_code

    @property
    def stdout(self) -> str:
        """
        Returns the asynchronously captured stdout.
        :return: The captured stdout.
        """
        with self._stdout_buff_lock:
            return self._stdout_buff

    @property
    def stderr(self) -> str:
        """
        Returns the asynchronously captured stderr.
        :return:
        """
        with self._stderr_buff_lock:
            return self._stderr_buff

    def close(self):
        """
        Closes the command, aborting it if it has not exit yet.
        """
        if not self.stdin.closed:
            self.stdin.close()
            self.stdin.channel.close()
        if not self._stdout.closed:
            self._stdout.close()
        if not self._stderr.closed:
            self._stderr.close()
        self._stdout_consumer.join()
        self._stderr_consumer.join()
        self._exit_listener.join()
