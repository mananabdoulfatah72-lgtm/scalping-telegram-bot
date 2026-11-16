using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;

namespace Bot3en1.Flux
{
    /// <summary>Une minute du NQ : prix, achats et ventes agressifs, ventes aux deux prix les plus bas et achats aux deux
    /// plus hauts (footprint), et volume par prix (ticks entiers, prix x 4) quand il est connu.</summary>
    public class BarreFlux
    {
        public double O, H, L, C, Achats, Ventes, VentesBas2 = double.NaN, AchatsHaut2 = double.NaN;
        public bool Presente;
        public Dictionary<long, double[]> ParPrix;            // tick -> { achats, ventes } (direct seulement)

        /// <summary>Remplit VentesBas2 et AchatsHaut2 a partir du volume par prix.</summary>
        public void CalculerFootprint()
        {
            if (ParPrix == null || ParPrix.Count == 0) return;
            long bas = ParPrix.Keys.Min(), haut = ParPrix.Keys.Max();
            double vb = 0, ah = 0;
            foreach (var kv in ParPrix)
            {
                if (kv.Key <= bas + 1) vb += kv.Value[1];
                if (kv.Key >= haut - 1) ah += kv.Value[0];
            }
            VentesBas2 = vb;
            AchatsHaut2 = ah;
        }
    }

    /// <summary>Photo du carnet : quantites affichees sur les 10 meilleurs prix de chaque cote.</summary>
    public class PhotoDom
    {
        public double[] PrixAchat = new double[0], QteAchat = new double[0], PrixVente = new double[0], QteVente = new double[0];
        public double SommeAchat => QteAchat.Sum();
        public double SommeVente => QteVente.Sum();
        public bool Vide => QteAchat.Length == 0 || QteVente.Length == 0;
    }

    /// <summary>Regle suivie par le bot (flux/README.md, « Le bot FluxNQ »).</summary>
    public class Regle
    {
        public string Nom;
        public int Famille;                 // 1 repli absorbe (S1), 2 cassure ratee (S2, S2b), 3 confluence (C1)
        public bool Agression;              // S2 : agression a la cassure exigee
        public double Objectif = 2.0;       // multiple du risque
        public int Duree = 30;              // minutes au plus
        public double StopMin = 3.0;        // points
        public int TMax = 330;              // derniere minute de signal

        public static List<Regle> Toutes() => new List<Regle>
        {
            new Regle { Nom = "S1", Famille = 1 },
            new Regle { Nom = "S2", Famille = 2, Agression = true },
            new Regle { Nom = "S2b", Famille = 2, Agression = false, Duree = 60, TMax = 150 },
            new Regle { Nom = "C1", Famille = 3 },
        };
    }

    public class TradeFlux
    {
        public Regle Regle;
        public DateTime Jour;
        public int Signal, EntreeMinute = -1, SortieMinute = -1, Sens;
        public double StopStructure, Entree, Stop, Objectif, R, Sortie, Net;
        public string Motif = "", Raison = "";
        public bool Ouvert => EntreeMinute >= 0 && SortieMinute < 0;
    }

    public class Evenement
    {
        public string Texte;
        public TradeFlux Trade;
        public bool Signal, Sortie;       // Signal : a la cloture de la minute du signal (ordre reel a envoyer)
    }

    /// <summary>Moteur du bot FluxNQ, independant de la plateforme : memes decisions que flux/systeme.py (S1, S2),
    /// flux/reglages.py (S2b) et flux/confluence.py (C1). Une minute est donnee a sa cloture.</summary>
    public class MoteurFlux
    {
        public const int N = 390;
        const double TICK = 0.25, GLISSE = 0.25, COM = 0.5, RMAX = 0.0012;
        public readonly List<Regle> Regles;
        public bool IgnorerDom;                          // rejeu de l'historique (aucun DOM) : condition 4 de C1 ignoree
        public double RatioDom = 1.2;

