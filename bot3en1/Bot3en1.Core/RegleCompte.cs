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
    }
}
