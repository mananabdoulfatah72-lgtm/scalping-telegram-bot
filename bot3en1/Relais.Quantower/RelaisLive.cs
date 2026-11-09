using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Xml.Linq;
using TradingPlatform.BusinessLayer;

namespace RelaisNQ
{
    /// <summary>Terminal live (http://localhost:PORT/live) : les marches de la journee Globex (18 h - 17 h New York) recus de
    /// Rithmic transaction par transaction (prix, volume, achats et ventes a l'agression, gros ordres), et ce que le relais va
    /// chercher lui-meme sur Internet : nouvelles (flux RSS), calendrier economique, VIX et autres cotations (Yahoo, CBOE).
    /// Aucun ordre. Ce que la page affiche vient de ces sources ; elle ne devine rien.</summary>
    public partial class RelaisStrategy
    {
        [InputParameter("Terminal live : marche 3 (facultatif), ex. YMZ6 (Dow)", 100)] public Symbol Marche3;
        [InputParameter("Terminal live : marche 4 (facultatif), ex. RTYZ6 (Russell 2000)", 101)] public Symbol Marche4;
        [InputParameter("Terminal live : marche 5 (facultatif), ex. CLZ6 (petrole)", 102)] public Symbol Marche5;
        [InputParameter("Terminal live : marche 6 (facultatif), ex. GCZ6 (or)", 103)] public Symbol Marche6;
        [InputParameter("Terminal live : marche 7 (facultatif), ex. 6EZ6 (euro)", 104)] public Symbol Marche7;
        [InputParameter("Terminal live : marche 8 (facultatif), ex. ZNZ6 (taux a 10 ans)", 105)] public Symbol Marche8;
        [InputParameter("Terminal live : gros ordre NQ a partir de (contrats)", 110, 1, 1000, 1, 0)] public int GrosNQ = 20;
        [InputParameter("Terminal live : gros ordre ES a partir de (contrats)", 111, 1, 5000, 1, 0)] public int GrosES = 100;
        [InputParameter("Terminal live : nouvelles (adresses RSS separees par ;)", 112)] public string SourcesNouvelles = DefautNouvelles;
        [InputParameter("Terminal live : calendrier economique (JSON)", 113)] public string AdresseCalendrier = "https://nfs.faireconomy.media/ff_calendar_thisweek.json";
        [InputParameter("Terminal live : cotations Yahoo (symboles separes par des virgules)", 114)] public string CotationsYahoo = DefautCotations;
        [InputParameter("Terminal live : adresse des cotations ({0} = symboles)", 115)]
        public string AdresseCotations = "https://query1.finance.yahoo.com/v7/finance/spark?symbols={0}&range=1d&interval=5m";
        [InputParameter("Terminal live : clotures du VIX (CBOE)", 116)] public string AdresseVIX = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv";
        [InputParameter("Terminal live : clotures du VIX a 3 mois (CBOE)", 117)] public string AdresseVIX3M = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX3M_History.csv";
        [InputParameter("Terminal live : secours du VIX en direct (CBOE, {0} = VIX, VIX3M...)", 118)]
        public string AdresseSecoursVIX = "https://cdn.cboe.com/api/global/delayed_quotes/quotes/_{0}.json";

        /// <summary>Secondes entre deux lectures des nouvelles et des cotations (le calendrier : toutes les 30 minutes).</summary>
        public int PeriodeLive = 60;

        public const string DefautNouvelles =
            "https://investinglive.com/feed/;" +
            "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114;" +
            "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258;" +
            "https://feeds.content.dowjones.io/public/rss/mw_topstories;" +
            "https://www.federalreserve.gov/feeds/press_all.xml;" +
            "https://www.federalreserve.gov/feeds/speeches.xml;" +
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=%5ENDX&region=US&lang=en-US;" +
            "https://seekingalpha.com/market_currents.xml;" +
            "https://www.investing.com/rss/news_25.rss;" +
            "https://www.nasdaq.com/feed/rssoutbound?category=Markets;" +
            "https://news.google.com/rss/search?q=Nasdaq+OR+%22Wall+Street%22+when:1d&hl=en-US&gl=US&ceid=US:en;" +
            "https://news.google.com/rss/search?q=Wall+Street+OR+Nasdaq+OR+Fed+when:1d&hl=fr&gl=FR&ceid=FR:fr";
        public const string DefautCotations = "^VIX,^VIX3M,^VIX9D,^VVIX,^VXN,^TNX,DX-Y.NYB,BTC-USD,^NDX,^GSPC,NVDA,MSFT,AAPL,AMZN,GOOGL,META,AVGO,TSLA";
        const int G = 1380;                                    // minutes de 18 h a 17 h (New York)
        const string UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36";

