# ocrd_typegroups_classifier

> Typegroups classifier for OCR

## Installation

### From PyPI

```sh
pip3 install ocrd_typegroup_classifier
```

### From source

If needed, create a virtual environment for Python 3 (it was tested
successfully with Python 3.7), activate it, and install ocrd.

```sh
virtualenv -p python3 ocrd-venv3
source ocrd-venv3/bin/activate
pip3 install ocrd
```

Enter in the folder containing the tool:

```
cd ocrd_typegroups_classifier/
```

Install the module and its dependencies

```
make install
```

Finally, run the test:

```
sh test/test.sh
```

## Models

The model densenet121.tgc is based on a DenseNet with 121 layers, and
is trained on the following 12 classes:

- Antiqua

- Bastarda

- Fraktur

- Gotico-Antiqua

- Greek

- Hebrew

- Italic

- Rotunda

- Schwabacher

- Textura

- other_font

- not_a_font

The confusion matrix obtained with a DenseNet-121 on the pages with a single font from the dataset (see "Training a classifier" below) is:

|                | Antiqua | Bastarda | Fraktur | Got.-Ant. | Greek | Hebrew | Italic | Rotunda | Schwabacher | Textura | Other font | Not a font | Recall |
|----------------|---------|----------|---------|-----------|-------|--------|--------|---------|-------------|---------|------------|------------|--------|
| Antiqua        | 1531    |          | 10      |           |       |        | 5      | 2       |             |         |            | 5          | 98.6%  |
| Bastarda       |         | 286      |         |           |       |        |        | 6       | 10          | 1       |            |            | 94.4   |
| Fraktur        |         |          | 1933    |           |       |        |        | 1       | 5           | 1       |            | 2          | 99.5%  |
| Gotico-Antiqua |         |          |         | 269       |       |        |        |         |             | 1       |            |            | 99.6   |
| Greek          |         |          |         |           | 58    | 1      |        |         |             |         | 1          |            | 96.7%  |
| Hebrew         |         |          |         |           | 1     | 326    |        |         |             |         |            |            | 99.7%  |
| Italic         |         |          | 1       |           |       |        | 187    |         |             |         |            |            | 99.5%  |
| Rotunda        |         |          |         | 9         |       |        |        | 1495    | 5           | 11      |            | 1          | 98.3%  |
| Schwabacher    |         | 16       | 4       |           |       |        |        | 2       | 452         |         |            |            | 95.4%  |
| Textura        |         |          |         | 2         |       |        |        |         |             | 371     |            | 1          | 99.2%  |
| Other font     |         |          |         |           |       |        |        |         |             |         | 288        | 15         | 94.1%  |
| Not a font     | 4       |          | 2       | 2         | 1     |        | 5      | 1       | 7           |         | 4          | 2331       | 98.9%  |
| Precision      | 99.7%   | 94.7%    | 99.1%   | 95.4%     | 96.7% | 99.4%  | 94.9%  | 99.1%   | 94.2%       | 96.4%   | 98.3%      | 99.0%      |        |

## Updating PyTorch
If you update PyTorch, it is possible that the model cannot be loaded
anymore. To solve this issue, proceed as follows.

1) Downgrade to a version of PyTorch which can load the model,

2) Run the following code:

```python
import torch
from ocrd_typegroups_classifier.typegroups_classifier import TypegroupsClassifier
tgc = TypegroupsClassifier.load('ocrd_typegroups_classifier/models/densenet121.tgc')
torch.save(tgc.model.state_dict(), 'model.pt')
```

3) Upgrade to the desired version of PyTorch

4) Run the following code:

```python
import torch
from ocrd_typegroups_classifier.network.densenet import densenet121
from ocrd_typegroups_classifier.typegroups_classifier import TypegroupsClassifier
print('Creating the network')
net = densenet121(num_classes=12)
net.load_state_dict(torch.load('model.pt'))
print('Creating the classifier')
tgc = TypegroupsClassifier(
    {
        'antiqua':0,
        'bastarda':1,
        'fraktur':2,
        'gotico_antiqua':3,
        'greek':4,
        'hebrew':5,
        'italic':6,
        'rotunda':7,
        'schwabacher':8,
        'textura':9,
        'other_font':10,
        'not_a_font':11
    },
    net
)
tgc.save('ocrd_typegroups_classifier/models/densenet121.tgc')
```

5) delete model.mdl

If PyTorch cannot load model.mdl, then you will have to train a new
model from scratch.


## Training a classifier

The data used for training the classifier provided in this repository
is freely available at the following address:

https://doi.org/10.1145/3352631.3352640

The script in tool/create_training_patches.py can be used to extract
a suitable amount of crops to train the network, with data balancing.

The script in tools/train_densenet121.py continues the training of
any existing densenet121.tgc in the models/ folder. If there is none
present, then a new one is created and trained from scratch.

Note that you might have to adapt the paths in these scripts so that
they correspond to where data is in your system.


## Generating activation heatmaps

For investigation purpose, it is possible to produce heatmaps showing
where and how much the network gets activated for specific classes.

You need first to install an additional dependency which is not required
by the OCR-D tool with:

```
pip install tqdm
```

Then, you can run heatmap.py:

```
python3 heatmap.py --layer 9 --image_path sample2.jpg
```

You can specify which layer of the network you are interested in,
between 0 and 11. Best results are to be expected with larger values.
If no layer is specified, then the 11th is used by default.
