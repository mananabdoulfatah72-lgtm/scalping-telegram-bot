using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;

namespace Bot3en1.Flux
{
    /// <summary>Regles de tendance du bot FluxNQ, memes decisions que la recherche (scalping/README.md, parties F et H) :
    /// H1 ORB 5 min, H5 cassure du plus haut / plus bas de la veille, H12 Supertrend 10-3 sur barres de 5 minutes,
    /// F3 pivots R1/S1 version tendance. Une minute est donnee a sa cloture ; les entrees et sorties « a l'ouverture » se
    /// font a l'ouverture de la minute suivante. Gains en $ pour 1 contrat micro : sens x (sortie - entree) x 2 $ x Echelle
    /// - Frais (Echelle = 1 en direct ; 30 900 / ouverture dans le rejeu « au prix d'aujourd'hui »).</summary>
    public class MoteurTendance
    {
        public const int N = 390;
        const double TICK = 0.25, PT = 2.0;
        public static readonly string[] Noms = { "H1", "H5", "H12", "F3" };
        public static readonly string[] Libelles =
        {
            "ORB 5 min", "cassure de la veille", "Supertrend 10-3 (5 min)", "pivots R1/S1"
        };

        public double Frais = 3.0;                 // $ par aller-retour : 1 $ + 1 tick (0,5 $) par ordre
        public DateTime Jour;
        bool ok;
        double echelle = 1.0;
        readonly BarreFlux[] b = new BarreFlux[N];
        int derniere = -1;
        BarreFlux[] veille;

        // Supertrend continu (toutes les seances donnees, barres de 5 minutes)
        int iBarre = -1;
        double atr, hb = double.NaN, lb = double.NaN, dir = 1.0, cPrec;
        double st;                                  // direction de la derniere barre (0 avant la 10e barre)

        /// <summary>Etat de chaque regle pour la seance.</summary>
        public class Etat
        {
            public string Nom;
            public int Pos, M0 = -1, Trades;        // position (+1 / -1 / 0), minute d'entree
            public double Px, Stop = double.NaN, Obj = double.NaN, Gain;
            public bool Fini, Joue;
            public int Attente;                     // H12 : position voulue a l'ouverture suivante (int.MinValue : rien)
            public string Raison = "";
        }

        public readonly Dictionary<string, Etat> Etats = new Dictionary<string, Etat>();

        public class Evenement { public string Regle, Texte, Motif; public bool Entree, Sortie; public int Sens, Minute; public double Prix, Stop, Objectif, Gain; }

        /// <summary>prec : seance complete precedente du meme contrat (null : aucune) ; ok : seance jouable (complete et pas
        /// un jour de changement de contrat).</summary>
        public void DebutSeance(DateTime jour, bool jouable, BarreFlux[] prec, double ech = 1.0)
        {
            Jour = jour;
            ok = jouable;
            veille = prec;
            echelle = ech;
            derniere = -1;
            Array.Clear(b, 0, N);
            Etats.Clear();
            foreach (var n in Noms) Etats[n] = new Etat { Nom = n, Attente = int.MinValue };
        }

        public double StopCourant(string regle) => Etats.TryGetValue(regle, out var e) ? e.Stop : double.NaN;
        public double ObjectifCourant(string regle) => Etats.TryGetValue(regle, out var e) ? e.Obj : double.NaN;
        public double Gain(string regle) => Etats.TryGetValue(regle, out var e) && e.Joue ? e.Gain : double.NaN;
        public int Position(string regle) => Etats.TryGetValue(regle, out var e) ? e.Pos : 0;

        /// <summary>Position voulue apres la cloture de la minute t (ce que la regle tient a l'ouverture suivante).</summary>
        public int PositionVoulue(string regle)
        {
            var e = Etats[regle];
            if (regle == "H12" && e.Attente != int.MinValue) return e.Attente;
            if (e.M0 >= 0 && e.Pos == 0 && !e.Fini && e.M0 == derniere + 1) return e.Attente;   // entree a la prochaine ouverture
            return e.Pos;
        }

        /// <summary>Cloture de la minute t (toutes les minutes de 0 a 389, dans l'ordre).</summary>
        public List<Evenement> FermerMinute(int t, BarreFlux x)
        {
            var ev = new List<Evenement>();
            if (t <= derniere || t >= N) return ev;
            for (int m = derniere + 1; m < t; m++) Poser(m, null);
            Poser(t, x);
            derniere = t;
            // barre de 5 minutes terminee : Supertrend
            if (t % 5 == 4) Supertrend(t);
            if (ok)
            {
                H12(t, ev);
                Seance(t, ev);
            }
            return ev;
        }

