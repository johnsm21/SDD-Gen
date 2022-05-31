import torch
import torch.nn as nn
import numpy as np
import math
from torch.autograd import Variable

class Embedder(nn.Module):
    def __init__(self, weights):
        super().__init__()
        (vocab_size, vector_size) = np.shape(weights)
        self.embed = nn.Embedding(vocab_size, vector_size)
        self.embed.weight.data.copy_(weights)

    def forward(self, x):
        return self.embed(x)

class PositionalEncoder(nn.Module):
    def __init__(self, d_model, max_seq_len = 80):
        super().__init__()
        self.d_model = d_model

        # create constant 'pe' matrix with values dependant on
        # pos and i
        pe = torch.zeros(max_seq_len, self.d_model)
        for pos in range(max_seq_len):
            for i in range(0, self.d_model, 2):
                pe[pos, i] = \
                math.sin(pos / (10000 ** ((2 * i)/self.d_model)))
                pe[pos, i + 1] = \
                math.cos(pos / (10000 ** ((2 * (i + 1))/self.d_model)))

        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)


    def forward(self, x):
        # make embeddings relatively larger
        x = x * math.sqrt(self.d_model)
        #add constant to embedding
        seq_len = x.size(1)
        x = x + Variable(self.pe[:,:seq_len], \
        requires_grad=False)
        return x
