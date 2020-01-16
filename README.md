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

** Important: ** The test makes sure that the system does work. For
speed reasons, a very small neural network is used and applied only to
the top-left corner of the image, therefore the quality of the results
will be of poor quality.

## Models

The model classifier-1.tgc is based on a ResNet-18, with less neurons
per layer than the usual model. It was briefly trained on 12 classes:
Adornment, Antiqua, Bastarda, Book covers and other irrelevant data,
Empty Pages, Fraktur, Griechisch, Hebräisch, Kursiv, Rotunda, Textura,
and Woodcuts - Engravings.

## Heatmap Generation ##
Given a trained model, it is possible to produce heatmaps corresponding
to classification results. Syntax:

```
python3 tools/heatmap.py ocrd_typegroups_classifier/models/classifier.tgc sample.jpg out
```
