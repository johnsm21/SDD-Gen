import embedding
import attentionLayer

import torch
import torch.nn as nn
import numpy as np
import copy

# build an encoder layer with one multi-head attention layer and one # feed-forward layer
class EncoderLayer(nn.Module):
    def __init__(self, d_model, heads, dropout = 0.1):
        super().__init__()
        self.norm_1 = attentionLayer.Norm(d_model)
        self.norm_2 = attentionLayer.Norm(d_model)
        self.attn = attentionLayer.MultiHeadAttention(heads, d_model)
        self.ff = attentionLayer.FeedForward(d_model)
        self.dropout_1 = nn.Dropout(dropout)
        self.dropout_2 = nn.Dropout(dropout)

    def forward(self, x, mask):
        x2 = self.norm_1(x)

        x = x + self.dropout_1(self.attn(x2,x2,x2,mask))
        x2 = self.norm_2(x)
        x = x + self.dropout_2(self.ff(x2))
        return x

def get_clones(module, N):
    return nn.ModuleList([copy.deepcopy(module) for i in range(N)])


class Encoder(nn.Module):
    def __init__(self, weights, N, heads, max_seq_len):
        super().__init__()
        (_, d_model) = np.shape(weights)

        self.N = N
        self.max_seq_len = max_seq_len
        self.d_model = d_model
        self.embed = embedding.Embedder(weights)
        self.pe = embedding.PositionalEncoder(d_model, max_seq_len)
        self.layers = get_clones(EncoderLayer(d_model, heads), N)
        self.norm = attentionLayer.Norm(d_model)

        self.out = nn.Linear(d_model*max_seq_len, d_model)



    def forward(self, src, mask):
        x = self.embed(src)
        x = self.pe(x)
        for i in range(self.N):
            x = self.layers[i](x, mask)

        x = self.norm(x)

        # print('Encoder Output Size:')
        # print(x.size())

        x = x.reshape(-1, self.d_model * self.max_seq_len)
        # print('Resized Encoder Output Size:')
        # print(x.size())

        return self.out(x)
