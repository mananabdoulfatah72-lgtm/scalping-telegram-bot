using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Net.Http;
using System.Threading;
using RelaisNQ;
using TradingPlatform.BusinessLayer;

// Usage : test <dossier vide> <minutes.csv (t,o,h,l,c,v,...)> <page station-direct.html> <jour AAAA-MM-JJ> <ms par minute> [secondes de service apres la seance]
// Les seances avant <jour> deviennent la copie locale de l'historique du robot ; <jour> est joue en transactions (4 par minute),
// l'horloge avance minute par minute ; un faux journal d'agent recoit une ligne par trade ; une position MNQ est ouverte a 11 h.
class Program
{
    static int Main(string[] a)
    {
        var inv = CultureInfo.InvariantCulture;
        string dossier = a[0]; Directory.CreateDirectory(dossier);
        var jour = DateTime.Parse(a[3], inv); int pas = int.Parse(a[4]); int servir = a.Length > 5 ? int.Parse(a[5]) : 0;
        var lignes = File.ReadAllLines(a[1]);
        using (var gz = new GZipStream(File.Create(Path.Combine(dossier, "nq_1min.csv.gz")), CompressionLevel.Fastest))
        using (var w = new StreamWriter(gz)) { w.WriteLine(lignes[0]); foreach (var l in lignes.Skip(1)) if (string.CompareOrdinal(l, 0, a[3], 0, 10) < 0) w.WriteLine(l); }
        File.Copy(a[2], Path.Combine(dossier, "station-direct.html"), true);
        var agent = Path.Combine(dossier, "SupertrendNQ"); Directory.CreateDirectory(agent); File.WriteAllText(Path.Combine(agent, "journal.txt"), "");
        var du_jour = lignes.Skip(1).Where(l => l.StartsWith(a[3])).Select(l => l.Split(',')).ToList();
        var ny = TimeZoneInfo.FindSystemTimeZoneById("America/New_York");
        DateTime Utc(DateTime t) => TimeZoneInfo.ConvertTimeToUtc(DateTime.SpecifyKind(t, DateTimeKind.Unspecified), ny);
        var horloge = Core.Instance.TimeUtils;
        var compte = new Account { Name = "BX-TEST", Balance = 50000 };
        var mnq = new Symbol { Name = "MNQZ6" };
        var r = new RelaisStrategy { SymboleNQ = new Symbol { Name = "NQZ6" }, Compte = compte, SymboleMNQ = mnq, Dossier = dossier,
                                     DossiersAgents = agent, AdresseHistorique = "http://127.0.0.1:9/absent", Port = int.Parse(Environment.GetEnvironmentVariable("PORT") ?? "8765") };
        horloge.DateTimeUtcNow = Utc(jour.AddHours(9).AddMinutes(25));
        r.Lancer();
        if (r.Arretee) { Console.WriteLine("ECHEC : relais arrete au lancement"); r.Logs.ForEach(Console.WriteLine); return 1; }
        r.Logs.ForEach(Console.WriteLine);
        var client = new HttpClient { BaseAddress = new Uri($"http://localhost:{r.Port}") };
        var hist = client.GetStringAsync("/historique").Result;
        Console.WriteLine($"/historique : {hist.Length / 1024} Ko, seances : {System.Text.Json.JsonDocument.Parse(hist).RootElement.GetProperty("nq").GetProperty("jours").GetArrayLength()}");
        var page = client.GetStringAsync("/").Result; Console.WriteLine($"/ : {page.Length / 1024} Ko de page");
        // un lecteur du flux en parallele
        int evenements = 0; string dernier = "";
        var lecteur = new Thread(() => { try { using var s = client.GetStreamAsync("/flux").Result; using var rd = new StreamReader(s);
            string l; while ((l = rd.ReadLine()) != null) if (l.StartsWith("data: ")) { evenements++; dernier = l; } } catch { } }) { IsBackground = true };
        lecteur.Start();
        var rnd = new Random(1);
        foreach (var x in du_jour)
        {
            var t = DateTime.ParseExact(x[0], "yyyy-MM-dd HH:mm", inv);
            double o = double.Parse(x[1], inv), h = double.Parse(x[2], inv), l = double.Parse(x[3], inv), c = double.Parse(x[4], inv), v = double.Parse(x[5], inv);
            foreach (var (s, p, f) in new[] { (0, o, AggressorFlag.Buy), (15, h, AggressorFlag.Buy), (30, l, AggressorFlag.Sell), (45, c, rnd.Next(2) == 0 ? AggressorFlag.Buy : AggressorFlag.Sell) })
            {
                horloge.DateTimeUtcNow = Utc(t.AddSeconds(s));
                r.SymboleNQ.Emettre(new Last { Time = Utc(t.AddSeconds(s)), Price = p, Size = Math.Max(1, Math.Round(v / 4)), AggressorFlag = f });
            }
            int m = t.Hour * 60 + t.Minute - 570;
            if (m == 5) File.AppendAllText(Path.Combine(agent, "journal.txt"), $"{horloge.DateTimeUtcNow:yyyy-MM-dd HH:mm:ss} UTC achat 15h35 (Paris) a {o.ToString("F2", inv)} (Supertrend haussier, test)\n");
            if (m == 90) { Core.Instance.Liste.Add(new Position { Account = compte, Symbol = mnq, Side = Side.Buy, Quantity = 1, GrossPnL = new PnLItem { Value = 12.5 } }); }
            if (m == 115) File.AppendAllText(Path.Combine(agent, "journal.txt"), $"{horloge.DateTimeUtcNow:yyyy-MM-dd HH:mm:ss} UTC sortie de l'achat 17h25 (Paris) a {o.ToString("F2", inv)} (retournement du Supertrend, test)\n");
            horloge.DateTimeUtcNow = Utc(t.AddSeconds(59));
            Thread.Sleep(pas);
        }
        Thread.Sleep(Math.Max(600, servir * 1000));
        Console.WriteLine($"/flux : {evenements} evenements recus ; dernier : {(dernier.Length > 300 ? dernier.Substring(0, 300) + "..." : dernier)}");
        r.Arreter();
        return evenements > 0 ? 0 : 2;
    }
}