        /// <summary>Un marche sur la journee Globex : barres d'une minute depuis 18 h (o, h, l, c, volume, achats, ventes).</summary>
        class Suivi
        {
            public string Nom; public Symbol S; public int Gros;
            public DateTime Jour = DateTime.MinValue;          // date de fin de la seance (17 h New York)
            public double[][] B = new double[G][];
            public double Dernier; public DateTime DernierTick = DateTime.MinValue;
            public double? CloturePrec; public DateTime? JourPrec;
            public double[] VolMoyen; public double? PlageMoyenne; public int Seances;
            public readonly List<double[]> VolJours = new List<double[]>();   // volumes par minute des seances passees (20 au plus)
            public readonly List<double> Plages = new List<double>();
        }

        class Nouvelle { public string Cle, Titre, Lien, Source, Resume; public DateTime Date, Vu; }

        readonly List<Suivi> suivis = new List<Suivi>();
        readonly Dictionary<Symbol, Suivi> parSymbole = new Dictionary<Symbol, Suivi>();
        readonly object verrouLive = new object();
        readonly List<object> grosOrdres = new List<object>();
        long versionGros, versionNouvelles, versionCalendrier, versionCotations;
        readonly Dictionary<string, Nouvelle> nouvelles = new Dictionary<string, Nouvelle>();
        readonly Dictionary<string, object> etatSources = new Dictionary<string, object>();
        List<object> calendrier = new List<object>(); string calendrierBrut = "";
        object cotations, vixVeille, etatCotations, etatCalendrier;
        DateTime jourVixVeille = DateTime.MinValue;
        static readonly CultureInfo inv = CultureInfo.InvariantCulture;

        // ------------------------------------------------------------------ demarrage et arret
        void DemarrerLive()
        {
            try
            {
                Ajouter("NQ", SymboleNQ, GrosNQ); Ajouter("ES", SymboleES, GrosES);
                foreach (var s in new[] { Marche3, Marche4, Marche5, Marche6, Marche7, Marche8 }) Ajouter(null, s, 0);
                foreach (var m in suivis) m.S.NewLast += SurLive;                  // le direct d'abord ; l'historique arrive en arriere-plan
                var jeton = arret.Token;
                _ = Task.Run(async () =>
                {
                    foreach (var m in suivis) try { HistoriqueLive(m); } catch (Exception e) { Log($"{m.Nom} : historique du terminal live ({e.Message})", StrategyLoggingLevel.Info); }
                    await Boucle(jeton);
                });
                Log($"terminal live : http://localhost:{Port}/live ({suivis.Count} marches : {string.Join(", ", suivis.Select(m => m.Nom))} ; nouvelles, calendrier et cotations lus par le relais)",
                    StrategyLoggingLevel.Info);
            }
            catch (Exception e) { Log($"terminal live indisponible ({e.Message}) : la station continue", StrategyLoggingLevel.Error); }
        }

        void ArreterLive()
        {
            foreach (var m in suivis) try { m.S.NewLast -= SurLive; } catch { }
        }

        void Ajouter(string nom, Symbol s, int gros)
        {
            if (s == null || parSymbole.ContainsKey(s)) return;
            var m = new Suivi { Nom = nom ?? NomCourt(s.Name), S = s, Gros = gros };
            suivis.Add(m); parSymbole[s] = m;
        }

        /// <summary>« YMZ6 » -> « YM », « 6EZ6 » -> « 6E » : le code du contrat sans le mois ni l'annee.</summary>
        static string NomCourt(string n)
        {
            var g = Regex.Match(n ?? "", @"^(.+?)[FGHJKMNQUVXZ]\d{1,2}$");
            return g.Success ? g.Groups[1].Value : (n ?? "?");
        }

        /// <summary>Journee Globex d'un instant de New York : (date de fin, minute depuis 18 h), -1 pendant la pause de 17 h.</summary>
        static (DateTime jour, int i) Globex(DateTime t)
        {
            if (t.Hour >= 18) return (t.Date.AddDays(1), (t.Hour - 18) * 60 + t.Minute);
            if (t.Hour < 17) return (t.Date, (t.Hour + 6) * 60 + t.Minute);
            return (t.Date, -1);
        }

