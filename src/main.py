from abc import ABC
import json
import requests
import asyncio
import io

from typing import ClassVar, Mapping, Optional, Sequence

from typing_extensions import Self

from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.types import Model
from viam.components.generic import Generic
from viam.resource.easy_resource import EasyResource
from viam.module.module import Module
from google.protobuf import json_format
from viam import logging
from viam.components.camera import Camera
from viam.utils import ValueTypes

from threading import Thread
from threading import Event

LOGGER = logging.getLogger(__name__)

class StartStopLoopService(ABC):
    task = None
    event = Event()
    config: ComponentConfig = None
    dependencies: Mapping[ResourceName, ResourceBase] = None
    auto_start = False

    def start(self):
        loop = asyncio.get_event_loop()
        self.task = loop.create_task(self.looper())
        self.event.clear()

    def stop(self):
        self.event.set()
        if self.task is not None:
            self.task.cancel()

    async def looper(self):
        while not self.event.is_set():
            await self.on_loop()
            await asyncio.sleep(0)  # Yield control to the event loop

    @abstractmethod
    async def on_loop(self):
        """Method must be implemented by service implementation."""
        pass

    @classmethod
    def new(
        cls,
        config: ComponentConfig,
        dependencies: Mapping[ResourceName, ResourceBase],
        auto_start=False,
    ) -> Self:
        start_stop_service = cls(config.name)
        start_stop_service.auto_start = auto_start
        start_stop_service.reconfigure(config, dependencies)
        return start_stop_service

    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        LOGGER.info("Reconfiguring")
        self.stop()
        self.config = config
        self.dependencies = dependencies
        if self.auto_start:
            self.start()

    async def do_command(
        self,
        command: Mapping[str, ValueTypes],
        *,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Mapping[str, ValueTypes]:
        LOGGER.info(f"do_command called with: {command}")
        result = {key: False for key in command.keys()}
        for name, args in command.items():
            if name == "start":
                self.start()
                result[name] = True
            if name == "stop":
                self.stop()
                result[name] = True
        return result

    def __del__(self):
        self.stop()

class PrusaConnectCameraServer(Generic, EasyResource, StartStopLoopService):
    MODEL: ClassVar[Model] = Model.from_string("michaellee1019:prusa_connect:camera_server")

    cameras_config = {}
    cameras = list()

    @classmethod
    def new(cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]) -> Self:
        snapshotter = cls(config.name)
        snapshotter.reconfigure(config, dependencies)
        return snapshotter
    
    async def on_loop(self):
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
                    LOGGER.error("failed to upload image to prusa for camera '{}'. status code {}: {}".format(camera.name, resp.status_code, resp.text))
            except Exception as e:
                LOGGER.error("failed to upload image to prusa for camera '{}': {}".format(camera.name,e))
                continue
            LOGGER.info("processed {} cameras.".format(len(self.cameras)))

        await asyncio.sleep(5)

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

        self.cameras = list()
        self.cameras_config = json.loads(json_format.MessageToJson(config.attributes.fields["cameras_config"]))
        for camera_name in self.cameras_config.keys():
            camera = dependencies[Camera.get_resource_name(camera_name)]
            if camera is None:
                LOGGER.error("camera '{}' is missing from dependencies. Be sure to add the camera to 'depends_on' field".format(camera))
            else:
                self.cameras.append(camera)

if __name__ == "__main__":
    asyncio.run(Module.run_from_registry())