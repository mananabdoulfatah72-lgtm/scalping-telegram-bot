"""Trajectoires de Kronos (github.com/shiyu-coder/Kronos, licence MIT) avec un cache des cles et valeurs d'attention.

Kronos genere une bougie apres l'autre en recalculant toute la fenetre a chaque pas (model/kronos.py,
auto_regressive_inference) : 100 trajectoires de 24 bougies prennent environ 4 minutes par decision sur 4 coeurs. Ici, le
contexte est calcule une seule fois, puis chaque nouvelle bougie ne calcule que sa propre ligne (cache des cles et
valeurs, comme les modeles de langage). Exact tant que contexte + horizon <= 512 (pas de fenetre glissante) : verifie par
`verifier()` contre le code d'origine, memes graines.

Difference voulue avec KronosPredictor.predict : les trajectoires sont rendues une par une (predict en fait la moyenne).
Variables : KRONOS_DIR (le depot Kronos clone), KRONOS_POIDS (dossier des poids telecharges de Hugging Face).
"""
import os
import sys

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, os.environ.get("KRONOS_DIR", "/home/user/etude/Kronos"))
from model import Kronos, KronosTokenizer  # noqa: E402
from model.kronos import auto_regressive_inference, sample_from_logits  # noqa: E402

POIDS = os.environ.get("KRONOS_POIDS", "/home/user/etude/poids")


def charger(modele="Kronos-small", tokenizer="Kronos-Tokenizer-base"):
    tok = KronosTokenizer.from_pretrained(os.path.join(POIDS, tokenizer)).eval()
    mod = Kronos.from_pretrained(os.path.join(POIDS, modele)).eval()
    return tok, mod


def _rope(rot, x, pos):
    t = torch.tensor([float(pos)], dtype=rot.inv_freq.dtype)
    fr = torch.einsum("i,j->ij", t, rot.inv_freq)
    emb = torch.cat((fr, fr), dim=-1)
    return x * emb.cos()[None, None] + rot._rotate_half(x) * emb.sin()[None, None]