        // ------------------------------------------------------------------ marches
        void SurLive(Symbol s, Last l)
        {
            if (!parSymbole.TryGetValue(s, out var m)) m = suivis.FirstOrDefault(x => x.S.Name == s?.Name);   // meme contrat, autre objet
            if (m == null || l == null || double.IsNaN(l.Price) || l.Price <= 0) return;
            var t = Ny(l.Time); var (jour, i) = Globex(t);
            if (i < 0) return;
            int cote = l.AggressorFlag == AggressorFlag.Buy ? 1 : l.AggressorFlag == AggressorFlag.Sell ? -1 : 0;
            lock (verrou)
            {
                if (jour > m.Jour) NouvelleSeance(m, jour);
                if (jour < m.Jour) return;
                m.Dernier = l.Price; m.DernierTick = Core.Instance.TimeUtils.DateTimeUtcNow;
                var x = m.B[i];
                if (x == null) m.B[i] = x = new[] { l.Price, l.Price, l.Price, l.Price, 0.0, 0.0, 0.0 };
                x[1] = Math.Max(x[1], l.Price); x[2] = Math.Min(x[2], l.Price); x[3] = l.Price; x[4] += l.Size;
                if (cote > 0) x[5] += l.Size; else if (cote < 0) x[6] += l.Size;
            }
            if (m.Gros > 0 && l.Size >= m.Gros)
                lock (verrouLive)
                {
                    grosOrdres.Add(new { marche = m.Nom, heure = t.ToString("HH:mm:ss"), jour = jour.ToString("yyyy-MM-dd"), prix = l.Price, taille = l.Size, sens = cote });
                    if (grosOrdres.Count > 200) grosOrdres.RemoveRange(0, grosOrdres.Count - 200);
                    versionGros++;
                }
        }

        /// <summary>Passage a une nouvelle seance : la seance finie devient la cloture de la veille et entre dans les moyennes.</summary>
        void NouvelleSeance(Suivi m, DateTime jour)
        {
            if (m.Jour != DateTime.MinValue && m.B.Any(b => b != null)) Archiver(m, m.Jour, m.B);
            m.Jour = jour; m.B = new double[G][];
        }

        void Archiver(Suivi m, DateTime jour, double[][] b)
        {
            var der = b.LastOrDefault(x => x != null);
            if (der == null) return;
            if (m.JourPrec == null || jour > m.JourPrec) { m.CloturePrec = der[3]; m.JourPrec = jour; }
            var pleines = b.Where(x => x != null).ToList();
            if (pleines.Count >= 600)                                         // une vraie seance (pas un bout de journee)
            {
                m.VolJours.Add(b.Select(x => x?[4] ?? 0).ToArray()); if (m.VolJours.Count > 20) m.VolJours.RemoveAt(0);
                m.Plages.Add(pleines.Max(x => x[1]) - pleines.Min(x => x[2])); if (m.Plages.Count > 20) m.Plages.RemoveAt(0);
            }
            m.Seances = m.VolJours.Count;
            m.VolMoyen = m.VolJours.Count == 0 ? null : Enumerable.Range(0, G).Select(k => m.VolJours.Average(v => v[k])).ToArray();
            m.PlageMoyenne = m.Plages.Count == 0 ? (double?)null : m.Plages.Average();
        }

