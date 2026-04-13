# ComfyUI-SAM3

ComfyUI integration for Meta's SAM3 (Segment Anything Model 3). Open-vocabulary image and video segmentation using natural language text prompts.

## Installation

This node does a little more setup than a typical custom node.

After you add the repo to ComfyUI, the first launch will finish setup automatically inside your ComfyUI Python environment.

The installer is intentionally loud. It tells you what it is about to do, then tells you what finished, so you can follow the whole setup as it runs.

### What the installer does

The install script does four things:

1. Installs the Python packages listed in `requirements.txt`
2. Installs three extra prebuilt wheels outside `requirements.txt`
   - `cc-torch`
   - `torch-generic-nms`
   - `flash-attn`
3. Copies this repo's bundled example assets into your ComfyUI `input/` directory
4. Writes an install receipt that the uninstall tool uses to remove only installer-owned artifacts

These are wheel installs, not source builds. Right now the installer pulls them from third-party hosting. ComfyOrg hosting is not live yet.

| Package | ComfyOrg Hosting | 3rd Party Hosting |
|:--|:--|:--|
| `cc-torch` | Not hosted yet | [`cc_torch-0.2+cu130torch2.11-cp312-cp312-manylinux_2_34_x86_64.manylinux_2_35_x86_64.whl`](https://github.com/PozzettiAndrea/cuda-wheels/releases/download/cc_torch-latest/cc_torch-0.2%2Bcu130torch2.11-cp312-cp312-manylinux_2_34_x86_64.manylinux_2_35_x86_64.whl) |
| `torch-generic-nms` | Not hosted yet | [`torch_generic_nms-0.1+cu130torch2.11-cp312-cp312-manylinux_2_34_x86_64.manylinux_2_35_x86_64.whl`](https://github.com/PozzettiAndrea/cuda-wheels/releases/download/torch_generic_nms-latest/torch_generic_nms-0.1%2Bcu130torch2.11-cp312-cp312-manylinux_2_34_x86_64.manylinux_2_35_x86_64.whl) |
| `flash-attn` | Not hosted yet | [`flash_attn-2.8.3+cu130torch2.10-cp312-cp312-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl`](https://github.com/PozzettiAndrea/cuda-wheels/releases/download/flash_attn-latest/flash_attn-2.8.3%2Bcu130torch2.10-cp312-cp312-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl) |

On first launch, ComfyUI runs this setup automatically. Later launches only run it again if something it installed is missing.

### Install

If you want to run setup yourself instead of waiting for first launch, you can still run the installer directly:

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
