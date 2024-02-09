import asyncio
import sys
from viam import logging

LOGGER = logging.getLogger(__name__)
sys.path.append("..")

from viam.module.module import Module
from viam.resource.registry import Registry, ResourceCreatorRegistration
from viam.components.generic import Generic

from models import PrusaConnectCameraServer

Registry.register_resource_creator(Generic.SUBTYPE, PrusaConnectCameraServer.MODEL, ResourceCreatorRegistration(PrusaConnectCameraServer.new, PrusaConnectCameraServer.validate_config))

async def main():
    LOGGER.info("Starting camera_snapshot module...")
    module = Module.from_args()

    module.add_model_from_registry(Generic.SUBTYPE, PrusaConnectCameraServer.MODEL)
    await module.start()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise Exception("Need socket path as command line argument")

    asyncio.run(main())