        /// <summary>Barres d'une minute de la plateforme (25 derniers jours, par reflexion comme la station) : seances passees
        /// pour les moyennes et la cloture de la veille, et le debut de la seance en cours. Pour le NQ et l'ES, a defaut,
        /// l'historique de la station (9 h 30 - 16 h) donne au moins la cloture de 16 h et le volume moyen de la seance.</summary>
        void HistoriqueLive(Suivi m)
        {
            var maintenant = Globex(Ny(Core.Instance.TimeUtils.DateTimeUtcNow));
            var jours = new SortedDictionary<DateTime, double[][]>();
            try
            {
                var asm = typeof(Symbol).Assembly;
                var tAgg = asm.GetType("TradingPlatform.BusinessLayer.HistoryAggregationTime");
                var tPer = asm.GetType("TradingPlatform.BusinessLayer.Period");
                if (tAgg != null && tPer != null)
                {
                    var min1 = tPer.GetProperty("MIN1")?.GetValue(null) ?? tPer.GetField("MIN1")?.GetValue(null);
                    var agg = Activator.CreateInstance(tAgg, min1, HistoryType.Last);
                    var fin = Core.Instance.TimeUtils.DateTimeUtcNow;
                    var h = m.S.GetHistory(new HistoryRequestParameters { Symbol = m.S, FromTime = fin.AddDays(-25), ToTime = fin, Aggregation = agg });
                    for (int k = 0; k < h.Count; k++)
                    {
                        object it = h[k, SeekOriginHistory.Begin];
                        object Val(string p) => it.GetType().GetProperty(p)?.GetValue(it) ?? it.GetType().GetField(p)?.GetValue(it);
                        double V(string p) { var v = Val(p); return v == null ? double.NaN : Convert.ToDouble(v, inv); }
                        if (!(Val("TimeLeft") is DateTime t0)) continue;
                        var (j, i) = Globex(Ny(t0));
                        if (i < 0 || new[] { V("Open"), V("High"), V("Low"), V("Close") }.Any(z => double.IsNaN(z) || double.IsInfinity(z) || z <= 0)) continue;
                        if (!jours.TryGetValue(j, out var b)) { b = new double[G][]; jours[j] = b; }
                        b[i] = new[] { V("Open"), V("High"), V("Low"), V("Close"), double.IsNaN(V("Volume")) ? 0 : V("Volume"), 0.0, 0.0 };
                    }
                }
            }
            catch (Exception e) { Log($"{m.Nom} : historique d'une minute indisponible pour le terminal live ({e.Message})", StrategyLoggingLevel.Info); }
            lock (verrou)
            {
                foreach (var kv in jours.Where(kv => kv.Key < maintenant.jour)) Archiver(m, kv.Key, kv.Value);
                if (jours.TryGetValue(maintenant.jour, out var auj))              // debut de la seance en cours : complete ce que le direct n'a pas vu
                {
                    if (m.Jour < maintenant.jour) { if (m.Jour != DateTime.MinValue && m.B.Any(x => x != null)) Archiver(m, m.Jour, m.B); m.Jour = maintenant.jour; m.B = new double[G][]; }
                    if (m.Jour == maintenant.jour) for (int k = 0; k < G; k++) if (m.B[k] == null && auj[k] != null) m.B[k] = auj[k];
                    if (m.Dernier == 0) m.Dernier = auj.Last(x => x != null)[3];
                }
                if (jours.Count == 0)                                             // la station : seances 9 h 30 - 16 h
                {
                    var rth = m.S == SymboleNQ ? nq : m.S == SymboleES ? es : null;
                    if (rth != null)
                        foreach (var kv in rth.Jours.Where(kv => kv.Key < maintenant.jour))
                        {
                            var b = new double[G][];
                            for (int k = 0; k < N; k++) if (kv.Value[k] != null) b[930 + k] = (double[])kv.Value[k].Clone();
                            var der = b.LastOrDefault(x => x != null);
                            if (der == null) continue;
                            m.CloturePrec = der[3]; m.JourPrec = kv.Key;
                            m.VolJours.Add(b.Select(x => x?[4] ?? 0).ToArray()); if (m.VolJours.Count > 20) m.VolJours.RemoveAt(0);
                            var p = b.Where(x => x != null).ToList(); m.Plages.Add(p.Max(x => x[1]) - p.Min(x => x[2])); if (m.Plages.Count > 20) m.Plages.RemoveAt(0);
                        }
                    m.Seances = m.VolJours.Count;
                    m.VolMoyen = m.VolJours.Count == 0 ? null : Enumerable.Range(0, G).Select(k => m.VolJours.Average(v => v[k])).ToArray();
                    m.PlageMoyenne = m.Plages.Count == 0 ? (double?)null : m.Plages.Average();
                }
            }
        }

        // ------------------------------------------------------------------ sources sur Internet (nouvelles, calendrier, cotations)
        async Task Boucle(CancellationToken jeton)
        {
            DateTime dernierCalendrier = DateTime.MinValue;
            while (!jeton.IsCancellationRequested)
            {
                var t = DateTime.UtcNow;
                await LireNouvelles(jeton);
                await LireCotations(jeton);
                if ((t - dernierCalendrier).TotalMinutes >= 30) { await LireCalendrier(jeton); dernierCalendrier = t; }
                var jourNy = Ny(Core.Instance.TimeUtils.DateTimeUtcNow).Date;
                if (jourNy != jourVixVeille) { await LireVixVeille(jourNy, jeton); }
                try { await Task.Delay(TimeSpan.FromSeconds(Math.Max(2, PeriodeLive)), jeton); } catch { break; }
            }
        }

        async Task<string> Telecharger(string adresse, CancellationToken jeton)
        {
            if (!adresse.StartsWith("http", StringComparison.OrdinalIgnoreCase)) return File.ReadAllText(adresse);   // tests : fichier local
            using var req = new HttpRequestMessage(HttpMethod.Get, adresse);
            req.Headers.TryAddWithoutValidation("User-Agent", UA);
            req.Headers.TryAddWithoutValidation("Accept", "application/rss+xml, application/xml, text/xml, application/json, text/csv, */*");
            using var rep = await http.SendAsync(req, jeton);
            rep.EnsureSuccessStatusCode();
            return await rep.Content.ReadAsStringAsync();
        }

