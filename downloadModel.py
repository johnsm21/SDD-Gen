import gdown

# there are other models available at https://drive.google.com/drive/folders/1kwuXBSVQNDNWPJRqIUoXWI6YgJ71cBDe?ths=true

# download Glove model
url = 'https://drive.google.com/uc?id=1FiZUy-nBv-3BbQDReHnR-sszrOX_ih8C'
output = 'lib/glove.6B.50d.pckl'
gdown.download(url, output, quiet=False);

# download transformers
url = 'https://drive.google.com/uc?id=1imYNGCvRv1y5QxSf7VYXzmsX1WoRPKGn'
output = 'lib/attributeSDD_10ke.pt'
gdown.download(url, output, quiet=False);
