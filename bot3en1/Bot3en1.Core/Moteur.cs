using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;

namespace Bot3en1
{
    /// <summary>Une minute de NQ (9 h 30 = minute 0) : prix, volume, et volumes agresseurs acheteurs et vendeurs.</summary>
    public class Barre
    {
        public double O, H, L, C, V, Achats, Ventes;
        public bool Presente;
    }

    /// <summary>Resume d'une seance, une ligne de historique.csv : ce dont la zone et le RSI(2) ont besoin les jours suivants.</summary>
    public class Resume
    {
        public DateTime Jour;
        public string Contrat;
        public bool Complete, RsiOk;
        public double O0, Cloture, Cx, Px;
        public int Dec;
        public double[] Mv = new double[Moteur.NMOMENTS];         // |cloture(m) / ouverture - 1| aux minutes 30, 60, ..., 360

        public static string Entete => "jour,contrat,complete,rsi_ok,o0,cloture,cx,px,dec," +
                                       string.Join(",", Enumerable.Range(1, Moteur.NMOMENTS).Select(i => $"mv{i * Moteur.PAS}"));

        public string Ligne() => string.Join(",", new[] { Jour.ToString("yyyy-MM-dd"), Contrat, Complete ? "1" : "0", RsiOk ? "1" : "0",
            F(O0), F(Cloture), F(Cx), F(Px), Dec.ToString(CultureInfo.InvariantCulture) }.Concat(Mv.Select(F)));

        public static Resume Lire(string l)
        {
            var x = l.Split(',');
            var r = new Resume { Jour = DateTime.ParseExact(x[0], "yyyy-MM-dd", CultureInfo.InvariantCulture), Contrat = x[1],
                Complete = x[2] == "1", RsiOk = x[3] == "1", O0 = D(x[4]), Cloture = D(x[5]), Cx = D(x[6]), Px = D(x[7]),
                Dec = int.Parse(x[8], CultureInfo.InvariantCulture) };
            for (int i = 0; i < Moteur.NMOMENTS; i++) r.Mv[i] = D(x[9 + i]);
            return r;
        }

        static string F(double v) => double.IsNaN(v) ? "" : v.ToString("R", CultureInfo.InvariantCulture);
        static double D(string s) => s == "" ? double.NaN : double.Parse(s, CultureInfo.InvariantCulture);
    }

    /// <summary>Un ordre voulu par le bot : nouvelle position nette en MNQ, et la raison.</summary>
    public class Signal
    {
        public int Minute;
        public string Source;          // "zone" ou "rsi2"
        public string Texte;
        public double PrixReference;   // prix du backtest (cloture de la minute pour la zone, ouverture de 15 h 50 pour le RSI(2))
    }

    /// <summary>Le bot 3 en 1 : zone de bruit V1 (zone/robot.py zone_de_bruit) dont chaque entree n'est prise que si le delta
    /// des 30 minutes va dans son sens (filtre H1, orderflow/), plus le RSI(2) de Connors (zone/robot.py rsi2). 1 MNQ par
    /// source. Le moteur ne passe pas d'ordres : il dit quelle position nette tenir, l'hote (Quantower ou le rejeu) execute.</summary>
    public class Moteur
    {
        public const int N = 390, PAS = 30, NMOMENTS = 12, JOURS_MOYENNE = 14, FENETRE_DELTA = 30;
        public int Taille = 1;                       // MNQ par source
        public double PlafondJour = 0;               // 0 : pas de plafond. Systeme Static (static50k/) : 500 $ sur le compte Pro
        public bool FiltreDelta = true;
        public bool ZoneAutorisee = true;            // le rejeu le met a faux pour une seance incomplete (le robot ne la trade pas)

        public readonly List<Resume> Historique;
        public Func<DateTime, string, string> ContratSuivant;   // (jour, contrat du jour) -> contrat de la seance suivante

