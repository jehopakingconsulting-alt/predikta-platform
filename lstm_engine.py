"""
PREDIKTA — Lightweight LSTM prediction engine (pure NumPy, no TensorFlow/PyTorch).
Captures long-range sequential dependencies in Pick 3/4 digit sequences.

Architecture per position:
  Input  : sequence of last SEQ_LEN draws (digits 0-9, normalized)
  LSTM   : 1 layer, HIDDEN=32 units  (forget/input/cell/output gates)
  Output : Dense(10) + softmax  — probability distribution over digits 0-9

Training: BPTT (backpropagation through time), Adam optimizer, 60 epochs.
Designed to be fast: < 2 s on 400 draws on Render free tier.
"""

import numpy as np
from collections import defaultdict

# ── Hyper-parameters ──────────────────────────────────────────────────────
SEQ_LEN   = 15       # timesteps fed to the LSTM
HIDDEN    = 32       # LSTM hidden units
LR        = 3e-3     # Adam learning rate
EPOCHS    = 60       # training epochs
MIN_DRAWS = 80       # minimum history required to train
POSITIONS = ["d1", "d2", "d3"]        # Pick 3
POSITIONS4 = ["d1", "d2", "d3", "d4"] # Pick 4


# ── Activations ───────────────────────────────────────────────────────────
def _sigmoid(x):
    return np.where(x >= 0, 1 / (1 + np.exp(-np.clip(x, -30, 30))),
                    np.exp(np.clip(x, -30, 30)) / (1 + np.exp(np.clip(x, -30, 30))))

def _tanh(x):
    return np.tanh(np.clip(x, -15, 15))

def _softmax(x):
    e = np.exp(x - x.max())
    return e / e.sum()


