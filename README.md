# viam-modular-resources
This repository contains a monolith of [Viam Robotics Modular Resources](https://docs.viam.com/extend/modular-resources/) that I have needed support for in my hobby projects.

## Models included

### michaellee1019:prusa-connect:camera-snapshot
This component provides a bridge a webcamera and PrusaConnect. Use this to easily setup one or more webcams connected to a Raspberry Pi, or other types of boards, and feed snapshots to PrusaConnect.

First, add each camera as a [webcam](https://docs.viam.com/components/camera/webcam/) using Viam. You can also add a [Camera Serial Interface (CSI) camera](https://docs.viam.com/modular-resources/examples/csi/) that is integrated into the Raspberry Pi. I highly recommend using the builder to auto detect your connected cameras and generate the correct configuration.

After adding each camera, add this component to your config. The full example of the relationship between cameras and this component is shown below:

You need to populate two attributes for each camera. First go to the Cameras tab on connect.prusa.com. Click "Add new other camera" and copy the Token value provided into your Viam config as the `token`. Next is the `fingerprint` attribute. This can be any value you'd like between but it has to have at least 16 and maximum of 64 characters. I usually use the associated camera's video path.

Note that names must match throughout the config! The camera components name must match the attributes in camera_snapshot, and camera_snapshot must have each camera in its `depends_on` field.

Example Config
```
{
      "attributes": {
        "video_path": "usb-046d_HD_Pro_Webcam_C920_79AA2B6F-video-index0"
      },
      "depends_on": [],
      "model": "webcam",
      "name": "prusaxl2",
      "namespace": "rdk",
      "type": "camera"
    },
    {
      "attributes": {
        "video_path": "usb-046d_C922_Pro_Stream_Webcam_F684FE8F-video-index0"
      },
      "depends_on": [],
      "model": "webcam",
      "name": "prusaxl1",
      "namespace": "rdk",
      "type": "camera"
    },
    {
      "attributes": {
        "cameras_config": {
          "prusaxl1": {
            "fingerprint": "usb-046d_C922_Pro_Stream_Webcam_F684FE8F-video-index0",
            "token": "<secret from connect.prusa.com>"
          },
          "prusaxl2": {
            "fingerprint": "usb-046d_HD_Pro_Webcam_C920_79AA2B6F-video-index0",
            "token": "<secret from connect.prusa.com>"
          }
        }
      },
      "depends_on": [
        "prusaxl1",
        "prusaxl2"
      ],
      "model": "michaellee1019:prusa-connect:camera-snapshot",
      "name": "prusa-connect",
      "type": "generic"
    }
```

## Development
Read this section if developing within this repository.

### Copy SSH Key
Save yourself some hassle and time. The first time connecting to a robot, run the following to copy the SSH key to your computer. Afterwards you never have to enter the password again.
```
make ssh-keygen target=username@hostname.local
```

### Robot Config
```
"modules": [
    {
      "executable_path": "/viam-modular-resources-build",
      "type": "local",
      "name": "build"
    },
    {
      "executable_path": "/home/username/test.sh",
      "type": "local",
      "name": "test"
    }
  ]
```

## Development Workflow
For a faster development cycle, follow the steps below, except run python directly instead of pyinstaller. This will do some runtime evaluation and return errors. If you get to the point where it warns of missing socket arguments, you have to deploy as a module and follow the full steps below.

```
make development-workflow  target=username@hostname.local
```

### Testing Workflow
Test changes to models by running an unpackaged version of the module on a single robot. This command will copy code onto your robot and make the module ready to start by Viam. This is the fastest option provided to iterate with your code using a real robot to test hardware.

```
make test-workflow target=username@hostname.local
```

The following configuration needs to be added to your Viam robot. It points to the [test.sh](test.sh) file which installs the required dependencies, and then starts the module program. Note that `test-workflow` restarts `viam-server` each time it is ran, which is required to reload any code that has changed in the module.

```
"modules": [
    {
      "executable_path": "/home/username/test.sh",
      "type": "local",
      "name": "test"
    }
  ]
```

### Packaging workflow
The package workflow is used to generate a bundle of your module. It utilizes [pyinstaller](https://pyinstaller.org/en/stable/) to produce a single file containing all dependencies as well as the python runtime. Packaging the module means it can be deployed to any board with a compatible platform without installing any dependencies.

**Note:** Run the Development Workflow at least once, as the process will install all dependencies onto the pi that will be used for packaging.

```
make package-workflow target=username@hostname.local
```

The workflow will copy the bundle into the root directory for you to try running on your robot. Do this to make sure the packaged module works before sharing with others.
```
"modules": [
    {
      "executable_path": "/viam-module",
      "type": "local",
      "name": "packaged"
    }
  ]
``` 

### Upload to Viam
You can upload the packaged moduled to Viam to use on multiple robots within your organization, or can make it public to share with others.
1. Install the Viam CLI 
1. Upload to registry using the CLI
```
viam module upload --version <version> --platform linux/arm64 archive.tar.gz
```