        // seance
        public DateTime Jour;
        public bool Jouable;
        readonly BarreFlux[] b = new BarreFlux[N];
        readonly double[] v = new double[N], delta = new double[N], imb = new double[N], vwap = new double[N], cd = new double[N],
                          sigv = new double[N];
        double sv, stv, st2v, scd;
        int derniere = -1;
        double q10, q25, q75, q90, fb75 = double.NaN, fh75 = double.NaN;
        double pdh = double.NaN, pdl = double.NaN, pocV = double.NaN, valV = double.NaN, vahV = double.NaN;
        public readonly Dictionary<long, double> ProfilSeance = new Dictionary<long, double>();
        readonly Dictionary<Regle, EtatRegle> etats = new Dictionary<Regle, EtatRegle>();
        public readonly List<TradeFlux> Trades = new List<TradeFlux>();

        class EtatRegle
        {
            public int Libre;
            public List<TradeFlux> Attente = new List<TradeFlux>();     // signaux de la minute d'avant, entree a cette minute
            public TradeFlux Position;
            public NiveauS2[] Niveaux;
        }

        class NiveauS2 { public double L; public int Haut, Debut, Etat, B; }      // Etat : 0 attend, 1 cassure, 2 fini

        public MoteurFlux(IEnumerable<Regle> regles = null) { Regles = (regles ?? Regle.Toutes()).ToList(); }

        // ------------------------------------------------------------------ outils identiques a numpy
        /// <summary>np.percentile(x, p), methode lineaire, au bit pres (interpolation de numpy).</summary>
        public static double Percentile(double[] trie, double p)
        {
            int n = trie.Length;
            double vi = p / 100.0 * (n - 1);
            int i = (int)Math.Floor(vi);
            double g = vi - i;
            if (i >= n - 1) return trie[n - 1];
            double a = trie[i], c = trie[i + 1], d = c - a;
            return g >= 0.5 ? c - d * (1 - g) : a + d * g;
        }

        static double Mediane(double[] x)
        {
            var s = (double[])x.Clone();
            Array.Sort(s);
            int n = s.Length;
            return n % 2 == 1 ? s[n / 2] : (s[n / 2 - 1] + s[n / 2]) / 2;
        }

        static double Imb(BarreFlux x)
        {
            double vv = x.Achats + x.Ventes;
            return vv > 0 ? (x.Achats - x.Ventes) / vv : 0.0;
        }

        /// <summary>POC, VAL, VAH d'un profil (tick -> volume) : expansion d'un tick du cote le plus fort jusqu'a 70 %.</summary>
        public static (double poc, double val, double vah) ZoneValeur(Dictionary<long, double> profil)
        {
            long k0 = profil.Keys.Min(), k1 = profil.Keys.Max();
            var vol = new double[k1 - k0 + 1];
            foreach (var kv in profil) vol[kv.Key - k0] = kv.Value;
            int poc = 0;
            for (int i = 1; i < vol.Length; i++) if (vol[i] > vol[poc]) poc = i;
            int lo = poc, hi = poc;
            double acc = vol[poc], tot = 0;
            foreach (var x in vol) tot += x;
            while (acc < 0.7 * tot)
            {
                double up = hi + 1 < vol.Length ? vol[hi + 1] : -1.0, dn = lo - 1 >= 0 ? vol[lo - 1] : -1.0;
                if (up >= dn) { hi++; acc += up; } else { lo--; acc += dn; }
            }
            return ((k0 + poc) * TICK, (k0 + lo) * TICK, (k0 + hi) * TICK);
        }

