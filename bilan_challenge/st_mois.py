import numpy as np
import st_detail as X
from st_option2 import journee
ok = [dd for dd in range(X.nj) if X.complete[dd]]
for lim in (400, 800):
    s = np.array([journee(dd, lim)[0] for dd in ok]); w = np.convolve(s, np.ones(24), "valid")
    p = np.percentile(w, [10, 25, 50, 75, 90])
    print(f"limite {lim} : mois de 24 seances ({len(w)}) : moyenne {w.mean():+,.0f} $ | 10 % des mois sous {p[0]:+,.0f} $ | 25 % sous {p[1]:+,.0f} $ | "
          f"mediane {p[2]:+,.0f} $ | 25 % au-dessus de {p[3]:+,.0f} $ | 10 % au-dessus de {p[4]:+,.0f} $ | perdants {(w<0).mean()*100:.0f} % | "
          f">= +2 000 $ {(w>=2000).mean()*100:.0f} % | >= +6 000 $ {(w>=6000).mean()*100:.1f} % | pire {w.min():+,.0f} $")
    p_ = X.prm(1, lim); p_[12] = 1
    deb = [i for i in range(X.nj) if X.complete[i] and i + 250 <= X.nj]
    R = [X.sim.fenetre(i, 250, p_, 51000.0, 51700.0, *X.ARGS, np.ones(len(X.T), np.bool_), 53550.0, 2500.0, 50100.0, 0) for i in deb]
    iss = np.array([r[0] for r in R]); q = np.array([r[2] for r in R]) + 1
    print(f"   Master Option 2 : retrait en {np.median(q[iss==1]):.0f} seances (mediane) quand il arrive ; perte en {np.median(q[iss==-1]):.0f} seances (mediane) quand il est perdu ; "
          f"perdu dans le 1er mois {((iss==-1)&(q<=22)).mean()*100:.0f} %")
