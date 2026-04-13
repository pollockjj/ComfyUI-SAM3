# ComfyUI-SAM3

ComfyUI integration for Meta's SAM3 (Segment Anything Model 3). Open-vocabulary image and video segmentation using natural language text prompts.

## Installation

This node is not a normal custom-node-only install.

To finish setup, you must run this repo's install script inside your ComfyUI Python environment. The installer is intentionally loud: it prints every action before it runs it, then prints the concrete completion record after each action finishes.

### What the installer does

The install script mutates the host ComfyUI environment in four ways:

1. Installs the Python packages listed in `requirements.txt`
2. Installs three extra wheels outside `requirements.txt`
   - `cc-torch`
   - `torch-generic-nms`
   - `flash-attn`
3. Copies this repo's bundled example assets into your ComfyUI `input/` directory
4. Writes an install receipt that the uninstall tool uses to remove only installer-owned artifacts

The current startup path also re-copies the bundled assets into `input/` when ComfyUI loads the node.

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

<div align="center">
<a href="https://pozzettiandrea.github.io/ComfyUI-SAM3/">
<img src="https://pozzettiandrea.github.io/ComfyUI-SAM3/gallery-preview.png" alt="Workflow Test Gallery" width="800">
</a>
<br>
<b><a href="https://pozzettiandrea.github.io/ComfyUI-SAM3/">View Live Test Gallery →</a></b>
</div>

https://github.com/user-attachments/assets/323df482-1f05-4c69-8681-9bfb4073f766

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
