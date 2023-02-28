from threading import Thread


def make_completed_thread() -> Thread:
    thread = Thread(target=lambda: None, daemon=True)
    thread.start()
    thread.join()
    return thread
