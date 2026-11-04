using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using XGBoostNQ;

// Usage : XGBoost.Replay <minutes.csv[.gz]> <reference_xgb.csv> [depuis AAAA-MM-JJ] [comparer depuis AAAA-MM-JJ]
// Rejoue le moteur sur toutes les seances du fichier (ou depuis une date, pour mesurer le rodage des indicateurs) et compare,
// bougie par bougie depuis 2023, les 21 variables et la probabilite a celles de Python (ml/xgb_final.py).
class Program
{
    static int Main(string[] a)
    {
        var inv = CultureInfo.InvariantCulture;
        var modele = Arbres.Lire(typeof(MoteurXGB).Assembly.GetManifestResourceStream("modele_xgb.json"));
        var bot = new MoteurXGB(modele);
        DateTime depuis = a.Length > 2 ? DateTime.Parse(a[2], inv) : DateTime.MinValue;
        DateTime comparer = a.Length > 3 ? DateTime.Parse(a[3], inv) : new DateTime(2023, 1, 1);
        var jours = RejeuXGB.LireJours(RejeuXGB.Lignes(a[0]), DateTime.MaxValue, depuis);
        var reference = new Dictionary<string, double[]>();
        foreach (var l in File.ReadLines(a[1]).Skip(1))
        {
            var x = l.Split(',');
            reference[x[0] + "|" + x[1]] = x.Skip(2).Select(v => v == "nan" ? double.NaN : double.Parse(v, inv)).ToArray();
        }
        var ecart = new double[22]; int compares = 0, signauxDiff = 0, signaux = 0, manquantes = 0; double pire = 0; string pireOu = "";
        foreach (var kv in jours)
        {
            string j = kv.Key.ToString("yyyy-MM-dd");
            RejeuXGB.JouerSeance(bot, kv.Key, kv.Value, m =>
            {
                if (m % 15 != 14 || kv.Key < comparer) return;
                int b = m / 15;
                if (!reference.TryGetValue(j + "|" + b, out var r)) { manquantes++; return; }
                compares++;
                for (int k = 0; k < 21; k++)
                {
                    double u = bot.Variables[k], w = r[k];
                    if (double.IsNaN(u) != double.IsNaN(w)) { ecart[k] = double.PositiveInfinity; continue; }
                    if (!double.IsNaN(u)) ecart[k] = Math.Max(ecart[k], Math.Abs(u - w));
                }
                double p = bot.DerniereProba, q = r[21];
                if (!double.IsNaN(p) && !double.IsNaN(q))
                {
                    double d = Math.Abs(p - q); if (d > pire) { pire = d; pireOu = $"{j} bougie {b}"; }
                    int sp = p > 0.55 ? 1 : p < 0.45 ? -1 : 0, sq = q > 0.55 ? 1 : q < 0.45 ? -1 : 0;
                    if (b <= 21) { if (sq != 0) signaux++; if (sp != sq) signauxDiff++; }
                }
            });
        }
        Console.WriteLine($"{jours.Count} seances rejouees, {compares} bougies comparees depuis 2023 ({manquantes} absentes de la reference)");
        Console.WriteLine("ecart max par variable : " + string.Join(" ", ecart.Take(21).Select((e, k) => $"f{k}={e:G3}")));
        Console.WriteLine($"probabilite : ecart max {pire:G3} ({pireOu}) ; signaux (bougies 0-21) : {signaux}, differents : {signauxDiff}");
        var t = bot.Trades.Where(x => x.Jour.Year >= 2023).ToList();
        Console.WriteLine($"trades du moteur depuis 2023 : {t.Count} (modele entraine jusqu'au {modele.EntraineJusqua} : dans l'echantillon, pour la verification seulement)");
        return 0;
    }
}