        Task LireNouvelles(CancellationToken jeton)
        {
            var adresses = (SourcesNouvelles ?? "").Split(new[] { ';' }, StringSplitOptions.RemoveEmptyEntries).Select(x => x.Trim()).Where(x => x.Length > 0).Distinct();
            return Task.WhenAll(adresses.Select(a => LireSource(a, jeton)));                 // en parallele : une source lente n'attend pas les autres
        }

        async Task LireSource(string adresse, CancellationToken jeton)
        {
            var maintenant = Core.Instance.TimeUtils.DateTimeUtcNow;
            {
                if (jeton.IsCancellationRequested) return;
                try
                {
                    var lues = LireFlux(await Telecharger(adresse, jeton), adresse).ToList();
                    int neuves = 0;
                    lock (verrouLive)
                    {
                        foreach (var n in lues)
                        {
                            if (nouvelles.ContainsKey(n.Cle)) continue;
                            n.Vu = maintenant;
                            if (n.Date == DateTime.MinValue || n.Date > maintenant.AddMinutes(10)) n.Date = maintenant;   // date absente ou fausse
                            if ((maintenant - n.Date).TotalHours > 72) continue;                                      // vieux articles
                            nouvelles[n.Cle] = n; neuves++;
                        }
                        if (nouvelles.Count > 600)
                            foreach (var k in nouvelles.Values.OrderBy(x => x.Date).Take(nouvelles.Count - 600).Select(x => x.Cle).ToList()) nouvelles.Remove(k);
                        if (neuves > 0) versionNouvelles++;
                        etatSources[adresse] = new { source = lues.FirstOrDefault()?.Source ?? Hote(adresse), ok = true, articles = lues.Count, heure = maintenant.ToString("o") };
                    }
                }
                catch (Exception e)
                {
                    lock (verrouLive) { etatSources[adresse] = new { source = Hote(adresse), ok = false, erreur = Court(e.Message), heure = maintenant.ToString("o") }; versionNouvelles++; }
                }
            }
        }

        static string Court(string s) => s == null ? "" : s.Length > 120 ? s.Substring(0, 120) : s;
        static string Hote(string adresse) { try { return new Uri(adresse).Host.Replace("www.", ""); } catch { return Path.GetFileName(adresse); } }

        /// <summary>Flux RSS 2.0 ou Atom : titre, lien, date, source, resume (sans balises).</summary>
        static IEnumerable<Nouvelle> LireFlux(string xml, string adresse)
        {
            var doc = XDocument.Parse(xml);
            string Texte(XElement e, params string[] noms) => e?.Elements().FirstOrDefault(c => noms.Contains(c.Name.LocalName))?.Value?.Trim();
            var canal = doc.Descendants().FirstOrDefault(e => e.Name.LocalName == "channel") ?? doc.Root;
            var nomCanal = Texte(canal, "title");
            if (string.IsNullOrWhiteSpace(nomCanal) || nomCanal.Length > 60) nomCanal = Hote(adresse);
            foreach (var it in doc.Descendants().Where(e => e.Name.LocalName == "item" || e.Name.LocalName == "entry"))
            {
                var titre = Nettoyer(Texte(it, "title"));
                if (string.IsNullOrWhiteSpace(titre)) continue;
                var lien = Texte(it, "link");
                if (string.IsNullOrWhiteSpace(lien)) lien = it.Elements().FirstOrDefault(c => c.Name.LocalName == "link")?.Attribute("href")?.Value ?? "";
                if (!lien.StartsWith("http", StringComparison.OrdinalIgnoreCase)) lien = "";
                var source = Texte(it, "source");
                var resume = Nettoyer(Texte(it, "description", "summary"));
                if (resume.Length > 300) resume = resume.Substring(0, 297) + "...";
                if (resume == titre || resume.StartsWith(titre)) resume = "";
                var d = LireDate(Texte(it, "pubDate", "published", "updated", "date"));
                yield return new Nouvelle
                {
                    Cle = (lien.Length > 0 ? lien : titre).ToLowerInvariant(), Titre = titre.Length > 300 ? titre.Substring(0, 300) : titre, Lien = lien,
                    Source = string.IsNullOrWhiteSpace(source) ? nomCanal : source, Resume = resume, Date = d ?? DateTime.MinValue
                };
            }
        }