        // ------------------------------------------------------------------ seance
        /// <summary>precedentes : seances d'avant, la derniere est la veille (au moins 5 pour les seuils) ; profilVeille :
        /// volume par tick de la veille (null : pas de C1) ; jouable : faux un jour de changement de contrat ou de seance
        /// mince.</summary>
        public void DebutSeance(DateTime jour, IList<BarreFlux[]> precedentes, Dictionary<long, double> profilVeille, bool jouable)
        {
            Jour = jour;
            derniere = -1;
            sv = stv = st2v = scd = 0;
            ProfilSeance.Clear();
            Array.Clear(b, 0, N);
            int n = precedentes?.Count ?? 0;
            Jouable = jouable && n >= 5;
            q10 = q25 = q75 = q90 = double.NaN;
            fb75 = fh75 = double.NaN;
            if (n >= 5)
            {
                var x = new List<double>();
                var fb = new List<double>();
                var fh = new List<double>();
                bool fpOk = true;
                for (int k = n - 5; k < n; k++)
                    for (int t = 30; t < N; t++)
                    {
                        var y = precedentes[k][t] ?? new BarreFlux();
                        x.Add(Imb(y));
                        fb.Add(y.VentesBas2); fh.Add(y.AchatsHaut2);
                        if (double.IsNaN(y.VentesBas2) || double.IsNaN(y.AchatsHaut2)) fpOk = false;
                    }
                var xs = x.ToArray(); Array.Sort(xs);
                q10 = Percentile(xs, 10); q25 = Percentile(xs, 25); q75 = Percentile(xs, 75); q90 = Percentile(xs, 90);
                if (fpOk)
                {
                    var a = fb.ToArray(); Array.Sort(a); fb75 = Percentile(a, 75);
                    var c = fh.ToArray(); Array.Sort(c); fh75 = Percentile(c, 75);
                }
            }
            if (n >= 1)
            {
                var v1 = precedentes[n - 1];
                pdh = v1.Where(y => y != null).Max(y => y.H);
                pdl = v1.Where(y => y != null).Min(y => y.L);
            }
            else pdh = pdl = double.NaN;
            if (profilVeille != null && profilVeille.Count > 0) (pocV, valV, vahV) = ZoneValeur(profilVeille);
            else pocV = valV = vahV = double.NaN;
            etats.Clear();
            foreach (var r in Regles)
            {
                var e = new EtatRegle();
                if (r.Famille == 2)
                    e.Niveaux = new[] { new NiveauS2 { L = pdh, Haut = 1, Debut = 30 }, new NiveauS2 { L = pdl, Haut = -1, Debut = 30 },
                                        new NiveauS2 { Haut = 1, Debut = 60 }, new NiveauS2 { Haut = -1, Debut = 60 } };
                etats[r] = e;
            }
        }

        public bool AFootprint(int t) => b[t] != null && !double.IsNaN(b[t].VentesBas2);
        public double Vwap(int t) => vwap[t];
        public double SigmaV(int t) => sigv[t];
        public double D30(int t) => t >= 30 ? cd[t] - cd[t - 30] : cd[t];
        public double Cvd(int t) => cd[t];
        public double Desequilibre(int t) => imb[t];
        public (double q10, double q25, double q75, double q90) Seuils => (q10, q25, q75, q90);
        public (double pdh, double pdl, double poc, double val, double vah) Veille => (pdh, pdl, pocV, valV, vahV);
        public BarreFlux Barre(int t) => b[t];

        // ------------------------------------------------------------------ minute
        /// <summary>Cloture de la minute t. dom : photo du carnet a la cloture (null si inconnue).</summary>
        public List<Evenement> FermerMinute(int t, BarreFlux barre, PhotoDom dom = null)
        {
            var ev = new List<Evenement>();
            if (t <= derniere || t >= N) return ev;
            // minutes sans transaction : recopiees a plat sur la cloture d'avant, volume nul (donnees du projet)
            for (int m = derniere + 1; m < t; m++)
                Enregistrer(m, PlatSur(m));
            Enregistrer(t, barre != null && barre.Presente ? barre : PlatSur(t));
            derniere = t;
            if (!Jouable) return ev;
            foreach (var r in Regles) Avancer(r, t, dom, ev);
            return ev;
        }

        BarreFlux PlatSur(int m)
        {
            double p = m > 0 && b[m - 1] != null ? b[m - 1].C : 0;
            return new BarreFlux { O = p, H = p, L = p, C = p, Presente = false, VentesBas2 = 0, AchatsHaut2 = 0 };
        }

