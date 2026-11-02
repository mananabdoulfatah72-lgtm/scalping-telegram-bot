using System;
using System.Collections.Generic;

namespace SupertrendNQ
{
    /// <summary>Une minute de la seance (9 h 30 + m, heure de New York).</summary>
    public class BarreMin { public double O, H, L, C; public bool Presente; }

    /// <summary>Trade termine : sens (+1 achat, -1 vente), minutes d'entree et de sortie (sortie 385 = a plat de 15 h 55),
    /// prix d'entree (ouverture de la minute d'entree) et de sortie.</summary>
    public class Trade { public DateTime Jour; public int Sens, MinuteEntree, MinuteSortie; public double Entree, Sortie; }

    public class Signal { public int Minute; public string Texte; }

    /// <summary>Supertrend (Periode, Multiple) sur les barres de 5 minutes de la seance (9 h 30 - 16 h), calcule en continu d'une
    /// seance a l'autre. Regle testee sur 15 ans (scalping/partie_h.py, H12 ; audit/machine6/supertrend.py) : a la cloture de
    /// chaque barre de 5 minutes, position dans le sens du Supertrend (retournement si le sens change), executee a l'ouverture
    /// de la minute suivante ; entrees jusqu'a 15 h 30 ; tout est ferme a la cloture de la minute de 15 h 54 (15 h 55).
    /// Ce moteur ne connait ni le compte ni la taille : il donne la position voulue (+1, -1, 0) et le journal des trades.</summary>
    public class MoteurST
    {
        public const int N = 390, DERNIERE_ENTREE = 360, A_PLAT = 384, DERNIERE_DECISION = 75;
        public int Periode = 10;
        public double Multiple = 3;

        // indicateur, continu d'une seance a l'autre
        long nb;
        double atr, hb = double.NaN, lb = double.NaN, dir = 1, cPrec = double.NaN;
        public int Sens { get; private set; }                       // 0 tant qu'il n'y a pas Periode barres
        public double Ligne => dir > 0 ? lb : hb;                    // ligne du Supertrend (sous le prix a l'achat)
        public long Barres => nb;

        // seance
        public DateTime Jour { get; private set; }
        public bool Trader { get; set; } = true;                     // seance tradee (fausse : jour court, ferie, a l'arret)
        public int Position { get; private set; }                    // position voulue
        public double Entree { get; private set; } = double.NaN;     // prix d'entree de la position en cours
        public int MinuteEntree { get; private set; } = -1;
        public double RealiseJour { get; private set; }              // $ pour 1 MNQ, frais de 3 $ par aller-retour compris
        public readonly List<Trade> Trades = new List<Trade>();
        double h5, l5, dernierC = double.NaN;
        int executer = -1, sensAttendu, sortieAttendue, bloque;     // bloque : sens abandonne, pas repris avant un retournement              // decision en attente de l'ouverture de la minute `executer`
        double entreeSortie;
        int minuteEntreeSortie;
        public bool ActionEnAttente => executer >= 0;

        /// <summary>Nouvelle seance : aucune position (le bot est a plat a 15 h 55).</summary>
        public void DebutSeance(DateTime jour, bool trader)
        {
            Jour = jour.Date; Trader = trader; Position = 0; Entree = double.NaN; MinuteEntree = -1; RealiseJour = 0;
            executer = -1; bloque = 0;
        }