        void Poser(int m, BarreFlux x)
        {
            if (x == null || !x.Presente)
            {
                double p = m > 0 && b[m - 1] != null ? b[m - 1].C : (x?.O ?? 0);
                x = new BarreFlux { O = p, H = p, L = p, C = p };
            }
            b[m] = x;
        }

        void Supertrend(int t)
        {
            int k = t - 4;
            double h = double.MinValue, l = double.MaxValue;
            for (int m = k; m <= t; m++) { h = Math.Max(h, b[m].H); l = Math.Min(l, b[m].L); }
            double c = b[t].C;
            iBarre++;
            if (iBarre >= 1)
            {
                double tr = Math.Max(h - l, Math.Max(Math.Abs(h - cPrec), Math.Abs(l - cPrec)));
                atr = iBarre == 1 ? tr : (atr * 9 + tr) / 10;
                double mid = (h + l) / 2, hb2 = mid + 3 * atr, lb2 = mid - 3 * atr;
                if (iBarre > 1)
                {
                    hb2 = (hb2 < hb || cPrec > hb) ? hb2 : hb;
                    lb2 = (lb2 > lb || cPrec < lb) ? lb2 : lb;
                    if (dir > 0 && c < lb2) dir = -1.0;
                    else if (dir < 0 && c > hb2) dir = 1.0;
                }
                hb = hb2; lb = lb2;
                st = iBarre >= 10 ? dir : 0.0;
            }
            else st = 0.0;
            cPrec = c;
        }

        void Sortir(Etat e, double prix, int m, string motif, List<Evenement> ev)
        {
            double g = e.Pos * (prix - e.Px) * PT * echelle - Frais;
            e.Gain += g;
            e.Trades++;
            ev.Add(new Evenement { Regle = e.Nom, Sortie = true, Sens = e.Pos, Prix = prix, Minute = m, Motif = motif, Gain = g,
                Texte = $"{e.Nom} : sortie {(e.Pos > 0 ? "achat" : "vente")} ({motif}) a {prix.ToString("F2", CultureInfo.InvariantCulture)}, "
                        + $"{(e.Pos * (prix - e.Px) * PT * echelle - Frais).ToString("+0.00;-0.00", CultureInfo.InvariantCulture)} $ par MNQ" });
            e.Pos = 0;
        }

        void Entrer(Etat e, int sens, double prix, int m, List<Evenement> ev)
        {
            e.Pos = sens; e.Px = prix; e.Joue = true;
            if (e.M0 < 0) e.M0 = m;
            ev.Add(new Evenement { Regle = e.Nom, Entree = true, Sens = sens, Prix = prix, Stop = e.Stop, Objectif = e.Obj, Minute = m,
                Texte = $"{e.Nom} : entree {(sens > 0 ? "ACHAT" : "VENTE")} a {prix.ToString("F2", CultureInfo.InvariantCulture)}"
                        + (double.IsNaN(e.Stop) ? "" : $", stop {e.Stop.ToString("F2", CultureInfo.InvariantCulture)}")
                        + (double.IsNaN(e.Obj) ? "" : $", objectif {e.Obj.ToString("F2", CultureInfo.InvariantCulture)}")
                        + (e.Raison == "" ? "" : $" ({e.Raison})") });
        }

        // ------------------------------------------------------------------ H12 Supertrend (retournement a chaque changement)
        void H12(int t, List<Evenement> ev)
        {
            var e = Etats["H12"];
            // execution a l'ouverture de cette minute de la decision prise a la cloture de la barre precedente
            if (e.Attente != int.MinValue)
            {
                int cible = e.Attente;
                e.Attente = int.MinValue;
                double o = b[t].O;
                if (cible != e.Pos && e.Pos != 0) Sortir(e, o, t, "retournement du Supertrend", ev);
                if (cible != 0 && e.Pos == 0 && t <= 360) { e.Raison = cible > 0 ? "Supertrend haussier" : "Supertrend baissier"; Entrer(e, cible, o, t, ev); }
            }
            if (t == 384 && e.Pos != 0) Sortir(e, b[384].C, t, "15 h 55", ev);
            // decision a la cloture de la barre b (0 a 75)
            if (t % 5 == 4 && t / 5 <= 75)
            {
                int cible = st != 0 ? (int)st : e.Pos;
                if (cible != e.Pos) e.Attente = cible;
            }
        }