        void Enregistrer(int t, BarreFlux x)
        {
            b[t] = x;
            v[t] = x.Achats + x.Ventes;
            delta[t] = x.Achats - x.Ventes;
            imb[t] = v[t] > 0 ? delta[t] / v[t] : 0.0;
            double typ = (x.H + x.L + x.C) / 3;
            sv += v[t]; stv += typ * v[t]; st2v += typ * typ * v[t]; scd += delta[t];
            cd[t] = scd;
            vwap[t] = sv > 0 ? stv / sv : typ;
            double m2 = sv > 0 ? st2v / sv : typ * typ;
            sigv[t] = Math.Sqrt(Math.Max(m2 - vwap[t] * vwap[t], 0.0));
            if (x.ParPrix != null)
                foreach (var kv in x.ParPrix)
                    ProfilSeance[kv.Key] = (ProfilSeance.TryGetValue(kv.Key, out var y) ? y : 0) + kv.Value[0] + kv.Value[1];
            if (t == 59)
                foreach (var e in etats.Values)
                    if (e.Niveaux != null)
                    {
                        double ibh = double.MinValue, ibl = double.MaxValue;
                        for (int m = 0; m < 60; m++) { ibh = Math.Max(ibh, b[m].H); ibl = Math.Min(ibl, b[m].L); }
                        e.Niveaux[2].L = ibh; e.Niveaux[3].L = ibl;
                    }
        }

        void Avancer(Regle r, int t, PhotoDom dom, List<Evenement> ev)
        {
            var e = etats[r];
            // 1. entree des signaux de la minute d'avant, a l'ouverture de cette minute
            if (e.Attente.Count > 0)
            {
                foreach (var x in e.Attente)
                {
                    if (!Geometrie(x, b[t].O, r)) { x.Raison = "risque au-dela de 0,12 % du prix"; continue; }
                    x.EntreeMinute = t;
                    x.Jour = Jour;
                    e.Position = x;
                    Trades.Add(x);
                    break;
                }
                e.Attente.Clear();
            }
            // 2. sortie de la position (ordre le plus defavorable dans la minute)
            if (e.Position != null && e.Position.Ouvert)
            {
                var p = e.Position;
                int fin = Math.Min(p.EntreeMinute + r.Duree - 1, N - 1);
                var x = b[t];
                double? sortie = null; string motif = null;
                if (p.Sens > 0)
                {
                    if (t > p.EntreeMinute && x.O <= p.Stop) { sortie = x.O - GLISSE; motif = "stop"; }
                    else if (x.L <= p.Stop) { sortie = p.Stop - GLISSE; motif = "stop"; }
                    else if (x.H >= p.Objectif + TICK) { sortie = p.Objectif; motif = "objectif"; }
                }
                else
                {
                    if (t > p.EntreeMinute && x.O >= p.Stop) { sortie = x.O + GLISSE; motif = "stop"; }
                    else if (x.H >= p.Stop) { sortie = p.Stop + GLISSE; motif = "stop"; }
                    else if (x.L <= p.Objectif - TICK) { sortie = p.Objectif; motif = "objectif"; }
                }
                if (sortie == null && t >= fin) { sortie = x.C - p.Sens * GLISSE; motif = "temps"; }
                if (sortie != null)
                {
                    p.SortieMinute = t; p.Sortie = sortie.Value; p.Motif = motif;
                    p.Net = p.Sens * (p.Sortie - p.Entree) - 2 * COM;
                    e.Libre = t;
                    e.Position = null;
                    ev.Add(new Evenement { Trade = p, Sortie = true,
                        Texte = $"{r.Nom} : sortie {(p.Sens > 0 ? "achat" : "vente")} ({motif}) a {p.Sortie.ToString("F2", CultureInfo.InvariantCulture)}, "
                                + $"{p.Net.ToString("+0.00;-0.00", CultureInfo.InvariantCulture)} point(s) net" });
                }
            }
            // 3. signaux a la cloture de cette minute
            var sig = Signaux(r, t, e, dom);
            if (sig.Count == 0 || t > r.TMax) return;
            if (t < e.Libre || e.Position != null) return;
            foreach (var x in sig) e.Attente.Add(x);
            var s0 = sig[0];
            ev.Add(new Evenement { Trade = s0, Signal = true,
                Texte = $"{r.Nom} : signal {(s0.Sens > 0 ? "ACHAT" : "VENTE")} a la cloture de {b[t].C.ToString("F2", CultureInfo.InvariantCulture)} ({s0.Raison})" });
        }

