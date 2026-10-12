using System;

namespace Bot3en1
{
    /// <summary>Regles d'un compte de prop firm a perte max suivie en fin de journee (Bulenox option 2, FundedNext...), comme
    /// vague4/moteur4.py : plancher = plus haut de fin de journee - perte max, arrete a solde de depart + blocage ; coussin =
    /// solde - plancher. Frein de la vague 10 : la zone passe sur MES quand le coussin est sous perte max - frein (Bulenox :
    /// 2 500 - 750 = 1 750 $, soit 750 $ sous le plus haut tant que le plancher suit).</summary>
    public static class RegleCompte
    {
        public static double Plancher(double picFinJour, double depart, double perteMax, double blocage) =>
            Math.Min(picFinJour - perteMax, depart + blocage);

        public static double Coussin(double solde, double picFinJour, double depart, double perteMax, double blocage) =>
            solde - Plancher(picFinJour, depart, perteMax, blocage);

        public static bool Frein(double solde, double picFinJour, double depart, double perteMax, double blocage, double frein) =>
            frein > 0 && perteMax > 0 && Coussin(solde, picFinJour, depart, perteMax, blocage) < perteMax - frein;

        // ------------------------------------------------------------------ challenge de 30 jours (vague 13, version D)

        /// <summary>Marge au-dessus de l'objectif pour l'arret a l'objectif : de quoi payer les frais de sortie (vague13/regles13.py
        /// MARGE).</summary>
        public const double MargeObjectif = 50;

        /// <summary>Objectif du challenge deja atteint au debut de la journee de trading (0 = pas d'objectif).</summary>
        public static bool ObjectifAtteint(double objectif, double soldeDebut) => objectif > 0 && soldeDebut >= objectif;

        /// <summary>Plafond du jour a appliquer en mode a plat : le plus petit des plafonds actifs, 0 = aucun. Arret a l'objectif
        /// (vague13/moteur13.py defi13) : plafond = objectif + marge - solde du debut de la journee.</summary>
        public static double PlafondEffectif(double plafondJour, double objectif, double soldeDebut)
        {
            double p = plafondJour > 0 ? plafondJour : 0;
            if (objectif > 0)
            {
                double o = Math.Max(objectif + MargeObjectif - soldeDebut, 0.01);
                p = p > 0 ? Math.Min(p, o) : o;
            }
            return p;
        }

        /// <summary>Seances de la Bourse (ni week-end, ni ferie, ni jour ferme du CME) du jour a la date de fin, les deux
        /// comprises. 0 si la date de fin est passee.</summary>
        public static int SeancesRestantes(DateTime jour, DateTime fin)
        {
            int n = 0;
            for (var d = jour.Date; d <= fin.Date; d = d.AddDays(1))
                if (!Calendrier.JourFerme(d) && !Calendrier.Ferie(d)) n++;
            return n;
        }

        /// <summary>Taille de la journee (MNQ par source) : la taille de fin de course pendant les nFin dernieres seances du
        /// challenge (defi13 : reste = seances restantes, aujourd'hui compris, reste &lt;= n_fin), la taille normale sinon.</summary>
        public static int TailleDuJour(int taille, int tailleFin, int nFin, int restantes) =>
            tailleFin > 0 && nFin > 0 && restantes >= 1 && restantes <= nFin ? tailleFin : taille;
    }
}
