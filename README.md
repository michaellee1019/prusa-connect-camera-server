# Module michaellee1019:prusa-connect-camera-server
This Viam module provides images for a PrusaConnect enabled printer. Out of the box, Prusa does not support USB camera support that are viewable online. This module can be added to a Raspberry Pi that has multiple cameras attached to it. Each camera is registered on connect.prusa.com. Viam will then capture images and upload them to Prusa, providing images that automatically refresh every 10 seconds.

## Model michaellee1019:prusa_connect:camera_server
This component provides a bridge between a webcamera and PrusaConnect. Use this to easily setup one or more webcams connected to a Raspberry Pi, other types of boards, and feed snapshots to PrusaConnect.

First, add each camera as a [webcam](https://docs.viam.com/components/camera/webcam/) using Viam. You can also add a [Camera Serial Interface (CSI) camera](https://github.com/viam-modules/csi-camera/) that is integrated into the Raspberry Pi. I highly recommend using the Viam machine builder to auto detect your connected cameras and generate the correct configuration.

After adding each camera, add this component to your config. The full example of the relationship between cameras and this component is shown below:

You need to populate two attributes for each camera. First go to the Cameras tab on connect.prusa.com. Click "Add new other camera" and copy the Token value provided into your Viam config as the `token`. Next is the `fingerprint` attribute. This can be any value you'd like between but it has to have at least 16 and maximum of 64 characters. I usually use the associated camera's video path.

Note that names must match throughout the config! The camera components name must match the attributes in camera_snapshot, and camera_snapshot must have each camera in its `depends_on` field.

### Configuration
```json
{
  "cameras_config": {
    "camera_name_1": {
      "fingerprint": "<camera_video_path_1>",
      "token": "<secret from connect.prusa.com>"
    },
    "camera_name_2": {
      "fingerprint": "camera_video_path_2",
      "token": "<secret from connect.prusa.com>"
    }
  }
}
```

### Attributes
The following attributes are available for this model:

| Name                                        | Type     | Inclusion | Description                                                                                                                                                                                                                                |
|---------------------------------------------|----------|-----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------| 
| `cameras_config`                            | object   | Required  | A mapping of camera names to the secrets identifying the camera on connect.prusa.com. The key of the map must match the name of the camera component and the camera component must be in the `depends_on` field. |
| `cameras_config.<camera_name>.fingerprint`  | string   | Required  | A unique identifier for the camera. You can use the video path of the camera, or any other unique identifier. It cannot be changed once this model runs once and the camera is registered on connect.prusa.com.                             |
| `cameras_config.<camera_name>.token`        | string   | Required  | The secret from connect.prusa.com. 

### Full Configuration Example with 2 Cameras
Note: This extended example can be pasted into your Viam config after switching from "Builder" to "JSON" mode.
```json
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
      "model": "michaellee1019:prusa_connect:camera_server",
      "name": "Camera Server",
      "type": "generic"
    }
```
