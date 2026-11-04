using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;

namespace XGBoostNQ
{
    /// <summary>Minutes historiques (CSV t,o,h,l,c,v,..., heure de New York) rejouees dans le moteur, comme ml/caracteristiques.py :
    /// toutes les seances du fichier, minutes absentes recopiees sur la cloture (vers l'avant, puis vers l'arriere en debut de
    /// seance), volume 0. Seules les seances completes (premiere et derniere minute, au moins 370 minutes) sont tradees.</summary>
    public static class RejeuXGB
    {
        public static IEnumerable<string> Lignes(string f)
        {
            Stream s = File.OpenRead(f);
            if (f.EndsWith(".gz")) s = new GZipStream(s, CompressionMode.Decompress);
            using var r = new StreamReader(s);
            string l;
            while ((l = r.ReadLine()) != null) yield return l;
        }

        /// <summary>Seances du fichier jusqu'au jour `jusqua` compris : [o, h, l, c, v][minute], NaN si absente.</summary>
        public static SortedDictionary<DateTime, double[][]> LireJours(IEnumerable<string> lignes, DateTime jusqua, DateTime depuis = default)
        {
            var inv = CultureInfo.InvariantCulture;
            var jours = new SortedDictionary<DateTime, double[][]>();
            foreach (var l in lignes.Skip(1))
            {
                var x = l.Split(',');
                if (x.Length < 6) continue;
                var t = DateTime.ParseExact(x[0], "yyyy-MM-dd HH:mm", inv);
                if (t.Date > jusqua || t.Date < depuis) continue;
                int m = t.Hour * 60 + t.Minute - 570;
                if (m < 0 || m >= MoteurXGB.N) continue;
                if (!jours.TryGetValue(t.Date, out var j))
                {
                    j = Enumerable.Range(0, 5).Select(_ => Enumerable.Repeat(double.NaN, MoteurXGB.N).ToArray()).ToArray();
                    jours[t.Date] = j;
                }
                for (int k = 0; k < 5; k++) j[k][m] = double.Parse(x[1 + k], inv);
            }
            return jours;
        }

        /// <summary>Joue une seance complete du fichier ; rappel apres chaque minute (pour suivre les variables).</summary>
        public static void JouerSeance(MoteurXGB bot, DateTime jour, double[][] j, Action<int> apres = null)
        {
            var pres = j[3].Select(v => !double.IsNaN(v)).ToArray();
            bool complete = pres[0] && pres[MoteurXGB.N - 1] && pres.Count(p => p) >= 370;
            var c = (double[])j[3].Clone();
            for (int m = 1; m < MoteurXGB.N; m++) if (double.IsNaN(c[m])) c[m] = c[m - 1];
            for (int m = MoteurXGB.N - 2; m >= 0; m--) if (double.IsNaN(c[m])) c[m] = c[m + 1];
            bot.DebutSeance(jour, complete);
            for (int m = 0; m < MoteurXGB.N; m++)
            {
                double o = double.IsNaN(j[0][m]) ? c[m] : j[0][m], h = double.IsNaN(j[1][m]) ? c[m] : j[1][m], l = double.IsNaN(j[2][m]) ? c[m] : j[2][m];
                double v = pres[m] && !double.IsNaN(j[4][m]) ? j[4][m] : 0;
                bot.MinuteFermee(m, new BarreMin { O = o, H = h, L = l, C = c[m], V = v, Presente = true, Reelle = pres[m] });
                apres?.Invoke(m);
            }
        }

        public static void Jouer(MoteurXGB bot, SortedDictionary<DateTime, double[][]> jours)
        {
            foreach (var kv in jours) JouerSeance(bot, kv.Key, kv.Value);
        }
    }
}
