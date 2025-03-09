from config import DEBUG, DETAIL_DEBUG


def logs(message):
    if DEBUG:
        print(message)

    return


def detail_logs(message):
    if DETAIL_DEBUG:
        print(message)

    return
