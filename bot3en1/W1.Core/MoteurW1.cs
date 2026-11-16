using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;

namespace W1NQ
{
    /// <summary>Une minute de la seance (9 h 30 + m, heure de New York). Presente = la minute a des valeurs ; Reelle = elle vient de
    /// vraies transactions (une minute recopiee sur la cloture precedente est presente mais pas reelle).</summary>
    public class BarreMin { public double O, H, L, C, V; public bool Presente, Reelle = true; }

    /// <summary>Trade du bot (pris par le modele) : sortie 385 = a plat de 15 h 55.</summary>
    public class Trade { public DateTime Jour; public int Sens, MinuteEntree, MinuteSortie; public double Entree, Sortie, Proba; }

    public class Signal { public int Minute; public string Texte; }

    /// <summary>Chaque signal du Supertrend NQ, pris ou ecarte : les 28 variables vues par le modele, sa probabilite.</summary>
    public class Decision { public DateTime Jour; public int Minute, Sens; public double[] Variables; public double Proba; public bool Pris; }

    /// <summary>Le modele de tri de W1 (ml/arene/w1_prod.py) : 10 modeles XGBoost de 200 arbres (graines 0 a 9), parcourus comme XGBoost
    /// (variables en flottants 32 bits, x &lt; seuil a gauche, valeur manquante dans la branche par defaut) ; probabilite de chacun =
    /// sigmoide(marge de base + somme des feuilles) ; probabilite du modele = moyenne des 10.</summary>
    public class Arbres
    {
        class Arbre { public int[] G, D, V; public float[] S; public bool[] M; }
        class Modele { public double Marge; public readonly List<Arbre> Arbres = new List<Arbre>(); }
        readonly List<Modele> modeles = new List<Modele>();
        public string EntraineJusqua { get; private set; } = "";
        public double Seuil { get; private set; }
        public int Variables { get; private set; }
        public int Nombre => modeles.Count;

        public static Arbres Lire(Stream s)
        {
            using var doc = JsonDocument.Parse(s);
            var r = doc.RootElement; var a = new Arbres();
            a.EntraineJusqua = r.GetProperty("entraine_jusqua").GetString();
            a.Seuil = r.GetProperty("seuil").GetDouble();
            a.Variables = r.GetProperty("variables").GetArrayLength();
            foreach (var md in r.GetProperty("modeles").EnumerateArray())
            {
                double b = md.GetProperty("base").GetDouble();
                var m = new Modele { Marge = Math.Log(b / (1 - b)) };
                foreach (var t in md.GetProperty("arbres").EnumerateArray())
                    m.Arbres.Add(new Arbre
                    {
                        G = t.GetProperty("g").EnumerateArray().Select(x => x.GetInt32()).ToArray(),
                        D = t.GetProperty("d").EnumerateArray().Select(x => x.GetInt32()).ToArray(),
                        V = t.GetProperty("v").EnumerateArray().Select(x => x.GetInt32()).ToArray(),
                        S = t.GetProperty("s").EnumerateArray().Select(x => (float)x.GetDouble()).ToArray(),
                        M = t.GetProperty("m").EnumerateArray().Select(x => x.GetBoolean()).ToArray()
                    });
                a.modeles.Add(m);
            }
            return a;
        }

        public double Proba(double[] x)
        {
            double somme = 0;
            foreach (var md in modeles)
            {
                float tot = 0f;
                foreach (var a in md.Arbres)
                {
                    int n = 0;
                    while (a.G[n] != -1)
                    {
                        float v = (float)x[a.V[n]];
                        n = float.IsNaN(v) ? (a.M[n] ? a.G[n] : a.D[n]) : (v < a.S[n] ? a.G[n] : a.D[n]);
                    }
                    tot += a.S[n];
                }
                somme += 1.0 / (1.0 + Math.Exp(-(md.Marge + tot)));
            }
            return somme / modeles.Count;
        }
    }