        static string Nettoyer(string s)
        {
            if (string.IsNullOrEmpty(s)) return "";
            s = Regex.Replace(s, "<[^>]*>", " ");
            s = System.Net.WebUtility.HtmlDecode(s);
            return Regex.Replace(s, @"\s+", " ").Trim();
        }

        /// <summary>Dates des flux : « Mon, 09 Nov 2026 01:32:17 GMT », « ... -0500 », ISO 8601, ou « 2026-11-09 02:29:07 »
        /// (heure universelle). Renvoie l'heure universelle.</summary>
        public static DateTime? LireDate(string s)
        {
            if (string.IsNullOrWhiteSpace(s)) return null;
            s = s.Trim();
            foreach (var (z, o) in new[] { (" GMT", "+00:00"), (" UTC", "+00:00"), (" UT", "+00:00"), (" Z", "+00:00"), (" EST", "-05:00"), (" EDT", "-04:00"),
                                          (" CST", "-06:00"), (" CDT", "-05:00"), (" PST", "-08:00"), (" PDT", "-07:00") })
                if (s.EndsWith(z)) { s = s.Substring(0, s.Length - z.Length) + " " + o; break; }
            s = Regex.Replace(s, @" ([+-]\d{2})(\d{2})$", " $1:$2");
            var formats = new[] { "ddd, d MMM yyyy HH:mm:ss zzz", "ddd, dd MMM yyyy HH:mm:ss zzz", "d MMM yyyy HH:mm:ss zzz", "ddd, d MMM yyyy HH:mm zzz",
                                  "ddd, dd MMM yyyy HH:mm zzz", "yyyy-MM-dd HH:mm:ss" };
            if (DateTimeOffset.TryParseExact(s, formats, inv, DateTimeStyles.AssumeUniversal | DateTimeStyles.AllowWhiteSpaces, out var d)) return d.UtcDateTime;
            if (DateTimeOffset.TryParse(s, inv, DateTimeStyles.AssumeUniversal, out d)) return d.UtcDateTime;
            return null;
        }

        async Task LireCalendrier(CancellationToken jeton)
        {
            if (string.IsNullOrWhiteSpace(AdresseCalendrier)) return;
            var maintenant = Core.Instance.TimeUtils.DateTimeUtcNow;
            try
            {
                var brut = await Telecharger(AdresseCalendrier, jeton);
                var liste = new List<object>();
                using (var doc = JsonDocument.Parse(brut))
                    foreach (var e in doc.RootElement.EnumerateArray())
                    {
                        string S(string k) => e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : "";
                        var d = DateTimeOffset.TryParse(S("date"), inv, DateTimeStyles.None, out var dd) ? dd.UtcDateTime.ToString("o") : null;
                        if (d == null) continue;
                        liste.Add(new { titre = S("title"), pays = S("country"), date = d, impact = S("impact"), prevision = S("forecast"), precedent = S("previous"), reel = S("actual") });
                    }
                lock (verrouLive)
                {
                    if (brut != calendrierBrut) { calendrier = liste; calendrierBrut = brut; versionCalendrier++; }
                    etatCalendrier = new { ok = true, evenements = liste.Count, heure = maintenant.ToString("o") };
                }
            }
            catch (Exception e) { lock (verrouLive) { etatCalendrier = new { ok = false, erreur = Court(e.Message), heure = maintenant.ToString("o") }; versionCalendrier++; } }
        }

