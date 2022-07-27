# create conda virtual enviroment and activate it
echo "[*] Creating Conda VENV"
conda create -n tree_linearization python=3.8
conda activate tree_linearization

# install python libraries
echo "[*] Installing Python libraries"
pip install torch==1.7.0 torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu110
pip install allennlp==1.3
pip install transformers==4.0.0
pip install networkx
pip install stanza
pip install conllu

echo "[*] All done"