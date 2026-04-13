# ComfyUI-SAM3

ComfyUI integration for Meta's SAM3 (Segment Anything Model 3). Open-vocabulary image and video segmentation using natural language text prompts.

## Installation

This node needs one extra setup step after you add the repo to ComfyUI.

ComfyUI Manager can fetch the repo for you, but SAM3 also needs this repo's `install.py` script to finish setup inside your ComfyUI Python environment.

The installer is intentionally loud. It tells you what it is about to do, then tells you what finished, so you can follow the whole setup as it runs.

### What the installer does

The install script does four things:

1. Installs the Python packages listed in `requirements.txt`
2. Installs three extra wheels outside `requirements.txt`
   - `cc-torch`
   - `torch-generic-nms`
   - `flash-attn`
3. Copies this repo's bundled example assets into your ComfyUI `input/` directory
4. Writes an install receipt that the uninstall tool uses to remove only installer-owned artifacts

Right now, ComfyUI startup also copies those bundled assets back into `input/` when the node loads.

### Install

If you use ComfyUI Manager, treat it as the repo fetch step only. The full SAM3 install still requires this repo's installer:

```bash
COMFY_ROOT=/path/to/ComfyUI /path/to/ComfyUI/.venv/bin/python install.py
```

### Uninstall

This repo includes a matching uninstall tool:

```bash
COMFY_ROOT=/path/to/ComfyUI /path/to/ComfyUI/.venv/bin/python uninstall.py
```

The uninstall tool is also loud. It prints every package removal, file removal, and cleanup step as it runs. It removes the installer-owned packages and the bundled assets it copied into `ComfyUI/input/`, then removes its install receipt.

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