        /// <summary>Cotations en une requete (Yahoo « spark ») : dernier prix, cloture de la veille, heure, courbe de 5 minutes.
        /// Si Yahoo ne repond pas, le VIX et le VIX a 3 mois viennent du CBOE (cotation differee).</summary>
        async Task LireCotations(CancellationToken jeton)
        {
            var symboles = (CotationsYahoo ?? "").Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries).Select(x => x.Trim()).Where(x => x.Length > 0).ToList();
            if (symboles.Count == 0) return;
            var maintenant = Core.Instance.TimeUtils.DateTimeUtcNow;
            var res = new List<object>(); string erreur = null;
            try
            {
                var brut = await Telecharger(string.Format(AdresseCotations, string.Join(",", symboles.Select(Uri.EscapeDataString))), jeton);
                using var doc = JsonDocument.Parse(brut);
                foreach (var r in doc.RootElement.GetProperty("spark").GetProperty("result").EnumerateArray())
                {
                    var rep = r.GetProperty("response")[0]; var meta = rep.GetProperty("meta");
                    double? D(JsonElement e, string k) => e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.Number ? v.GetDouble() : (double?)null;
                    var serie = new List<double?>(); var temps = new List<long>();
                    if (rep.TryGetProperty("indicators", out var ind) && ind.TryGetProperty("quote", out var q) && q.GetArrayLength() > 0 && q[0].TryGetProperty("close", out var cl)
                        && rep.TryGetProperty("timestamp", out var ts))
                    {
                        var c = cl.EnumerateArray().ToList(); var tt = ts.EnumerateArray().ToList();
                        for (int k = 0; k < Math.Min(c.Count, tt.Count); k++)
                            if (c[k].ValueKind == JsonValueKind.Number) { serie.Add(Math.Round(c[k].GetDouble(), 4)); temps.Add(tt[k].GetInt64()); }
                    }
                    res.Add(new
                    {
                        symbole = r.GetProperty("symbol").GetString(), nom = meta.TryGetProperty("shortName", out var sn) ? sn.GetString() : null,
                        dernier = D(meta, "regularMarketPrice"), veille = D(meta, "previousClose") ?? D(meta, "chartPreviousClose"),
                        haut = D(meta, "regularMarketDayHigh"), bas = D(meta, "regularMarketDayLow"), heure = D(meta, "regularMarketTime"), serie, temps
                    });
                }
            }
            catch (Exception e) { erreur = Court(e.Message); }
            if (res.Count == 0)                                                   // secours : le CBOE pour la volatilite
                foreach (var v in new[] { "VIX", "VIX3M", "VIX9D", "VVIX" })
                    try
                    {
                        using var doc = JsonDocument.Parse(await Telecharger(string.Format(AdresseSecoursVIX, v), jeton));
                        var d = doc.RootElement.GetProperty("data");
                        double? D(string k) => d.TryGetProperty(k, out var x) && x.ValueKind == JsonValueKind.Number ? x.GetDouble() : (double?)null;
                        var cour = D("current_price"); var chg = D("price_change");
                        res.Add(new { symbole = "^" + v, nom = v + " (CBOE, differe)", dernier = cour, veille = cour - chg, haut = D("high"), bas = D("low"), heure = (double?)null,
                                      serie = new List<double?>(), temps = new List<long>() });
                    }
                    catch { }
            lock (verrouLive)
            {
                if (res.Count > 0) { cotations = res; versionCotations++; }
                etatCotations = new { ok = erreur == null, erreur, symboles = res.Count, heure = maintenant.ToString("o") };
            }
        }

        /// <summary>Le filtre VIX du Bot 3 en 1 (Z12) : clotures du CBOE de la derniere seance avant aujourd'hui (New York).</summary>
        async Task LireVixVeille(DateTime jour, CancellationToken jeton)
        {
            try
            {
                var a = Clotures(await Telecharger(AdresseVIX, jeton)); var b = Clotures(await Telecharger(AdresseVIX3M, jeton));
                var d = a.Keys.Intersect(b.Keys).Where(x => x < jour).DefaultIfEmpty(DateTime.MinValue).Max();
                if (d == DateTime.MinValue) return;
                lock (verrouLive)
                {
                    vixVeille = new { pour = jour.ToString("yyyy-MM-dd"), date = d.ToString("yyyy-MM-dd"), vix = a[d], vix3m = b[d], inverse = a[d] >= b[d] };
                    jourVixVeille = jour; versionCotations++;
                }
            }
            catch (Exception e) { lock (verrouLive) vixVeille = new { pour = jour.ToString("yyyy-MM-dd"), erreur = Court(e.Message) }; }
        }

        static Dictionary<DateTime, double> Clotures(string csv)
        {
            var r = new Dictionary<DateTime, double>();
            var lignes = csv.Split('\n').Select(l => l.Trim()).Where(l => l.Length > 0).ToList();
            if (lignes.Count == 0) return r;
            var tete = lignes[0].ToUpperInvariant().Split(',');
            int id = Array.IndexOf(tete, "DATE"), ic = Array.IndexOf(tete, "CLOSE");
            if (id < 0 || ic < 0) return r;
            foreach (var l in lignes.Skip(1))
            {
                var x = l.Split(',');
                if (x.Length <= Math.Max(id, ic)) continue;
                if (DateTime.TryParseExact(x[id].Trim(), new[] { "MM/dd/yyyy", "yyyy-MM-dd", "M/d/yyyy" }, inv, DateTimeStyles.None, out var d)
                    && double.TryParse(x[ic].Trim(), NumberStyles.Float, inv, out var c)) r[d.Date] = c;
            }
            return r;
        }

