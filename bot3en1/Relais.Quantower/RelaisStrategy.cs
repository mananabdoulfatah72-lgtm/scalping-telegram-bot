using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using TradingPlatform.BusinessLayer;

namespace RelaisNQ
{
    /// <summary>Relais du direct pour la station NQ : ne passe aucun ordre. Lit les transactions du NQ (et de l'ES) recues de
    /// Rithmic, en fait des barres d'une minute (seance 9 h 30 - 16 h, New York), lit la position MNQ et le solde du compte, suit
    /// les journaux des agents, et sert le tout sur ce PC seulement (http://localhost:PORT) : la page de la station, l'historique
    /// des dernieres seances et un flux continu (Server-Sent Events).</summary>
    public class RelaisStrategy : Strategy
    {
        [InputParameter("NQ (prix), contrat du moment, ex. NQZ6", 10)] public Symbol SymboleNQ;
        [InputParameter("ES (facultatif), ex. ESZ6", 20)] public Symbol SymboleES;
        [InputParameter("Compte a surveiller (facultatif : position et solde)", 30)] public Account Compte;
        [InputParameter("MNQ du compte (facultatif), ex. MNQZ6", 40)] public Symbol SymboleMNQ;
        [InputParameter("Port local (la station s'ouvre sur http://localhost:PORT)", 50, 1024, 65000, 1, 0)] public int Port = 8765;
        [InputParameter("Dossier de la station (page et copie de l'historique)", 60)] public string Dossier = @"C:\StationNQ";
        [InputParameter("Journaux des agents a suivre (dossiers separes par ;)", 70)] public string DossiersAgents = @"C:\Bot3en1;C:\SupertrendNQ;C:\XGBoostNQ";
        [InputParameter("Historique : adresse des barres du robot", 80)]
        public string AdresseHistorique = "https://raw.githubusercontent.com/mananabdoulfatah72-lgtm/scalping-telegram-bot/main/zone/robot/nq_1min.csv.gz";

        const string Version = "3 novembre 2026";
        const int N = 390, SEANCES = 30;
        static readonly HttpClient http = new HttpClient { Timeout = TimeSpan.FromSeconds(20) };
        readonly object verrou = new object();
        TimeZoneInfo ny;
        TcpListener ecoute;
        CancellationTokenSource arret;
        Timer horloge;
        readonly List<NetworkStream> clients = new List<NetworkStream>();
        readonly Marche nq = new Marche("NQ"), es = new Marche("ES");
        readonly List<object> journauxNeufs = new List<object>();
        readonly List<object> journauxRecents = new List<object>();     // envoyes a chaque page qui se branche
        readonly Dictionary<string, long> positions = new Dictionary<string, long>();
        int envoisSansClient;

        /// <summary>Barres d'une minute d'un marche, par seance (cle : jour de New York), et dernier prix.</summary>
        class Marche
        {
            public readonly string Nom;
            public readonly SortedDictionary<DateTime, double[][]> Jours = new SortedDictionary<DateTime, double[][]>();   // [minute] = o,h,l,c,v,achats,ventes
            public double Dernier; public DateTime DernierTick = DateTime.MinValue;
            public Marche(string nom) { Nom = nom; }
            public double[][] Jour(DateTime j) { if (!Jours.TryGetValue(j, out var b)) { b = new double[N][]; Jours[j] = b; } return b; }
            public void Ajouter(DateTime j, int m, double p, double v, int cote)
            {
                if (m < 0 || m >= N) return;
                var b = Jour(j); var x = b[m];
                if (x == null) b[m] = x = new[] { p, p, p, p, 0.0, 0.0, 0.0 };
                x[1] = Math.Max(x[1], p); x[2] = Math.Min(x[2], p); x[3] = p; x[4] += v;
                if (cote > 0) x[5] += v; else if (cote < 0) x[6] += v;
            }
        }

        public RelaisStrategy() : base()
        {
            Name = "Relais NQ (station en direct)";
            Description = "Sert la station NQ en direct sur ce PC (http://localhost:8765). Aucun ordre.";
        }

