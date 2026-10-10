using System;
using System.Collections.Generic;
using System.Linq;

namespace Bot3en1
{
    /// <summary>Calendrier de la Bourse et des echeances du NQ, recopie de zone/robot.py (feries_bourse, jour_court,
    /// contrat_nq). Toutes les dates sont des jours de New York.</summary>
    public static class Calendrier
    {
        /// <summary>Dimanche de Paques (algorithme gregorien anonyme).</summary>
        public static DateTime Paques(int a)
        {
            int b = a % 19, c = a / 100, d = a % 100, e = c / 4, f = c % 4, g = (c + 8) / 25, h = (c - g + 1) / 3;
            int i = (19 * b + c - e - h + 15) % 30, k = d / 4, l = d % 4, m = (32 + 2 * f + 2 * k - i - l) % 7;
            int n = (b + 11 * i + 22 * m) / 451, mois = (i + m - 7 * n + 114) / 31, jour = (i + m - 7 * n + 114) % 31 + 1;
            return new DateTime(a, mois, jour);
        }

        static DateTime Nieme(int a, int mois, DayOfWeek js, int n)
        {
            var l = new List<DateTime>();
            for (var d = new DateTime(a, mois, 1); d.Month == mois; d = d.AddDays(1))
                if (d.DayOfWeek == js) l.Add(d);
            return n >= 0 ? l[n] : l[l.Count + n];
        }

        static DateTime? Reporte(DateTime d, bool samediVendredi)
        {
            if (d.DayOfWeek == DayOfWeek.Sunday) return d.AddDays(1);
            if (d.DayOfWeek == DayOfWeek.Saturday) return samediVendredi ? d.AddDays(-1) : (DateTime?)null;
            return d;
        }

        static readonly Dictionary<int, HashSet<DateTime>> cache = new Dictionary<int, HashSet<DateTime>>();

        /// <summary>Jours feries de la Bourse de New York (avec reports), comme robot.py feries_bourse.</summary>
        public static HashSet<DateTime> Feries(int a)
        {
            lock (cache)
            {
                if (cache.TryGetValue(a, out var s)) return s;
                var l = new List<DateTime?>
                {
                    Reporte(new DateTime(a, 1, 1), false), Nieme(a, 1, DayOfWeek.Monday, 2), Nieme(a, 2, DayOfWeek.Monday, 2),
                    Paques(a).AddDays(-2), Nieme(a, 5, DayOfWeek.Monday, -1), Reporte(new DateTime(a, 7, 4), true),
                    Nieme(a, 9, DayOfWeek.Monday, 0), Nieme(a, 11, DayOfWeek.Thursday, 3), Reporte(new DateTime(a, 12, 25), true)
                };
                if (a >= 2022) l.Add(Reporte(new DateTime(a, 6, 19), true));
                s = new HashSet<DateTime>();
                foreach (var d in l) if (d.HasValue) s.Add(d.Value.Date);
                cache[a] = s;
                return s;
            }
        }

        public static bool Ferie(DateTime d) => Feries(d.Year).Contains(d.Date);

        /// <summary>Fetes ou le CME ferme tot, et demi-seances (robot.py jour_court) : la zone ne trade pas ces jours-la.</summary>
        public static bool JourCourt(DateTime d)
        {
            int a = d.Year, m = d.Month, j = d.Day, w = ((int)d.DayOfWeek + 6) % 7;     // 0 = lundi
            bool ouvre = w < 5, lundi = w == 0;
            return (m == 1 && lundi && 15 <= j && j <= 21) || (m == 2 && lundi && 15 <= j && j <= 21) || (m == 5 && lundi && j >= 25)
                || (m == 9 && lundi && j <= 7)
                || (a >= 2022 && m == 6 && ((j == 19 && ouvre) || (j == 18 && w == 4) || (j == 20 && lundi)))
                || (m == 7 && (((j == 3 || j == 4) && ouvre) || (j == 5 && lundi)))
                || (m == 11 && ((w == 3 && 22 <= j && j <= 28) || (w == 4 && 23 <= j && j <= 29))) || (m == 12 && j == 24 && ouvre);
        }

        /// <summary>Contrat suivi un jour donne : changement le mercredi avant le 3e vendredi de mars, juin, septembre et
        /// decembre (robot.py contrat_nq). Renvoie par exemple "Z26".</summary>
        public static string Contrat(DateTime jour)
        {
            var d = jour.Date;
            for (int a = d.Year; a <= d.Year + 1; a++)
                foreach (int mo in new[] { 3, 6, 9, 12 })
                {
                    var premier = new DateTime(a, mo, 1);
                    var vendredi3 = premier.AddDays(((int)DayOfWeek.Friday - (int)premier.DayOfWeek + 7) % 7 + 14);
                    if (vendredi3.AddDays(-2) > d) return $"{"HMUZ"[mo / 3 - 1]}{a % 100:00}";
                }
            throw new InvalidOperationException("contrat introuvable");
        }

        /// <summary>Seance suivante ouvrable (ni week-end, ni Nouvel an, ni Vendredi saint, ni Noel), comme une seance CME.</summary>
        public static DateTime SeanceSuivante(DateTime d)
        {
            var x = d.Date.AddDays(1);
            while (x.DayOfWeek == DayOfWeek.Saturday || x.DayOfWeek == DayOfWeek.Sunday || JourFerme(x)) x = x.AddDays(1);
            return x;
        }

        /// <summary>Jours d'annonce de la Fed (decision du FOMC), comme fonds/fomc.py annonces() : la regle « pas de zone les
        /// jours de la Fed » de la vague 9 (mode a plat). Calendrier officiel de la Fed (federalreserve.gov) ; a completer
        /// dans les reglages pour les annees suivantes.</summary>
        public static readonly HashSet<DateTime> JoursFed = new HashSet<DateTime>(new[]
        {
            "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10",
            "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-09",
            "2027-01-27", "2027-03-17", "2027-04-28", "2027-06-09", "2027-07-28", "2027-09-15", "2027-10-27", "2027-12-08",
        }.Select(x => DateTime.ParseExact(x, "yyyy-MM-dd", System.Globalization.CultureInfo.InvariantCulture)));

        /// <summary>Jours sans seance CME (robot.py jour_ferme).</summary>
        public static bool JourFerme(DateTime d)
        {
            if (d.DayOfWeek == DayOfWeek.Saturday || d.DayOfWeek == DayOfWeek.Sunday) return true;
            var an = Reporte(new DateTime(d.Year, 1, 1), false);
            var noel = new DateTime(d.Year, 12, 25);
            var noelObs = noel.DayOfWeek == DayOfWeek.Saturday ? noel.AddDays(-1) : noel.DayOfWeek == DayOfWeek.Sunday ? noel.AddDays(1) : noel;
            return d.Date == an || d.Date == Paques(d.Year).AddDays(-2) || d.Date == noelObs;
        }
    }
}