        /// <summary>Fin de la minute m. Une minute absente est recopiee a plat sur la derniere cloture connue.</summary>
        public List<Signal> MinuteFermee(int m, BarreMin b)
        {
            var s = new List<Signal>();
            if (m < 0 || m >= N) return s;
            double o = b.O, h = b.H, l = b.L, c = b.C;
            if (!b.Presente)
            {
                if (double.IsNaN(dernierC)) return s;
                o = h = l = c = dernierC;
            }
            dernierC = c;
            // decision de la barre precedente : executee a l'ouverture de cette minute
            if (executer == m)
            {
                if (sortieAttendue != 0) Fermer(sortieAttendue, entreeSortie, minuteEntreeSortie, m, o, s, "retournement du Supertrend");
                if (sensAttendu != 0)
                {
                    Entree = o; MinuteEntree = m;
                    s.Add(new Signal { Minute = m, Texte = $"{(sensAttendu > 0 ? "achat" : "vente")} {Heure(m)} a {o:F2} (Supertrend {(sensAttendu > 0 ? "haussier" : "baissier")}, ligne {Ligne:F2})" });
                }
                executer = -1;
            }
            if (m % 5 == 0) { h5 = h; l5 = l; }
            else { h5 = Math.Max(h5, h); l5 = Math.Min(l5, l); }
            if (m % 5 == 4)
            {
                MettreAJour(h5, l5, c);
                int barre = m / 5;
                if (Trader && barre <= DERNIERE_DECISION && Sens != 0) Decider(m + 1);
            }
            if (m == A_PLAT && Position != 0 && executer < 0)
            {
                Fermer(Position, Entree, MinuteEntree, A_PLAT + 1, c, s, "15 h 55, a plat");
                Position = 0;
            }
            return s;
        }

        void MettreAJour(double h, double l, double c)
        {
            if (nb >= 1)
            {
                double tr = Math.Max(Math.Max(h - l, Math.Abs(h - cPrec)), Math.Abs(l - cPrec));
                atr = nb == 1 ? tr : (atr * (Periode - 1) + tr) / Periode;
                double mid = (h + l) / 2, hb2 = mid + Multiple * atr, lb2 = mid - Multiple * atr;
                if (nb > 1)
                {
                    hb2 = (hb2 < hb || cPrec > hb) ? hb2 : hb;
                    lb2 = (lb2 > lb || cPrec < lb) ? lb2 : lb;
                    if (dir > 0 && c < lb2) dir = -1;
                    else if (dir < 0 && c > hb2) dir = 1;
                }
                hb = hb2; lb = lb2;
            }
            Sens = nb >= Periode ? (int)dir : 0;
            cPrec = c;
            nb++;
        }

        void Decider(int m)
        {
            int cible = Sens;
            if (bloque != 0)
            {
                if (cible == bloque) return;                 // meme sens que la position abandonnee : on attend le retournement
                bloque = 0;
            }
            if (cible == Position) return;
            sortieAttendue = 0; sensAttendu = 0;
            if (Position != 0)
            {
                sortieAttendue = Position; entreeSortie = Entree; minuteEntreeSortie = MinuteEntree;
                Position = 0; Entree = double.NaN; MinuteEntree = -1;
            }
            if (m <= DERNIERE_ENTREE) { Position = cible; sensAttendu = cible; }
            executer = m;
        }

        void Fermer(int sens, double entree, int minuteEntree, int minuteSortie, double prix, List<Signal> s, string pourquoi)
        {
            double r = 2 * sens * (prix - entree) - 3.0;
            RealiseJour += r;
            Trades.Add(new Trade { Jour = Jour, Sens = sens, MinuteEntree = minuteEntree, MinuteSortie = minuteSortie, Entree = entree, Sortie = prix });
            s.Add(new Signal { Minute = minuteSortie, Texte = $"sortie {(sens > 0 ? "de l'achat" : "de la vente")} {Heure(Math.Min(minuteSortie, N - 1))} a {prix:F2} ({pourquoi}) : {sens * (prix - entree):+0.00;-0.00} points, {r:+0;-0} $ par MNQ" });
        }

        /// <summary>Position abandonnee hors du moteur (fermee a la main, limite du jour) : le moteur n'a plus de position et
        /// n'en reprend une qu'au prochain retournement du Supertrend.</summary>
        public void Abandonner()
        {
            bloque = Position != 0 ? Position : Sens;
            Position = 0; Entree = double.NaN; MinuteEntree = -1; executer = -1;
        }

        /// <summary>Reprise d'une position deja sur le compte (relance du bot en cours de seance).</summary>
        public void Reprendre(int sens, double entree, int minute)
        {
            Position = sens; Entree = entree; MinuteEntree = minute; executer = -1;
        }

        /// <summary>Plus de nouvelle position aujourd'hui (limite du jour, objectif) ; la position eventuelle est oubliee.</summary>
        public void Arreter() { Abandonner(); Trader = false; }

        public static string Heure(int m) => $"{(570 + m) / 60}h{(570 + m) % 60:00}";
    }
}
