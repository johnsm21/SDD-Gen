# SDD-Gen
Knowledge graphs have become an essential technology for both businesses and governments. They enable a wide variety of critical tasks, such as aligning diverse datasets, improving the capabilities of search engines, supporting error checking, and generating explanations using inference engines. However, populating or augmenting a knowledge graph can be challenging because developers need domain knowledge to understand their data and experience in ontology modeling to align concepts.

To address this issue, our team has created the semantic data dictionary generator (SDD-Gen), a web service that automates the tabular alignment process [1]. SDD-Gen aligns tabular data to ontological terms for knowledge graph generation. Our methodology uses transformer networks to leverage context information from data dictionary descriptions to generate column embeddings that capture each column's upper-level class types. We then compare these embeddings to ontology class embeddings generated using the L1-normalized average word vectors of the class label. All suggested alignments are represented using the [Semantic Data Dictionary](https://tetherless-world.github.io/sdd/)(SDD) format [2].

## Requirements
[python 3.11](https://www.python.org/downloads/release/python-3115/)

## Docker Install
``` bash
docker pull johnsm21/sdd-gen
docker run -p 5000:5000 johnsm21/sdd-gen
```
## GitHub Install
``` bash
# Install dependencies
apt-get install unzip
apt-get install python3-venv
apt-get install python3-dev

# Clone Project
git clone https://github.com/johnsm21/SDD-Gen.git
cd SDD-Gen

# Install python packages and NLP libraries
pip3 install -r lib/requirements.txt
python3 -m nltk.downloader all

# Copy GloVe vectors and transformer model into the SDD-Gen/lib folder
python3 downloadModel.py

# Run Server
python3 app/main.py
```

## References
[1] M. Johnson, J. A. Stingone, S. Bengoa, J. Masters, and D. L. McGuinness, “Complex semantic tabular interpretation using sdd-gen,” in *2024 IEEE 18th International Conference on Semantic Computing (ICSC)*. IEEE, 2024.

[2] S. M. Rashid, K. Chastain, J. A. Stingone, D. L. McGuinness, and J. McCusker, “The semantic data dictionary approach to data annotation & integration.” *SemSci@ ISWC*, vol. 2017, 2017.
