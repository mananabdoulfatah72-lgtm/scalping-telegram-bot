using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using TradingPlatform.BusinessLayer;

namespace Bot3en1
{
    /// <summary>Exporte les transactions du NQ fournies par Rithmic (cote agresseur compris), regroupees par minute, pour
    /// tester le filtre delta sur des mois qu'il n'a jamais vus (filtre_h1/README.md, version Rithmic) et chercher un
    /// scalping de nuit sur de vraies transactions (scalping/README.md, partie D). Ne passe aucun ordre. Un fichier par
    /// contrat et par seance (jour,minute,o,h,l,c,v,achats,ventes,sans_cote,contrat) :
    /// - jour (9 h 30 - 16 h, heure de New York) : C:\Bot3en1\export\transactions_NQZ6.csv, minute 0 = 9 h 30 ;
    /// - nuit (18 h la veille - 9 h 30) : transactions_nuit_NQZ6.csv, minute 0 = 18 h la veille, 930 = 9 h 30 exclu ;
    /// - 24 h (18 h la veille - 17 h) : transactions_24h_NQZ6.csv, minute 0 = 18 h la veille, 930 = 9 h 30.
    /// La colonne jour est toujours la date de la seance de jour qui suit (la nuit du lundi part du dimanche 18 h).</summary>
    public class ExportTransactions : Strategy
    {
        [InputParameter("NQ : contrat a exporter (ex. NQZ6, puis NQU6, NQM6, NQH6...)", 10)] public Symbol SymboleNQ;
        [InputParameter("Premier jour (AAAA-MM-JJ), vide = 3 ans en arriere", 20)] public string Debut = "";
        [InputParameter("Dernier jour (AAAA-MM-JJ), vide = hier", 30)] public string Fin = "";
        [InputParameter("Seulement les jours ou ce contrat est l'echeance suivie (regle du calendrier)", 40)] public bool SeulementEcheance = true;
        [InputParameter("Seance : 0 = jour (9 h 30 - 16 h), 1 = nuit (18 h la veille - 9 h 30), 2 = 24 h (18 h la veille - 17 h)", 45, 0, 2, 1, 0)] public int Seance = 0;
        [InputParameter("Dossier des donnees du bot", 50)] public string Dossier = @"C:\Bot3en1";

        public ExportTransactions() : base()
        {
            Name = "Export transactions NQ (test du filtre delta)";
            Description = "Exporte les transactions Rithmic du NQ par minute (jour, nuit ou 24 h), avec le cote agresseur. Aucun ordre.";
        }

