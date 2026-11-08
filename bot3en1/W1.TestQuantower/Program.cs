using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Reflection;
using Bot3en1;
using W1NQ;
using TradingPlatform.BusinessLayer;

// Joue la strategie Quantower W1 NQ sur des journees reelles : chaque minute devient 4 transactions (ouverture, plus haut,
// plus bas, cloture), l'horloge avance minute par minute (tic 3 s apres chaque minute), les ordres sont remplis tout de suite.
// Compare les ordres au rejeu verifie du moteur (memes minutes, memes positions).
// Usage : test <dossier vide> <minutes.csv> <debut> <fin>
// Scenarios (premier jour seulement) : LIMITE=300 (limite du jour), MAIN=12:00 (position fermee a la main a la fin de cette
// minute), REPRISE=12:00 (strategie relancee a cette minute, position gardee, historique des transactions fourni),
// STOP_DE=12:00 STOP_A=12:30 (fichier STOP), OBJECTIF=50500 avec SOLDE=50000 (le solde suit les gains de la strategie).
class Program
{
    static int Main(string[] a)
    {
        var inv = CultureInfo.InvariantCulture;
        string dossier = a[0];
        Directory.CreateDirectory(dossier);
        foreach (var f in new[] { "etat.json", "journal.txt", "STOP" }) File.Delete(Path.Combine(dossier, f));
        DateTime debut = DateTime.Parse(a[2], inv), fin = DateTime.Parse(a[3], inv);
        var lignes = RejeuW1.Lignes(a[1]).ToList();
        var tous = RejeuW1.LireJours(lignes, fin);
        // historique de la strategie : toutes les minutes avant le premier jour (copie locale, l'adresse ne repond pas)
        using (var gz = new GZipStream(File.Create(Path.Combine(dossier, "nq_1min.csv.gz")), CompressionLevel.Fastest))
        using (var w = new StreamWriter(gz))
        {
            w.WriteLine(lignes[0]);
            foreach (var l in lignes.Skip(1)) if (string.CompareOrdinal(l, 0, debut.ToString("yyyy-MM-dd"), 0, 10) < 0) w.WriteLine(l);
        }
        // reference : le moteur rejoue sur tout, trades des jours testes
        var refb = new MoteurW1(Arbres.Lire(typeof(MoteurW1).Assembly.GetManifestResourceStream("modele_w1.json")));
        RejeuW1.Jouer(refb, tous);
        var jours = tous.Keys.Where(j => j >= debut && j <= fin).ToList();
        var attendus = new List<string>();
        foreach (var t in refb.Trades.Where(t => t.Jour >= debut))
        {
            attendus.Add($"{t.Jour:yyyy-MM-dd} {t.MinuteEntree} -> {t.Sens}");
            attendus.Add($"{t.Jour:yyyy-MM-dd} {t.MinuteSortie} -> 0");
        }
        // une sortie et une entree a la meme minute = un retournement
        var reference = attendus.GroupBy(x => x.Substring(0, x.IndexOf(" ->"))).Select(g => g.Last()).ToList();

        var ny = TimeZoneInfo.FindSystemTimeZoneById("America/New_York");
        DateTime Utc(DateTime t) => TimeZoneInfo.ConvertTimeToUtc(DateTime.SpecifyKind(t, DateTimeKind.Unspecified), ny);
        var horloge = Core.Instance.TimeUtils;
        string Nom(DateTime j, string r) { var c = Calendrier.Contrat(j); return $"{r}{c[0]}{c[^1]}"; }
        string Env(string k) => Environment.GetEnvironmentVariable(k);
        var compte = new Account { Balance = double.Parse(Env("SOLDE") ?? "0", inv) };
        W1Strategy Nouvelle() => new W1Strategy
        {
            Compte = compte, SymboleNQ = new Symbol { Name = Nom(jours[0], "NQ") }, SymboleMNQ = new Symbol { Name = Nom(jours[0], "MNQ") },
            Dossier = dossier, AdresseHistorique = "http://127.0.0.1:9/absent", Papier = Env("PAPIER") == "1", Taille = int.Parse(Env("TAILLE") ?? "1", inv),
            LimiteJour = double.Parse(Env("LIMITE") ?? "0", inv), Objectif = double.Parse(Env("OBJECTIF") ?? "0", inv)
        };
        var strat = Nouvelle();
        var tic = typeof(W1Strategy).GetMethod("Tic", BindingFlags.NonPublic | BindingFlags.Instance);
        TimeSpan? Heure(string k) => Env(k) is string s ? TimeSpan.Parse(s, inv) : null;
        var main = Heure("MAIN"); var reprise = Heure("REPRISE"); var stopDe = Heure("STOP_DE"); var stopA = Heure("STOP_A");
        int Pos(Symbol s) { var p = Core.Instance.Liste.FirstOrDefault(x => x.Symbol == s); return p == null ? 0 : (p.Side == Side.Buy ? 1 : -1) * (int)p.Quantity; }

        horloge.DateTimeUtcNow = Utc(jours[0].AddHours(9).AddMinutes(20));
        strat.Lancer();
        if (strat.Arretee) { Console.WriteLine("ECHEC : la strategie s'est arretee au lancement"); strat.Logs.ForEach(Console.WriteLine); return 1; }
        var vus = new List<string>();
        var ticksDuJour = new List<HistoryItemLast>();
        int posAvant = 0;
        double soldeDepart = compte.Balance, prixMNQ = 0, entreePrix = 0;
        foreach (var j in jours)
        {
            var b = tous[j];
            ticksDuJour.Clear();
            horloge.DateTimeUtcNow = Utc(j.AddHours(9).AddMinutes(29).AddSeconds(30));
            tic.Invoke(strat, null);
            for (int m = 0; m < MoteurW1.N; m++)
            {
                var t0 = j.AddMinutes(570 + m);
                if (!double.IsNaN(b[3][m]))
                    foreach (var (dt, p) in new[] { (0, b[0][m]), (15, b[1][m]), (30, b[2][m]), (45, b[3][m]) })
                    {
                        horloge.DateTimeUtcNow = Utc(t0.AddSeconds(dt));
                        double q = double.IsNaN(b[4][m]) ? 0 : b[4][m] / 4;          // volume de la minute en 4 parts (VWAP identique)
                        var last = new Last { Time = Utc(t0.AddSeconds(dt)), Price = p, Size = q };
                        ticksDuJour.Add(new HistoryItemLast { TimeLeft = last.Time, Price = p, Volume = q });
                        strat.SymboleNQ.Emettre(last);
                        prixMNQ = p;
                    }
                // scenarios du premier jour
                if (j == jours[0] && main.HasValue && t0.TimeOfDay == main.Value && Pos(strat.SymboleMNQ) != 0)
                {
                    Core.Instance.Liste.Clear();
                    vus.Add($"{j:yyyy-MM-dd} {m + 1} -> 0 (a la main)");
                }
                if (j == jours[0] && stopDe.HasValue && t0.TimeOfDay == stopDe.Value) File.WriteAllText(Path.Combine(dossier, "STOP"), "");
                if (j == jours[0] && stopA.HasValue && t0.TimeOfDay == stopA.Value) File.Delete(Path.Combine(dossier, "STOP"));
                if (j == jours[0] && reprise.HasValue && t0.TimeOfDay == reprise.Value)
                {
                    // relance sans arret (coupure de Quantower) : la position reste, l'historique de la seance est fourni
                    horloge.DateTimeUtcNow = Utc(t0.AddMinutes(1).AddSeconds(1));
                    var copie = ticksDuJour.ToList();
                    strat = Nouvelle();
                    strat.SymboleNQ.Histoire = p => { var h = new HistoricalData(); h.Items.AddRange(copie.Where(x => x.TimeLeft >= p.FromTime && x.TimeLeft < p.ToTime)); return h; };
                    var ancienne = Core.Instance.Liste.FirstOrDefault();
                    if (ancienne != null) ancienne.Symbol = strat.SymboleMNQ;
                    strat.Lancer();
                    vus.Add($"{j:yyyy-MM-dd} {m + 1} relance");
                }
                horloge.DateTimeUtcNow = Utc(t0.AddMinutes(1).AddSeconds(3));
                tic.Invoke(strat, null);
                int pos = Pos(strat.SymboleMNQ);
                if (pos != posAvant)
                {
                    // solde du compte : suit les gains (pour l'objectif), au prix de la cloture de la minute
                    if (posAvant != 0) compte.Balance += posAvant * (prixMNQ - entreePrix) * 2;
                    entreePrix = prixMNQ;
                    vus.Add($"{j:yyyy-MM-dd} {m + 1} -> {pos / strat.Taille}");
                    posAvant = pos;
                }
            }
            horloge.DateTimeUtcNow = Utc(j.AddHours(16).AddSeconds(30));
            tic.Invoke(strat, null);
            if (Pos(strat.SymboleMNQ) != 0) { Console.WriteLine($"ECHEC : position ouverte apres 16 h le {j:yyyy-MM-dd}"); return 1; }
        }
        File.WriteAllLines(Path.Combine(dossier, "test_ordres.txt"), vus);
        File.WriteAllLines(Path.Combine(dossier, "test_reference.txt"), reference);
        File.WriteAllLines(Path.Combine(dossier, "test_logs.txt"), strat.Logs);
        bool scenario = main.HasValue || reprise.HasValue || stopDe.HasValue || strat.LimiteJour > 0 || strat.Objectif > 0;
        var vusComp = vus.Where(x => !x.Contains("main") && !x.Contains("relance")).ToList();
        // jours a comparer : tous sauf le premier quand un scenario le change
        bool Complete(DateTime j) { var c = tous[j][3]; return !double.IsNaN(c[0]) && !double.IsNaN(c[MoteurW1.N - 1]) && c.Count(x => !double.IsNaN(x)) >= 370; }
        var incompletes = jours.Where(j => !Complete(j)).ToList();
        if (incompletes.Count > 0) Console.WriteLine("seances incompletes dans les donnees (non comparees) : " + string.Join(", ", incompletes.Select(j => j.ToString("yyyy-MM-dd"))));
        var comparer = jours.Where(j => !(scenario && j == jours[0]) && !Calendrier.JourCourt(j) && Complete(j)).Select(j => j.ToString("yyyy-MM-dd")).ToHashSet();
        var v = vusComp.Where(x => comparer.Contains(x.Substring(0, 10))).ToList();
        var r = reference.Where(x => comparer.Contains(x.Substring(0, 10))).ToList();
        int diff = v.Except(r).Count() + r.Except(v).Count();
        Console.WriteLine($"{jours.Count} seances, {r.Count} changements de position attendus, {v.Count} vus ; differences : {diff}");
        foreach (var x in v.Except(r).Take(5)) Console.WriteLine($"  en trop : {x}");
        foreach (var x in r.Except(v).Take(5)) Console.WriteLine($"  manquant : {x}");
        if (scenario)
        {
            Console.WriteLine("premier jour, strategie :  " + string.Join(" | ", vus.Where(x => x.StartsWith(jours[0].ToString("yyyy-MM-dd"))).Select(x => x.Substring(11))));
            Console.WriteLine("premier jour, reference :  " + string.Join(" | ", reference.Where(x => x.StartsWith(jours[0].ToString("yyyy-MM-dd"))).Select(x => x.Substring(11))));
            foreach (var l in strat.Logs.Where(l => l.Contains("limite") || l.Contains("main") || l.Contains("STOP") || l.Contains("OBJECTIF") || l.Contains("reprise") || l.Contains("lancement")).Take(12))
                Console.WriteLine("  " + l);
        }
        return diff == 0 ? 0 : 2;
    }
}
