using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;

namespace Bot3en1
{
    /// <summary>Rejoue des seances passees dans le moteur : sert au rejeu de verification et au demarrage du bot en direct
    /// (historique de la zone et etat de la regle du RSI(2) refaits a partir des barres d'une minute).</summary>
    public static class Rejoueur
    {
        public static IEnumerable<string> Lignes(string fichier)
        {
            Stream s = File.OpenRead(fichier);
            if (fichier.EndsWith(".gz")) s = new GZipStream(s, CompressionMode.Decompress);
            using var r = new StreamReader(s);
            string l;
            while ((l = r.ReadLine()) != null) yield return l;
        }

        /// <summary>Barres d'une minute (CSV t,o,h,l,c,v,contrat, heure de New York) groupees par seance. contratCalendrier :
        /// le contrat de chaque seance est celui de la regle du calendrier (comme en direct) au lieu de la colonne contrat.</summary>
        public static SortedDictionary<DateTime, (Barre[] b, string contrat)> LireMinutes(IEnumerable<string> lignes, DateTime jusqua,
                                                                                         bool contratCalendrier)
        {
            var inv = CultureInfo.InvariantCulture;
            var seances = new SortedDictionary<DateTime, (Barre[] b, string contrat)>();
            foreach (var l in lignes.Skip(1))
            {
                var x = l.Split(',');
                if (x.Length < 7) continue;
                var t = DateTime.ParseExact(x[0], "yyyy-MM-dd HH:mm", inv);
                if (t.Date > jusqua) continue;
                int m = t.Hour * 60 + t.Minute - 570;
                if (m < 0 || m >= Moteur.N) continue;
                if (!seances.TryGetValue(t.Date, out var s))
                    s = (Enumerable.Range(0, Moteur.N).Select(_ => new Barre()).ToArray(), "");
                s.b[m] = new Barre { O = double.Parse(x[1], inv), H = double.Parse(x[2], inv), L = double.Parse(x[3], inv),
                                     C = double.Parse(x[4], inv), V = double.Parse(x[5], inv), Presente = true };
                s.contrat = contratCalendrier ? Calendrier.Contrat(t.Date) : x[6];
                seances[t.Date] = s;
            }
            return seances;
        }

        /// <summary>Seance "ok" pour le RSI(2) (robot.py rsi2) : 60 minutes au moins, premiere minute presente, decision
        /// possible, pas un jour ferie de la Bourse.</summary>
        public static bool RsiOk(DateTime j, Barre[] b)
        {
            int n = b.Count(x => x.Presente), der = Array.FindLastIndex(b, x => x.Presente);
            return n >= 60 && b[0].Presente && der - 9 >= 2 && !Calendrier.Ferie(j);
        }

        /// <summary>Joue une seance complete dans le moteur, minute par minute ; surSignal recoit chaque signal.</summary>
        public static void JouerSeance(Moteur bot, DateTime j, Barre[] b, string contrat, Action<Signal> surSignal)
        {
            bool complete = b[0].Presente && b[Moteur.N - 1].Presente && b.Count(x => x.Presente) >= 370;
            int der = Array.FindLastIndex(b, x => x.Presente);
            bot.DebutSeance(j, contrat, der);
            bot.ZoneAutorisee = complete;
            bool rsiOk = RsiOk(j, b);
            for (int m = 0; m < Moteur.N; m++)
            {
                if (bot.MinuteDecisionRsi == m && rsiOk)
                {
                    double px = b[m].Presente ? b[m].O : ClotureAvant(b, m, bot);
                    foreach (var s in bot.DecisionRsi(px)) surSignal?.Invoke(s);
                }
                foreach (var s in bot.MinuteFermee(m, b[m])) surSignal?.Invoke(s);
            }
            bot.FinSeance();
        }

        public static double ClotureAvant(Barre[] b, int m, Moteur bot)
        {
            for (int i = m - 1; i >= 0; i--) if (b[i].Presente) return b[i].C;
            return bot.Historique.Count > 0 ? bot.Historique[^1].Cloture : 0;
        }

        /// <summary>Moteur pret pour la seance `jour` : toutes les seances d'avant rejouees (historique, regle du RSI(2)),
        /// sans position. Le contrat suivant vient du calendrier, comme en direct.</summary>
        public static Moteur Preparer(SortedDictionary<DateTime, (Barre[] b, string contrat)> seances, DateTime jour)
        {
            var bot = new Moteur(new List<Resume>()) { ContratSuivant = (j, c) => Calendrier.Contrat(Calendrier.SeanceSuivante(j)) };
            foreach (var kv in seances)
            {
                if (kv.Key >= jour.Date) break;
                JouerSeance(bot, kv.Key, kv.Value.b, kv.Value.contrat, null);
            }
            bot.RemettreAPlat();
            return bot;
        }
    }
}