        // ------------------------------------------------------------------ H1, H5, F3 (une position par jour)
        void Seance(int t, List<Evenement> ev)
        {
            // H1 : sens de la premiere barre de 5 minutes, entree a 9 h 35
            var h1 = Etats["H1"];
            if (t == 4 && b[4].C != b[0].O)
            {
                h1.Attente = b[4].C > b[0].O ? 1 : -1;
                h1.M0 = 5;
                double hi = double.MinValue, lo = double.MaxValue;
                for (int m = 0; m < 5; m++) { hi = Math.Max(hi, b[m].H); lo = Math.Min(lo, b[m].L); }
                h1.Stop = h1.Attente > 0 ? lo : hi;
                h1.Raison = $"premiere barre de 5 min {(h1.Attente > 0 ? "haussiere" : "baissiere")}";
            }
            // H5 : premiere cloture au-dela du plus haut / plus bas de la veille (jusqu'a 14 h 59), stop a l'ouverture du jour
            var h5 = Etats["H5"];
            if (veille != null && h5.M0 < 0 && t < 360)
            {
                double hi = veille.Max(y => y.H), lo = veille.Min(y => y.L);
                int p = b[t].C > hi ? 1 : (b[t].C < lo ? -1 : 0);
                if (p != 0)
                {
                    h5.Attente = p; h5.M0 = t + 1; h5.Stop = b[0].O;
                    h5.Raison = $"cloture au-dela du {(p > 0 ? "plus haut" : "plus bas")} de la veille {(p > 0 ? hi : lo).ToString("F2", CultureInfo.InvariantCulture)}";
                }
            }
            // F3 : pivots de la veille, premiere cloture au-dela de R1 / S1 (jusqu'a 14 h 59), ouverture entre S1 et R1
            var f3 = Etats["F3"];
            if (veille != null && f3.M0 < 0 && t < 330)
            {
                double hp = veille.Max(y => y.H), lp = veille.Min(y => y.L), cp = veille[N - 1].C;
                double piv = (hp + lp + cp) / 3, r1 = 2 * piv - lp, s1 = 2 * piv - hp;
                if (!(b[0].O >= r1 || b[0].O <= s1))
                {
                    int p = b[t].C > r1 ? 1 : (b[t].C < s1 ? -1 : 0);
                    if (p != 0)
                    {
                        f3.Attente = p; f3.M0 = t + 1;
                        f3.Raison = $"cloture au-dela du {(p > 0 ? "R1" : "S1")} {(p > 0 ? r1 : s1).ToString("F2", CultureInfo.InvariantCulture)} (pivot {piv.ToString("F2", CultureInfo.InvariantCulture)})";
                    }
                }
                else f3.M0 = int.MaxValue;              // ouverture deja au-dela : pas de trade aujourd'hui
            }
            foreach (var e in new[] { h1, h5, f3 })
            {
                if (e.Fini) continue;
                // entree a l'ouverture de la minute M0
                if (e.Pos == 0 && e.M0 == t && e.Attente != int.MinValue)
                {
                    int p = e.Attente;
                    e.Attente = int.MinValue;
                    double px = b[t].O;
                    if (e.Nom == "H1")
                    {
                        double risque = Math.Abs(px - e.Stop);
                        e.Obj = risque > 0 ? px + p * 10 * risque : double.NaN;
                    }
                    Entrer(e, p, px, t, ev);
                }
                // gestion a partir de la minute d'entree : stop avant objectif, sinon 15 h 55
                if (e.Pos != 0 && t >= e.M0)
                {
                    var x = b[t];
                    double? sortie = null;
                    string motif = null;
                    if (!double.IsNaN(e.Stop))
                    {
                        if (e.Pos > 0 && x.L <= e.Stop) { sortie = Math.Min(x.O, e.Stop); motif = "stop"; }
                        else if (e.Pos < 0 && x.H >= e.Stop) { sortie = Math.Max(x.O, e.Stop); motif = "stop"; }
                    }
                    if (sortie == null && !double.IsNaN(e.Obj))
                    {
                        if (e.Pos > 0 && (x.O > e.Obj || x.H >= e.Obj + TICK)) { sortie = x.O > e.Obj ? x.O : e.Obj; motif = "objectif"; }
                        else if (e.Pos < 0 && (x.O < e.Obj || x.L <= e.Obj - TICK)) { sortie = x.O < e.Obj ? x.O : e.Obj; motif = "objectif"; }
                    }
                    if (sortie == null && t == 384) { sortie = x.C; motif = "15 h 55"; }
                    if (sortie != null)
                    {
                        Sortir(e, sortie.Value, t, motif, ev);
                        e.Fini = true;
                    }
                }
            }
        }
    }
}
