using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using TradingPlatform.BusinessLayer;

namespace Bot3en1
{
    /// <summary>Exporte les transactions du NQ fournies par Rithmic (cote agresseur compris), regroupees par minute de
    /// 9 h 30 a 16 h (heure de New York), pour tester le filtre delta sur des mois qu'il n'a jamais vus
    /// (filtre_h1/README.md, version Rithmic). Ne passe aucun ordre. Un fichier par contrat :
    /// C:\Bot3en1\export\transactions_NQZ6.csv (jour,minute,o,h,l,c,v,achats,ventes,sans_cote,contrat).</summary>
    public class ExportTransactions : Strategy
    {
        [InputParameter("NQ : contrat a exporter (ex. NQZ6, puis NQU6, NQM6, NQH6...)", 10)] public Symbol SymboleNQ;
        [InputParameter("Premier jour (AAAA-MM-JJ), vide = 3 ans en arriere", 20)] public string Debut = "";
        [InputParameter("Dernier jour (AAAA-MM-JJ), vide = hier", 30)] public string Fin = "";
        [InputParameter("Seulement les jours ou ce contrat est l'echeance suivie (regle du calendrier)", 40)] public bool SeulementEcheance = true;
        [InputParameter("Dossier des donnees du bot", 50)] public string Dossier = @"C:\Bot3en1";

        public ExportTransactions() : base()
        {
            Name = "Export transactions NQ (test du filtre delta)";
            Description = "Exporte les transactions Rithmic du NQ par minute, avec le cote agresseur. Aucun ordre.";
        }

        protected override void OnRun()
        {
            try
            {
                if (SymboleNQ == null) throw new Exception("choisis le contrat NQ a exporter");
                var ny = TrouverFuseau();
                var inv = CultureInfo.InvariantCulture;
                var aujourdhui = TimeZoneInfo.ConvertTimeFromUtc(Core.Instance.TimeUtils.DateTimeUtcNow, ny).Date;
                var d0 = string.IsNullOrWhiteSpace(Debut) ? aujourdhui.AddYears(-3) : DateTime.ParseExact(Debut.Trim(), "yyyy-MM-dd", inv);
                var d1 = string.IsNullOrWhiteSpace(Fin) ? aujourdhui.AddDays(-1) : DateTime.ParseExact(Fin.Trim(), "yyyy-MM-dd", inv);
                string nom = (SymboleNQ.Name ?? "NQ").Replace("/", "").Replace(" ", "");
                string dossier = Path.Combine(Dossier, "export");
                Directory.CreateDirectory(dossier);
                string fichier = Path.Combine(dossier, $"transactions_{nom}.csv");
                var lignes = new List<string> { "jour,minute,o,h,l,c,v,achats,ventes,sans_cote,contrat" };
                int jours = 0, vides = 0;
                double volCote = 0, volTotal = 0;
                for (var j = d0.Date; j <= d1.Date; j = j.AddDays(1))
                {
                    if (Calendrier.JourFerme(j)) continue;
                    if (SeulementEcheance)
                    {
                        string c = Calendrier.Contrat(j), court = $"{c[0]}{c[^1]}";
                        if (!nom.ToUpperInvariant().EndsWith(court) && !nom.ToUpperInvariant().Contains(c)) continue;
                    }
                    var debutUtc = TimeZoneInfo.ConvertTimeToUtc(j.AddMinutes(570), ny);
                    var finUtc = TimeZoneInfo.ConvertTimeToUtc(j.AddMinutes(960), ny);
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
                        int k = tn.Hour * 60 + tn.Minute - 570;
                        if (tn.Date != j || k < 0 || k >= Moteur.N) continue;
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
                    if (jours % 20 == 0) Log($"{jours} seances exportees (derniere : {j:yyyy-MM-dd})", StrategyLoggingLevel.Info);
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
