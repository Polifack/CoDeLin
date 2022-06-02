# Tree linearization

### Features

Allows for the linearization of trees using different algorithms and for two formalisms

- Constituent tree
	- Absolute encoding
	- Relative encoding
	- Dynamic encoding
- Dependency tree
	- Absolute encoding
	- Relative encoding
	- POS based encoding
	- Bracket encoding

Also, for bracket encoding in dependency trees can split the tree in two planes using two different algorithms

### Usage

Can be used to encode single files with main.py or to encode a whole training set formed by train/dev/test files and generate the corresponding ncrfpp configuration

Example command to encode single file:
```
$ python3.8 encode.py --time --form CONST --enc ABS --input test.gold --output test.labels
$ python3.8 encode.py --time --form DEPS --enc BRK_2P --planar PROPAGATE --disp --nogold --lang en --input test.gold --output test.labels
```
Example command to decode single file
```
$ python3.8 encode.py --time --form CONST --enc REL --input test.labels --output test.decoded
$ python3.8 decode.py --time --form DEPS --enc ABS --input test.labels --output test.decoded
```
Example command to generate train:
```
python3.8 generate_train.py --form deps --indir ./treebanks/dependencies/UD_Spanish-GSD --outlbl ./labels/dependencies/UD_Spanish-GSD --outcfg ./ncrf_configs/UD_Spanish-GSD --outmodel ./models/UD_Spanish-GSD --config ./default.config
```