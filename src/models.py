import json
import requests
import asyncio

from typing import ClassVar, Mapping, Sequence

from typing_extensions import Self

from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.types import Model
from viam.components.generic import Generic
from google.protobuf import json_format
from viam import logging
from viam.components.camera import Camera

from threading import Thread
from threading import Event

LOGGER = logging.getLogger(__name__)

class PrusaConnectCameraSnapshot(Generic):
    MODEL: ClassVar[Model] = Model.from_string("michaellee1019:prusa-connect:camera-server")

    cameras_config = {}
    cameras = list()
    thread = None
    event = Event()

    def thread_run(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.capture_images())

    def start_thread(self):
        self.thread = Thread(target=self.thread_run())
        self.thread.start()

    def stop_thread(self):
        self.event.set()
        self.thread.join()

    @classmethod
    def new(cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]) -> Self:
        LOGGER.info("Starting camera_snapshot...")
        snapshotter = cls(config.name)
        snapshotter.reconfigure(config, dependencies)
        snapshotter.start_thread()
        return snapshotter
    
    async def capture_images(self):
        while True:
            if self.event.is_set():
                break
            for camera in self.cameras:
                try:
                    image = await camera.get_image()
                    config = self.cameras_config.get(camera.name)

                    resp = requests.put(
                        "https://connect.prusa3d.com/c/snapshot",
                        headers={
                            'Token': config['token'],
                            'Fingerprint': config['fingerprint'],
                            "Content-Type": "image/jpg"
                        },
                        data=image.data
                    )
                    if resp.status_code > 299:
                        LOGGER.error("failed to upload image to prusa. status code {}: {}".format(resp.status_code, resp.text))
                except Exception as e:
                    LOGGER.error("failed to upload image to prusa: {}".format(e))
                    continue
                LOGGER.info("processed {} cameras.".format(len(self.cameras)))

            time.sleep(5)

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        if "cameras_config" not in config.attributes.fields:
            raise Exception("A cameras_config attribute is required for camera_snapshot component.")
        
        cameras_config = json.loads(json_format.MessageToJson(config.attributes.fields["cameras_config"]))
        for camera_name, config in cameras_config.items():
            if 'token' not in config or 'fingerprint' not in config:
                raise Exception("camera '{}' is missing 'token' and/or 'fingerprint' fields".format(camera_name))

        return [""]
    
    def reconfigure(self,
                    config: ComponentConfig,
                    dependencies: Mapping[ResourceName, ResourceBase]):
        LOGGER.info("Reconfiguring camera_snapshot...")
        self.stop_thread()

        snapshotter.cameras_config = json.loads(json_format.MessageToJson(config.attributes.fields["cameras_config"]))
        for camera_name in snapshotter.cameras_config.keys():
            camera = dependencies[Camera.get_resource_name(camera_name)]
            if camera is None:
                LOGGER.error("camera '{}' is missing from dependencies. Be sure to add the camera to 'depends_on' field".format(camera))
            else:
                snapshotter.cameras.append(camera)

        self.start_thread()

    def __del__(self):
        LOGGER.info("Stopping camera_snapshot...")
        self.stop_thread()