    /// <summary>Moteur du bot W1 (ml/arene/VAGUE4.md, VAGUE5.md : P3 ; modele de production ml/arene/w1_prod.py) : les signaux du
    /// Supertrend NQ (10, 3) sur barres de 5 minutes, calcule en continu d'une seance a l'autre (decision a la cloture de la barre,
    /// ordre a l'ouverture de la minute suivante, entrees jusqu'a 15 h 30, a plat a la cloture de 15 h 54), tries par le modele :
    /// a chaque nouveau signal, 28 variables connues a la decision (21 variables du labo a la derniere bougie de 15 min terminee,
    /// sens, minute, ecart a la VWAP en ATR, rendement depuis l'ouverture, ecart d'ouverture, trades du Supertrend deja commences
    /// dans la seance et leur resultat) ; le trade est pris si la probabilite depasse le seuil du modele, sinon le bot reste a plat
    /// jusqu'au signal suivant. Le Supertrend est suivi en entier (positions virtuelles) pour les variables. Le moteur ne connait
    /// ni le compte ni la taille.</summary>
    public class MoteurW1
    {
        public const int N = 390, NB = 26, DERNIERE_ENTREE = 360, A_PLAT = 384, DERNIERE_DECISION = 75;
        public const double PREF = 28500, FRAIS = 3.0;
        static readonly int[] EMAS = { 8, 13, 21, 34, 55, 89 };
        readonly Arbres modele;
        public MoteurW1(Arbres m) { modele = m; }
        public double Seuil => modele.Seuil;

        // ------------------------------------------------------------------ bougies de 15 min et indicateurs continus (comme XGBoost NQ)
        readonly List<double> c15 = new List<double>(), lr = new List<double>(), bw = new List<double>();
        readonly double[] ema = new double[6];
        double e12, e26, macdSig, au, ad, atr = double.NaN, rsi = double.NaN, macdH, upSomme, dnSomme, trSomme;
        double bbM = double.NaN, bbH = double.NaN, bbB = double.NaN, rang = double.NaN;
        long nb15;

        class Resume { public double O0, C389; public bool Complete; public double[] Mv = new double[12]; public double[] Rv = new double[NB]; }
        readonly List<Resume> passees = new List<Resume>();

        // ------------------------------------------------------------------ Supertrend 10-3 continu (barres de 5 min)
        long nb5; double stAtr, stHb = double.NaN, stLb = double.NaN, stDir = 1, stCp = double.NaN, stD, stLigne = double.NaN, h5, l5;
        public int SensSupertrend => (int)stD;
        public double LigneSupertrend => stLigne;

        // ------------------------------------------------------------------ seance en cours
        public DateTime Jour { get; private set; }
        public bool Trader { get; set; } = true;
        readonly double[] O = new double[N], H = new double[N], L = new double[N], C = new double[N], V = new double[N];
        readonly bool[] reelle = new bool[N];
        double dernierC = double.NaN, cumV, cumTV, cumT, cumR2;
        int remplies;
        double[] zoneH, zoneB;
        double qH, qL;
        public double[] Variables { get; } = new double[21];

        // ------------------------------------------------------------------ Supertrend virtuel (tous ses trades) et position du bot
        int vPos, vMinute; double vEntree = double.NaN;
        int nbAvant; double resAvant;
        public int Position { get; private set; }
        public double Entree { get; private set; } = double.NaN;
        public int MinuteEntree { get; private set; } = -1;
        public double ProbaEntree { get; private set; } = double.NaN;
        public double DerniereProba { get; private set; } = double.NaN;
        public double RealiseJour { get; private set; }
        public readonly List<Trade> Trades = new List<Trade>();
        public readonly List<Decision> Decisions = new List<Decision>();
        public bool GarderDecisions = false;
        int executer = -1, vAttendu, vSortie, attendu, rSortie, rMinuteEntreeSortie;
        double vEntreeSortie, rEntreeSortie, rProbaSortie, probaAttendue;
        public bool ActionEnAttente => executer >= 0;

