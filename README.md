# SDDGen
Datasets in the wild often have data dictionaries (definitions explaining a column or row within a dataset) associated with them to provide humans with a better understanding of the data. Recently researchers have developed a formal methodology to capture and share this information in a machine-readable way through [Semantic Data Dictionaries](https://tetherless-world.github.io/sdd/)(SDD)[1]. However, to form a SDD a domain expert (medical doctor, scientist) needs to manually map attribute/subjects to ontological terms. This process can be challenging because domain experts are often not ontology experts.

To address this issue our team has created SDDGen a web service that automates the SDD generation process. Provided with a data dictionary and a list of ontologies to form mappings from SDDGen generates an SDD along with the other N-1 most likely mappings for each cell. This allows domain experts to focus on reviewing mappings instead of exploring ontologies for terms which expedites SDD creation.

To form mappings SDDGen uses a transformer network to generate embeddings for ontology class descriptions and data dictionary definitions. Then within this new search space we find which ontology classes align best with SDD properties.

## Requirements
[python 3](https://www.python.org/download/releases/3.0/)
[java 8](https://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html)
[blazegraph](https://www.blazegraph.com/download/)

## Install
``` bash
# Install dependencies
apt-get install unzip
apt-get install python3-venv
apt-get install python3-dev

# Clone Project
git clone https://github.com/johnsm21/SDDGen.git

# Create Virtual environment
cd SDDGen
python3 -m venv env
source env/bin/activate
pip3 install -r requirements.txt

# Copy glove model glove.6B.50d.txt into SDDGen/lib folder
https://drive.google.com/file/d/1Lf3rHNTjb1UFTEM0XeK2djimXQZaYjJO/view?usp=sharing

# Copy transformer model 1000ep.pt into SDDGen/lib folder
https://drive.google.com/file/d/1GdVpDEI7MRJRMng78CmNOKO4yzpQiY7C/view?usp=sharing
```

## Running
``` bash
# Run blazegraph (a copy of RWStore.properties is within SDDGen/lib)
java -server -Xmx4g -Dbigdata.propertyFile=RWStore.properties -jar blazegraph.jar

# Run Server
cd SDDGen
FLASK_APP=main.py flask run

# Break down Virtual environment
deactivate
```
## References
[1] Rashid, Sabbir M., et al. "The Semantic Data Dictionary Approach to Data Annotation & Integration." SemSci@ ISWC. 2017.
