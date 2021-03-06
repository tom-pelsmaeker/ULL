"""
Skipgram model in PyTorch.
"""
import torch
from torch import nn
import torch.nn.functional as F


class SkipGram(nn.Module):
    """
    SkipGram model in PyTorch.
    For faster computations, the loss uses the negative sampling softmax approximation. Unavailable contexts should
    be padded in the data, so all contexts have the same size. The pad index will be embedded to zeros, thus won't
    contribute to the loss.
    Input:
    * v_dim: size of the vocabulary.
    * d_dim: size of the embeddings.
    * pad_idx: index used for padding. Default -1.
    """

    def __init__(self, v_dim, d_dim, pad_index):
        super().__init__()

        # Embedding matrices for both context and center words; pad_idx will return 0-vector embeddings.
        self.center_embedding = nn.Embedding(v_dim, d_dim, padding_idx=pad_index, sparse=True)
        self.context_embedding = nn.Embedding(v_dim, d_dim, padding_idx=pad_index, sparse=True)
        self.sparse_params = [p for p in self.parameters()]

    def forward(self, data_in):
        """Compute the positive and negative score of a batch of center words based on context, return them as loss."""
        # Embed; center should be [B], pos_c should be [B x W], neg_c should be [B x K * W]
        center = self.center_embedding(data_in[0])
        pos_c = self.context_embedding(data_in[1])
        neg_c = self.context_embedding(data_in[2])

        # For efficient matrix multiplication with bmm, we add an extra singleton dimension to the center word embeddings
        center = center.unsqueeze(2)

        # Compute scores; score dimension [B]
        # bmm: batch matrix multiply two tensors such that bmm([B x K x D], [B x D x 1]) -> [B, K, 1], effectively
        # computing a row-wise dot product between the rows in the [B x D] embedding matrices.
        pos_scores = F.logsigmoid(torch.bmm(pos_c, center).squeeze()).sum(dim=1)
        neg_scores = F.logsigmoid(torch.bmm(-neg_c, center).squeeze()).sum(dim=1)

        # Directly return the loss, i.e. the negative normalized sum of the positive and negative 'score'
        return -(pos_scores + neg_scores).sum() / pos_scores.shape[0]

    def lst_pass(self, data_in):
        """Return embeddings in a format suited for lst processing."""
        center = self.center_embedding(data_in[0])

        # None is the 'sigma' of these embeddings
        return center, None
