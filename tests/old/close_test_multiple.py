#!/usr/bin/python3

import multiprocessing
import threading
import time

from scicamera import Camera, CameraInfo


def run_camera(idx):
    with Camera(idx) as camera:
        camera.start_preview()
        camera.start()
        camera.discard_frames(10)
        camera.stop()


if __name__ == "__main__":
    if CameraInfo.n_cameras() <= 1:
        print("SKIPPED (one camera)")
        quit()

    multiprocessing.set_start_method("spawn")

    print("Test two processes")
    procs = []
    for i in range(2):
        p = multiprocessing.Process(target=run_camera, args=(i,))
        p.start()
        procs += [p]
    for proc in procs:
        proc.join()

    print("Test camera in main process")
    with Camera(0) as camera:
        camera.start_preview()
        camera.start()
        time.sleep(3)
        camera.stop()

    print("Test camera in subprocess")
    p = multiprocessing.Process(target=run_camera, args=(0,))
    p.start()
    p.join()

    print("Test camera in main process and subprocess")
    with Camera(0) as camera:
        camera.start_preview()
        camera.start()
        p = multiprocessing.Process(target=run_camera, args=(1,))
        p.start()
        p.join()
        camera.stop()

    print("Test two threads")
    threads = []
    for i in range(2):
        thread = threading.Thread(target=run_camera, args=(i,), daemon=True)
        thread.start()
        threads += [thread]
    for thread in threads:
        thread.join()

    print("Test camera in main process and thread")
    with Camera(0) as camera:
        camera.start_preview()
        camera.start()
        thread = threading.Thread(target=run_camera, args=(1,), daemon=True)
        thread.start()
        thread.join()
        camera.stop()