        bool Geometrie(TradeFlux x, double ouverture, Regle r)
        {
            double ent = ouverture + x.Sens * GLISSE;
            double st = x.Sens > 0 ? Math.Floor(Math.Min(x.StopStructure, ent - r.StopMin) / TICK) * TICK
                                   : Math.Ceiling(Math.Max(x.StopStructure, ent + r.StopMin) / TICK) * TICK;
            double R = Math.Abs(ent - st);
            if (R > RMAX * ent) return false;
            double ob = ent + x.Sens * r.Objectif * R;
            ob = x.Sens > 0 ? Math.Ceiling(ob / TICK) * TICK : Math.Floor(ob / TICK) * TICK;
            x.Entree = ent; x.Stop = st; x.Objectif = ob; x.R = R;
            return true;
        }

        // ------------------------------------------------------------------ signaux
        List<TradeFlux> Signaux(Regle r, int t, EtatRegle e, PhotoDom dom)
        {
            var l = new List<TradeFlux>();
            if (r.Famille == 1) SignalS1(r, t, l);
            else if (r.Famille == 2) SignauxS2(r, t, e, l);
            else SignalC1(r, t, dom, l);
            return l;
        }

        void SignalS1(Regle r, int t, List<TradeFlux> l)
        {
            if (t < 30 || t > 330 || double.IsNaN(q10)) return;
            var x = b[t];
            var fen = new double[30];
            Array.Copy(v, t - 30, fen, 0, 30);
            bool volOk = v[t] >= Mediane(fen);
            double milieu = (x.H + x.L) / 2, lo = double.MaxValue, hi = double.MinValue;
            for (int j = t - 5; j < t; j++) { lo = Math.Min(lo, b[j].L); hi = Math.Max(hi, b[j].H); }
            double d30 = D30(t);
            if (x.C > vwap[t] && d30 > 0 && x.L <= lo && x.C >= milieu && imb[t] <= q10 && volOk)
                l.Add(new TradeFlux { Regle = r, Signal = t, Sens = 1, StopStructure = x.L - TICK,
                                      Raison = $"repli sur un plus bas de 5 min au-dessus du VWAP, delta 30 min {d30:+0;-0}, ventes absorbees (desequilibre {imb[t]:+0.00;-0.00})" });
            else if (x.C < vwap[t] && d30 < 0 && x.H >= hi && x.C <= milieu && imb[t] >= q90 && volOk)
                l.Add(new TradeFlux { Regle = r, Signal = t, Sens = -1, StopStructure = x.H + TICK,
                                      Raison = $"rebond sur un plus haut de 5 min sous le VWAP, delta 30 min {d30:+0;-0}, achats absorbes (desequilibre {imb[t]:+0.00;-0.00})" });
        }

        void SignauxS2(Regle r, int t, EtatRegle e, List<TradeFlux> l)
        {
            if (double.IsNaN(q10) || e.Niveaux == null || double.IsNaN(pdh)) return;
            var noms = new[] { "plus haut de la veille", "plus bas de la veille", "plus haut de la 1re heure", "plus bas de la 1re heure" };
            for (int k = 0; k < 4; k++)
            {
                var n = e.Niveaux[k];
                if (n.Etat == 2 || t < n.Debut) continue;
                double L = n.L;
                if (n.Etat == 0)
                {
                    if (t > 330) { n.Etat = 2; continue; }
                    bool casse = n.Haut == 1 ? b[t].H >= L + TICK && b[t - 1].C <= L : b[t].L <= L - TICK && b[t - 1].C >= L;
                    if (!casse) continue;
                    bool agresse = n.Haut == 1 ? imb[t] >= q75 : imb[t] <= q25;
                    if (r.Agression && !agresse) { n.Etat = 2; continue; }
                    n.Etat = 1; n.B = t;
                }
                if (n.Etat == 1)
                {
                    int finFen = Math.Min(n.B + 5, 330);
                    bool echec = n.Haut == 1 ? b[t].C <= L - TICK : b[t].C >= L + TICK;
                    if (echec && t <= finFen)
                    {
                        double ext = n.Haut == 1 ? double.MinValue : double.MaxValue;
                        for (int j = n.B; j <= t; j++) ext = n.Haut == 1 ? Math.Max(ext, b[j].H) : Math.Min(ext, b[j].L);
                        l.Add(new TradeFlux { Regle = r, Signal = t, Sens = -n.Haut, StopStructure = n.Haut == 1 ? ext + TICK : ext - TICK,
                                              Raison = $"cassure ratee du {noms[k]} {L.ToString("F2", CultureInfo.InvariantCulture)} (cassure a la minute {n.B}, retour a {t})" });
                        n.Etat = 2;
                    }
                    else if (t >= finFen) n.Etat = 2;
                }
            }
            // meme ordre que sorted() de la partie 1 : minute, sens, stop
            l.Sort((a, c) => a.Sens != c.Sens ? a.Sens.CompareTo(c.Sens) : a.StopStructure.CompareTo(c.StopStructure));
        }

