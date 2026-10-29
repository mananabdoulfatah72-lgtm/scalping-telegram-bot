using System;
using System.Collections.Generic;
using Bot3en1;

// Controles du plafond du jour (static50k/ : gain de la journee de trading mesure depuis 17 h la veille, verifie aussi
// hors seance, arret jusqu'a 18 h). Usage : dotnet run --project Bot3en1.TestPlafond
class Program
{
    static int echecs = 0;
    static void Verifier(bool ok, string quoi) { Console.WriteLine($"{(ok ? "ok" : "ECHEC")} : {quoi}"); if (!ok) echecs++; }
    static bool Proche(double a, double b) => Math.Abs(a - b) < 1e-9;

    static Moteur Nouveau(double plafond)
    {
        var bot = new Moteur(new List<Resume>()) { PlafondJour = plafond };
        bot.DebutSeance(new DateTime(2026, 10, 7), "Z26");          // sans historique : zone inactive, RSI(2) seul
        return bot;
    }

    static Barre B(double c) => new Barre { O = c, H = c, L = c, C = c, V = 1, Presente = true };

    static int Main()
    {
        // 1. RSI(2) achete il y a plusieurs jours a 100, garde la nuit ; la journee commence a 110 (prix de 17 h la veille)
        var bot = Nouveau(500);
        bot.RestaurerRsi(true, 100);
        bot.NouvelleJournee(110);
        Verifier(Proche(bot.ValeurJour(120), 20), "gain du jour compte depuis 17 h la veille (+10 points = +20 $), pas depuis l'achat");
        Verifier(Proche(bot.ValeurJour(110), 0), "gain du jour nul au prix de reference");

        // 2. hors seance : +250 points dans la journee = +500 $ -> RSI(2) ferme, arret jusqu'a 18 h
        Verifier(!bot.VerifierPlafondHorsSeance(359.75), "plafond pas atteint a +499,50 $");
        Verifier(bot.VerifierPlafondHorsSeance(360), "plafond atteint a +500 $ hors seance");
        Verifier(bot.Rsi == 0 && bot.Arret && bot.PositionNette == 0, "RSI(2) ferme, plus de position, arret");
        Verifier(Proche(bot.RealiseJour, 500 - 1.5), "gain realise du jour = +500 $ - frais d'un ordre");
        Verifier(!bot.VerifierPlafondHorsSeance(400), "pas de second declenchement le meme jour");

        // 3. 18 h : nouvelle journee, plafond leve, gain du jour a zero
        bot.NouvelleJournee(360);
        Verifier(!bot.Arret && Proche(bot.RealiseJour, 0), "18 h : plafond leve et gain du jour remis a zero");

        // 4. en seance : RSI(2) garde depuis la veille, plafond mesure depuis la reference, ferme a la cloture de la minute
        var b2 = Nouveau(500);
        b2.RestaurerRsi(true, 100);
        b2.NouvelleJournee(300);                                    // le RSI(2) a deja gagne 400 $ avant cette journee
        var s1 = b2.MinuteFermee(0, B(400));                        // +100 points dans la journee = +200 $
        Verifier(s1.Count == 0 && b2.Rsi == 1, "en seance : +200 $ dans la journee, pas de plafond (l'ancien calcul aurait dit +600 $)");
        var s2 = b2.MinuteFermee(1, B(550));                        // +250 points = +500 $
        Verifier(s2.Exists(x => x.Source == "plafond") && b2.Rsi == 0 && b2.Arret, "en seance : plafond a +500 $, tout ferme");
        Verifier(Proche(b2.RealiseJour, 500 - 1.5), "gain realise du jour en seance = +500 $ - frais");

        // 5. plafond a 0 : jamais de declenchement
        var b3 = Nouveau(0);
        b3.RestaurerRsi(true, 100);
        b3.NouvelleJournee(100);
        Verifier(!b3.VerifierPlafondHorsSeance(100000) && b3.MinuteFermee(0, B(100000)).Count == 0 && b3.Rsi == 1,
                 "plafond 0 : aucun declenchement");

        // 6. redemarrage apres un plafond atteint dans la journee : arret retabli
        var b4 = Nouveau(500);
        b4.ArreterJusqua18h();
        Verifier(b4.Arret, "redemarrage : arret jusqu'a 18 h retabli");

        // 7. redemarrage en cours de journee : gain deja realise (+400 $) et reference du RSI(2) repris
        var b5 = Nouveau(500);
        b5.RestaurerRsi(true, 100);
        b5.RestaurerJournee(400, 200, false);
        Verifier(Proche(b5.ValeurJour(240), 480), "redemarrage : +400 $ realises + 40 points du RSI(2) depuis sa reference = +480 $");
        Verifier(!b5.VerifierPlafondHorsSeance(240) && b5.VerifierPlafondHorsSeance(250),
                 "redemarrage : le plafond tient compte du gain deja realise (+500 $ atteint a 250)");

        Console.WriteLine(echecs == 0 ? "tous les controles passent" : $"{echecs} echec(s)");
        return echecs == 0 ? 0 : 1;
    }
}
