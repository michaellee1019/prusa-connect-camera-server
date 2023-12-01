import asyncio
import sys

sys.path.append("..")

from viam.module.module import Module
from viam.resource.registry import Registry, ResourceCreatorRegistration
from viam.components.generic import Generic

from models import PrusaConnectCameraSnapshot

Registry.register_resource_creator(Generic.SUBTYPE, PrusaConnectCameraSnapshot.MODEL, ResourceCreatorRegistration(PrusaConnectCameraSnapshot.new, PrusaConnectCameraSnapshot.validate_config))

async def main():
    module = Module.from_args()

    module.add_model_from_registry(Generic.SUBTYPE, PrusaConnectCameraSnapshot.MODEL)
    await module.start()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise Exception("Need socket path as command line argument")

    asyncio.run(main())