        protected override void OnRun()
        {
            try
            {
                if (SymboleNQ == null) throw new Exception("choisis le symbole NQ dans les reglages");
                ny = TrouverFuseau();
                Directory.CreateDirectory(Dossier);
                Historique();
                SymboleNQ.NewLast += SurNQ;
                if (SymboleES != null) SymboleES.NewLast += SurES;
                foreach (var d in Agents()) { var f = Path.Combine(d, "journal.txt"); positions[f] = File.Exists(f) ? Math.Max(0, new FileInfo(f).Length - 4000) : 0; }
                arret = new CancellationTokenSource();
                ecoute = new TcpListener(IPAddress.Loopback, Port);
                ecoute.Start();
                _ = Task.Run(() => Accepter(arret.Token));
                horloge = new Timer(_ => Envoyer(), null, 250, 250);
                Log($"relais demarre (version du {Version}) : ouvre http://localhost:{Port} dans Chrome ou Edge. {nq.Jours.Count} seances NQ"
                    + $"{(SymboleES != null ? $", {es.Jours.Count} seances ES" : "")} en memoire. Aucun ordre n'est passe.", StrategyLoggingLevel.Info);
            }
            catch (Exception e)
            {
                Log($"ERREUR au demarrage du relais : {e.Message}", StrategyLoggingLevel.Error);
                Stop();
            }
        }

        protected override void OnStop()
        {
            horloge?.Dispose();
            try { arret?.Cancel(); ecoute?.Stop(); } catch { }
            lock (clients) { foreach (var c in clients) try { c.Dispose(); } catch { } clients.Clear(); }
            if (SymboleNQ != null) SymboleNQ.NewLast -= SurNQ;
            if (SymboleES != null) SymboleES.NewLast -= SurES;
            Log("relais arrete", StrategyLoggingLevel.Info);
        }

        static TimeZoneInfo TrouverFuseau()
        {
            foreach (var id in new[] { "Eastern Standard Time", "America/New_York" })
                try { return TimeZoneInfo.FindSystemTimeZoneById(id); } catch { }
            throw new Exception("fuseau horaire de New York introuvable");
        }

        static DateTime EnUtc(DateTime d) => d.Kind == DateTimeKind.Local ? d.ToUniversalTime()
            : d.Kind == DateTimeKind.Unspecified ? DateTime.SpecifyKind(d, DateTimeKind.Utc) : d;
        DateTime Ny(DateTime utc) => TimeZoneInfo.ConvertTimeFromUtc(EnUtc(utc), ny);
        static int Minute(DateTime t) => t.Hour * 60 + t.Minute - 570;
        IEnumerable<string> Agents() => (DossiersAgents ?? "").Split(new[] { ';' }, StringSplitOptions.RemoveEmptyEntries).Select(x => x.Trim()).Where(x => x.Length > 0);

        // ------------------------------------------------------------------ historique
        /// <summary>Les 30 dernieres seances : barres du robot (GitHub, copie locale sinon), puis barres d'une minute de
        /// Quantower si la plateforme les donne, puis transactions de la seance du jour deja passees.</summary>
        void Historique()
        {
            var aujourdhui = Ny(Core.Instance.TimeUtils.DateTimeUtcNow).Date;
            string local = Path.Combine(Dossier, "nq_1min.csv.gz");
            try { File.WriteAllBytes(local, http.GetByteArrayAsync(AdresseHistorique).GetAwaiter().GetResult()); }
            catch (Exception e) { Log($"historique du robot non telecharge ({e.Message}) : copie locale si elle existe", StrategyLoggingLevel.Info); }
            if (File.Exists(local)) LireRobot(local, aujourdhui);
            MinutesQuantower(SymboleNQ, nq, aujourdhui);
            if (SymboleES != null) MinutesQuantower(SymboleES, es, aujourdhui);
            Transactions(SymboleNQ, nq, aujourdhui);
            if (SymboleES != null) Transactions(SymboleES, es, aujourdhui);
            foreach (var m in new[] { nq, es }) while (m.Jours.Count > SEANCES) m.Jours.Remove(m.Jours.Keys.First());
        }

        void LireRobot(string f, DateTime avant)
        {
            var inv = CultureInfo.InvariantCulture;
            var lignes = new List<string>();
            using (var s = new GZipStream(File.OpenRead(f), CompressionMode.Decompress))
            using (var r = new StreamReader(s)) { string l; r.ReadLine(); while ((l = r.ReadLine()) != null) lignes.Add(l); }
            var jours = lignes.Select(l => l.Length >= 10 ? l.Substring(0, 10) : "").Where(j => j.Length == 10).Distinct().OrderBy(j => j).ToList();
            var garder = new HashSet<string>(jours.Where(j => string.CompareOrdinal(j, avant.ToString("yyyy-MM-dd")) < 0).Reverse().Take(SEANCES));
            foreach (var l in lignes)
            {
                if (l.Length < 16 || !garder.Contains(l.Substring(0, 10))) continue;
                var x = l.Split(',');
                var t = DateTime.ParseExact(x[0], "yyyy-MM-dd HH:mm", inv);
                int m = Minute(t); if (m < 0 || m >= N) continue;
                nq.Jour(t.Date)[m] = new[] { double.Parse(x[1], inv), double.Parse(x[2], inv), double.Parse(x[3], inv), double.Parse(x[4], inv), x.Length > 5 ? double.Parse(x[5], inv) : 0, 0.0, 0.0 };
            }
        }

