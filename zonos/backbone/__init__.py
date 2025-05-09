BACKBONES = {}

from ._mamba_ssm import MambaSSMZonosBackbone

BACKBONES["mamba_ssm"] = MambaSSMZonosBackbone

from ._torch import TorchZonosBackbone

BACKBONES["torch"] = TorchZonosBackbone
