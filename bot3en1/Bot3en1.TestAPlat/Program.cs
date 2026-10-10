using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Bot3en1;

// Controles du mode a plat sur le moteur seul. Les decisions du RSI(2) de nuit sont verifiees a part contre la recherche
// Python (TestQuantower A_PLAT=1 : memes 19 nuits d'avril a septembre 2026 que vague4/moteur4.py, rsi = 4).
class Program
{
    static int echecs = 0;
    static void Ok(bool c, string quoi) { Console.WriteLine($"{(c ? "ok" : "ECHEC")} : {quoi}"); if (!c) echecs++; }

    static void Poser(Moteur m, string prop, object v) =>
        typeof(Moteur).GetProperty(prop).GetSetMethod(true).Invoke(m, new[] { v });

    static Moteur AvecHistorique(bool aPlat)
    {
        var h = new List<Resume>();
        var j = new DateTime(2026, 9, 1);
        for (int i = 0; i < 20; i++, j = Calendrier.SeanceSuivante(j))
        {
            var r = new Resume { Jour = j, Contrat = "Z26", Complete = true, RsiOk = true, O0 = 25000, Cloture = 25000, Cx = 25000, Px = 25000, Dec = 380 };
            for (int k = 0; k < Moteur.NMOMENTS; k++) r.Mv[k] = 0.002;
            h.Add(r);
        }
        return new Moteur(h) { ModeAPlat = aPlat, JoursFed = new HashSet<DateTime>(Calendrier.JoursFed) };
    }

    static int Main()
    {
        // 1. frein (Bulenox 50K : perte 2 500 $, plancher arrete a 50 100 $, frein 750 $ -> coussin < 1 750 $)
        Ok(!RegleCompte.Frein(49250, 50000, 50000, 2500, 100, 750), "frein : 750 $ sous le plus haut, coussin 1 750 $ -> MNQ");
        Ok(RegleCompte.Frein(49249, 50000, 50000, 2500, 100, 750), "frein : 751 $ sous le plus haut -> MES");
        Ok(RegleCompte.Frein(50900, 51800, 50000, 2500, 100, 750), "frein : plancher qui suit (51 800 - 2 500), 900 $ sous le plus haut -> MES");
        Ok(RegleCompte.Plancher(52700, 50000, 2500, 100) == 50100, "plancher bloque a 50 100 $ quand le plus haut depasse 52 600 $");
        Ok(RegleCompte.Frein(51849, 53500, 50000, 2500, 100, 750) && !RegleCompte.Frein(51850, 53500, 50000, 2500, 100, 750),
           "frein apres blocage : MES sous 51 850 $ (coussin 1 750 $ au-dessus de 50 100 $)");
        Ok(!RegleCompte.Frein(40000, 50000, 50000, 2500, 100, 0), "frein a 0 : jamais");

        // 2. jours de la Fed
        var fed = new DateTime(2026, 10, 28);
        var m1 = AvecHistorique(true); m1.DebutSeance(fed, "Z26");
        var m0 = AvecHistorique(false); m0.DebutSeance(fed, "Z26");
        var m2 = AvecHistorique(true); m2.DebutSeance(new DateTime(2026, 10, 27), "Z26");
        Ok(m1.JourFed && !m1.ZoneActive, "mode a plat : pas de zone le 28 octobre 2026 (Fed)");
        Ok(!m0.JourFed && m0.ZoneActive, "ancien mode : la zone trade le jour de la Fed, comme avant");
        Ok(!m2.JourFed && m2.ZoneActive, "mode a plat : la zone trade la veille de la Fed");

        // 3. RSI(2) de nuit et positions par contrat
        var m = AvecHistorique(true); m.DebutSeance(new DateTime(2026, 10, 27), "Z26");
        m.PrixES = 6000;
        Ok(m.OuvrirNuit(25000).Count == 0 && m.RsiNuit == 0, "pas d'achat de nuit si la regle ne le veut pas");
        Poser(m, "NuitVoulue", true);
        Ok(m.OuvrirNuit(25000).Count == 1 && m.RsiNuit == 1 && m.PositionMES == 1 && m.PositionMNQ == 0, "achat de nuit : 1 MES, 0 MNQ");
        Ok(m.OuvrirNuit(25000).Count == 0, "pas de deuxieme achat la meme nuit");
        m.PrixES = 6010;
        Ok(Math.Abs(m.ValeurJourAPlat(25000) - (-2.25 + 50)) < 1e-9, "valeur du jour : +10 points de l'ES x 5 $ - 2,25 $ de frais d'entree");
        m.FermerNuit(25000);
        Ok(m.RsiNuit == 0 && Math.Abs(m.RealiseAPlat - (50 - 4.5)) < 1e-9, "vente a 9 h 30 : +50 $ - 4,50 $ d'aller-retour");
        Poser(m, "ZoneTenue", 1);
        m.ZoneSurMES = false;
        Ok(m.PositionMNQ == 1 && m.PositionMES == 0, "zone sans frein : 1 MNQ");
        m.ZoneSurMES = true;
        Ok(m.PositionMNQ == 0 && m.PositionMES == 1, "zone avec frein : 1 MES");
        m.OuvrirNuit(25000);
        Ok(m.PositionMES == 2, "zone sur MES + RSI(2) de nuit : 2 MES");

        // 4. plafond / limite du jour constate par l'hote : tout ferme, plus d'achat de nuit jusqu'a 18 h
        m.ArreterJournee(25000, "plafond du jour atteint");
        Ok(m.Arret && m.PositionMES == 0 && m.PositionMNQ == 0, "plafond : tout ferme");
        Ok(m.OuvrirNuit(25000).Count == 0, "plafond : pas d'achat de nuit avant 18 h");
        m.NouvelleJournee(25000);
        Ok(!m.Arret && m.RealiseAPlat == 0 && m.OuvrirNuit(25000).Count == 1, "18 h : journee neuve, achat de nuit de nouveau possible");

        // 5. ancien mode : positions inchangees (zone + RSI(2) en MNQ, rien en MES)
        var v = AvecHistorique(false);
        Poser(v, "ZoneTenue", -1);
        Ok(v.PositionMNQ == v.PositionNette && v.PositionMES == 0, "ancien mode : tout en MNQ, comme avant");

        Console.WriteLine(echecs == 0 ? "tous les controles passent" : $"{echecs} ECHEC(S)");
        return echecs == 0 ? 0 : 1;
    }
}
