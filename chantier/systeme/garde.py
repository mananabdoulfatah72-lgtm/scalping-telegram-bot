"""Controle du risque avant chaque ordre, pour un compte Master Bulenox 50K (Option 2) ou un compte personnel.

Aucune dependance : `python3 garde.py` lance les tests du fichier.

    g = Garde()                                   # reglages Bulenox par defaut
    rep = g.verifier(taille=2, risque_par_contrat=300, heure_ny="10:30", jour="2026-11-12")
    if rep.autorise: ...passer rep.taille contrats...   ;   rep.raisons explique chaque refus ou reduction
    g.maj_latent(-250)                            # a chaque variation du gain du jour (realise + latent)
    g.fin_de_journee(gain=-250, a_trade=True)     # a la cloture : solde, plus haut, plancher, compteur d'inactivite
"""
from dataclasses import dataclass, field


def n(x):
    return format(x, ",.0f").replace(",", " ")


@dataclass
class Reponse:
    autorise: bool
    taille: int
    raisons: list = field(default_factory=list)


@dataclass
class Garde:
    solde: float = 50000.0
    depart: float = 50000.0
    perte_max: float = 2500.0            # plancher = plus haut des fins de journee - perte_max, arrete au solde de depart
    limite_firme: float = 1100.0         # limite de perte du jour de Bulenox
    limite_bot: float = 1000.0           # le bot s'arrete avant
    frein: float = 1750.0                # sous cette marge : demi-taille
    taille_max: int = 4                  # MNQ
    jours_fed: frozenset = frozenset()
    inactivite_max: int = 5              # jours de trading sans trade = compte perdu
    baisse_max: float = 0.15             # compte personnel : plus d'ordre si le solde a baisse de 15 % depuis son plus haut
    plus_haut: float = 50000.0           # plus haut des soldes de fin de journee
    sommet: float = 50000.0              # plus haut du solde (pour la limite de baisse en %)
    gain_jour: float = 0.0               # realise + latent de la journee de trading (18 h -> 17 h, nuit comprise)
    jours_sans_trade: int = 0
    arrete: bool = False                 # limite du jour touchee : plus rien jusqu'a demain

    @property
    def plancher(self):
        return min(self.plus_haut - self.perte_max, self.depart)

    @property
    def marge(self):
        return self.solde + self.gain_jour - self.plancher

    def maj_latent(self, gain_jour):
        """A appeler quand le gain du jour change. Renvoie True s'il faut tout fermer (limite du jour ou plancher)."""
        self.gain_jour = gain_jour
        if gain_jour <= -self.limite_bot or self.marge <= 0:
            self.arrete = True
        return self.arrete

    def verifier(self, taille, risque_par_contrat, heure_ny, jour=""):
        """Avant un ordre. risque_par_contrat = perte en $ pour 1 contrat si le stop est touche (0 si pas de stop :
        le risque compte alors est tout ce qui reste de la limite du jour)."""
        r = []
        h, m = (int(x) for x in heure_ny.split(":")); minute = h * 60 + m
        if self.arrete:
            return Reponse(False, 0, ["limite du jour déjà touchée : plus d'ordre aujourd'hui"])
        if 16 * 60 + 55 <= minute < 18 * 60:
            return Reponse(False, 0, ["entre 16 h 55 et 18 h (New York) le compte doit être à plat"])
        if jour in self.jours_fed:
            return Reponse(False, 0, ["jour d'annonce de la Fed : pas de trade"])
        if self.sommet > 0 and (self.sommet - (self.solde + self.gain_jour)) / self.sommet >= self.baisse_max:
            return Reponse(False, 0, [f"baisse de {self.baisse_max:.0%} depuis le plus haut du compte : arrêt"])
        reste_jour = self.limite_bot + self.gain_jour                      # ce qu'on peut encore perdre aujourd'hui
        if reste_jour <= 0:
            return Reponse(False, 0, ["limite du jour atteinte"])
        t = min(int(taille), self.taille_max)
        if t < taille:
            r.append(f"taille ramenée de {taille} à {t} (maximum {self.taille_max})")
        if self.marge < self.frein and t > 1:
            t2 = max(1, t // 2); r.append(f"frein : marge {n(self.marge)} $ sous {n(self.frein)} $, taille {t} -> {t2}"); t = t2
        budget = min(reste_jour, self.marge)                               # ni la limite du jour ni le plancher ne doivent sauter
        if budget <= 0:
            return Reponse(False, 0, r + ["plus de marge au-dessus du plancher"])
        if risque_par_contrat > 0:
            while t >= 1 and t * risque_par_contrat > budget:
                t -= 1
            if t < 1:
                return Reponse(False, 0, r + [f"risque de {n(risque_par_contrat)} $ par contrat pour {n(budget)} $ disponibles : ordre refusé"])
            if t * risque_par_contrat > 0.5 * self.marge:
                r.append(f"attention : ce trade risque {n(t * risque_par_contrat)} $, plus de la moitié de la marge ({n(self.marge)} $)")
        else:
            r.append(f"pas de stop : le risque compté est la limite du jour restante ({n(reste_jour)} $)")
            if reste_jour > self.marge:
                r.append(f"attention : la limite du jour restante dépasse la marge ({n(self.marge)} $) : une seule perte peut coûter le compte")
        return Reponse(True, t, r)

    def fin_de_journee(self, gain, a_trade):
        """A la cloture de la journee de trading. Renvoie la liste des alertes pour le lendemain."""
        self.solde += gain; self.gain_jour = 0.0; self.arrete = False
        self.plus_haut = max(self.plus_haut, self.solde); self.sommet = max(self.sommet, self.solde)
        self.jours_sans_trade = 0 if a_trade else self.jours_sans_trade + 1
        a = []
        if self.solde <= self.plancher:
            a.append("COMPTE PERDU : le solde est sous le plancher")
        reste = self.inactivite_max - self.jours_sans_trade
        if reste <= 0:
            a.append("COMPTE PERDU : règle d'inactivité")
        elif reste <= 2:
            a.append(f"inactivité : {self.jours_sans_trade} jours sans trade, il en reste {reste} avant la perte du compte")
        if self.solde - self.plancher < self.limite_bot:
            a.append(f"marge de {n(self.solde - self.plancher)} $ : plus petite que la limite du jour, une seule mauvaise journée suffit")
        return a


def _tests():
    g = Garde()
    assert g.plancher == 47500 and g.marge == 2500
    assert g.verifier(4, 300, "10:30").taille == 3                         # 4 x 300 = 1 200 $ > limite du jour de 1 000 $
    assert g.verifier(8, 100, "10:30").taille == 4                         # taille maximale
    assert not g.verifier(1, 300, "17:10").autorise                        # fenetre a plat
    assert not Garde(jours_fed=frozenset({"2026-12-16"})).verifier(1, 300, "10:30", "2026-12-16").autorise
    g.fin_de_journee(1800, True); assert g.solde == 51800 and g.plancher == 49300
    assert g.fin_de_journee(-1100, True) == [] and round(g.marge) == 1400  # le cas du 11 novembre : marge 1 400 $
    rep = g.verifier(4, 250, "10:30"); assert rep.taille == 2 and any("frein" in x for x in rep.raisons)
    assert g.maj_latent(-1000) is True and not g.verifier(1, 100, "11:00").autorise
    g.fin_de_journee(-1000, True); assert round(g.marge) == 400
    assert g.verifier(1, 500, "10:30").autorise is False                   # 500 $ de risque pour 400 $ de marge
    for _ in range(3):
        al = g.fin_de_journee(0, False)
    assert any("inactivité" in x for x in al)
    g = Garde(solde=52700, plus_haut=52700); assert g.plancher == 50000   # plancher arrete au solde de depart
    p = Garde(solde=8400, depart=10000, plus_haut=10000, sommet=10000, perte_max=1e9, limite_bot=1e9, frein=0)
    assert not p.verifier(1, 50, "10:30").autorise                         # compte personnel : -16 % depuis le plus haut
    print("garde.py : tests passes")


if __name__ == "__main__":
    _tests()
