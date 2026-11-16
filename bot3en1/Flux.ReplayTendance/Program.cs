using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;
using Bot3en1.Flux;

// Rejoue MoteurTendance sur les fichiers de flux/tendance_ref.py et compare le gain de chaque seance (H1, H5, H12, F3, L2) a
// celui du code de la recherche (L2 : flux/gamma_0dte.py). Usage : Flux.ReplayTendance <dossier>
class Program
{
    static IEnumerable<string> Lignes(string f)
    {
        using var s = File.OpenRead(f);
        using var z = f.EndsWith(".gz") ? (Stream)new GZipStream(s, CompressionMode.Decompress) : s;
        using var r = new StreamReader(z);
        r.ReadLine();
        string l;
        while ((l = r.ReadLine()) != null) yield return l;
    }

    static double D(string x) => string.IsNullOrEmpty(x) || x == "nan" ? double.NaN : double.Parse(x, CultureInfo.InvariantCulture);

    static int Main(string[] args)
    {
        var inv = CultureInfo.InvariantCulture;
        var seances = Lignes(Path.Combine(args[0], "seances.csv")).Select(l => l.Split(','))
            .Select(c => (jour: DateTime.ParseExact(c[0], "yyyy-MM-dd", inv), ok: c[1] == "1", prec: int.Parse(c[2]), ech: D(c[3]),
                          gamma: c.Length > 4 ? D(c[4]) : double.NaN)).ToList();
        int S = seances.Count;
        var barres = new BarreFlux[S][];
        for (int s = 0; s < S; s++) barres[s] = new BarreFlux[MoteurTendance.N];
        foreach (var l in Lignes(Path.Combine(args[0], "minutes.csv.gz")))
        {
            var c = l.Split(',');
            barres[int.Parse(c[0])][int.Parse(c[1])] = new BarreFlux { O = D(c[2]), H = D(c[3]), L = D(c[4]), C = D(c[5]), Presente = true };
        }
        var att = Lignes(Path.Combine(args[0], "attendus_tendance.csv")).Select(l => l.Split(',')).ToList();
        var entete = File.ReadLines(Path.Combine(args[0], "attendus_tendance.csv")).First().Split(',');
        var moteur = new MoteurTendance();
        int erreurs = 0;
        var ecarts = MoteurTendance.Noms.ToDictionary(n => n, n => 0);
        var totaux = MoteurTendance.Noms.ToDictionary(n => n, n => (c: 0.0, p: 0.0, nc: 0, np: 0));
        for (int s = 0; s < S; s++)
        {
            var (jour, ok, prec, ech, gamma) = seances[s];
            moteur.DebutSeance(jour, ok, prec >= 0 ? barres[prec] : null, ech, gamma);
            for (int t = 0; t < MoteurTendance.N; t++) moteur.FermerMinute(t, barres[s][t]);
            foreach (var n in MoteurTendance.Noms)
            {
                double g = moteur.Gain(n), a = D(att[s][Array.IndexOf(entete, n)]);
                bool same = (double.IsNaN(g) && double.IsNaN(a)) || Math.Abs(g - a) < 1e-6;
                var tt = totaux[n];
                if (!double.IsNaN(g)) { tt.c += g; tt.nc++; }
                if (!double.IsNaN(a)) { tt.p += a; tt.np++; }
                totaux[n] = tt;
                if (!same && ecarts[n]++ < 3) Console.WriteLine($"  {n} {jour:yyyy-MM-dd} : C# {g}, recherche {a}");
            }
        }
        foreach (var n in MoteurTendance.Noms)
        {
            var tt = totaux[n];
            Console.WriteLine($"{n} : {tt.nc} seances jouees par le C#, {tt.np} par la recherche, ecarts {ecarts[n]}, total C# {tt.c:+0;-0} $, recherche {tt.p:+0;-0} $");
            erreurs += ecarts[n];
        }
        Console.WriteLine(erreurs == 0 ? "IDENTIQUE a la recherche" : $"DIFFERENT : {erreurs} seance(s)");
        return erreurs == 0 ? 0 : 1;
    }
}