        void SignalC1(Regle r, int t, PhotoDom dom, List<TradeFlux> l)
        {
            if (t < 30 || t > 330 || double.IsNaN(fb75) || double.IsNaN(pocV) || double.IsNaN(pdh) || !AFootprint(t)) return;
            var x = b[t];
            double vw = vwap[t], s = sigv[t];
            double[] bas = { pdl, valV, pocV, vahV, vw - s }, haut = { pdh, vahV, pocV, valV, vw + s };
            string[] nb = { "plus bas de la veille", "VAL de la veille", "POC de la veille", "VAH de la veille", "VWAP - 1 ecart-type" },
                     nh = { "plus haut de la veille", "VAH de la veille", "POC de la veille", "VAL de la veille", "VWAP + 1 ecart-type" };
            bool domAchat = IgnorerDom || (dom != null && !dom.Vide && dom.SommeAchat >= RatioDom * dom.SommeVente);
            bool domVente = IgnorerDom || (dom != null && !dom.Vide && dom.SommeVente >= RatioDom * dom.SommeAchat);
            int iA = -1, iV = -1;
            for (int i = 0; i < 5 && iA < 0; i++)
            {
                double L = bas[i];
                if (x.L <= L + 2 * TICK && x.L >= L - 8 * TICK && x.C >= L && b[t - 1].C > L + 2 * TICK) iA = i;
            }
            for (int i = 0; i < 5 && iV < 0; i++)
            {
                double L = haut[i];
                if (x.H >= L - 2 * TICK && x.H <= L + 8 * TICK && x.C <= L && b[t - 1].C < L - 2 * TICK) iV = i;
            }
            string carnet(bool achat) => IgnorerDom || dom == null ? "" :
                $", carnet {dom.SommeAchat:0} achat / {dom.SommeVente:0} vente sur 10 niveaux";
            if (delta[t] < 0 && x.VentesBas2 >= fb75 && iA >= 0 && domAchat)
                l.Add(new TradeFlux { Regle = r, Signal = t, Sens = 1, StopStructure = x.L - 2 * TICK,
                                      Raison = $"{nb[iA]} {bas[iA].ToString("F2", CultureInfo.InvariantCulture)} tenu, {x.VentesBas2:0} contrats vendus aux 2 prix les plus bas (seuil {fb75:0}), delta {delta[t]:+0;-0}{carnet(true)}" });
            else if (delta[t] > 0 && x.AchatsHaut2 >= fh75 && iV >= 0 && domVente)
                l.Add(new TradeFlux { Regle = r, Signal = t, Sens = -1, StopStructure = x.H + 2 * TICK,
                                      Raison = $"{nh[iV]} {haut[iV].ToString("F2", CultureInfo.InvariantCulture)} tenu, {x.AchatsHaut2:0} contrats achetes aux 2 prix les plus hauts (seuil {fh75:0}), delta {delta[t]:+0;-0}{carnet(false)}" });
        }
    }
}
