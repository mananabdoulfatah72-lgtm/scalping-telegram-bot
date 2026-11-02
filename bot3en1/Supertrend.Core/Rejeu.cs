using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;

namespace SupertrendNQ
{
    /// <summary>Minutes historiques (CSV t,o,h,l,c,..., heure de New York) rejouees dans le moteur : toutes les seances
    /// alimentent l'indicateur ; seules les seances completes (premiere et derniere minute, au moins 370 minutes) sont
    /// tradees. Minutes absentes : cloture recopiee vers l'avant, puis vers l'arriere en debut de seance (comme le test).</summary>
    public static class Rejeu
    {
        public static IEnumerable<string> Lignes(string f)
        {
            Stream s = File.OpenRead(f);
            if (f.EndsWith(".gz")) s = new GZipStream(s, CompressionMode.Decompress);
            using var r = new StreamReader(s);
            string l;
            while ((l = r.ReadLine()) != null) yield return l;
        }

        /// <summary>Seances du fichier jusqu'au jour `jusqua` compris : [o, h, l, c][minute], NaN si absente.</summary>
        public static SortedDictionary<DateTime, double[][]> LireJours(IEnumerable<string> lignes, DateTime jusqua)
        {
            var inv = CultureInfo.InvariantCulture;
            var jours = new SortedDictionary<DateTime, double[][]>();
            foreach (var l in lignes.Skip(1))
            {
                var x = l.Split(',');
                if (x.Length < 5) continue;
                var t = DateTime.ParseExact(x[0], "yyyy-MM-dd HH:mm", inv);
                if (t.Date > jusqua) continue;
                int m = t.Hour * 60 + t.Minute - 570;
                if (m < 0 || m >= MoteurST.N) continue;
                if (!jours.TryGetValue(t.Date, out var j))
                {
                    j = Enumerable.Range(0, 4).Select(_ => Enumerable.Repeat(double.NaN, MoteurST.N).ToArray()).ToArray();
                    jours[t.Date] = j;
                }
                for (int k = 0; k < 4; k++) j[k][m] = double.Parse(x[1 + k], inv);
            }
            return jours;
        }

        public static void Jouer(MoteurST bot, SortedDictionary<DateTime, double[][]> jours)
        {
            foreach (var kv in jours)
            {
                var j = kv.Value;
                var pres = j[3].Select(v => !double.IsNaN(v)).ToArray();
                bool complete = pres[0] && pres[MoteurST.N - 1] && pres.Count(p => p) >= 370;
                var c = (double[])j[3].Clone();
                for (int m = 1; m < MoteurST.N; m++) if (double.IsNaN(c[m])) c[m] = c[m - 1];
                for (int m = MoteurST.N - 2; m >= 0; m--) if (double.IsNaN(c[m])) c[m] = c[m + 1];
                bot.DebutSeance(kv.Key, complete);
                for (int m = 0; m < MoteurST.N; m++)
                {
                    double o = double.IsNaN(j[0][m]) ? c[m] : j[0][m], h = double.IsNaN(j[1][m]) ? c[m] : j[1][m], l = double.IsNaN(j[2][m]) ? c[m] : j[2][m];
                    bot.MinuteFermee(m, new BarreMin { O = o, H = h, L = l, C = c[m], Presente = true });
                }
            }
        }
    }
}
