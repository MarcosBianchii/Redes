class InvalidArgs(Exception):
    def __init__(self, msg: str):
        self._msg = msg

    def __str__(self) -> str:
        return self._msg


class Config:
    def __init__(self, args: list[str], help_msg: str):
        self._verbose = False
        self._host = "127.0.0.1"
        self._port = 12000

        i = 1
        while i < len(args):
            match args[i]:
                case "-h" | "--help":
                    print(help_msg.format(args[0]))
                    exit(0)

                case "-v" | "--verbose":
                    self._verbose = True

                case "-q" | "--quiet":
                    self._verbose = False

                case "-H" | "--host":
                    try:
                        self._host = args[i + 1]
                    except IndexError:
                        raise InvalidArgs("No host was provided")

                case "-p" | "--port":
                    try:
                        self._port = int(args[i + 1])
                    except IndexError:
                        raise InvalidArgs("No port was provided")
                    except ValueError:
                        raise InvalidArgs("The given port is not a number")

            i += 1

    def addr(self) -> tuple[str, int]:
        return self._host, self._port

    def verbose(self) -> bool:
        return self._verbose


SERVER_HELP: str = """
usage : {} [-h] [-v | -q] [-H ADDR] [-p PORT] [-s DIRPATH]

optional arguments:
    -h , --help     show this help message and exit
    -v , --verbose  increase output verbosity
    -q , --quiet    decrease output verbosity
    -H , --host     service IP address
    -p , --port     service port
    -s , --storage  storage dir path
"""


class ServerConfig(Config):
    def __init__(self, args: list[str]):
        super().__init__(args, SERVER_HELP)
        self._storage = "storage"

        i = 1
        while i < len(args):
            if args[i] == "-s" or args[i] == "--storage":
                try:
                    self._storage = args[i + 1]
                except IndexError:
                    raise InvalidArgs("No storage directory was given")

            i += 1

    def storage(self) -> str:
        return self._storage


class ClientConfig(Config):
    def __init__(self, args: list[str], help_msg: str):
        super().__init__(args, help_msg)
        self._name = None

        i = 1
        while i < len(args):
            if args[i] == "-n" or args[i] == "--name":
                try:
                    self._name = args[i + 1]
                except IndexError:
                    raise InvalidArgs("No file name was provided")

            i += 1

        if self._name is None:
            raise InvalidArgs("No file name was provided")

    def name(self) -> str:
        return self._name


UPLOAD_HELP: str = """
usage : {} [-h] [-v | -q] [-H ADDR] [-p PORT] [-s FILEPATH] [-n FILENAME]

optional arguments:
    -h, --help     show this help message and exit
    -v, --verbose  increase output verbosity
    -q, --quiet    decrease output verbosity
    -H, --host     server IP address
    -p, --port     server port
    -s, --src      source file path
    -n, --name     file name
"""


class UploadConfig(ClientConfig):
    def __init__(self, args: list[str]):
        super().__init__(args, UPLOAD_HELP)
        self._src = "."

        i = 1
        while i < len(args):
            if args[i] == "-s" or args[i] == "--src":
                try:
                    self._src = args[i + 1]
                except IndexError:
                    raise InvalidArgs("No src directory was provided")

            i += 1

    def src(self) -> str:
        return self._src


DOWNLOAD_HELP: str = """
usage : {} [-h] [-v | -q] [-H ADDR] [-p PORT] [-d FILEPATH] [-n FILENAME]

optional arguments:
    -h, --help     show this help message and exit
    -v, --verbose  increase output verbosity
    -q, --quiet    decrease output verbosity
    -H, --host     server IP address
    -p, --port     server port
    -d, --dst      destination file path
    -n, --name     file name
"""


class DownloadConfig(ClientConfig):
    def __init__(self, args: list[str]):
        super().__init__(args, DOWNLOAD_HELP)
        self._dst = "."

        i = 1
        while i < len(args):
            if args[i] == "-d" or args[i] == "--dst":
                try:
                    self._dst = args[i + 1]
                except IndexError:
                    raise InvalidArgs("No destination file path was given")

            i += 1

    def dst(self) -> str:
        return self._dst