        // etat de la seance
        public DateTime Jour { get; private set; }
        public string Contrat { get; private set; }
        public bool ZoneActive { get; private set; }
        public int MinuteDecisionRsi { get; private set; } = -1;
        public double Veille { get; private set; } = double.NaN;
        public double[] Sigma { get; private set; } = new double[NMOMENTS];
        readonly Barre[] barres = new Barre[N];
        double cumTv, cumV, cumT;
        int nPresentes;

        // positions (en unites de Taille) : zone virtuelle (chemin d'origine), zone tenue (apres filtre), RSI(2)
        public int ZoneVirtuelle { get; private set; }
        public int ZoneTenue { get; private set; }
        public int Rsi { get; private set; }
        public bool RsiRegle { get; private set; }   // etat de la regle du RSI(2) (tenu ou non), meme si on n'a pas la position
        public bool RsiAttendSignal { get; set; }    // au demarrage au milieu d'un trade : on attend un nouveau signal
        public double EntreeZone { get; private set; }
        public double EntreeRsi { get; private set; }
        /// <summary>Prix a partir duquel le RSI(2) compte dans le gain de la journee de trading : dernier prix avant la
        /// pause de 17 h la veille, ou prix d'achat s'il a ete achete dans la journee.</summary>
        public double RefRsi { get; private set; }
        public bool Arret { get; private set; }      // plafond du jour atteint : plus de trade jusqu'a 18 h
        public double RealiseJour { get; private set; }   // gain realise de la journee de trading (depuis 18 h la veille)
        public readonly List<Signal> Journal = new List<Signal>();

        public Moteur(List<Resume> historique) { Historique = historique; }

        public int PositionNette => (ZoneTenue + Rsi) * Taille;

        public static List<Resume> LireHistorique(string fichier) =>
            File.ReadAllLines(fichier).Skip(1).Where(l => l.Trim() != "").Select(Resume.Lire).ToList();

        public void EcrireHistorique(string fichier) =>
            File.WriteAllLines(fichier, new[] { Resume.Entete }.Concat(Historique.Select(r => r.Ligne())));

        /// <summary>Prepare la seance : parametres de la zone (veille, sigma) et minute de decision du RSI(2).
        /// derniereMinute : derniere minute de la seance (389 un jour normal, plus tot un jour de cloture anticipee).</summary>
        public void DebutSeance(DateTime jour, string contrat, int derniereMinute = N - 1)
        {
            Jour = jour.Date; Contrat = contrat;
            for (int i = 0; i < N; i++) barres[i] = new Barre();
            cumTv = cumV = cumT = 0; nPresentes = 0;
            ZoneVirtuelle = 0; ZoneTenue = 0;          // Arret et RealiseJour : remis a zero a 18 h (NouvelleJournee)
            // veille : cloture de la derniere seance complete du meme contrat, sans changement de contrat entre les deux
            Veille = double.NaN;
            for (int i = Historique.Count - 1; i >= 0; i--)
            {
                if (Historique[i].Contrat != contrat) break;
                if (Historique[i].Complete) { Veille = Historique[i].Cloture; break; }
            }
            // sigma : moyenne des 14 dernieres seances completes (tous contrats), a chaque moment de controle
            var completes = Historique.Where(r => r.Complete).Skip(Math.Max(0, Historique.Count(r => r.Complete) - JOURS_MOYENNE)).ToList();
            bool assez = completes.Count == JOURS_MOYENNE;
            for (int k = 0; k < NMOMENTS; k++) Sigma[k] = assez ? completes.Average(r => r.Mv[k]) : double.NaN;
            ZoneActive = assez && !double.IsNaN(Veille) && !Calendrier.JourCourt(jour) && !Calendrier.JourFerme(jour);
            MinuteDecisionRsi = Calendrier.Ferie(jour) ? -1 : derniereMinute - 9;
        }

