from scicamera import Camera, CameraConfig
from scicamera.tuning import find_tuning_algo, load_tuning_file
from scicamera.testing import requires_camera_model

# Here we load up the tuning for the HQ cam and alter the default exposure profile.
# For more information on what can be changed, see chapter 5 in
# https://datasheets.raspberrypi.com/camera/raspberry-pi-camera-guide.pdf

def test_tuning_file():
    tuning = load_tuning_file("imx477.json")
    algo = find_tuning_algo(tuning, "rpi.agc")
    algo["exposure_modes"]["normal"] = {"shutter": [100, 66666], "gain": [1.0, 8.0]}

    with Camera(tuning=tuning) as camera:
        requires_camera_model(camera, "imx477")

        camera.configure(CameraConfig.for_preview(camera))
        camera.start_runloop()
        camera.start()
        camera.discard_frames(2).result()
        camera.stop()