# ── Single-layer LSTM ─────────────────────────────────────────────────────
class LSTMModel:
    """
    LSTM (1 layer) + Dense output for one digit position.
    Weights stored as flat numpy arrays; Adam optimizer state maintained.
    """

    def __init__(self, input_size: int = 1, hidden: int = HIDDEN, output_size: int = 10):
        self.H = hidden
        self.I = input_size
        self.O = output_size
        D = input_size + hidden   # combined input dimension

        # Xavier init for all gate weights
        scale = np.sqrt(2.0 / (D + hidden))
        self.Wf = np.random.randn(D, hidden) * scale
        self.Wi = np.random.randn(D, hidden) * scale
        self.Wg = np.random.randn(D, hidden) * scale
        self.Wo = np.random.randn(D, hidden) * scale
        self.bf = np.zeros(hidden)
        self.bi = np.zeros(hidden)
        self.bg = np.zeros(hidden)
        self.bo = np.zeros(hidden)

        # Output layer
        self.Wy = np.random.randn(hidden, output_size) * np.sqrt(2.0 / (hidden + output_size))
        self.by = np.zeros(output_size)

        # Adam state
        self._params = ['Wf','Wi','Wg','Wo','bf','bi','bg','bo','Wy','by']
        self._m = {k: np.zeros_like(getattr(self, k)) for k in self._params}
        self._v = {k: np.zeros_like(getattr(self, k)) for k in self._params}
        self._t = 0

    def _forward_step(self, x, h, c):
        """One LSTM cell step. x: (input_size,), h/c: (hidden,)"""
        z = np.concatenate([x, h])          # (D,)
        f = _sigmoid(z @ self.Wf + self.bf)
        i = _sigmoid(z @ self.Wi + self.bi)
        g = _tanh(z @ self.Wg + self.bg)
        o = _sigmoid(z @ self.Wo + self.bo)
        c_new = f * c + i * g
        h_new = o * _tanh(c_new)
        return h_new, c_new, (z, f, i, g, o, c, c_new, h_new)

    def forward(self, seq):
        """
        Full forward pass over a sequence.
        seq: (T, input_size) → returns (T, output_size) logits and cache.
        """
        T = len(seq)
        h = np.zeros(self.H)
        c = np.zeros(self.H)
        caches = []
        logits = []

        for t in range(T):
            h, c, cache = self._forward_step(seq[t], h, c)
            logit = h @ self.Wy + self.by
            logits.append(logit)
            caches.append(cache)

        return np.array(logits), caches, h

    def _bptt(self, seq, target: int):
        """
        BPTT for one sequence — many-to-one: loss computed only at last timestep.
        seq: (T, input_size)
        target: int digit label for the next draw
        Returns: (loss, grads dict)
        """
        T = len(seq)
        logits, caches, _ = self.forward(seq)

        grads = {k: np.zeros_like(getattr(self, k)) for k in self._params}

        dh_next = np.zeros(self.H)
        dc_next = np.zeros(self.H)

        for t in reversed(range(T)):
            z, f, i, g, o, c_prev, c_cur, h_cur = caches[t]

            if t == T - 1:
                # Loss only at last step (predict next draw)
                y_pred = _softmax(logits[t])
                y_true = np.zeros(self.O)
                y_true[target] = 1.0
                dy = y_pred - y_true
                loss = -np.log(np.clip(y_pred[target], 1e-9, 1.0))
                grads['Wy'] += np.outer(h_cur, dy)
                grads['by'] += dy
                dh = self.Wy @ dy + dh_next
            else:
                dh = dh_next

            # LSTM cell gradients
            tanh_c = _tanh(c_cur)
            do = dh * tanh_c
            dc = dh * o * (1 - tanh_c ** 2) + dc_next

            dg = dc * i * (1 - g ** 2)
            di = dc * g * i * (1 - i)
            df = dc * c_prev * f * (1 - f)
            dc_next = dc * f

            for name, dgate in [('Wf', df), ('Wi', di), ('Wg', dg), ('Wo', do)]:
                grads[name] += np.outer(z, dgate)
            for name, dgate in [('bf', df), ('bi', di), ('bg', dg), ('bo', do)]:
                grads[name] += dgate

            dh_next = (self.Wf @ df + self.Wi @ di + self.Wg @ dg + self.Wo @ do)[self.I:]

        for k in grads:
            np.clip(grads[k], -5, 5, out=grads[k])

        return loss, grads

    def _adam_step(self, grads, lr=LR, beta1=0.9, beta2=0.999, eps=1e-8):
        self._t += 1
        for k in self._params:
            g = grads[k]
            self._m[k] = beta1 * self._m[k] + (1 - beta1) * g
            self._v[k] = beta2 * self._v[k] + (1 - beta2) * g ** 2
            m_hat = self._m[k] / (1 - beta1 ** self._t)
            v_hat = self._v[k] / (1 - beta2 ** self._t)
            param = getattr(self, k)
            param -= lr * m_hat / (np.sqrt(v_hat) + eps)

    def train(self, X, y, epochs=EPOCHS, lr=LR):
        """
        Train on sequences.
        X: list of (T, input_size) arrays
        y: list of int scalar targets (one per sequence)
        """
        indices = list(range(len(X)))
        for epoch in range(epochs):
            np.random.shuffle(indices)
            for idx in indices:
                loss, grads = self._bptt(X[idx], int(y[idx]))
                self._adam_step(grads, lr=lr)

    def predict_proba(self, seq):
        """Return softmax probability for last timestep."""
        logits, _, _ = self.forward(seq)
        return _softmax(logits[-1])


# ── Feature builder ───────────────────────────────────────────────────────

def _build_sequences(draws: list[dict], position: str, seq_len: int = SEQ_LEN):
    """
    Build (X, y) pairs for one position.
    Each X[i] is a window of seq_len digits (normalized to 0-0.9).
    y[i] is the digit at position i (int 0-9).
    """
    seq = [int(d[position]) for d in reversed(draws)]   # oldest → newest
    X, y = [], []
    for i in range(seq_len, len(seq)):
        window = np.array(seq[i-seq_len:i], dtype=np.float32) / 9.0
        X.append(window.reshape(-1, 1))   # (seq_len, 1)
        y.append(np.array([seq[i]], dtype=np.int32))
    return X, y


# ── Public API ─────────────────────────────────────────────────────────────

