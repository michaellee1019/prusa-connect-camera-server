import json
import requests
import asyncio
import time
import io

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

class PrusaConnectCameraServer(Generic):
    MODEL: ClassVar[Model] = Model.from_string("michaellee1019:prusa_connect:camera_server")

    cameras_config = {}
    cameras = list()
    thread = None
    event = None

    def thread_run(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.capture_images())

    def start_thread(self):
        self.thread = Thread(target=self.thread_run())
        self.event = Event()
        self.thread.start()

    def stop_thread(self):
        if self.thread is not None and self.event is not None:
            self.event.set()
            self.thread.join()

    @classmethod
    def new(cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]) -> Self:
        snapshotter = cls(config.name)
        snapshotter.reconfigure(config, dependencies)
        return snapshotter
    
    async def capture_images(self):
        while True:
            if self.event.is_set():
                return
            for camera in self.cameras:
                try:
                    image = await camera.get_image()
                    config = self.cameras_config.get(camera.name)

                    image_bytes = io.BytesIO()
                    image.save(image_bytes, format='JPEG')

                    resp = requests.put(
                        "https://connect.prusa3d.com/c/snapshot",
                        headers={
                            'Token': config['token'],
                            'Fingerprint': config['fingerprint'],
                            "Content-Type": "image/jpg"
                        },
                        data=image_bytes.getvalue()
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
        LOGGER.info("validating config...")
        # Custom validation can be done by specifiying a validate function like this one. Validate functions
        # can raise errors that will be returned to the parent through gRPC. Validate functions can
        # also return a sequence of strings representing the implicit dependencies of the resource.
        if "cameras_config" not in config.attributes.fields:
            raise Exception("A cameras_config attribute is required for camera_snapshot component.")
        
        cameras_config = json.loads(json_format.MessageToJson(config.attributes.fields["cameras_config"]))
        for camera_name, config in cameras_config.items():
            if 'token' not in config or 'fingerprint' not in config:
                raise Exception("camera '{}' is missing 'token' and/or 'fingerprint' fields".format(camera_name))

        return None
    
    def reconfigure(self,
                    config: ComponentConfig,
                    dependencies: Mapping[ResourceName, ResourceBase]):
        LOGGER.info("Reconfiguring camera_snapshot...")
        self.stop_thread()

        self.cameras = list()
        self.cameras_config = json.loads(json_format.MessageToJson(config.attributes.fields["cameras_config"]))
        for camera_name in self.cameras_config.keys():
            camera = dependencies[Camera.get_resource_name(camera_name)]
            if camera is None:
                LOGGER.error("camera '{}' is missing from dependencies. Be sure to add the camera to 'depends_on' field".format(camera))
            else:
                self.cameras.append(camera)

        self.start_thread()

    def __del__(self):
        LOGGER.info("Stopping camera_snapshot...")
        self.stop_thread()
