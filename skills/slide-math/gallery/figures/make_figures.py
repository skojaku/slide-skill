"""Build every figure of the gallery deck (one example of each figure type in FIGURES.md).

    cd ~/.claude/skills/slide-math/gallery && python3 figures/make_figures.py

Pure Python (no numpy); needs xelatex and pdftocairo on PATH.
"""

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "figkit"))
from figkit import P, arrow, brace, build, graph, hrule_axis, label, lineplot, node, pin, raw, vecdots, zoom  # noqa: E402

OUT = HERE

LOGITS = [0.5, -0.8, 2.6, 0.2, -1.2, 1.1, -0.3, 0.7, None, -0.6]
LABELS = ["1", "2", "3", "4", "5", "6", "7", "8", r"\cdots", "K"]


def softmax(z):
    zs = [v for v in z if v is not None]
    m = max(zs)
    e = [math.exp(v - m) if v is not None else None for v in z]
    s = sum(v for v in e if v is not None)
    return [v / s if v is not None else None for v in e]


# ---- 1. vector dot plots: logits, probabilities, shifted logits, a one-hot target -------

def vectors():
    build("logits", vecdots(LOGITS, labels=LABELS, highlight=[2], yticks=[-1, 0, 1, 2], unit=30, step=22), outdir=OUT)
    build("probs", vecdots(softmax(LOGITS), labels=LABELS, highlight=[2], yticks=[0, 1], unit=100, step=22, ref=1), outdir=OUT)
    zmax = max(v for v in LOGITS if v is not None)
    shifted = [v - zmax if v is not None else None for v in LOGITS]
    build("shifted", vecdots(shifted, labels=LABELS, highlight=[2], yticks=[-3, -2, -1, 0], unit=26, step=22, ymax=0.3), outdir=OUT)
    onehot = [0, 0, 1, 0, 0, 0, 0, 0, None, 0]
    build("target", vecdots(onehot, labels=LABELS, highlight=[2], yticks=[0, 1], unit=100, step=22, ref=1), outdir=OUT)
    # two small vectors for the margin slide: a clear winner and a near tie
    build("margin-clear", vecdots([-1, 4, 0.5], highlight=[1], yticks=[-1, 0, 1, 2, 3, 4], unit=24, step=40), outdir=OUT)
    build("margin-tied", vecdots([1, 1.5, 0.2], highlight=[1], yticks=[-1, 0, 1, 2, 3, 4], unit=24, step=40, ymin=-1, ymax=4), outdir=OUT)


# ---- 2. flow diagram: one training step -------------------------------------------------

def flow():
    p = softmax(LOGITS)
    st = 28
    parts = []
    # input tokens and the model
    for i in range(8):
        x = 70 + i * 50
        parts.append(node(f"t{i}", (x, 20), "", style="smallbox", w=30, h=30))
        parts.append(arrow((x, 37), (x, 72)))
    parts.append(node("llm", (245, 104), r"\bfseries Model", w=450, h=58))
    # logits and probabilities
    parts.append(arrow((245, 135), (245, 172)))
    parts.append(vecdots(LOGITS, labels=LABELS, highlight=[2], yticks=[-1, 0, 1, 2], unit=30, step=st,
                         origin=(110, 245), name="z"))
    parts.append(label((88, 262), r"logits\\[2\px]$\bm z =$", anchor="east", size="fslabel", extra="align=right"))
    parts.append(arrow((245, 346), (245, 384)))
    parts.append(vecdots(p, labels=LABELS, highlight=[2], yticks=[0, 1], unit=110, step=st,
                         origin=(110, 410), ref=1, name="q"))
    parts.append(label((88, 460), r"probabilities\\[2\px]$\operatorname{softmax}(\bm z) =$", anchor="east",
                       size="fslabel", extra="align=right"))
    # target
    parts.append(vecdots([0, 0, 1, 0, 0, 0, 0, 0, None, 0], labels=LABELS, highlight=[2], yticks=[0, 1], unit=110,
                         step=st, origin=(730, 410), ref=1, name="p"))
    parts.append(label((1045, 460), r"target\\[2\px]$=\bm p$", anchor="west", size="fslabel"))
    # loss and gradient boxes
    parts.append(node("ce", (880, 262), r"cross-entropy\\[6\px]\fslarge$L(\bm z,\bm p)=-\sum_k p_k\log\operatorname{softmax}(\bm z)_k$",
                      w=500, h=96, left=True))
    parts.append(node("gr", (880, 100), r"gradient with respect to a parameter\\[6\px]\fslarge$\dfrac{\partial L}{\partial\theta_i}"
                      r"=\displaystyle\sum_{k=1}^{K}\dfrac{\partial L}{\partial z_k}\dfrac{\partial z_k}{\partial\theta_i}$",
                      w=500, h=120, left=True))
    parts.append(arrow((430, 465), (560, 465), (560, 262), "(ce.west)"))
    parts.append(arrow((880, 386), "(ce.north)"))
    parts.append(arrow("(ce.south)", "(gr.north)"))
    parts.append(arrow("(gr.west)", "(llm.east)", text="parameter update"))
    build("flow", *parts, outdir=OUT)


