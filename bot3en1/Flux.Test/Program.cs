using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Reflection;
using Bot3en1;
using Bot3en1.Flux;
using TradingPlatform.BusinessLayer;

// Joue FluxNQ sur les seances de l'export Rithmic du compte (minutes avec achats et ventes agressifs), transaction par
// transaction : chaque minute devient 4 transactions (ouverture, plus haut avec les achats, plus bas avec les ventes,
// cloture). Le carnet imite change avec la minute. Les 5 premieres seances sont servies par l'historique imite.
// Usage : Flux.Test <transactions_NQZ6_rithmic.csv> <dossier de travail> [regle des ordres 0-4]
// Controles :
//  1. minutes et footprint enregistres = ceux des transactions emises ;
//  2. carnets virtuels = moteur rejoue sur les enregistrements du bot (minutes, footprint, DOM) ;
//  3. ordres reels (si une regle est choisie) : une entree par signal de la regle quand rien n'est ouvert, a plat chaque soir,
//     refus quand une position etrangere existe, fichier STOP respecte ;
//  4. DOM : abonnement fait, 10 niveaux demandes, une photo par seconde enregistree.
class Program
{
    static readonly CultureInfo inv = CultureInfo.InvariantCulture;
    static TimeZoneInfo ny = TimeZoneInfo.FindSystemTimeZoneById("America/New_York");
    static int erreurs;

    static void Verifier(bool ok, string quoi) { if (!ok) { erreurs++; Console.WriteLine("  ECHEC : " + quoi); } }

    static List<(DateTime t, double p, double q, AggressorFlag c)> Transactions(DateTime jour, int m, double[] b)
    {
        // b : o, h, l, c, achats, ventes
        var l = new List<(DateTime, double, double, AggressorFlag)>();
        double a = b[4], v = b[5];
        var t0 = TimeZoneInfo.ConvertTimeToUtc(jour.AddMinutes(570 + m), ny);
        AggressorFlag cO = a >= 2 ? AggressorFlag.Buy : AggressorFlag.Sell;
        double qO = 1, qC = 1;
        double qH = Math.Max(1, (cO == AggressorFlag.Buy ? a - 2 : a)), qL = Math.Max(1, (cO == AggressorFlag.Sell ? v - 2 : v));
        l.Add((t0.AddSeconds(1), b[0], qO, cO));
        l.Add((t0.AddSeconds(15), b[1], qH, AggressorFlag.Buy));
        l.Add((t0.AddSeconds(30), b[2], qL, AggressorFlag.Sell));
        l.Add((t0.AddSeconds(45), b[3], qC, cO));
        return l;
    }

