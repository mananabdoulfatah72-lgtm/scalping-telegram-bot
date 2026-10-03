using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Bot3en1;

// Rejeu du bot 3 en 1 sur des barres d'une minute (CSV : t,o,h,l,c,v,contrat) et des volumes agresseurs par minute
// (CSV : jour,minute,achats,ventes). Verifie que le moteur C# prend exactement les decisions du robot Python.
// Usage : rejeu <minutes.csv[.gz]> <agresseurs.csv[.gz]|-> <debut AAAA-MM-JJ> <fin AAAA-MM-JJ> [historique_sortie.csv]
// SANS_FILTRE=1 : zone sans le filtre delta. CONTRAT_CALENDRIER=1 : contrats de la regle du calendrier (comme en direct).
class Program
{
    static int Main(string[] a)
    {
        var inv = CultureInfo.InvariantCulture;
        DateTime debut = DateTime.Parse(a[2], inv), fin = DateTime.Parse(a[3], inv);
        var seances = Rejoueur.LireMinutes(Rejoueur.Lignes(a[0]), fin, Environment.GetEnvironmentVariable("CONTRAT_CALENDRIER") == "1");
        var agr = new Dictionary<(DateTime, int), (double, double)>();
        if (a[1] != "-")
            foreach (var l in Rejoueur.Lignes(a[1]).Skip(1))
            {
                var x = l.Split(',');
                agr[(DateTime.Parse(x[0], inv), int.Parse(x[1]))] = (double.Parse(x[2], inv), double.Parse(x[3], inv));
            }
        foreach (var kv in seances)
            for (int m = 0; m < Moteur.N; m++)
                if (agr.TryGetValue((kv.Key, m), out var av)) { kv.Value.b[m].Achats = av.Item1; kv.Value.b[m].Ventes = av.Item2; }
        // contrat de la seance ok suivante, tire des donnees (comme robot.py rsi2)
        var ok = seances.Where(kv => Rejoueur.RsiOk(kv.Key, kv.Value.b)).Select(kv => kv.Key).ToList();
        var suivant = new Dictionary<DateTime, string>();
        for (int i = 0; i < ok.Count; i++) suivant[ok[i]] = seances[i + 1 < ok.Count ? ok[i + 1] : ok[i]].contrat;
        var bot = new Moteur(new List<Resume>()) { ContratSuivant = (j, c) => suivant.TryGetValue(j, out var s) ? s : c,
                                                    FiltreDelta = Environment.GetEnvironmentVariable("SANS_FILTRE") != "1" };
        var trades = new List<string>();
        double zone = 0, rsi = 0, entreeZ = 0, entreeR = 0; int sensZ = 0, nZone = 0, nEcartes = 0, nRsi = 0;
        bool demarre = false;
        foreach (var kv in seances)
        {
            var j = kv.Key;
            if (!demarre && j >= debut) { demarre = true; bot.RemettreAPlat(); }
            Rejoueur.JouerSeance(bot, j, kv.Value.b, kv.Value.contrat, s =>
            {
                if (!demarre) return;
                if (s.Source == "rsi2")
                {
                    if (bot.Rsi == 1) { entreeR = s.PrixReference; rsi -= 1.5; nRsi++; }
                    else rsi += (s.PrixReference - entreeR) * 2 - 1.5;
                }
                else if (s.Source == "zone-ecarte") nEcartes++;
                else if (s.Source == "zone")
                {
                    if (s.Texte.StartsWith("sortie")) zone += (sensZ * (s.PrixReference - entreeZ) - 1.5) * 2;
                    else { sensZ = s.Texte.StartsWith("achat") ? 1 : -1; entreeZ = s.PrixReference; nZone++; }
                }
                trades.Add($"{j:yyyy-MM-dd} {s.Texte}");
            });
            if (j == fin) break;
        }
        foreach (var t in trades) Console.WriteLine(t);
        Console.WriteLine($"\nZone : {nZone} trades gardes, {nEcartes} ecartes, {zone:+0.0;-0.0} $ (1 MNQ)");
        Console.WriteLine($"RSI(2) : {nRsi} entrees, {rsi:+0.0;-0.0} $ (trades fermes){(bot.Rsi == 1 ? " ; position encore ouverte" : "")}");
        Console.WriteLine($"Total : {zone + rsi:+0.0;-0.0} $");
        if (a.Length > 4) { bot.EcrireHistorique(a[4]); Console.WriteLine($"historique ecrit : {bot.Historique.Count} seances"); }
        return 0;
    }
}