# ---- 3. number line: float32 spacing near 0 and near 1 --------------------------------------

def numberline():
    s = 520  # px per unit
    ticks = []
    for e in range(-7, 1):  # binade [2^e, 2^(e+1)) with 8 steps each
        lo = 2.0 ** e
        ticks += [lo + j * lo / 8 for j in range(8)]
    ticks = [t for t in ticks if t <= 2] + [2.0]
    parts = [hrule_axis(0, 2.08, 0, ticks, {0: "$0$", 0.25: r"$\tfrac14$", 0.5: r"$\tfrac12$", 1: "$1$", 2: "$2$"},
                        scale=s, tick=22)]
    parts.append(raw(f"\\fill[ink] {P(-4, -6)} rectangle {P(5, 6)};"))
    # a value just above 1 rounds down to 1
    x = 1.03 * s
    parts.append(raw(f"\\fill[ink] {P(x, 0)} circle (6\\px);"))
    parts.append(raw(f"\\draw[arr] {P(x + 2, 18)} to[out=90, in=60, looseness=1.6] {P(s - 4, 22)};"))
    parts.append(node("c0", (200, 82), r"near 0 the grid is finer than near 1", style="tag", extra=r"font=\fsbody, inner xsep=10\px, inner ysep=5\px"))
    parts.append(node("c1", (x + 20, 82), r"a value near 1 is rounded to 1", style="tag", extra=r"font=\fsbody, inner xsep=10\px, inner ysep=5\px"))
    build("float-line", *parts, outdir=OUT)


# ---- 4. data figures: training loss and logit margin, standard vs fixed ----------------------

def training_curves():
    steps = list(range(0, 10001, 10))
    spikes = [1650, 3020, 4470, 5980, 7330, 8550, 9990]
    def loss_std(t):
        if t < spikes[0]:
            return max(3.5 * math.exp(-t / 95), 1.5e-7) + 2e-7
        last = max(s for s in spikes if s <= t)
        dt = t - last
        return 3e-1 * math.exp(-dt / 60) + 3e-3 * math.exp(-dt / 190) + 1.5e-7
    def loss_fix(t):
        return 3.5 * math.exp(-t / 95) + 9e-8 * (1 - 0.35 * t / 10000)
    def rise(t):  # margin while every example is still learnt: fast start, then linear
        return -2.7 + 7.2 * (1 - math.exp(-t / 40)) + 12.1 * min(1.0, t / 1650)
    def m_std(t):
        if t < spikes[0]:
            return rise(t)
        last = max(s for s in spikes if s <= t)
        nxt = min([s for s in spikes if s > t] + [last + 1400])
        dt = t - last
        if dt < 140:
            return 16.6 - 10.6 * dt / 140
        return 6.0 + 10.6 * (dt - 140) / max(nxt - last - 140, 1)
    def m_fix(t):
        return rise(t) + (0.9 * (t - 1650) / 8350 if t > 1650 else 0)
    loss = lineplot(
        [{"x": steps, "y": [loss_std(t) for t in steps], "style": "base"},
         {"x": steps, "y": [loss_fix(t) for t in steps], "style": "new"}],
        w=500, h=170, ymode="log", ymin=1e-8, ymax=8, xmin=0, xmax=10000, ylabel="training loss",
        legend=None,
        extra=r"ytick={1e-7,1e-5,1e-3,1e-1}, scaled x ticks=false, xticklabel style={/pgf/number format/1000 sep={}}",
        after=r"\draw[zoom] (axis cs:2700,4e-8) rectangle (axis cs:3300,1.5);"
              r"\fill[ink] (axis cs:3020,0.3) circle (4.5\px);"
              r"\draw[lead] (axis cs:3020,0.3) -- (axis cs:2200,40) node[note, anchor=east] {loss jumps};"
              r"\node[note, text=sbase, anchor=south east] at (axis cs:9950,1e-3) {standard};"
              r"\node[note, text=snew, anchor=north east] at (axis cs:9950,5e-8) {fixed};")
    build("loss", loss, outdir=OUT)
    margin = lineplot(
        [{"x": steps, "y": [m_std(t) for t in steps], "style": "base"},
         {"x": steps, "y": [m_fix(t) for t in steps], "style": "new"}],
        w=500, h=170, xmin=0, xmax=10000, ymin=-4, ymax=21, xlabel="step", ylabel="mean margin $m$",
        legend=None,
        extra=r"ytick={0,5,10,16.6}, yticklabels={$0$,$5$,$10$,$16.6$}, scaled x ticks=false, xticklabel style={/pgf/number format/1000 sep={}}",
        after=r"\draw[refline] (axis cs:0,16.6) -- (axis cs:10000,16.6);"
              r"\node[note, text=snew, anchor=south east] at (axis cs:9950,17.3) {fixed};"
              r"\node[note, text=sbase, anchor=north east] at (axis cs:9950,4.5) {standard};")
    build("margin", margin, outdir=OUT)


# ---- 5. two small panels: gradient descent and Adam on the same loss --------------------------

