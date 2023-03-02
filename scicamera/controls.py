from __future__ import annotations

from typing import Set

from libcamera import ControlType, Rectangle, Size


def _framerates_to_durations(framerates):
    if not isinstance(framerates, (tuple, list)):
        framerates = (framerates, framerates)
    return (int(1000000 / framerates[1]), int(1000000 / framerates[0]))


def _durations_to_framerates(durations):
    if durations[0] == durations[1]:
        return 1000000 / durations[0]
    return (1000000 / durations[1], 1000000 / durations[0])


class Controls:
    def __init__(self, camera, controls={}):
        self._camera = camera
        self._controls = []
        self.set_controls(controls)

    def available_control_names(self) -> Set[str]:
        """Returns a set of all available control names"""
        return set(self._camera.camera_ctrl_info.keys())

    def __setattr__(self, name, value):
        if not name.startswith("_"):
            if name not in self.available_control_names():
                raise RuntimeError(f"Control {name} is not advertised by libcamera")
            self._controls.append(name)
        self.__dict__[name] = value

    def __repr__(self):
        return f"<Controls: {self.make_dict()}>"

    def set_controls(self, controls: dict | Controls):
        if isinstance(controls, dict):
            for k, v in controls.items():
                self.__setattr__(k, v)
        elif isinstance(controls, Controls):
            for k in controls._controls:
                v = controls.__dict__[k]
                self.__setattr__(k, v)
        else:
            raise RuntimeError(f"Cannot update controls with {type(controls)} type")

    def get_frame_rate(self) -> float:
        return _durations_to_framerates(self.FrameDurationLimits)

    def set_frame_rate(self, value: float):
        self.FrameDurationLimits = _framerates_to_durations(value)

    def get_libcamera_controls(self) -> dict:
        libcamera_controls = {}
        for k in self._controls:
            v = self.__dict__[k]
            id = self._camera.camera_ctrl_info[k][0]
            if id.type == ControlType.Rectangle:
                v = Rectangle(*v)
            elif id.type == ControlType.Size:
                v = Size(*v)
            libcamera_controls[id] = v
        return libcamera_controls

    def make_dict(self):
        dict_ = {}
        for k in self._controls:
            v = self.__dict__[k]
            dict_[k] = v
        return dict_
