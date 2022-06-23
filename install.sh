# create conda virtual enviroment and activate it
echo "[*] Creating Conda VENV"
conda create -n tree_linearization python=3.8
conda activate tree_linearization

# install pytorch
echo "[*] Installing PYTORCH"
conda install pytorch torchvision torchaudio cudatoolkit=11.3 -c pytorch

# install python libraries
echo "[*] Installing Python libraries"
pip install stanza
pip install conllu

echo "[*] All done"