        /// <summary>Debut d'une journee de trading de la firme (18 h, New York, la veille de la seance) : le gain du jour
        /// repart de zero, le plafond est leve, et un RSI(2) garde la nuit compte a partir de prixReference (dernier prix
        /// avant la pause de 17 h). Comme static50k/ : le gain du jour est mesure depuis la fin de la journee d'avant.</summary>
        public void NouvelleJournee(double prixReference)
        {
            RealiseJour = 0; Arret = false;
            if (Rsi != 0 && prixReference > 0) RefRsi = prixReference;
        }

        /// <summary>Plafond du jour hors de la seance (16 h - 17 h, puis la nuit) : seul le RSI(2) peut etre en position.
        /// Renvoie vrai si le plafond vient d'etre atteint (le RSI(2) est ferme, plus rien jusqu'a 18 h).</summary>
        public bool VerifierPlafondHorsSeance(double prix)
        {
            if (PlafondJour <= 0 || Arret || Rsi == 0 || prix <= 0 || ValeurJour(prix) < PlafondJour) return false;
            Arret = true;
            RealiseJour += Taille * ((prix - RefRsi) * 2 - 1.5);
            Rsi = 0;
            Journal.Add(new Signal { Minute = -1, Source = "plafond", PrixReference = prix,
                                     Texte = $"plafond du jour atteint hors seance a {prix:F2} : RSI(2) ferme jusqu'a 18 h" });
            return true;
        }

        /// <summary>Plafond deja atteint dans cette journee de trading (redemarrage du bot) : plus de trade jusqu'a 18 h.</summary>
        public void ArreterJusqua18h() { Arret = true; }

        double Vwap(int m) => cumV > 0 ? cumTv / cumV : cumT / (m + 1);

        double Delta(int m)
        {
            double a = 0, v = 0;
            for (int i = Math.Max(0, m - FENETRE_DELTA + 1); i <= m; i++) { a += barres[i].Achats; v += barres[i].Ventes; }
            return a - v;
        }

        /// <summary>Appelee a la fin de chaque minute m (barre complete). Renvoie les signaux de cette minute.</summary>
        public List<Signal> MinuteFermee(int m, Barre b)
        {
            var sortie = new List<Signal>();
            if (m < 0 || m >= N) return sortie;
            // minutes absentes : comme robot.py tableaux (prix = derniere cloture connue, volume 0)
            if (!b.Presente)
            {
                double c = PrecedenteCloture(m);
                b = new Barre { O = c, H = c, L = c, C = c, V = 0, Achats = b.Achats, Ventes = b.Ventes, Presente = false };
            }
            else nPresentes++;
            barres[m] = b;
            double typique = (b.H + b.L + b.C) / 3;
            cumTv += typique * b.V; cumV += b.V; cumT += typique;
            int k = (m % PAS == 0) ? m / PAS - 1 : -1;
            if (k >= 0 && k < NMOMENTS && ZoneActive && ZoneAutorisee && barres[0].Presente && !double.IsNaN(Sigma[k]))
                Zone(m, k, b.C, sortie);
            if (m == N - 1 && ZoneVirtuelle != 0)
                SortieZone(m, b.C, "sortie 16h00", sortie);
            if (PlafondJour > 0 && !Arret && ValeurJour(b.C) >= PlafondJour)
            {
                Arret = true;
                if (ZoneTenue != 0) { RealiseJour += Taille * (ZoneTenue * (b.C - EntreeZone) - 1.5) * 2; ZoneTenue = 0; }
                if (Rsi != 0) { RealiseJour += Taille * ((b.C - RefRsi) * 2 - 1.5); Rsi = 0; }
                sortie.Add(new Signal { Minute = m, Source = "plafond", Texte = $"plafond du jour atteint : tout ferme", PrixReference = b.C });
            }
            Journal.AddRange(sortie);
            return sortie;
        }

        double PrecedenteCloture(int m)
        {
            for (int i = m - 1; i >= 0; i--) if (barres[i] != null && barres[i].C != 0) return barres[i].C;
            return Historique.Count > 0 ? Historique[^1].Cloture : 0;
        }

