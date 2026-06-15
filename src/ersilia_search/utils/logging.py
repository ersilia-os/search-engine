import logging

from rich.logging import RichHandler


SUCCESS_LEVEL_NUM = 25
logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")


class Logger(object):
    """
    A singleton class to manage logging in Ersilia-Search.

    Methods
    -------
    set_verbosity(verbose)
        Set the verbosity of the logger.
    debug(text)
        Log a debug message.
    info(text)
        Log an info message.
    warning(text)
        Log a warning message.
    error(text)
        Log an error message.
    critical(text)
        Log a critical message.
    success(text)
        Log a success message.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(*args, **kwargs)
        return cls._instance

    def _initialize(self):
        self.logger = logging.getLogger("Ersilia-Search")
        self.logger.propagate = False
        self.set_verbosity()
        if not self.logger.hasHandlers():
            handler = RichHandler(rich_tracebacks=True)
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def set_verbosity(self, verbose: bool = False):
        """
        Set the verbosity of the logger.

        Parameters
        ----------
        verbose : bool
            If True, set the logger to DEBUG level. If False, set it to INFO level.
        """
        if verbose:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    def debug(self, text):
        """
        Log a debug message.

        Parameters
        ----------
        text : str
            The message to log.
        """
        self.logger.debug(text)

    def info(self, text):
        """
        Log an info message.

        Parameters
        ----------
        text : str
            The message to log.
        """
        self.logger.info(text)

    def warning(self, text):
        """
        Log a warning message.

        Parameters
        ----------
        text : str
            The message to log.
        """
        self.logger.warning(text)

    def error(self, text):
        """
        Log an error message.

        Parameters
        ----------
        text : str
            The message to log.
        """
        self.logger.error(text)

    def critical(self, text):
        """
        Log a critical message.

        Parameters
        ----------
        text : str
            The message to log.
        """
        self.logger.critical(text)

    def success(self, text):
        """
        Log a success message.

        Parameters
        ----------
        text : str
            The message to log.
        """
        self.logger.log(SUCCESS_LEVEL_NUM, text)


logger = Logger()
