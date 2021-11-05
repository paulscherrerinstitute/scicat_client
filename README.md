# scicat_client

This code provides a simple client for SciCat, a scientific metadata catalogue (https://scicatproject.github.io/).
It provides basic functionalities, as:
* listing of owned datasets
* dump of archived files
* retrive of Scicat tokens

When installed as conda package, there are three commands that are made available:
* `scicat-client`: basic tool to query scicat
* `scicat-verify`: simple tool to verify data archived vs data on-disk, using file sizes information
* `scicat-check` : simple tool to check what data on disk is not present in Scicat archvied data

**At the moment, the client is customized for the needs of PSI:** in case of interest for different features, please open an issue.

# Installation

`scicat_client` can be installed as a conda package:

```bash
conda install -c paulscherrerinstitute scicat_client
```