        /// <summary>Gain de la journee de trading au prix donne (realise + positions ouvertes, depuis 18 h la veille).</summary>
        public double ValeurJour(double prix) => RealiseJour + Taille * 2 * (ZoneTenue * (prix - EntreeZone) + Rsi * (prix - RefRsi));

        void Zone(int m, int k, double p, List<Signal> s)
        {
            double o0 = barres[0].O;
            double haut = Math.Max(o0, Veille) * (1 + Sigma[k]), bas = Math.Min(o0, Veille) * (1 - Sigma[k]), vw = Vwap(m);
            if (ZoneVirtuelle > 0 && p <= Math.Max(haut, vw)) SortieZone(m, p, "sortie", s);
            else if (ZoneVirtuelle < 0 && p >= Math.Min(bas, vw)) SortieZone(m, p, "sortie", s);
            if (ZoneVirtuelle == 0 && (p > haut || p < bas))
            {
                int sens = p > haut ? 1 : -1;
                ZoneVirtuelle = sens;
                double d = Delta(m);
                bool garde = !FiltreDelta || Math.Sign(d) == sens;
                string h = Heure(m);
                if (garde && !Arret)
                {
                    ZoneTenue = sens; EntreeZone = p;
                    s.Add(new Signal { Minute = m, Source = "zone", PrixReference = p,
                        Texte = $"{(sens > 0 ? "achat" : "vente")} {h} a {p:F2} (delta 30 min {d:+0;-0;0}, GARDE)" });
                }
                else
                    s.Add(new Signal { Minute = m, Source = "zone-ecarte", PrixReference = p,
                        Texte = $"{(sens > 0 ? "achat" : "vente")} {h} a {p:F2} ecarte (delta 30 min {d:+0;-0;0})" });
            }
        }

        void SortieZone(int m, double p, string quoi, List<Signal> s)
        {
            if (ZoneTenue != 0)
            {
                RealiseJour += Taille * (ZoneTenue * (p - EntreeZone) - 1.5) * 2;
                s.Add(new Signal { Minute = m, Source = "zone", PrixReference = p, Texte = $"{quoi} {Heure(m)} a {p:F2}" });
            }
            ZoneVirtuelle = 0; ZoneTenue = 0;
        }

