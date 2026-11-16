using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;
using Bot3en1.Flux;

// Rejoue le moteur FluxNQ sur les minutes de l'historique (Databento + export Rithmic) et compare ses trades a ceux du
// Python (flux/confluence.py <dossier>). Usage : Flux.Replay <dossier>. C1 est rejouee sans la condition du DOM.
class Program
{
    static IEnumerable<string> Lignes(string f)
    {
        using var s = File.OpenRead(f);
        using var z = f.EndsWith(".gz") ? (Stream)new GZipStream(s, CompressionMode.Decompress) : s;
        using var r = new StreamReader(z);
        string l;
        r.ReadLine();
        while ((l = r.ReadLine()) != null) yield return l;
    }

    static double D(string x) => string.IsNullOrEmpty(x) || x == "nan" ? double.NaN : double.Parse(x, CultureInfo.InvariantCulture);

    static int Main(string[] args)
    {
        string dossier = args[0];
        var inv = CultureInfo.InvariantCulture;
        var jours = new List<string>();
        var jouable = new Dictionary<string, bool>();
        foreach (var l in Lignes(Path.Combine(dossier, "seances.csv"))) { var c = l.Split(','); jours.Add(c[0]); jouable[c[0]] = c[1] == "1"; }
        var barres = jours.ToDictionary(j => j, j => new BarreFlux[MoteurFlux.N]);
        foreach (var l in Lignes(Path.Combine(dossier, "minutes.csv.gz")))
        {
            var c = l.Split(',');
            barres[c[0]][int.Parse(c[1])] = new BarreFlux { O = D(c[2]), H = D(c[3]), L = D(c[4]), C = D(c[5]), Achats = D(c[6]), Ventes = D(c[7]),
                                                             VentesBas2 = D(c[8]), AchatsHaut2 = D(c[9]), Presente = true };
        }
        var profils = new Dictionary<string, Dictionary<long, double>>();
        foreach (var l in Lignes(Path.Combine(dossier, "profils.csv.gz")))
        {
            var c = l.Split(',');
            if (!profils.TryGetValue(c[0], out var p)) profils[c[0]] = p = new Dictionary<long, double>();
            p[(long)Math.Round(D(c[1]) / 0.25)] = D(c[2]);
        }
        var moteur = new MoteurFlux { IgnorerDom = true };
        for (int i = 0; i < jours.Count; i++)
        {
            var prec = jours.Take(i).Select(j => barres[j]).ToList();
            profils.TryGetValue(i > 0 ? jours[i - 1] : "", out var pv);
            moteur.DebutSeance(DateTime.ParseExact(jours[i], "yyyy-MM-dd", inv), prec, pv, jouable[jours[i]]);
            for (int t = 0; t < MoteurFlux.N; t++) moteur.FermerMinute(t, barres[jours[i]][t]);
        }
        int erreurs = 0;
        foreach (var nom in new[] { "S1", "S2", "S2b", "C1" })
        {
            var attendus = Lignes(Path.Combine(dossier, $"attendus_{nom}.csv")).Select(l => l.Split(','))
                .Select(c => (jour: c[0], signal: int.Parse(c[1]), net: D(c[2]))).ToList();
            var obtenus = moteur.Trades.Where(t => t.Regle.Nom == nom && t.SortieMinute >= 0)
                .Select(t => (jour: t.Jour.ToString("yyyy-MM-dd"), signal: t.Signal, net: t.Net)).ToList();
            int ecarts = 0;
            for (int k = 0; k < Math.Max(attendus.Count, obtenus.Count); k++)
            {
                bool ok = k < attendus.Count && k < obtenus.Count && attendus[k].jour == obtenus[k].jour && attendus[k].signal == obtenus[k].signal
                          && Math.Abs(attendus[k].net - obtenus[k].net) < 1e-6;
                if (!ok && ecarts++ < 5)
                    Console.WriteLine($"  {nom} ecart n.{k} : attendu {(k < attendus.Count ? attendus[k].ToString() : "-")}, obtenu {(k < obtenus.Count ? obtenus[k].ToString() : "-")}");
            }
            Console.WriteLine($"{nom} : {obtenus.Count} trades du moteur C#, {attendus.Count} du Python, ecarts {ecarts}, net C# {obtenus.Sum(x => x.net):+0.00;-0.00} pt");
            erreurs += ecarts;
        }
        Console.WriteLine(erreurs == 0 ? "IDENTIQUE au Python" : $"DIFFERENT : {erreurs} ecart(s)");
        return erreurs == 0 ? 0 : 1;
    }
}
