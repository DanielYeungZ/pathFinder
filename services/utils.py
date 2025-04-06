from config import DEBUG, DETAIL_DEBUG
from colorama import Fore, Style, init


init(autoreset=True)


def logs(message):
    if DEBUG:
        print("\n" + Fore.MAGENTA + str(message) + Style.RESET_ALL + "\n")

    return


def detail_logs(message):
    if DETAIL_DEBUG:
        print("\n" + Fore.GREEN + str(message) + Style.RESET_ALL + "\n")

    return