        /// <summary>Barres d'une minute de la plateforme (45 derniers jours), par reflexion : rien ne depend de ces noms a la
        /// compilation ; si la plateforme ne les donne pas, l'historique du robot reste.</summary>
        void MinutesQuantower(Symbol symbole, Marche marche, DateTime avant)
        {
            try
            {
                var asm = typeof(Symbol).Assembly;
                var tAgg = asm.GetType("TradingPlatform.BusinessLayer.HistoryAggregationTime");
                var tPer = asm.GetType("TradingPlatform.BusinessLayer.Period");
                if (tAgg == null || tPer == null) return;
                var min1 = tPer.GetProperty("MIN1")?.GetValue(null) ?? tPer.GetField("MIN1")?.GetValue(null);
                var agg = Activator.CreateInstance(tAgg, min1, HistoryType.Last);
                var fin = Core.Instance.TimeUtils.DateTimeUtcNow;
                var h = symbole.GetHistory(new HistoryRequestParameters { Symbol = symbole, FromTime = fin.AddDays(-45), ToTime = fin, Aggregation = agg });
                int n = 0;
                var lu = new Dictionary<DateTime, double[][]>();
                for (int i = 0; i < h.Count; i++)
                {
                    object it = h[i, SeekOriginHistory.Begin];
                    object Val(string p) => it.GetType().GetProperty(p)?.GetValue(it) ?? it.GetType().GetField(p)?.GetValue(it);
                    double V(string p) { var v = Val(p); return v == null ? double.NaN : Convert.ToDouble(v, CultureInfo.InvariantCulture); }
                    var tl = Val("TimeLeft");
                    if (!(tl is DateTime t0)) continue;
                    var t = Ny(t0); int m = Minute(t);
                    if (m < 0 || m >= N || t.Date >= avant || double.IsNaN(V("Close"))) continue;
                    if (!lu.TryGetValue(t.Date, out var b)) { b = new double[N][]; lu[t.Date] = b; }
                    b[m] = new[] { V("Open"), V("High"), V("Low"), V("Close"), double.IsNaN(V("Volume")) ? 0 : V("Volume"), 0.0, 0.0 };
                    n++;
                }
                foreach (var kv in lu) marche.Jours[kv.Key] = kv.Value;   // la plateforme remplace le robot pour ces seances
                if (n > 0) Log($"{marche.Nom} : {n} minutes lues dans l'historique de la plateforme ({lu.Count} seances)", StrategyLoggingLevel.Info);
            }
            catch (Exception e) { Log($"{marche.Nom} : barres d'une minute de la plateforme indisponibles ({e.Message}) : historique du robot seul", StrategyLoggingLevel.Info); }
        }

        void Transactions(Symbol symbole, Marche marche, DateTime jour)
        {
            var maintenant = Ny(Core.Instance.TimeUtils.DateTimeUtcNow);
            if (maintenant.Date != jour || Minute(maintenant) <= 0) return;
            try
            {
                var debut = TimeZoneInfo.ConvertTimeToUtc(jour.AddMinutes(570), ny);
                var ticks = symbole.GetHistory(new HistoryRequestParameters { Symbol = symbole, FromTime = debut, ToTime = Core.Instance.TimeUtils.DateTimeUtcNow,
                                                                             Aggregation = new HistoryAggregationTick(HistoryType.Last) });
                for (int i = 0; i < ticks.Count; i++)
                    if (ticks[i, SeekOriginHistory.Begin] is HistoryItemLast t)
                    {
                        var tn = Ny(t.TimeLeft);
                        marche.Ajouter(tn.Date, Minute(tn), t.Price, t.Volume, t.AggressorFlag == AggressorFlag.Buy ? 1 : t.AggressorFlag == AggressorFlag.Sell ? -1 : 0);
                    }
            }
            catch (Exception e) { Log($"{marche.Nom} : transactions deja passees de la seance indisponibles ({e.Message})", StrategyLoggingLevel.Info); }
        }

