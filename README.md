# ComfyUI-SAM3

ComfyUI integration for Meta's SAM3 (Segment Anything Model 3). Open-vocabulary image and video segmentation using natural language text prompts.

## Installation if SAM3 Extras Required for this Node Pack to function

This node does a little more setup than a typical custom node.

SAM3 needs two extra libraries to run in vanilla ComfyUI, `cc-torch` and `torch-generic-nms`, plus `flash-attn` as an optional speedup when it is available on your system.

After you add the repo to ComfyUI, the first launch will finish setup automatically inside your ComfyUI Python environment.

The installer tells you what it is about to do, then tells you what finished, so you can follow the whole setup as it runs via the console.

### What the installer does

The install script does three things:

1. Installs these extra prebuilt wheels outside `requirements.txt`:

   | Extra wheel | ComfyOrg Hosting | 3rd Party Hosting |
   |:--|:--|:--|
   | `cc-torch` | [Comfy-Org/wheels `cc_torch-latest`](https://github.com/Comfy-Org/wheels/releases/tag/cc_torch-latest) | [PozzettiAndrea/cuda-wheels `cc_torch-latest`](https://github.com/PozzettiAndrea/cuda-wheels/releases/tag/cc_torch-latest) |
   | `torch-generic-nms` | [Comfy-Org/wheels `torch_generic_nms-latest`](https://github.com/Comfy-Org/wheels/releases/tag/torch_generic_nms-latest) (Coming Soon!) | [PozzettiAndrea/cuda-wheels `torch_generic_nms-latest`](https://github.com/PozzettiAndrea/cuda-wheels/releases/tag/torch_generic_nms-latest) |
   | `flash-attn` | [Comfy-Org/wheels `flash_attn-latest`](https://github.com/Comfy-Org/wheels/releases/tag/flash_attn-latest) (Coming Soon!) | [PozzettiAndrea/cuda-wheels `flash_attn-latest`](https://github.com/PozzettiAndrea/cuda-wheels/releases/tag/flash_attn-latest) |

2. Copies these bundled example files into your ComfyUI `input/` directory:

   | Source file in this repo | Copied to | Removed by `uninstall.py` |
   |:--|:--|:--|
   | `assets/bedroom.mp4` | `ComfyUI/input/bedroom.mp4` | Yes |
   | `assets/example_image.jpg` | `ComfyUI/input/example_image.jpg` | Yes |
   | `assets/groceries.jpg` | `ComfyUI/input/groceries.jpg` | Yes |
   | `assets/image.png` | `ComfyUI/input/image.png` | Yes |
4. Writes an install receipt that the uninstall tool uses to remove only installer-owned artifacts

### Uninstall

If you want to uninstall the extra packages and files SAM3 adds, the uninstaller is in the root of this custom node:

```bash
cd /path/to/ComfyUI/custom_nodes/ComfyUI-SAM3
./uninstall.py
```

The uninstaller prints each removal step as it runs. It removes the three extra wheels, removes the example files listed above from `ComfyUI/input/`, and removes its install receipt.

### Examples

![bbox](docs/bbox.png)

![point](docs/point.png)

![text_prompt](docs/text_prompt.png)

![video](docs/video.png)

https://github.com/user-attachments/assets/57721801-f599-4ef1-8647-13468211ef63

## Credits

- **SAM3**: Meta AI Research (https://github.com/facebookresearch/sam3)
- **ComfyUI Integration**: ComfyUI-SAM3
- **Interactive Points Editor**: Adapted from [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes) by kijai (Apache 2.0 License). The SAM3PointsEditor node is based on the PointsEditor implementation from KJNodes, simplified for SAM3-specific point-based segmentation.