def train_and_predict(draws: list[dict], positions: list[str] = None,
                      top_n: int = 15) -> list[dict]:
    """
    Train one LSTM per position on the draw history and return top-N combo
    predictions with LSTM probability scores.

    Returns list of {combo, digits, lstm_score, lstm_prob_pct}.
    Returns [] if not enough draws.
    """
    if positions is None:
        positions = POSITIONS

    if len(draws) < MIN_DRAWS:
        return []

    np.random.seed(42)
    pos_probas = {}   # position → array of shape (10,)

    for pos in positions:
        X, y = _build_sequences(draws, pos)
        if len(X) < 30:
            pos_probas[pos] = np.ones(10) / 10   # uniform fallback
            continue

        # Scalar targets (one per sequence — many-to-one LSTM)
        y_flat = [int(yy[0]) for yy in y]

        model = LSTMModel(input_size=1, hidden=HIDDEN, output_size=10)
        model.train(X, y_flat, epochs=EPOCHS)

        # Predict: use the last SEQ_LEN draws as input
        last_seq = np.array([int(draws[i][pos]) for i in range(SEQ_LEN-1, -1, -1)],
                            dtype=np.float32) / 9.0
        pos_probas[pos] = model.predict_proba(last_seq.reshape(-1, 1))

    # Generate top combos
    if len(positions) == 3:
        p1, p2, p3 = pos_probas["d1"], pos_probas["d2"], pos_probas["d3"]
        # Top-4 per position = 64 candidates — precise enough, very fast
        top4 = [np.argsort(p)[-4:][::-1] for p in [p1, p2, p3]]
        scores = {}
        for a in top4[0]:
            for b in top4[1]:
                for c in top4[2]:
                    scores[(a, b, c)] = float(p1[a] * p2[b] * p3[c])
        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        max_s = top[0][1] if top else 1
        return [
            {
                "combo": f"{c[0]}-{c[1]}-{c[2]}",
                "digits": list(c),
                "lstm_score": round(s * 1000, 4),
                "lstm_prob_pct": round(s / max_s * 100, 2),
            }
            for c, s in top
        ]

    elif len(positions) == 4:
        p1,p2,p3,p4 = (pos_probas[p] for p in ["d1","d2","d3","d4"])
        top4 = [np.argsort(p)[-4:][::-1] for p in [p1, p2, p3, p4]]
        scores = {}
        for a in top4[0]:
            for b in top4[1]:
                for c in top4[2]:
                    for e in top4[3]:
                        scores[(a, b, c, e)] = float(p1[a] * p2[b] * p3[c] * p4[e])
        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        max_s = top[0][1] if top else 1
        return [
            {
                "combo": f"{c[0]}-{c[1]}-{c[2]}-{c[3]}",
                "digits": list(c),
                "lstm_score": round(s * 10000, 4),
                "lstm_prob_pct": round(s / max_s * 100, 2),
            }
            for c, s in top
        ]

    return []


def position_probas(draws: list[dict], positions: list[str] = None) -> dict:
    """
    Return raw LSTM probability distributions per position.
    Useful for integration into larger ensemble systems.
    """
    if positions is None:
        positions = POSITIONS
    if len(draws) < MIN_DRAWS:
        return {pos: {str(d): 0.1 for d in range(10)} for pos in positions}

    np.random.seed(42)
    result = {}

    for pos in positions:
        X, y = _build_sequences(draws, pos)
        if len(X) < 30:
            result[pos] = {str(d): 0.1 for d in range(10)}
            continue

        y_flat = [int(yy[0]) for yy in y]
        model = LSTMModel(input_size=1, hidden=HIDDEN, output_size=10)
        model.train(X, y_flat, epochs=EPOCHS)

        last_seq = np.array([int(draws[i][pos]) for i in range(SEQ_LEN-1, -1, -1)],
                            dtype=np.float32) / 9.0
        proba = model.predict_proba(last_seq.reshape(-1, 1))
        result[pos] = {str(d): round(float(proba[d]), 4) for d in range(10)}

    return result
