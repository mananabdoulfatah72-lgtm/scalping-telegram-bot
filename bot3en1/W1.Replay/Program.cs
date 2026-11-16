using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using W1NQ;

// Usage : W1.Replay <minutes.csv[.gz]> <reference_w1.csv> [comparer depuis AAAA-MM-JJ]
// Rejoue le moteur W1 sur toutes les seances du fichier et compare, signal par signal depuis 2023, les 28 variables, la
// probabilite et la decision a celles de Python (ml/arene/w1_prod.py).
class Program
{
    static int Main(string[] a)
    {
        var inv = CultureInfo.InvariantCulture;
        var modele = Arbres.Lire(typeof(MoteurW1).Assembly.GetManifestResourceStream("modele_w1.json"));
        var bot = new MoteurW1(modele) { GarderDecisions = true };
        DateTime comparer = a.Length > 2 ? DateTime.Parse(a[2], inv) : new DateTime(2023, 1, 1);
        var jours = RejeuW1.LireJours(RejeuW1.Lignes(a[0]), DateTime.MaxValue);
        RejeuW1.Jouer(bot, jours);
        var reference = new Dictionary<string, (int sens, double[] x, double p, bool pris)>();
        foreach (var l in File.ReadLines(a[1]).Skip(1))
        {
            var c = l.Split(',');
            var x = c.Skip(3).Take(28).Select(v => v == "nan" ? double.NaN : double.Parse(v, inv)).ToArray();
            reference[c[0] + "|" + c[1]] = (int.Parse(c[2]), x, double.Parse(c[31], inv), c[32] == "1");
        }
        var ecart = new double[28]; int compares = 0, sensDiff = 0, prisDiff = 0, absentsRef = 0; double pire = 0; string pireOu = "";
        var vus = new HashSet<string>();
        foreach (var d in bot.Decisions.Where(d => d.Jour >= comparer))
        {
            string cle = d.Jour.ToString("yyyy-MM-dd") + "|" + d.Minute;
            if (!reference.TryGetValue(cle, out var r)) { absentsRef++; continue; }
            vus.Add(cle); compares++;
            if (r.sens != d.Sens) sensDiff++;
            for (int k = 0; k < 28; k++)
            {
                double u = d.Variables[k], w = r.x[k];
                if (double.IsNaN(u) != double.IsNaN(w)) { ecart[k] = double.PositiveInfinity; continue; }
                if (!double.IsNaN(u)) ecart[k] = Math.Max(ecart[k], Math.Abs(u - w));
            }
            double e = Math.Abs(d.Proba - r.p); if (e > pire) { pire = e; pireOu = cle; }
            if (d.Pris != r.pris) prisDiff++;
        }
        int absentsMoteur = reference.Keys.Count(k => !vus.Contains(k));
        Console.WriteLine($"{jours.Count} seances rejouees ; signaux compares depuis {comparer:yyyy-MM-dd} : {compares} (absents de la reference : {absentsRef}, absents du moteur : {absentsMoteur})");
        Console.WriteLine("ecart max par variable : " + string.Join(" ", ecart.Select((x, k) => $"f{k}={x:G3}")));
        Console.WriteLine($"probabilite : ecart max {pire:G3} ({pireOu}) ; sens differents : {sensDiff} ; decisions (pris / ecarte) differentes : {prisDiff}");
        var t = bot.Trades.Where(x => x.Jour >= comparer).ToList();
        Console.WriteLine($"trades pris par le bot depuis {comparer:yyyy-MM-dd} : {t.Count}, resultat {t.Sum(x => 2 * x.Sens * (x.Sortie - x.Entree) - 3):F0} $ pour 1 MNQ (modele entraine jusqu'au {modele.EntraineJusqua} : dans l'echantillon, verification seulement)");
        return absentsMoteur == 0 && absentsRef == 0 && sensDiff == 0 && prisDiff <= Math.Max(2, compares / 500) ? 0 : 1;
    }
}
