# install.py
import subprocess
import sys

commands = [
    "pip install numpy==1.26.4 transformers==4.57.6",
    "pip install git+https://github.com/retico-team/retico-core",
    "pip install git+https://github.com/retico-team/retico-huggingfacelm",
    "pip install git+https://github.com/retico-team/retico-speechbraintts",
    "pip install git+https://github.com/retico-team/retico-whisperasr",
    "pip install torch==2.3.1+cu121 torchaudio==2.3.1+cu121 torchvision==0.18.1+cu121 --index-url https://download.pytorch.org/whl/cu121"
    #"pip install torch==2.3.1 torchaudio==2.3.1 torchvision==0.18.1 --index-url https://download.pytorch.org/whl/cu121" // uncomment for CPU not GPU
]

for cmd in commands:
    print(f"Running: {cmd}")
    subprocess.check_call([sys.executable, "-m"] + cmd.split())