        protected override void OnRun()
        {
            try
            {
                if (SymboleNQ == null) throw new Exception("choisis le contrat NQ a exporter");
                if (Seance < 0 || Seance > 2) throw new Exception("Seance : 0 = jour, 1 = nuit, 2 = 24 h");
                // debut de la seance en minutes depuis minuit du jour (negatif = la veille) et nombre de minutes
                int debutMin = Seance == 0 ? 570 : -360, nMin = Seance == 0 ? Moteur.N : Seance == 1 ? 930 : 1380;
                string prefixe = Seance == 0 ? "transactions_" : Seance == 1 ? "transactions_nuit_" : "transactions_24h_";
                var ny = TrouverFuseau();
                var inv = CultureInfo.InvariantCulture;
                var aujourdhui = TimeZoneInfo.ConvertTimeFromUtc(Core.Instance.TimeUtils.DateTimeUtcNow, ny).Date;
                var d0 = string.IsNullOrWhiteSpace(Debut) ? aujourdhui.AddYears(-3) : DateTime.ParseExact(Debut.Trim(), "yyyy-MM-dd", inv);
                var d1 = string.IsNullOrWhiteSpace(Fin) ? aujourdhui.AddDays(-1) : DateTime.ParseExact(Fin.Trim(), "yyyy-MM-dd", inv);
                string nom = (SymboleNQ.Name ?? "NQ").Replace("/", "").Replace(" ", "");
                string dossier = Path.Combine(Dossier, "export");
                Directory.CreateDirectory(dossier);
                string fichier = Path.Combine(dossier, $"{prefixe}{nom}.csv");
                var lignes = new List<string> { "jour,minute,o,h,l,c,v,achats,ventes,sans_cote,contrat" };
                int jours = 0, vides = 0;
                double volCote = 0, volTotal = 0;
                Log($"export de {nom} ({(Seance == 0 ? "jour" : Seance == 1 ? "nuit" : "24 h")}) du {d0:yyyy-MM-dd} au {d1:yyyy-MM-dd} : une ligne par seance exportee (environ une minute chacune)", StrategyLoggingLevel.Info);
                for (var j = d0.Date; j <= d1.Date; j = j.AddDays(1))
                {
                    if (Calendrier.JourFerme(j)) continue;
                    if (SeulementEcheance)
                    {
                        string c = Calendrier.Contrat(j), court = $"{c[0]}{c[^1]}";
                        if (!nom.ToUpperInvariant().EndsWith(court) && !nom.ToUpperInvariant().Contains(c)) continue;
                    }
                    var debutLocal = j.AddMinutes(debutMin);
                    var debutUtc = TimeZoneInfo.ConvertTimeToUtc(debutLocal, ny);
                    var finUtc = TimeZoneInfo.ConvertTimeToUtc(debutLocal.AddMinutes(nMin), ny);
                    HistoricalData h;
                    try
                    {
                        h = SymboleNQ.GetHistory(new HistoryRequestParameters
                        {
                            Symbol = SymboleNQ, FromTime = debutUtc, ToTime = finUtc,
                            Aggregation = new HistoryAggregationTick(HistoryType.Last)   // Quantower 1.146 : le type d'historique est dans l'agregation
                        });
                    }
                    catch (Exception e) { Log($"{j:yyyy-MM-dd} : pas d'historique ({e.Message})", StrategyLoggingLevel.Error); vides++; continue; }
                    var m = new Dictionary<int, double[]>();      // minute -> o, h, l, c, v, achats, ventes, sans cote
                    for (int i = 0; i < h.Count; i++)
                    {
                        if (!(h[i, SeekOriginHistory.Begin] is HistoryItemLast t)) continue;
                        var tn = TimeZoneInfo.ConvertTimeFromUtc(t.TimeLeft, ny);
                        // minutes d'horloge de New York depuis le debut (les changements d'heure tombent le dimanche a
                        // 2 h, marche ferme)
                        int k = (int)Math.Floor((tn - debutLocal).TotalMinutes);
                        if (k < 0 || k >= nMin) continue;
                        if (!m.TryGetValue(k, out var b)) m[k] = b = new double[] { t.Price, t.Price, t.Price, t.Price, 0, 0, 0, 0 };
                        b[1] = Math.Max(b[1], t.Price); b[2] = Math.Min(b[2], t.Price); b[3] = t.Price; b[4] += t.Volume;
                        if (t.AggressorFlag == AggressorFlag.Buy) b[5] += t.Volume;
                        else if (t.AggressorFlag == AggressorFlag.Sell) b[6] += t.Volume;
                        else b[7] += t.Volume;
                    }
                    if (m.Count == 0) { vides++; continue; }
                    jours++;
                    foreach (var kv in m.OrderBy(x => x.Key))
                    {
                        var b = kv.Value;
                        volCote += b[5] + b[6]; volTotal += b[4];
                        lignes.Add(string.Join(",", new[] { j.ToString("yyyy-MM-dd"), kv.Key.ToString(inv) }
                            .Concat(b.Select(x => x.ToString("R", inv))).Concat(new[] { nom })));
                    }
                    Log($"{j:yyyy-MM-dd} exportee ({m.Count} minutes) : {jours} seance(s) jusqu'ici", StrategyLoggingLevel.Info);
                }
                File.WriteAllLines(fichier, lignes);
                Log($"Termine : {jours} seances avec des transactions, {vides} sans, cote agresseur connu pour "
                    + $"{(volTotal > 0 ? volCote / volTotal : 0):P1} du volume. Fichier : {fichier}. Envoie-le a Claude.", StrategyLoggingLevel.Info);
            }
            catch (Exception e) { Log($"ERREUR : {e.Message}", StrategyLoggingLevel.Error); }
            Stop();
        }

        protected override void OnStop() { }

        static TimeZoneInfo TrouverFuseau()
        {
            foreach (var id in new[] { "Eastern Standard Time", "America/New_York" })
                try { return TimeZoneInfo.FindSystemTimeZoneById(id); } catch { }
            throw new Exception("fuseau horaire de New York introuvable");
        }
    }
}
