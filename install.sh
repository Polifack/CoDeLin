# create conda virtual enviroment and activate it
conda create -n tree_linearization python=3.8
conda activate tree_linearization

# install required modules
pip install stanza
pip install conllu

echo "[*] All done"