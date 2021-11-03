from enum import Enum


class ConsoleColor(Enum):
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'

    def cprint(self, message: str, *args, **kwargs):
        print(self.value + message, *args, **kwargs)


__all__ = [
    'ConsoleColor'
]