@torch.no_grad()
def trajectoires(tok, mod, x, x_stamp, y_stamp, n, pred_len, T=1.0, top_k=0, top_p=0.9, clip=5, graine=None):
    """x : (B, L, 6) deja normalise ; x_stamp : (B, L, 5) ; y_stamp : (B, H, 5). Rend (B, n, H, 6), normalise.
    Memes etapes que auto_regressive_inference avec sample_count=1 sur B x n lignes identiques."""
    if graine is not None:
        torch.manual_seed(graine)
    x = torch.clip(torch.as_tensor(x, dtype=torch.float32), -clip, clip)
    x_stamp = torch.as_tensor(x_stamp, dtype=torch.float32); y_stamp = torch.as_tensor(y_stamp, dtype=torch.float32)
    B, L, _ = x.shape
    assert L + pred_len <= 512, "contexte + horizon > 512 : le cache ne serait plus exact"
    s1, s2 = tok.encode(x, half=True)                               # (B, L) chacun
    # contexte : calcule une fois par decision
    h = mod.embedding([s1, s2]) + mod.time_emb(x_stamp)
    caches = []
    for couche in mod.transformer:
        a = couche.self_attn
        z = couche.norm1(h)
        q = a.q_proj(z).view(B, L, a.n_heads, a.head_dim).transpose(1, 2)
        k = a.k_proj(z).view(B, L, a.n_heads, a.head_dim).transpose(1, 2)
        v = a.v_proj(z).view(B, L, a.n_heads, a.head_dim).transpose(1, 2)
        q, k = a.rotary(q, k)
        o = F.scaled_dot_product_attention(q, k, v, is_causal=True).transpose(1, 2).contiguous().view(B, L, a.d_model)
        h = h + a.out_proj(o)
        h = h + couche.ffn(couche.norm2(h))
        K = torch.empty(B * n, a.n_heads, L + pred_len, a.head_dim); V = torch.empty_like(K)
        K[:, :, :L] = k.repeat_interleave(n, 0); V[:, :, :L] = v.repeat_interleave(n, 0)
        caches.append((K, V))
    fin = mod.norm(h)                                               # (B, L, d)
    dep = mod.dep_layer.cross_attn
    Kd = torch.empty(B * n, dep.n_heads, L + pred_len, dep.head_dim); Vd = torch.empty_like(Kd)
    Kd[:, :, :L] = dep.k_proj(fin).view(B, L, dep.n_heads, dep.head_dim).transpose(1, 2).repeat_interleave(n, 0)
    Vd[:, :, :L] = dep.v_proj(fin).view(B, L, dep.n_heads, dep.head_dim).transpose(1, 2).repeat_interleave(n, 0)
    dernier = fin[:, -1:].repeat_interleave(n, 0)                   # (B n, 1, d)
    ys = y_stamp.repeat_interleave(n, 0)
    gen1 = torch.empty(B * n, pred_len, dtype=s1.dtype); gen2 = torch.empty_like(gen1)
    for i in range(pred_len):
        T_ = L + i                                                  # positions deja calculees
        p1 = sample_from_logits(mod.head(dernier)[:, -1, :], temperature=T, top_k=top_k, top_p=top_p, sample_logits=True)
        # s2 : attention croisee de la bougie tiree sur toutes les positions (rotation a la position 0 = identite)
        sib = mod.embedding.emb_s1(p1)
        q = dep.q_proj(sib).view(B * n, 1, dep.n_heads, dep.head_dim).transpose(1, 2)
        o = F.scaled_dot_product_attention(q, Kd[:, :, :T_], Vd[:, :, :T_]).transpose(1, 2).contiguous().view(B * n, 1, dep.d_model)
        x2 = mod.dep_layer.norm(dernier + dep.out_proj(o))
        p2 = sample_from_logits(mod.head.cond_forward(x2)[:, -1, :], temperature=T, top_k=top_k, top_p=top_p, sample_logits=True)
        gen1[:, i] = p1.squeeze(-1); gen2[:, i] = p2.squeeze(-1)
        if i == pred_len - 1:
            break
        # la nouvelle bougie, a la position T_
        h = mod.embedding([p1, p2]) + mod.time_emb(ys[:, i:i + 1])
        for couche, (K, V) in zip(mod.transformer, caches):
            a = couche.self_attn
            z = couche.norm1(h)
            q = _rope(a.rotary, a.q_proj(z).view(B * n, 1, a.n_heads, a.head_dim).transpose(1, 2), T_)
            K[:, :, T_:T_ + 1] = _rope(a.rotary, a.k_proj(z).view(B * n, 1, a.n_heads, a.head_dim).transpose(1, 2), T_)
            V[:, :, T_:T_ + 1] = a.v_proj(z).view(B * n, 1, a.n_heads, a.head_dim).transpose(1, 2)
            o = F.scaled_dot_product_attention(q, K[:, :, :T_ + 1], V[:, :, :T_ + 1]).transpose(1, 2).contiguous().view(B * n, 1, a.d_model)
            h = h + a.out_proj(o)
            h = h + couche.ffn(couche.norm2(h))
        dernier = mod.norm(h)
        Kd[:, :, T_:T_ + 1] = dep.k_proj(dernier).view(B * n, 1, dep.n_heads, dep.head_dim).transpose(1, 2)
        Vd[:, :, T_:T_ + 1] = dep.v_proj(dernier).view(B * n, 1, dep.n_heads, dep.head_dim).transpose(1, 2)
    tout1 = torch.cat([s1.repeat_interleave(n, 0), gen1], 1); tout2 = torch.cat([s2.repeat_interleave(n, 0), gen2], 1)
    z = tok.decode([tout1, tout2], half=True)                       # comme le code d'origine : toute la sequence
    return z[:, -pred_len:, :].reshape(B, n, pred_len, -1).numpy()


@torch.no_grad()
def verifier(tok, mod, L=488, H=6, n=4, graine=7):
    """Compare au code d'origine (memes entrees, memes graines) : ecart maximal entre les trajectoires."""
    rng = np.random.default_rng(graine)
    x = rng.standard_normal((1, L, 6)).astype(np.float32)
    st = np.zeros((1, L + H, 5), np.float32)
    st[0, :, 0] = np.arange(L + H) % 60; st[0, :, 1] = 9 + (np.arange(L + H) // 12) % 7; st[0, :, 2] = 2; st[0, :, 3] = 15; st[0, :, 4] = 3
    torch.manual_seed(graine)
    ref = auto_regressive_inference(tok, mod, torch.from_numpy(np.repeat(x, n, 0)), torch.from_numpy(np.repeat(st[:, :L], n, 0)),
                                    torch.from_numpy(np.repeat(st[:, L:], n, 0)), 512, H, 5, 1.0, 0, 0.9, 1)[:, -H:, :]
    nous = trajectoires(tok, mod, x, st[:, :L], st[:, L:], n, H, graine=graine)[0]
    return float(np.abs(ref - nous).max())