def optimizers():
    lr, T = 0.05, 100
    gd1, gd2 = [1.0], [1.0]
    for _ in range(T):
        gd1.append(gd1[-1] - lr * gd1[-1])
        gd2.append(gd2[-1] - lr * 0.01 * gd2[-1])
    b1, b2, eps = 0.9, 0.999, 1e-8
    th = [1.0, 1.0]
    m = [0.0, 0.0]
    v = [0.0, 0.0]
    ad1, ad2 = [1.0], [1.0]
    for t in range(1, T + 1):
        g = [th[0], 0.01 * th[1]]
        for i in range(2):
            m[i] = b1 * m[i] + (1 - b1) * g[i]
            v[i] = b2 * v[i] + (1 - b2) * g[i] ** 2
            mh, vh = m[i] / (1 - b1 ** t), v[i] / (1 - b2 ** t)
            th[i] -= lr * mh / (math.sqrt(vh) + eps)
        ad1.append(th[0])
        ad2.append(th[1])
    xs = list(range(T + 1))
    common = dict(w=250, h=120, xmin=0, xmax=100, ymin=-0.2, ymax=1.08, xlabel="step", legend="north east",
                  extra=r"ytick={0,0.5,1}, legend style={at={(0.97,0.62)}, anchor=east}")
    gd = lineplot([{"x": xs, "y": gd1, "style": "draw=ink", "label": r"$\theta_1$ (gradient $\theta_1$)"},
                   {"x": xs, "y": gd2, "style": "draw=ink, dash pattern=on 6\\px off 4\\px", "label": r"$\theta_2$ (gradient $0.01\theta_2$)"}],
                  title="Gradient descent, learning rate 0.05", ylabel="parameter value", **common)
    build("gd", gd, raw(r"\draw[line width=0.6\px, draw=muted] (plot.south west |- 0,0) ;"), outdir=OUT)
    ad = lineplot([{"x": xs, "y": ad1, "style": "draw=ink", "label": r"$\theta_1$"},
                   {"x": xs, "y": ad2, "style": "draw=ink, dash pattern=on 6\\px off 4\\px", "label": r"$\theta_2$"}],
                  title="Adam, learning rate 0.05", **common)
    build("adam", ad, outdir=OUT)


# ---- 6. line art for the divider slide: softmax paths on the probability simplex ----------------

def art():
    W = 500
    A, B, C = (0, 0), (W, 0), (W / 2, W * math.sqrt(3) / 2)
    def xy(q):
        return (q[0] * A[0] + q[1] * B[0] + q[2] * C[0], q[0] * A[1] + q[1] * B[1] + q[2] * C[1])
    parts = [raw(f"\\draw[draw=muted, line width=1.6\\px] {P(*A)} -- {P(*B)} -- {P(*C)} -- cycle;")]
    for k in range(1, 10):  # barycentric grid
        t = k / 10
        for (u, v) in ((0, 1), (1, 2), (2, 0)):
            a = [0, 0, 0]; b = [0, 0, 0]
            a[u], a[v] = t, 1 - t
            w = 3 - u - v
            b[u], b[w] = t, 1 - t
            parts.append(raw(f"\\draw[draw=muted, line width=0.5\\px] {P(*xy(a))} -- {P(*xy(b))};"))
    for z in ([2.0, 1.0, 0.0], [0.0, 2.2, 0.6], [0.4, 0.0, 2.0], [1.6, 1.5, -0.5], [-0.3, 1.0, 1.1]):
        pts = []
        for j in range(60):
            T = 12 * (0.9 ** j)
            e = [math.exp((v - max(z)) / T) for v in z]
            q = [v / sum(e) for v in e]
            pts.append(xy(q))
        parts.append(raw("\\draw[draw=muted, line width=1.2\\px] " + " -- ".join(P(*p) for p in pts) + ";"))
        for p in pts[::6]:
            parts.append(raw(f"\\fill[muted] {P(*p)} circle (2.6\\px);"))
    build("art", *parts, outdir=OUT)


# ---- 7. a placeholder logo for the header slot (a deck uses its own) -----------------------------

def logo():
    build("logo", raw(f"\\draw[line width=3\\px] {P(0, 0)} rectangle {P(40, 40)};"),
          raw(f"\\node[font=\\fslarge\\bfseries] at {P(20, 20)} {{$\\Sigma$}};"), outdir=OUT)


# ---- 8. network diagram: a small directed graph, the most-visited node in lavender ---------------

def network():
    pos = {1: (0, 120), 2: (0, 0), 3: (110, 60), 4: (230, 120), 5: (230, 0), 6: (330, 60)}
    edges = [(1, 2), (1, 3), (3, 1), (2, 3), (4, 3), (5, 3), (4, 6), (6, 4), (5, 6), (3, 5), (5, 4)]
    build("network", graph(pos, edges, directed=True, highlight=[3]), outdir=OUT)


if __name__ == "__main__":
    vectors()
    flow()
    numberline()
    training_curves()
    optimizers()
    art()
    logo()
    network()
    print("figures written to", OUT)