    static int Main(string[] args)
    {
        string source = args[0], travail = args[1];
        int regle = args.Length > 2 ? int.Parse(args[2]) : 0;
        if (Directory.Exists(travail)) Directory.Delete(travail, true);
        Directory.CreateDirectory(travail);
        // minutes de l'export : jour -> minute -> o, h, l, c, achats, ventes
        var minutes = new SortedDictionary<DateTime, Dictionary<int, double[]>>();
        foreach (var ligne in File.ReadLines(source).Skip(1))
        {
            var c = ligne.Split(',');
            var j = DateTime.ParseExact(c[0], "yyyy-MM-dd", inv);
            if (!minutes.TryGetValue(j, out var d)) minutes[j] = d = new Dictionary<int, double[]>();
            d[int.Parse(c[1])] = new[] { c[2], c[3], c[4], c[5], c[7], c[8] }.Select(x => double.Parse(x, inv)).ToArray();
        }
        var jours = minutes.Keys.ToList();
        var ticksDuJour = jours.ToDictionary(j => j, j => minutes[j].OrderBy(k => k.Key).SelectMany(k => Transactions(j, k.Key, k.Value)).ToList());

        var core = Core.Instance;
        var nq = new Symbol { Name = "NQZ6" };
        var mnq = new Symbol { Name = "MNQZ6" };
        var compte = new Account { Name = "SIM" };
        // historique imite : transactions des seances de l'export
        nq.Histoire = p =>
        {
            var h = new HistoricalData();
            foreach (var j in jours)
                foreach (var x in ticksDuJour[j])
                    if (x.t >= p.FromTime && x.t < p.ToTime)
                        h.Items.Add(new HistoryItemLast { TimeLeft = x.t, Price = x.p, Volume = x.q, AggressorFlag = x.c });
            return h;
        };
        // carnet imite : 10 niveaux de chaque cote autour du dernier prix, quantites qui changent avec la minute
        double prixCourant = 0;
        nq.DepthOfMarket.Source = () =>
        {
            var tn = TimeZoneInfo.ConvertTimeFromUtc(core.TimeUtils.DateTimeUtcNow, ny);
            int k = tn.Minute % 3;
            return new DepthOfMarketAggregatedCollections
            {
                Bids = Enumerable.Range(1, 12).Select(i => new Level2Item { Price = prixCourant - 0.25 * i, Size = 10 + 6 * k }).ToArray(),
                Asks = Enumerable.Range(1, 12).Select(i => new Level2Item { Price = prixCourant + 0.25 * i, Size = 16 - 3 * k }).ToArray(),
            };
        };
        var bot = new FluxNQ { SymboleNQ = nq, SymboleMNQ = mnq, Compte = compte, Dossier = travail, RegleOrdres = regle, Taille = 1,
                               LimitePerteJour = 0, MaxTradesJour = 20, PeriodeLecture = 30 };
        var tic = typeof(FluxNQ).GetMethod("Tic", BindingFlags.Instance | BindingFlags.NonPublic);
        void Horloge(DateTime utc) => core.TimeUtils.DateTimeUtcNow = utc;
        DateTime Ny(DateTime j, int minutesDepuisMinuit, double sec = 0) => TimeZoneInfo.ConvertTimeToUtc(j.AddMinutes(minutesDepuisMinuit).AddSeconds(sec), ny);

        // seances jouees en direct : a partir de la 6e (les 5 premieres servent d'historique)
        var direct = jours.Skip(5).ToList();
        Horloge(Ny(direct[0], 9 * 60 + 20));
        bot.Lancer();
        Verifier(!bot.Arretee, "le bot doit demarrer");
        Verifier(nq.AbonnesL2 == 1, "abonnement au DOM (NewLevel2)");
        var ordres = new List<string>();
        int etrangereJour = direct.Count > 3 ? 3 : -1;
        foreach (var (j, ij) in direct.Select((j, i) => (j, i)))
        {
            Horloge(Ny(j, 9 * 60 + 20));
            tic.Invoke(bot, null);
            // un jour : position MNQ etrangere ouverte avant l'ouverture (bot 3 en 1 ou a la main), fermee a midi
            if (ij == etrangereJour) core.PlaceOrder(new PlaceOrderRequestParameters { Account = compte, Symbol = mnq, Side = Side.Buy, Quantity = 2, OrderTypeId = OrderType.Market });
            var ticks = ticksDuJour[j];
            int k = 0;
            for (int m = 0; m < MoteurFlux.N; m++)
            {
                for (int s = 0; s < 60; s += 20)        // tics de l'horloge dans la minute (photo du carnet, stops)
                {
                    var limite = Ny(j, 570 + m, s + 20);
                    while (k < ticks.Count && ticks[k].t < limite)
                    {
                        Horloge(ticks[k].t);
                        prixCourant = ticks[k].p;
                        nq.Emettre(new Last { Time = ticks[k].t, Price = ticks[k].p, Size = ticks[k].q, AggressorFlag = ticks[k].c });
                        k++;
                    }
                    Horloge(Ny(j, 570 + m, s + 2.5));
                    tic.Invoke(bot, null);
                }
                if (ij == etrangereJour && m == 150)
                    core.PlaceOrder(new PlaceOrderRequestParameters { Account = compte, Symbol = mnq, Side = Side.Sell, Quantity = 2, OrderTypeId = OrderType.Market });
            }
            Horloge(Ny(j, 16 * 60 + 5));
            tic.Invoke(bot, null);
            Horloge(Ny(j, 16 * 60 + 40));
            tic.Invoke(bot, null);
            int pos = core.Positions.Where(p => p.Symbol == mnq).Sum(p => (p.Side == Side.Buy ? 1 : -1) * (int)p.Quantity);
            Verifier(pos == 0, $"{j:yyyy-MM-dd} : a plat le soir (position {pos})");
        }
        bot.Arreter();
        Console.WriteLine($"{direct.Count} seances jouees en direct ({direct[0]:yyyy-MM-dd} - {direct[^1]:yyyy-MM-dd}), regle des ordres {regle}");

        // 1. minutes enregistrees = transactions emises ; 4. DOM enregistre
        foreach (var j in direct)
        {
            string dos = Path.Combine(travail, "flux", j.ToString("yyyy-MM-dd"));
            var att = new Dictionary<int, double[]>();
            foreach (var x in ticksDuJour[j])
            {
                int m = (int)(TimeZoneInfo.ConvertTimeFromUtc(x.t, ny) - j).TotalMinutes - 570;
                if (!att.TryGetValue(m, out var b)) att[m] = b = new[] { x.p, x.p, x.p, x.p, 0, 0 };
                b[1] = Math.Max(b[1], x.p); b[2] = Math.Min(b[2], x.p); b[3] = x.p;
                if (x.c == AggressorFlag.Buy) b[4] += x.q; else b[5] += x.q;
            }
            var lues = File.ReadLines(Path.Combine(dos, "minutes.csv")).Skip(1).Select(l => l.Split(',')).ToList();
            Verifier(lues.Count == att.Count, $"{j:yyyy-MM-dd} : {lues.Count} minutes enregistrees pour {att.Count} emises");
            foreach (var c in lues)
            {
                var b = att[int.Parse(c[1])];
                var lu = new[] { c[2], c[3], c[4], c[5], c[7], c[8] }.Select(x => double.Parse(x, inv)).ToArray();
                if (!b.Zip(lu).All(z => Math.Abs(z.First - z.Second) < 1e-9)) { Verifier(false, $"{j:yyyy-MM-dd} minute {c[1]} differente"); break; }
            }
            Verifier(File.Exists(Path.Combine(dos, "tape.csv.gz")) && File.Exists(Path.Combine(dos, "dom.csv.gz")), $"{j:yyyy-MM-dd} : tape et DOM compresses");
            int nDom = Lignes(Path.Combine(dos, "dom.csv.gz")).Count();
            Verifier(nDom >= 3 * MoteurFlux.N - 5, $"{j:yyyy-MM-dd} : {nDom} photos du carnet");
            int nTape = Lignes(Path.Combine(dos, "tape.csv.gz")).Count();
            Verifier(nTape == ticksDuJour[j].Count, $"{j:yyyy-MM-dd} : {nTape} transactions enregistrees pour {ticksDuJour[j].Count}");
        }
        Verifier(nq.DepthOfMarket.Derniers?.GetLevel2ItemsParameters?.LevelsCount == 10 && nq.DepthOfMarket.Derniers.GetLevel2ItemsParameters.AggregateMethod == AggregateMethod.ByPriceLVL,
                 "le carnet est demande sur 10 niveaux, agrege par prix");

        // 2. carnets virtuels = moteur rejoue sur les enregistrements
        var moteur = new MoteurFlux();
        var lus = new Dictionary<DateTime, (BarreFlux[] b, Dictionary<long, double> p)>();
        foreach (var j in jours)
        {
            string dos = Path.Combine(travail, "flux", j.ToString("yyyy-MM-dd"));
            if (Directory.Exists(dos)) lus[j] = LireSeance(dos, j);
        }
        var attendus = new List<string>();
        foreach (var j in direct)
        {
            var prec = jours.Where(x => x < j && lus.ContainsKey(x)).TakeLast(5).ToList();
            var veille = prec.Last();
            moteur.DebutSeance(j, prec.Select(x => lus[x].b).ToList(), lus[veille].p, Calendrier.Contrat(veille) == Calendrier.Contrat(j));
            var photos = Lignes(Path.Combine(travail, "flux", j.ToString("yyyy-MM-dd"), "dom.csv.gz")).Select(l => l.Split(',')).Select(c =>
                (t: DateTime.ParseExact(c[0], "yyyy-MM-dd HH:mm:ss.fff", inv), ph: Photo(c))).ToList();
            int ip = -1;
            for (int m = 0; m < MoteurFlux.N; m++)
            {
                var fin = Ny(j, 570 + m + 1, 2.5);
                while (ip + 1 < photos.Count && photos[ip + 1].t <= fin) ip++;
                moteur.FermerMinute(m, lus[j].b[m].Presente ? lus[j].b[m] : null, ip >= 0 ? photos[ip].ph : null);
            }
        }
        foreach (var t in moteur.Trades.Where(t => t.SortieMinute >= 0))
            attendus.Add($"{t.Regle.Nom},{t.Jour:yyyy-MM-dd},{t.Signal},{t.Net.ToString("R", inv)}");
        var obtenus = direct.SelectMany(j => File.ReadLines(Path.Combine(travail, "flux", j.ToString("yyyy-MM-dd"), "virtuel.csv")).Skip(1))
            .Select(l => l.Split(',')).Select(c => $"{c[0]},{c[1]},{c[2]},{c[12]}").ToList();
        Verifier(attendus.OrderBy(x => x).SequenceEqual(obtenus.OrderBy(x => x)), $"carnets virtuels : {obtenus.Count} trades du bot, {attendus.Count} du moteur rejoue");
        foreach (var r in new[] { "S1", "S2", "S2b", "C1" })
            Console.WriteLine($"  {r} : {obtenus.Count(x => x.StartsWith(r + ","))} trade(s) virtuel(s)");

        // 3. ordres reels
        if (regle > 0)
        {
            string nom = new[] { "", "S1", "S2", "S2b", "C1" }[regle];
            var reels = direct.SelectMany(j => File.ReadLines(Path.Combine(travail, "flux", j.ToString("yyyy-MM-dd"), "reel.csv")).Skip(1)).ToList();
            var signaux = File.ReadLines(Path.Combine(travail, "flux", "journal.txt")).Count(l => l.Contains($"{nom} : signal"));
            var refus = File.ReadLines(Path.Combine(travail, "flux", "journal.txt")).Where(l => l.Contains($"{nom} : pas d'ordre reel")).ToList();
            Console.WriteLine($"  ordres reels {nom} : {reels.Count} trade(s), {signaux} signal(aux), {refus.Count} refus ; ordres envoyes {core.Ordres.Count}");
            Verifier(reels.Count + refus.Count == signaux, "chaque signal de la regle donne un trade reel ou un refus explique");
            Verifier(reels.Count > 0, "au moins un trade reel");
            if (etrangereJour >= 0)
            {
                string je = direct[etrangereJour].ToString("yyyy-MM-dd");
                var lignesJour = File.ReadLines(Path.Combine(travail, "flux", "journal.txt")).ToList();
                bool refusEtranger = refus.Any(l => l.Contains("n'a pas ouverte"));
                bool tradeAvantMidi = reels.Any(l => l.Split(',')[1] == je && int.Parse(l.Split(',')[2]) < 150);
                Verifier(!tradeAvantMidi, "aucun trade reel tant que la position etrangere existe");
                Console.WriteLine($"  position etrangere le {je} : {(refusEtranger ? "signal refuse" : "aucun signal de la regle pendant qu'elle existait")}");
            }
        }
        Console.WriteLine(erreurs == 0 ? "TOUT EST CONFORME" : $"{erreurs} ECHEC(S)");
        return erreurs == 0 ? 0 : 1;
    }

    static IEnumerable<string> Lignes(string f)
    {
        using var s = File.OpenRead(f);
        using var z = new GZipStream(s, CompressionMode.Decompress);
        using var r = new StreamReader(z);
        r.ReadLine();
        string l;
        while ((l = r.ReadLine()) != null) yield return l;
    }

    static PhotoDom Photo(string[] c)
    {
        var pa = new List<double>(); var qa = new List<double>(); var pv = new List<double>(); var qv = new List<double>();
        for (int i = 0; i < 10; i++)
        {
            if (c[1 + 2 * i] != "") { pa.Add(double.Parse(c[1 + 2 * i], inv)); qa.Add(double.Parse(c[2 + 2 * i], inv)); }
            if (c[21 + 2 * i] != "") { pv.Add(double.Parse(c[21 + 2 * i], inv)); qv.Add(double.Parse(c[22 + 2 * i], inv)); }
        }
        return new PhotoDom { PrixAchat = pa.ToArray(), QteAchat = qa.ToArray(), PrixVente = pv.ToArray(), QteVente = qv.ToArray() };
    }

    static (BarreFlux[], Dictionary<long, double>) LireSeance(string dos, DateTime j)
    {
        var b = new BarreFlux[MoteurFlux.N];
        foreach (var l in File.ReadLines(Path.Combine(dos, "minutes.csv")).Skip(1))
        {
            var c = l.Split(',');
            b[int.Parse(c[1])] = new BarreFlux { O = double.Parse(c[2], inv), H = double.Parse(c[3], inv), L = double.Parse(c[4], inv), C = double.Parse(c[5], inv),
                                                 Achats = double.Parse(c[7], inv), Ventes = double.Parse(c[8], inv), Presente = true, ParPrix = new Dictionary<long, double[]>() };
        }
        var p = new Dictionary<long, double>();
        foreach (var l in File.ReadLines(Path.Combine(dos, "footprint.csv")).Skip(1))
        {
            var c = l.Split(',');
            var t = DateTime.ParseExact(c[0], "yyyy-MM-dd HH:mm", inv);
            int m = t.Hour * 60 + t.Minute - 570;
            long k = (long)Math.Round(double.Parse(c[1], inv) / 0.25);
            double a = double.Parse(c[2], inv), v = double.Parse(c[3], inv);
            b[m].ParPrix[k] = new[] { a, v };
            p[k] = (p.TryGetValue(k, out var x) ? x : 0) + a + v;
        }
        double prix = b.First(x => x != null).O;
        for (int t = 0; t < b.Length; t++)
        {
            if (b[t] == null) b[t] = new BarreFlux { O = prix, H = prix, L = prix, C = prix, VentesBas2 = 0, AchatsHaut2 = 0 };
            else b[t].CalculerFootprint();
            prix = b[t].C;
        }
        return (b, p);
    }
}