        // ------------------------------------------------------------------ marche en direct
        void SurNQ(Symbol s, Last l) => Recevoir(nq, l);
        void SurES(Symbol s, Last l) => Recevoir(es, l);
        void Recevoir(Marche m, Last l)
        {
            lock (verrou)
            {
                var t = Ny(l.Time);
                m.Dernier = l.Price; m.DernierTick = Core.Instance.TimeUtils.DateTimeUtcNow;
                m.Ajouter(t.Date, Minute(t), l.Price, l.Size, l.AggressorFlag == AggressorFlag.Buy ? 1 : l.AggressorFlag == AggressorFlag.Sell ? -1 : 0);
            }
        }

        // ------------------------------------------------------------------ compte et journaux
        static double? Lire(object o, string p)
        {
            try
            {
                var v = o?.GetType().GetProperty(p)?.GetValue(o);
                if (v == null) return null;
                var pv = v.GetType().GetProperty("Value")?.GetValue(v);          // PnLItem
                return Convert.ToDouble(pv ?? v, CultureInfo.InvariantCulture);
            }
            catch { return null; }
        }

        object EtatCompte()
        {
            if (Compte == null) return null;
            double? solde = Lire(Compte, "Balance");
            int q = 0; double? prix = null; double latent = 0;
            if (SymboleMNQ != null)
                foreach (var p in Core.Instance.Positions)
                    if (p.Account == Compte && p.Symbol == SymboleMNQ)
                    {
                        int s = (p.Side == Side.Buy ? 1 : -1) * (int)Math.Round(p.Quantity);
                        q += s; prix = Lire(p, "OpenPrice") ?? prix; latent += Lire(p, "GrossPnL") ?? 0;
                    }
            return new { nom = Compte.Name, solde, position = q, prix, latent };
        }

        void LireJournaux()
        {
            foreach (var d in Agents())
            {
                var f = Path.Combine(d, "journal.txt");
                try
                {
                    if (!File.Exists(f)) continue;
                    long deb = positions.TryGetValue(f, out var x) ? x : 0, taille = new FileInfo(f).Length;
                    if (taille < deb) deb = 0;                                        // journal recommence
                    if (taille == deb) continue;
                    using var s = new FileStream(f, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete);
                    s.Seek(deb, SeekOrigin.Begin);
                    using var r = new StreamReader(s, Encoding.UTF8);
                    var texte = r.ReadToEnd();
                    int fin = texte.LastIndexOf('\n');
                    if (fin < 0) continue;                                            // ligne pas encore finie
                    positions[f] = deb + Encoding.UTF8.GetByteCount(texte.Substring(0, fin + 1));
                    var agent = Path.GetFileName(d.TrimEnd('\\', '/'));
                    foreach (var l in texte.Substring(0, fin).Split('\n').Select(z => z.TrimEnd('\r')).Where(z => z.Length > 0))
                        lock (verrou) journauxNeufs.Add(new { agent, ligne = l });
                }
                catch { }
            }
        }

        // ------------------------------------------------------------------ flux
        object Barre(Marche m)
        {
            var t = Ny(Core.Instance.TimeUtils.DateTimeUtcNow);
            int mm = Minute(t);
            double[] b = null, p = null;
            if (m.Jours.TryGetValue(t.Date, out var j)) { if (mm >= 0 && mm < N) b = j[mm]; if (mm >= 1 && mm <= N) p = j[mm - 1]; }
            return new { jour = t.Date.ToString("yyyy-MM-dd"), m = mm, barre = b, prec = p, dernier = m.Dernier,
                         age = m.DernierTick == DateTime.MinValue ? (double?)null : (Core.Instance.TimeUtils.DateTimeUtcNow - m.DernierTick).TotalSeconds };
        }

        void Envoyer()
        {
            try
            {
                LireJournaux();
                string json;
                lock (verrou)
                {
                    var t = Core.Instance.TimeUtils.DateTimeUtcNow;
                    json = JsonSerializer.Serialize(new { utc = t.ToString("o"), ny = Ny(t).ToString("yyyy-MM-dd HH:mm:ss"), nq = Barre(nq),
                                                          es = SymboleES != null ? Barre(es) : null, compte = EtatCompte(), journaux = journauxNeufs.ToList() });
                    journauxRecents.AddRange(journauxNeufs);
                    if (journauxRecents.Count > 300) journauxRecents.RemoveRange(0, journauxRecents.Count - 300);
                    journauxNeufs.Clear();
                }
                var octets = Encoding.UTF8.GetBytes("data: " + json + "\n\n");
                lock (clients)
                {
                    for (int i = clients.Count - 1; i >= 0; i--)
                    {
                        try { clients[i].Write(octets, 0, octets.Length); clients[i].Flush(); }
                        catch { try { clients[i].Dispose(); } catch { } clients.RemoveAt(i); }
                    }
                    envoisSansClient = clients.Count == 0 ? envoisSansClient + 1 : 0;
                }
            }
            catch (Exception e) { Log($"ERREUR du flux : {e.Message}", StrategyLoggingLevel.Error); }
        }