        // ------------------------------------------------------------------ service
        (byte[] corps, string type, int code) ServirLive(string chemin, string cible)
        {
            const string J = "application/json; charset=utf-8";
            if (chemin == "/live" || chemin == "/live/")
            {
                var page = Path.Combine(Dossier, "live.html");
                return File.Exists(page) ? (File.ReadAllBytes(page), "text/html; charset=utf-8", 200)
                    : (Encoding.UTF8.GetBytes($"<p>Page du terminal live introuvable : {page}. Relance l'installation (ligne PowerShell).</p>"), "text/html; charset=utf-8", 404);
            }
            if (chemin == "/live/barres") return (Encoding.UTF8.GetBytes(BarresJson()), J, 200);
            if (chemin == "/live/etat")
            {
                var q = ParametresRequete(cible);
                long V(string k) => q.TryGetValue(k, out var s) && long.TryParse(s, out var v) ? v : -1;
                return (Encoding.UTF8.GetBytes(EtatJson(V("n"), V("c"), V("q"), V("g"))), J, 200);
            }
            return (Encoding.UTF8.GetBytes("introuvable"), "text/plain; charset=utf-8", 404);
        }

        static Dictionary<string, string> ParametresRequete(string cible)
        {
            var r = new Dictionary<string, string>();
            int k = cible.IndexOf('?'); if (k < 0) return r;
            foreach (var p in cible.Substring(k + 1).Split('&')) { var x = p.Split('='); if (x.Length == 2) r[x[0]] = Uri.UnescapeDataString(x[1]); }
            return r;
        }

        string BarresJson()
        {
            lock (verrou)
            {
                var t = Core.Instance.TimeUtils.DateTimeUtcNow;
                return JsonSerializer.Serialize(new
                {
                    utc = t.ToString("o"), ny = Ny(t).ToString("yyyy-MM-dd HH:mm:ss"), version = Version,
                    marches = suivis.Select(m => new
                    {
                        nom = m.Nom, symbole = m.S.Name, jour = m.Jour == DateTime.MinValue ? null : m.Jour.ToString("yyyy-MM-dd"),
                        barres = m.B.Select((b, i) => b == null ? null : new[] { i, b[0], b[1], b[2], b[3], b[4], b[5], b[6] }).Where(z => z != null).ToList(),
                        cloturePrec = m.CloturePrec, jourPrec = m.JourPrec?.ToString("yyyy-MM-dd"), plageMoyenne = m.PlageMoyenne, seances = m.Seances,
                        volMoyen = m.VolMoyen?.Select(v => Math.Round(v, 1)).ToArray()
                    }).ToList()
                });
            }
        }

        string EtatJson(long n, long c, long q, long g)
        {
            var t = Core.Instance.TimeUtils.DateTimeUtcNow;
            object marches;
            lock (verrou)
                marches = suivis.Select(m =>
                {
                    var (jour, i) = Globex(Ny(t));
                    double[] b = null, p = null;
                    if (m.Jour == jour && i >= 0) { b = m.B[i]; if (i >= 1) p = m.B[i - 1]; }
                    return new { nom = m.Nom, jour = m.Jour == DateTime.MinValue ? null : m.Jour.ToString("yyyy-MM-dd"), i, barre = b, prec = p, dernier = m.Dernier,
                                 age = m.DernierTick == DateTime.MinValue ? (double?)null : (t - m.DernierTick).TotalSeconds };
                }).ToList();
            List<object> journaux; object compte;
            lock (verrou) { journaux = journauxRecents.Skip(Math.Max(0, journauxRecents.Count - 60)).ToList(); compte = EtatCompte(); }
            lock (verrouLive)
            {
                return JsonSerializer.Serialize(new
                {
                    utc = t.ToString("o"), ny = Ny(t).ToString("yyyy-MM-dd HH:mm:ss"), marches, compte, journaux,
                    versions = new { n = versionNouvelles, c = versionCalendrier, q = versionCotations, g = versionGros },
                    nouvelles = n == versionNouvelles ? null : nouvelles.Values.OrderByDescending(x => x.Date).Take(300)
                        .Select(x => new { titre = x.Titre, lien = x.Lien, source = x.Source, resume = x.Resume, date = x.Date.ToString("o"), vu = x.Vu.ToString("o") }).ToList(),
                    sources = n == versionNouvelles ? null : etatSources.Values.ToList(),
                    calendrier = c == versionCalendrier ? null : calendrier, etatCalendrier = c == versionCalendrier ? null : etatCalendrier,
                    cotations = q == versionCotations ? null : cotations, etatCotations = q == versionCotations ? null : etatCotations,
                    vixVeille = q == versionCotations ? null : vixVeille,
                    gros = g == versionGros ? null : grosOrdres.Skip(Math.Max(0, grosOrdres.Count - 60)).ToList()
                });
            }
        }
    }
}