        public void DebutSeance(DateTime jour, bool trader)
        {
            Jour = jour.Date; Trader = trader; Position = 0; Entree = double.NaN; MinuteEntree = -1; RealiseJour = 0;
            vPos = 0; vEntree = double.NaN; vMinute = -1; nbAvant = 0; resAvant = 0;
            executer = -1; cumV = cumTV = cumT = cumR2 = 0; remplies = 0; DerniereProba = double.NaN;
            for (int m = 0; m < N; m++) { O[m] = H[m] = L[m] = C[m] = double.NaN; V[m] = 0; reelle[m] = false; }
            zoneH = zoneB = null;
            var comp = passees.Where(p => p.Complete).ToList();
            if (comp.Count >= 14)
            {
                var d14 = comp.Skip(comp.Count - 14).ToList();
                zoneH = new double[12]; zoneB = new double[12];
                for (int k = 0; k < 12; k++) zoneH[k] = d14.Sum(p => p.Mv[k]) / 14;      // sigma ; bornes fixees a la premiere minute
            }
        }

        /// <summary>Fin de la minute m. Minute sans transaction : recopiee a plat sur la derniere cloture connue.</summary>
        public List<Signal> MinuteFermee(int m, BarreMin b)
        {
            var s = new List<Signal>();
            if (m < 0 || m >= N) return s;
            double o = b.O, h = b.H, l = b.L, c = b.C, v = b.V;
            bool vraie = b.Presente && b.Reelle;
            if (!b.Presente)
            {
                if (double.IsNaN(dernierC)) return s;
                o = h = l = c = dernierC; v = 0;
            }
            if (vraie) remplies++;
            O[m] = o; H[m] = h; L[m] = l; C[m] = c; V[m] = v; reelle[m] = vraie;
            if (m == 0 && zoneH != null)
            {
                var comp = passees.Where(p => p.Complete).ToList();
                double veille = comp[^1].C389, rh = Math.Max(o, veille), rb = Math.Min(o, veille);
                var sig = zoneH; zoneH = new double[12]; zoneB = new double[12];
                for (int k = 0; k < 12; k++) { zoneH[k] = rh * (1 + sig[k]); zoneB[k] = rb * (1 - sig[k]); }
            }
            double r1 = m == 0 ? Math.Log(c) - Math.Log(o) : Math.Log(c) - Math.Log(C[m - 1]);
            cumR2 += r1 * r1;
            double ty = (h + l + c) / 3; cumV += v; cumTV += ty * v; cumT += ty;
            dernierC = c;
            // decision de la barre precedente : executee a l'ouverture de cette minute
            if (executer == m)
            {
                if (vSortie != 0) resAvant += Pnl(vSortie, vEntreeSortie, o);
                if (vAttendu != 0) { vPos = vAttendu; vEntree = o; vMinute = m; nbAvant++; } else vPos = 0;
                if (rSortie != 0) Fermer(rSortie, rEntreeSortie, rMinuteEntreeSortie, rProbaSortie, m, o, s, "retournement du Supertrend");
                if (attendu != 0)
                {
                    Entree = o; MinuteEntree = m; ProbaEntree = probaAttendue;
                    s.Add(new Signal { Minute = m, Texte = $"{(attendu > 0 ? "achat" : "vente")} {Heure(m)} a {o:F2} (Supertrend {(attendu > 0 ? "haussier" : "baissier")}, signal garde par le modele : {probaAttendue:P0} de chances de gagner, seuil {Seuil:P0})" });
                }
                else if (vAttendu != 0)
                    s.Add(new Signal { Minute = m, Texte = $"signal {(vAttendu > 0 ? "acheteur" : "vendeur")} du Supertrend a {Heure(m)} ecarte par le modele ({probaAttendue:P0} de chances de gagner, sous le seuil de {Seuil:P0}) : a plat jusqu'au signal suivant" });
                executer = -1;
            }
            if (m % 5 == 0) { h5 = h; l5 = l; } else { h5 = Math.Max(h5, h); l5 = Math.Min(l5, l); }
            if (m % 5 == 4) MajSupertrend(h5, l5, c);
            if (m % 15 == 0) { qH = h; qL = l; } else { qH = Math.Max(qH, h); qL = Math.Min(qL, l); }
            if (m % 15 == 14)
            {
                int bq = m / 15;
                MajIndicateurs(qH, qL, c);
                CalculerVariables(bq, m, c);
            }
            if (m % 5 == 4 && Trader && m / 5 <= DERNIERE_DECISION && stD != 0) Decider(m + 1, c);
            if (m == A_PLAT && executer < 0)
            {
                if (vPos != 0) { resAvant += Pnl(vPos, vEntree, c); vPos = 0; }
                if (Position != 0)
                {
                    Fermer(Position, Entree, MinuteEntree, ProbaEntree, A_PLAT + 1, c, s, "a plat de fin de seance");
                    Position = 0; Entree = double.NaN; MinuteEntree = -1;
                }
            }
            if (m == N - 1) FinSeance();
            return s;
        }