        string HistoriqueJson()
        {
            lock (verrou)
            {
                object Paquet(Marche m) => new
                {
                    jours = m.Jours.Keys.Select(j => j.ToString("yyyy-MM-dd")).ToList(),
                    minutes = m.Jours.ToDictionary(kv => kv.Key.ToString("yyyy-MM-dd"),
                        kv => kv.Value.Select((b, i) => b == null ? null : new[] { i, b[0], b[1], b[2], b[3], b[4], b[5], b[6] }).Where(z => z != null).ToList())
                };
                return JsonSerializer.Serialize(new { version = Version, nq = Paquet(nq), es = SymboleES != null ? Paquet(es) : null,
                    symboles = new { nq = SymboleNQ?.Name, es = SymboleES?.Name, mnq = SymboleMNQ?.Name, compte = Compte?.Name },
                    utc = Core.Instance.TimeUtils.DateTimeUtcNow.ToString("o") });
            }
        }

        // ------------------------------------------------------------------ serveur HTTP minimal (ce PC seulement)
        async Task Accepter(CancellationToken jeton)
        {
            while (!jeton.IsCancellationRequested)
            {
                TcpClient c;
                try { c = await ecoute.AcceptTcpClientAsync(); } catch { break; }
                _ = Task.Run(() => Servir(c));
            }
        }

        void Servir(TcpClient c)
        {
            var flux = c.GetStream();
            try
            {
                var lecteur = new StreamReader(flux, Encoding.ASCII, false, 1024, true);
                var demande = lecteur.ReadLine() ?? "";
                string l; while (!string.IsNullOrEmpty(l = lecteur.ReadLine())) { }
                var morceaux = demande.Split(' ');
                var chemin = morceaux.Length > 1 ? morceaux[1].Split('?')[0] : "/";
                if (chemin == "/flux")
                {
                    var tete = Encoding.ASCII.GetBytes("HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nCache-Control: no-cache\r\nConnection: keep-alive\r\n\r\n");
                    lock (clients)
                    {
                        string debut;
                        lock (verrou)
                        {
                            var t = Core.Instance.TimeUtils.DateTimeUtcNow;   // les dernieres lignes des agents, pour une page qui arrive
                            debut = JsonSerializer.Serialize(new { debut = true, utc = t.ToString("o"), ny = Ny(t).ToString("yyyy-MM-dd HH:mm:ss"), journaux = journauxRecents.ToList() });
                        }
                        var premier = Encoding.UTF8.GetBytes("data: " + debut + "\n\n");
                        flux.Write(tete, 0, tete.Length); flux.Write(premier, 0, premier.Length); flux.Flush();
                        clients.Add(flux);
                    }
                    return;                                                           // reste ouvert, alimente par Envoyer()
                }
                byte[] corps; string type; int code = 200;
                if (chemin == "/historique") { corps = Encoding.UTF8.GetBytes(HistoriqueJson()); type = "application/json; charset=utf-8"; }
                else if (chemin == "/" || chemin == "/index.html")
                {
                    var page = Path.Combine(Dossier, "station-direct.html");
                    if (File.Exists(page)) { corps = File.ReadAllBytes(page); type = "text/html; charset=utf-8"; }
                    else { corps = Encoding.UTF8.GetBytes($"<p>Page de la station introuvable : {page}. Relance l'installation (ligne PowerShell).</p>"); type = "text/html; charset=utf-8"; code = 404; }
                }
                else { corps = Encoding.UTF8.GetBytes("introuvable"); type = "text/plain; charset=utf-8"; code = 404; }
                var entete = Encoding.ASCII.GetBytes($"HTTP/1.1 {code} {(code == 200 ? "OK" : "Not Found")}\r\nContent-Type: {type}\r\nContent-Length: {corps.Length}\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n");
                flux.Write(entete, 0, entete.Length); flux.Write(corps, 0, corps.Length); flux.Flush();
                c.Close();
            }
            catch { try { c.Close(); } catch { } }
        }
    }
}