        /// <summary>Decision du RSI(2) a l'ouverture de la minute de decision (15 h 50 un jour normal), sur la cloture de la
        /// minute d'avant. prixOuverture : prix d'execution du backtest (ouverture de la minute de decision).</summary>
        public List<Signal> DecisionRsi(double prixOuverture)
        {
            var s = new List<Signal>();
            if (MinuteDecisionRsi < 2) return s;
            double cx = barres[MinuteDecisionRsi - 1]?.C ?? double.NaN;
            if (double.IsNaN(cx) || cx == 0) return s;
            var serie = Historique.Where(r => r.RsiOk).Select(r => r.Cx).ToList();
            serie.Add(cx);
            int n = serie.Count;
            if (n < 205) return s;
            double m200 = serie.Skip(n - 200).Average(), m5 = serie.Skip(n - 5).Average();
            double rsi = RsiWilder(serie);
            bool roule = ContratSuivant != null && ContratSuivant(Jour, Contrat) != Contrat;
            bool avant = RsiRegle;
            if (RsiRegle && cx > m5) RsiRegle = false;
            else if (!RsiRegle && cx > m200 && rsi < 10) RsiRegle = true;
            if (roule) RsiRegle = false;
            if (RsiAttendSignal && !RsiRegle) RsiAttendSignal = false;
            int voulu = (RsiRegle && !RsiAttendSignal && !Arret) ? 1 : 0;
            string h = Heure(MinuteDecisionRsi);
            if (voulu != Rsi)
            {
                if (voulu == 1) { EntreeRsi = RefRsi = prixOuverture; RealiseJour -= Taille * 1.5; }
                else RealiseJour += Taille * ((prixOuverture - RefRsi) * 2 - 1.5);
                Rsi = voulu;
                s.Add(new Signal { Minute = MinuteDecisionRsi, Source = "rsi2", PrixReference = prixOuverture,
                    Texte = $"RSI(2) : {(voulu == 1 ? "achat" : "vente")} {h} a {prixOuverture:F2} (cloture {cx:F2}, RSI {rsi:F1},"
                          + $" moyenne 200 {m200:F2}, moyenne 5 {m5:F2}{(roule ? ", changement d'echeance" : "")})" });
            }
            Journal.AddRange(s);
            return s;
        }

        /// <summary>RSI de Wilder sur 2 clotures, comme robot.py rsi2 (moyennes de depart sur les 2 premiers ecarts).</summary>
        public static double RsiWilder(List<double> c)
        {
            int n = c.Count;
            if (n < 3) return double.NaN;
            double g0 = Math.Max(c[1] - c[0], 0), g1 = Math.Max(c[2] - c[1], 0), p0 = Math.Max(c[0] - c[1], 0), p1 = Math.Max(c[1] - c[2], 0);
            double mg = (g0 + g1) / 2, mp = (p0 + p1) / 2, rsi = double.NaN;
            for (int i = 2; i < n; i++)
            {
                if (i > 2)
                {
                    double d = c[i] - c[i - 1];          // robot.py : gg[i - 1] = Cx[i] - Cx[i - 1]
                    mg = (mg + Math.Max(d, 0)) / 2; mp = (mp + Math.Max(-d, 0)) / 2;
                }
                rsi = mp == 0 ? 100.0 : 100 - 100 / (1 + mg / mp);
            }
            return rsi;
        }

        /// <summary>Fin de seance : resume ajoute a l'historique. Le RSI(2) garde sa position pour la nuit.</summary>
        public Resume FinSeance()
        {
            int derniere = -1;
            for (int i = N - 1; i >= 0; i--) if (barres[i] != null && barres[i].Presente) { derniere = i; break; }
            int dec = derniere - 9;
            var r = new Resume { Jour = Jour, Contrat = Contrat, O0 = barres[0].Presente ? barres[0].O : double.NaN,
                Cloture = derniere >= 0 ? barres[N - 1].C : double.NaN, Dec = dec };
            r.Complete = barres[0].Presente && barres[N - 1].Presente && nPresentes >= 370;
            r.RsiOk = nPresentes >= 60 && barres[0].Presente && dec >= 2 && !Calendrier.Ferie(Jour);
            r.Cx = dec >= 2 ? barres[dec - 1].C : double.NaN;
            r.Px = dec >= 2 ? (barres[dec].Presente ? barres[dec].O : barres[dec - 1].C) : double.NaN;
            for (int k = 0; k < NMOMENTS; k++)
                r.Mv[k] = barres[0].Presente ? Math.Abs(barres[(k + 1) * PAS].C / barres[0].O - 1) : double.NaN;
            Historique.Add(r);
            return r;
        }

        /// <summary>Apres un rejeu de demarrage : aucune position, et pas d'entree au milieu d'un trade du RSI(2).</summary>
        public void RemettreAPlat()
        {
            ZoneVirtuelle = ZoneTenue = Rsi = 0; RealiseJour = 0; Arret = false;
            RsiAttendSignal = RsiRegle;
            Journal.Clear();
        }

        /// <summary>Demarrage en cours de seance : la zone continue son chemin d'origine mais ne tient pas le trade en cours
        /// (pas d'entree au milieu d'un trade) ; elle prendra les signaux suivants.</summary>
        public void OublierZoneTenue() { ZoneTenue = 0; }

        /// <summary>Reprend la position du RSI(2) enregistree par le bot (fichier d'etat) apres un redemarrage.</summary>
        public void RestaurerRsi(bool tenue, double entree)
        {
            Rsi = tenue ? 1 : 0; EntreeRsi = RefRsi = entree;      // RefRsi : remplace par NouvelleJournee
            if (tenue) RsiAttendSignal = false;
        }

        public static string Heure(int m) => $"{(570 + m) / 60}h{(570 + m) % 60:00}";
    }
}
