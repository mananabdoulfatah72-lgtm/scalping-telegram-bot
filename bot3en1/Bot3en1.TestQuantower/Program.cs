using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using Bot3en1;
using TradingPlatform.BusinessLayer;

// Joue l'adaptateur Quantower sur des journees reelles : chaque minute devient 4 transactions (ouverture, plus haut avec
// les achats agressifs, plus bas avec les ventes agressives, cloture), l'horloge avance minute par minute, les ordres sont
// remplis tout de suite. Usage : test <dossier avec nq_1min.csv.gz> <minutes.csv.gz> <agresseurs.csv.gz> <debut> <fin>
// PLAFOND=500 : plafond du jour active ; une transaction est alors emise chaque soir a 19 h (au prix d'ouverture de la
// seance suivante) pour faire passer l'adaptateur par 18 h et par le plafond hors seance.
class Program
{
    static int Main(string[] a)
    {
        var inv = CultureInfo.InvariantCulture;
        string dossier = a[0];
        DateTime debut = DateTime.Parse(a[3], inv), fin = DateTime.Parse(a[4], inv);
        var seances = Rejoueur.LireMinutes(Rejoueur.Lignes(a[1]), fin, contratCalendrier: true);
        var agr = new Dictionary<(DateTime, int), (double, double)>();
        foreach (var l in Rejoueur.Lignes(a[2]).Skip(1))
        {
            var x = l.Split(',');
            agr[(DateTime.Parse(x[0], inv), int.Parse(x[1]))] = (double.Parse(x[2], inv), double.Parse(x[3], inv));
        }
        var ny = TimeZoneInfo.FindSystemTimeZoneById("America/New_York");
        DateTime Utc(DateTime t) => TimeZoneInfo.ConvertTimeToUtc(DateTime.SpecifyKind(t, DateTimeKind.Unspecified), ny);
        var horloge = Core.Instance.TimeUtils;
        var jours = seances.Keys.Where(j => j >= debut && j <= fin).ToList();
        string Nom(DateTime j, string racine) { var c = Calendrier.Contrat(j); return $"{racine}{c[0]}{c[^1]}"; }

        var strat = new Bot3en1Strategy
        {
            Compte = new Account(), SymboleNQ = new Symbol { Name = Nom(jours[0], "NQ") }, SymboleMNQ = new Symbol { Name = Nom(jours[0], "MNQ") },
            Dossier = dossier, AdresseHistorique = "http://127.0.0.1:9/absent",
            PlafondJour = double.Parse(Environment.GetEnvironmentVariable("PLAFOND") ?? "0", inv)
        };
        var tic = typeof(Bot3en1Strategy).GetMethod("Tic", BindingFlags.NonPublic | BindingFlags.Instance);
        horloge.DateTimeUtcNow = Utc(jours[0].AddHours(9).AddMinutes(29));
        strat.Lancer();
        ((IDisposable)typeof(Bot3en1Strategy).GetField("horloge", BindingFlags.NonPublic | BindingFlags.Instance).GetValue(strat))?.Dispose();
        if (strat.Arretee) { Console.WriteLine(string.Join("\n", strat.Logs)); return 1; }
        foreach (var j in jours)
        {
            strat.SymboleNQ.Name = Nom(j, "NQ"); strat.SymboleMNQ.Name = Nom(j, "MNQ");
            horloge.DateTimeUtcNow = Utc(j.AddHours(9).AddMinutes(29).AddSeconds(30));
            tic.Invoke(strat, null);
            var b = seances[j].b;
            int der = Array.FindLastIndex(b, x => x.Presente);
            for (int m = 0; m <= der; m++)
            {
                var t0 = j.AddMinutes(570 + m);
                if (b[m].Presente)
                {
                    agr.TryGetValue((j, m), out var av);
                    double reste = Math.Max(b[m].V - av.Item1 - av.Item2, 0);
                    void T(double p, double q, AggressorFlag f, int s) =>
                        strat.SymboleNQ.Emettre(new Last { Time = Utc(t0.AddSeconds(s)), Price = p, Size = q, AggressorFlag = f });
                    T(b[m].O, reste, AggressorFlag.None, 1); T(b[m].H, av.Item1, AggressorFlag.Buy, 2);
                    T(b[m].L, av.Item2, AggressorFlag.Sell, 3); T(b[m].C, 0, AggressorFlag.None, 4);
                }
                horloge.DateTimeUtcNow = Utc(t0.AddMinutes(1).AddSeconds(3));
                tic.Invoke(strat, null);
            }
            horloge.DateTimeUtcNow = Utc(j.AddHours(16).AddSeconds(30));
            tic.Invoke(strat, null);
            int i = jours.IndexOf(j);
            if (strat.PlafondJour > 0 && i + 1 < jours.Count && seances[jours[i + 1]].b[0].Presente)
            {
                var soir = j.AddHours(19);
                horloge.DateTimeUtcNow = Utc(soir);
                strat.SymboleNQ.Emettre(new Last { Time = Utc(soir), Price = seances[jours[i + 1]].b[0].O, Size = 1, AggressorFlag = AggressorFlag.None });
                horloge.DateTimeUtcNow = Utc(soir.AddSeconds(1));
                tic.Invoke(strat, null);
                horloge.DateTimeUtcNow = Utc(soir.AddSeconds(20));
                tic.Invoke(strat, null);
            }
        }
        var bot = (Moteur)typeof(Bot3en1Strategy).GetField("bot", BindingFlags.NonPublic | BindingFlags.Instance).GetValue(strat);
        double zone = 0, rsi = 0, eZ = 0, eR = 0; int sZ = 0, nZ = 0, nE = 0, nR = 0, nP = 0;
        bool zOuv = false, rOuv = false;
        foreach (var s in bot.Journal)
        {
            if (s.Source == "rsi2")
            {
                if (s.Texte.Contains("achat")) { eR = s.PrixReference; rsi -= 1.5; nR++; rOuv = true; }
                else { rsi += (s.PrixReference - eR) * 2 - 1.5; rOuv = false; }
            }
            else if (s.Source == "zone-ecarte") nE++;
            else if (s.Source == "zone")
            {
                if (s.Texte.StartsWith("sortie")) { zone += (sZ * (s.PrixReference - eZ) - 1.5) * 2; zOuv = false; }
                else { sZ = s.Texte.StartsWith("achat") ? 1 : -1; eZ = s.PrixReference; nZ++; zOuv = true; }
            }
            else if (s.Source == "plafond")                        // tout ferme au prix du declenchement
            {
                nP++;
                if (zOuv) { zone += (sZ * (s.PrixReference - eZ) - 1.5) * 2; zOuv = false; }
                if (rOuv) { rsi += (s.PrixReference - eR) * 2 - 1.5; rOuv = false; }
            }
        }
        File.WriteAllLines(Path.Combine(dossier, "test_journal.txt"), bot.Journal.Select(s => s.Texte));
        File.WriteAllLines(Path.Combine(dossier, "test_ordres.txt"), Core.Instance.Ordres);
        File.WriteAllLines(Path.Combine(dossier, "test_logs.txt"), strat.Logs);
        Console.WriteLine($"Zone : {nZ} trades gardes, {nE} ecartes, {zone:+0.0;-0.0} $ ; RSI(2) : {nR} entrees, {rsi:+0.0;-0.0} $ ;"
                          + $" total {zone + rsi:+0.0;-0.0} $ ; plafonds {nP} ; ordres envoyes {Core.Instance.Ordres.Count} ; position finale {strat_pos()}");
        int strat_pos() { var p = Core.Instance.Liste.FirstOrDefault(); return p == null ? 0 : (p.Side == Side.Buy ? 1 : -1) * (int)p.Quantity; }
        Console.WriteLine($"erreurs : {strat.Logs.Count(l => l.StartsWith("[Error]"))}");
        foreach (var l in strat.Logs.Where(l => l.StartsWith("[Error]")).Take(5)) Console.WriteLine("  " + l);
        return 0;
    }
}
