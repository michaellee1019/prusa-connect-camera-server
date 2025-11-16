from abc import ABC
import json
import requests
import asyncio
import io

from typing import ClassVar, Mapping, Optional, Sequence, Tuple

from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.types import Model
from viam.components.generic import Generic
from viam.resource.easy_resource import EasyResource
from viam.module.module import Module
from google.protobuf import json_format
from viam.components.camera import Camera
from viam.utils import ValueTypes
from viam import logging
from viam.media.utils.pil import viam_to_pil_image

LOGGER = logging.getLogger(__name__)

class PrusaConnectCameraServer(Generic, EasyResource):
    MODEL: ClassVar[Model] = Model.from_string("michaellee1019:prusa_connect:camera_server")

    cameras_config = {}
    cameras: list[Camera] = []

    @classmethod
    def validate_config(
        cls, config: ComponentConfig
    ) -> Tuple[Sequence[str], Sequence[str]]:
        LOGGER.debug("validating config...")
        if "cameras_config" not in config.attributes.fields:
            raise Exception("A cameras_config attribute is required for camera_snapshot component.")
        
        cameras_config = json.loads(json_format.MessageToJson(config.attributes.fields["cameras_config"]))
        camera_names = []
        for camera_name, config in cameras_config.items():
            if 'token' not in config or 'fingerprint' not in config:
                raise Exception("camera '{}' is missing 'token' and/or 'fingerprint' fields".format(camera_name))
            camera_names.append(camera_name)
        return [], camera_names
    
    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        LOGGER.debug("Reconfiguring camera_snapshot...")

        self.cameras = list[Camera]()
        self.cameras_config = json.loads(json_format.MessageToJson(config.attributes.fields["cameras_config"]))
        for camera_name in self.cameras_config.keys():
            camera = dependencies.get(Camera.get_resource_name(camera_name))
            if camera is None:
                LOGGER.error("camera '{}' is missing from dependencies. ".format(camera_name))
            else:
                self.cameras.append(camera)

    async def do_command(
        self,
        command: Mapping[str, ValueTypes],
        *,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Mapping[str, ValueTypes]:
        LOGGER.debug("received do_command '%s'", command)
        if command.get("upload_images") is not None:
            LOGGER.debug("uploading images to prusa...")
            for camera in self.cameras:
                try:
                    viam_image = await camera.get_image()
                    config = self.cameras_config.get(camera.name)

                    # Convert ViamImage to PIL Image
                    pil_image = viam_to_pil_image(viam_image)
                    
                    image_bytes = io.BytesIO()
                    pil_image.save(image_bytes, format='JPEG')

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
            LOGGER.debug("processed {} cameras.".format(len(self.cameras)))
            return {"success": True, "cameras_processed": len(self.cameras)}
        
        return {"success": False, "error": "unknown command"}

if __name__ == "__main__":
    asyncio.run(Module.run_from_registry())