        public static double Pnl(int sens, double entree, double sortie) => sens * (sortie - entree) * 2.0 * PREF / entree - FRAIS;

        void Decider(int m, double c)
        {
            int cible = (int)stD;
            if (cible == vPos) return;
            vSortie = vPos; vEntreeSortie = vEntree;
            rSortie = Position; rEntreeSortie = Entree; rMinuteEntreeSortie = MinuteEntree; rProbaSortie = ProbaEntree;
            vAttendu = m <= DERNIERE_ENTREE ? cible : 0;
            attendu = 0;
            if (vAttendu != 0)
            {
                double resDec = resAvant + (vPos != 0 ? Pnl(vPos, vEntree, c) : 0);
                var x = VariablesTrade(vAttendu, m, c, resDec);
                double p = modele.Proba(x);
                DerniereProba = p; probaAttendue = p;
                bool pris = p > Seuil;
                if (GarderDecisions) Decisions.Add(new Decision { Jour = Jour, Minute = m, Sens = vAttendu, Variables = x, Proba = p, Pris = pris });
                if (pris) attendu = vAttendu;
            }
            Position = attendu; Entree = double.NaN; MinuteEntree = -1;
            executer = m;
        }

        /// <summary>Les 28 variables du modele, connues a la cloture de la minute m - 1 (ml/arene/w1_prod.py).</summary>
        public double[] VariablesTrade(int sens, int m, double c, double resDec)
        {
            var x = new double[28];
            Array.Copy(Variables, x, 21);
            double vw = cumV > 0 ? cumTV / cumV : cumT / m;
            double a = !double.IsNaN(atr) && atr > 0 ? atr : double.NaN;
            double gap = passees.Count > 0 && passees[^1].Complete ? O[0] / passees[^1].C389 - 1 : double.NaN;
            x[21] = sens; x[22] = m; x[23] = sens * (c - vw) / a; x[24] = sens * (c / O[0] - 1); x[25] = sens * gap;
            x[26] = nbAvant; x[27] = resDec;
            return x;
        }

        void Fermer(int sens, double entree, int minuteEntree, double proba, int minuteSortie, double prix, List<Signal> s, string pourquoi)
        {
            double r = 2 * sens * (prix - entree) - 3.0;
            RealiseJour += r;
            Trades.Add(new Trade { Jour = Jour, Sens = sens, MinuteEntree = minuteEntree, MinuteSortie = minuteSortie, Entree = entree, Sortie = prix, Proba = proba });
            s.Add(new Signal { Minute = minuteSortie, Texte = $"sortie {(sens > 0 ? "de l'achat" : "de la vente")} {Heure(Math.Min(minuteSortie, N - 1))} a {prix:F2} ({pourquoi}) : {sens * (prix - entree):+0.00;-0.00} points, {r:+0;-0} $ par MNQ" });
        }

        void FinSeance()
        {
            var p = new Resume { O0 = O[0], C389 = C[N - 1], Complete = reelle[0] && reelle[N - 1] && remplies >= 370 };
            for (int k = 0; k < 12; k++) p.Mv[k] = Math.Abs(C[29 + 30 * k] / O[0] - 1);
            double cum = 0;
            for (int m = 0; m < N; m++)
            {
                double r1 = m == 0 ? Math.Log(C[0]) - Math.Log(O[0]) : Math.Log(C[m]) - Math.Log(C[m - 1]);
                cum += r1 * r1;
                if (m % 15 == 14) p.Rv[m / 15] = Math.Sqrt(cum);
            }
            passees.Add(p);
            if (passees.Count > 60) passees.RemoveAt(0);
        }

        // ------------------------------------------------------------------ indicateurs (terminal/prep2.py, ml/caracteristiques.py)
        void MajIndicateurs(double h, double l, double c)
        {
            long i = nb15;
            double cp = i == 0 ? c : c15[^1];
            c15.Add(c);
            lr.Add(i == 0 ? 0.0 : Math.Log(c / cp));
            for (int k = 0; k < 6; k++) { double a = 2.0 / (EMAS[k] + 1); ema[k] = i == 0 ? c : a * c + (1 - a) * ema[k]; }
            e12 = i == 0 ? c : 2.0 / 13 * c + (1 - 2.0 / 13) * e12;
            e26 = i == 0 ? c : 2.0 / 27 * c + (1 - 2.0 / 27) * e26;
            double macd = e12 - e26;
            macdSig = i == 0 ? macd : 2.0 / 10 * macd + (1 - 2.0 / 10) * macdSig;
            macdH = macd - macdSig;
            // RSI 14 de Wilder : moyennes initiales sur les variations 1 a 14, valeur a partir de la bougie 15
            double d = i == 0 ? 0 : c - cp, up = Math.Max(d, 0), dn = Math.Max(-d, 0);
            if (i >= 1 && i <= 14) { upSomme += up; dnSomme += dn; }
            if (i == 14) { au = upSomme / 14; ad = dnSomme / 14; }
            else if (i >= 15) { au = (au * 13 + up) / 14; ad = (ad * 13 + dn) / 14; }
            rsi = i < 15 ? double.NaN : ad == 0 ? 100 : 100 - 100 / (1 + au / ad);
            // ATR 14 de Wilder : moyenne des 14 premieres amplitudes, puis lissage
            double tr = Math.Max(h - l, Math.Max(Math.Abs(h - cp), Math.Abs(l - cp)));
            if (i <= 13) { trSomme += tr; if (i == 13) atr = trSomme / 14; }
            else atr = (atr * 13 + tr) / 14;
            // Bollinger 20-2 (ecart type de population) et rang de sa largeur sur 500 bougies (au moins 100)
            if (c15.Count >= 20)
            {
                double s = 0; for (int k = c15.Count - 20; k < c15.Count; k++) s += c15[k];
                double mo = s / 20, v = 0; for (int k = c15.Count - 20; k < c15.Count; k++) v += (c15[k] - mo) * (c15[k] - mo);
                double sd = Math.Sqrt(v / 20); bbM = mo; bbH = mo + 2 * sd; bbB = mo - 2 * sd;
                bw.Add((bbH - bbB) / bbM);
            }
            else { bbM = bbH = bbB = double.NaN; bw.Add(double.NaN); }
            rang = double.NaN;
            double x = bw[^1];
            if (!double.IsNaN(x))
            {
                int n = 0, moins = 0, egal = 0;
                for (int k = Math.Max(0, bw.Count - 500); k < bw.Count; k++)
                {
                    double y = bw[k]; if (double.IsNaN(y)) continue;
                    n++; if (y < x) moins++; else if (y == x) egal++;
                }
                if (n >= 100) rang = (moins + (egal + 1) / 2.0) / n * 100;
            }
            if (c15.Count > 600) { c15.RemoveRange(0, 100); lr.RemoveRange(0, 100); bw.RemoveRange(0, 100); }
            nb15++;
        }

        void MajSupertrend(double h, double l, double c)
        {
            if (nb5 >= 1)
            {
                double tr = Math.Max(Math.Max(h - l, Math.Abs(h - stCp)), Math.Abs(l - stCp));
                stAtr = nb5 == 1 ? tr : (stAtr * 9 + tr) / 10;
                double mid = (h + l) / 2, hb2 = mid + 3 * stAtr, lb2 = mid - 3 * stAtr;
                if (nb5 > 1)
                {
                    hb2 = (hb2 < stHb || stCp > stHb) ? hb2 : stHb;
                    lb2 = (lb2 > stLb || stCp < stLb) ? lb2 : stLb;
                    if (stDir > 0 && c < lb2) stDir = -1;
                    else if (stDir < 0 && c > hb2) stDir = 1;
                }
                stHb = hb2; stLb = lb2;
                stLigne = stDir > 0 ? stLb : stHb;
            }
            stD = nb5 >= 10 ? stDir : 0;
            stCp = c; nb5++;
        }

        double SommeLr(int k) { if (nb15 < k) return double.NaN; double s = 0; for (int j = lr.Count - k; j < lr.Count; j++) s += lr[j]; return s; }

        void CalculerVariables(int bq, int m, double c)
        {
            var f = Variables;
            f[0] = lr[^1]; f[1] = SommeLr(4); f[2] = SommeLr(16);
            f[3] = (rsi - 50) / 50; f[4] = macdH / c * 100; f[5] = (c - bbM) / (bbH - bbM); f[6] = atr / c * 100;
            f[7] = rang / 100; f[8] = (ema[0] - ema[4]) / c * 100;
            f[9] = Math.Sin(2 * Math.PI * bq / NB); f[10] = Math.Cos(2 * Math.PI * bq / NB);
            double vw = cumV > 0 ? cumTV / Math.Max(cumV, 1e-9) : cumT / (m + 1);
            f[11] = (c - vw) / atr;
            f[12] = Math.Log(c / O[0]);
            int np_ = passees.Count;
            double prevC = np_ > 0 ? passees[^1].C389 : double.NaN, prevO = np_ > 0 ? passees[^1].O0 : double.NaN;
            f[13] = Math.Log(O[0] / prevC);
            f[14] = Math.Log(prevC / prevO);
            if (np_ >= 20)
            {
                double s = 0; for (int k = np_ - 20; k < np_; k++) s += passees[k].Rv[bq];
                f[15] = Math.Sqrt(cumR2) / (s / 20);
            }
            else f[15] = double.NaN;
            f[16] = np_ >= 5 ? Math.Log(c / passees[np_ - 5].C389) : double.NaN;
            f[17] = ((int)Jour.DayOfWeek + 6) % 7;
            f[18] = stD;
            f[19] = (c - stLigne) / atr;
            if (zoneH != null && zoneB != null && m >= 0)
            {
                int kz = Math.Clamp((m + 1) / 30 - 1, 0, 11);
                f[20] = (c - (zoneH[kz] + zoneB[kz]) / 2) / ((zoneH[kz] - zoneB[kz]) / 2);
            }
            else f[20] = double.NaN;
        }

        // ------------------------------------------------------------------ hors du moteur
        /// <summary>Position abandonnee (fermee a la main, limite, fichier STOP) : le bot l'oublie ; le Supertrend continue d'etre
        /// suivi et un nouveau signal garde par le modele peut rouvrir.</summary>
        public void Abandonner() { Position = 0; Entree = double.NaN; MinuteEntree = -1; if (executer >= 0) attendu = 0; }

        /// <summary>Reprise d'une position deja sur le compte (relance du bot en cours de seance).</summary>
        public void Reprendre(int sens, double entree, int minute) { Position = sens; Entree = entree; MinuteEntree = minute; }

        /// <summary>Plus de nouvelle position aujourd'hui (limite du jour, objectif).</summary>
        public void Arreter() { Abandonner(); Trader = false; }

        public Func<int, string> HeureLocale;
        string Heure(int m) => HeureLocale?.Invoke(m) ?? HeureNY(m) + " (New York)";
        public static string HeureNY(int m) => $"{(570 + m) / 60}h{(570 + m) % 60:00}";
    }
}
