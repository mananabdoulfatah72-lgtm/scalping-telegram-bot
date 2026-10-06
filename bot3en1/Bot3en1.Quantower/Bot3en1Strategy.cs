using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using TradingPlatform.BusinessLayer;

namespace Bot3en1
{
    /// <summary>Bot 3 en 1 pour Quantower (compte Rithmic, par exemple DayTraders) : zone de bruit filtree par le vrai delta
    /// des 30 minutes + RSI(2), 1 MNQ par source. Les decisions viennent du moteur verifie (Bot3en1.Core, rejeu identique au
    /// robot Python) ; cette classe ne fait que lire le marche, appeler le moteur et aligner la position sur MNQ.
    /// A tester d'abord sur un compte de simulation (voir GUIDE.md).</summary>
    public class Bot3en1Strategy : Strategy
    {
        [InputParameter("Compte", 10)] public Account Compte;
        [InputParameter("NQ (barres et delta), contrat du moment, ex. NQZ6", 20)] public Symbol SymboleNQ;
        [InputParameter("MNQ (ordres), meme echeance, ex. MNQZ6", 30)] public Symbol SymboleMNQ;
        [InputParameter("Dossier des donnees du bot", 40)] public string Dossier = @"C:\Bot3en1";
        [InputParameter("MNQ par source", 50, 1, 5, 1, 0)] public int Taille = 1;
        [InputParameter("Plafond de gain du jour en $ (0 = aucun)", 60, 0, 5000, 50, 0)] public double PlafondJour = 0;
        [InputParameter("Telegram : jeton du bot (facultatif)", 70)] public string JetonTelegram = "";
        [InputParameter("Telegram : numero de conversation (facultatif)", 80)] public string ChatTelegram = "";
        [InputParameter("Historique : adresse des barres du robot", 90)]
        public string AdresseHistorique = "https://raw.githubusercontent.com/mananabdoulfatah72-lgtm/scalping-telegram-bot/main/zone/robot/nq_1min.csv.gz";

        Moteur bot;
        TimeZoneInfo ny;
        Timer horloge;
        readonly object verrou = new object();
        DateTime jour;
        int derniereMinute, prochaineMinute;
        readonly Barre[] barres = new Barre[Moteur.N];
        bool decisionRsiFaite, seanceFinie;
        DateTime ordreEnAttenteDepuis = DateTime.MinValue;
        DateTime dernierTick = DateTime.MinValue;
        bool alerteSilence;
        static readonly HttpClient http = new HttpClient { Timeout = TimeSpan.FromSeconds(20) };

        public Bot3en1Strategy() : base()
        {
            Name = "Bot 3 en 1 (zone + delta + RSI2)";
            Description = "Zone de bruit filtree par le vrai delta 30 min + RSI(2) sur MNQ, 1 MNQ par source.";
        }

        // ------------------------------------------------------------------ demarrage et arret
        protected override void OnRun()
        {
            try
            {
                if (Compte == null || SymboleNQ == null || SymboleMNQ == null)
                    throw new Exception("choisis le compte, le symbole NQ et le symbole MNQ dans les reglages");
                ny = TrouverFuseau();
                Directory.CreateDirectory(Dossier);
                var maintenant = HeureNY();
                jour = maintenant.Date;
                VerifierEcheance();
                PreparerMoteur();
                DemarrerSeance(maintenant);
                SymboleNQ.NewLast += SurTransaction;
                horloge = new Timer(_ => Tic(), null, 500, 500);
                Dire($"demarre le {jour:yyyy-MM-dd} a {maintenant:HH:mm} (New York). {EtatTexte()}");
            }
            catch (Exception e)
            {
                Dire($"ERREUR au demarrage : {e.Message}", true);
                Stop();
            }
        }

        protected override void OnStop()
        {
            horloge?.Dispose();
            if (SymboleNQ != null) SymboleNQ.NewLast -= SurTransaction;
            SauverEtat();
            Dire("arrete. Les positions ouvertes restent ouvertes (le RSI(2) peut tenir la nuit).");
        }

        static TimeZoneInfo TrouverFuseau()
        {
            foreach (var id in new[] { "Eastern Standard Time", "America/New_York" })
                try { return TimeZoneInfo.FindSystemTimeZoneById(id); } catch { }
            throw new Exception("fuseau horaire de New York introuvable");
        }

        static DateTime Maintenant() => Core.Instance.TimeUtils.DateTimeUtcNow;     // heure du serveur (UTC)
        DateTime HeureNY() => TimeZoneInfo.ConvertTimeFromUtc(Maintenant(), ny);

        void VerifierEcheance()
        {
            string attendu = Calendrier.Contrat(jour);                  // ex. "Z26"
            string court = $"{attendu[0]}{attendu[^1]}";                // ex. "Z6"
            foreach (var s in new[] { SymboleNQ, SymboleMNQ })
                if (!(s.Name ?? "").ToUpperInvariant().Contains(court) && !(s.Name ?? "").ToUpperInvariant().Contains(attendu))
                    Dire($"ATTENTION : le symbole {s.Name} ne semble pas etre l'echeance du jour ({court}). Change-le dans les reglages.", true);
        }

        /// <summary>Historique : barres d'une minute du robot (GitHub), rejouees dans le moteur jusqu'a hier. Position du RSI(2) :
        /// celle enregistree par le bot (etat.json).</summary>
        void PreparerMoteur()
        {
            string local = Path.Combine(Dossier, "nq_1min.csv.gz");
            try
            {
                var octets = http.GetByteArrayAsync(AdresseHistorique).GetAwaiter().GetResult();
                File.WriteAllBytes(local, octets);
            }
            catch (Exception e)
            {
                if (!File.Exists(local)) throw new Exception($"historique impossible a telecharger ({e.Message}) et aucune copie locale");
                Dire($"historique non telecharge ({e.Message}) : copie locale utilisee");
            }
            var seances = Rejoueur.LireMinutes(Rejoueur.Lignes(local), jour.AddDays(-1), contratCalendrier: true);
            if (seances.Count < 260) throw new Exception($"historique trop court ({seances.Count} seances)");
            var derniere = seances.Keys.Last();
            if (Calendrier.SeanceSuivante(derniere) < jour)
                Dire($"ATTENTION : l'historique s'arrete le {derniere:yyyy-MM-dd} (robot en retard ?). La zone utilise des parametres un peu anciens.", true);
            bot = Rejoueur.Preparer(seances, jour);
            bot.Taille = Math.Max(1, Taille);
            bot.PlafondJour = PlafondJour;
            bot.ContratSuivant = (j, c) => Calendrier.Contrat(Calendrier.SeanceSuivante(j));
            var etat = LireEtat();
            if (etat != null && etat.RsiTenu) bot.RestaurerRsi(true, etat.EntreeRsi);
        }

        void DemarrerSeance(DateTime maintenant)
        {
            derniereMinute = Calendrier.JourCourt(jour) ? (Calendrier.Ferie(jour) ? 209 : 224) : Moteur.N - 1;
            if (Calendrier.JourFerme(jour)) { seanceFinie = true; return; }
            for (int i = 0; i < Moteur.N; i++) barres[i] = new Barre();
            bot.DebutSeance(jour, Calendrier.Contrat(jour), derniereMinute);
            decisionRsiFaite = seanceFinie = false;
            prochaineMinute = 0;
            int m = Minute(maintenant);
            if (m > 0)
            {
                // demarrage apres 9 h 30 : barres et delta deja passes rejoues sans ordre ; aucune entree de zone au milieu d'un trade
                Rattraper(Math.Min(m, derniereMinute + 1));
                bot.OublierZoneTenue();
                Dire($"demarrage en cours de seance : la zone ne prendra que les nouveaux signaux apres {maintenant:HH:mm}");
            }
        }

        static int Minute(DateTime ny) => ny.Hour * 60 + ny.Minute - 570;

        /// <summary>Barres d'une minute et transactions (cote agresseur) de la seance, de 9 h 30 a la minute `jusqua` exclue.</summary>
        void Rattraper(int jusqua)
        {
            if (jusqua <= 0) return;
            var debutUtc = TimeZoneInfo.ConvertTimeToUtc(jour.AddMinutes(570), ny);
            var finUtc = TimeZoneInfo.ConvertTimeToUtc(jour.AddMinutes(570 + jusqua), ny);
            try
            {
                var ticks = SymboleNQ.GetHistory(new HistoryRequestParameters
                {
                    Symbol = SymboleNQ, FromTime = debutUtc, ToTime = finUtc,
                    Aggregation = new HistoryAggregationTick(HistoryType.Last)   // Quantower 1.146 : le type d'historique est dans l'agregation
                });
                for (int i = 0; i < ticks.Count; i++)
                    if (ticks[i, SeekOriginHistory.Begin] is HistoryItemLast t)
                        Ajouter(TimeZoneInfo.ConvertTimeFromUtc(t.TimeLeft, ny), t.Price, t.Volume, t.AggressorFlag);
            }
            catch (Exception e) { Dire($"rattrapage des transactions impossible ({e.Message}) : la zone est coupee pour aujourd'hui", true); bot.ZoneAutorisee = false; }
            for (int m = 0; m < jusqua; m++) FermerMinute(m, executer: false);
            prochaineMinute = jusqua;
        }

        // ------------------------------------------------------------------ marche
        void SurTransaction(Symbol s, Last last)
        {
            var t = TimeZoneInfo.ConvertTimeFromUtc(last.Time, ny);
            lock (verrou)
            {
                dernierTick = Maintenant();
                if (t.Date == jour) Ajouter(t, last.Price, last.Size, last.AggressorFlag);
            }
        }

        void Ajouter(DateTime t, double prix, double taille, AggressorFlag cote)
        {
            int m = Minute(t);
            if (m < 0 || m >= Moteur.N || m < prochaineMinute) return;
            var b = barres[m];
            if (!b.Presente) { b.O = b.H = b.L = prix; b.Presente = true; }
            b.H = Math.Max(b.H, prix); b.L = Math.Min(b.L, prix); b.C = prix; b.V += taille;
            if (cote == AggressorFlag.Buy) b.Achats += taille;
            else if (cote == AggressorFlag.Sell) b.Ventes += taille;
        }

        void Tic()
        {
            try
            {
                lock (verrou)
                {
                    var maintenant = HeureNY();
                    if (maintenant.Date != jour)
                    {
                        jour = maintenant.Date;
                        VerifierEcheance();
                        DemarrerSeance(maintenant);
                    }
                    if (seanceFinie) return;
                    if (File.Exists(Path.Combine(Dossier, "STOP"))) { ToutFermer("fichier STOP present"); return; }
                    int m = Minute(maintenant);
                    // une minute est fermee quand l'horloge a passe la minute suivante (+2 s pour les dernieres transactions)
                    while (prochaineMinute <= derniereMinute && maintenant >= jour.AddMinutes(570 + prochaineMinute + 1).AddSeconds(2))
                    {
                        FermerMinute(prochaineMinute, executer: true);
                        prochaineMinute++;
                    }
                    if (prochaineMinute > derniereMinute) FinDeSeance();
                    if (m >= 0 && m <= derniereMinute && dernierTick != DateTime.MinValue && (Maintenant() - dernierTick).TotalMinutes > 3 && !alerteSilence)
                    {
                        alerteSilence = true;
                        Dire("ALERTE : plus aucune transaction NQ recue depuis 3 minutes (connexion Rithmic ?)", true);
                    }
                    if ((Maintenant() - dernierTick).TotalMinutes < 1) alerteSilence = false;
                    Aligner();
                }
            }
            catch (Exception e) { Dire($"ERREUR : {e.Message}", true); }
        }

        void FermerMinute(int m, bool executer)
        {
            foreach (var s in bot.MinuteFermee(m, barres[m]))
                if (executer) Dire(s.Texte);
            // decision du RSI(2) a l'ouverture de sa minute (15 h 50), des que la minute d'avant est fermee
            if (m == bot.MinuteDecisionRsi - 1 && !decisionRsiFaite)
            {
                decisionRsiFaite = true;
                foreach (var s in bot.DecisionRsi(barres[m].C)) if (executer) Dire(s.Texte);
                if (executer) SauverEtat();
            }
        }

        void FinDeSeance()
        {
            if (seanceFinie) return;
            seanceFinie = true;
            bot.FinSeance();
            SauverEtat();
            Dire($"seance du {jour:yyyy-MM-dd} terminee. {EtatTexte()}");
        }

        // ------------------------------------------------------------------ ordres
        int PositionReelle()
        {
            int q = 0;
            foreach (var p in Core.Instance.Positions)
                if (p.Account == Compte && p.Symbol == SymboleMNQ)
                    q += (p.Side == Side.Buy ? 1 : -1) * (int)Math.Round(p.Quantity);
            return q;
        }

        void Aligner()
        {
            if (bot == null) return;
            if ((Maintenant() - ordreEnAttenteDepuis).TotalSeconds < 15) return;     // laisser le temps a l'ordre precedent
            int voulu = bot.PositionNette, reel = PositionReelle(), ecart = voulu - reel;
            if (ecart == 0) return;
            var r = Core.Instance.PlaceOrder(new PlaceOrderRequestParameters
            {
                Account = Compte, Symbol = SymboleMNQ, Side = ecart > 0 ? Side.Buy : Side.Sell,
                Quantity = Math.Abs(ecart), OrderTypeId = OrderType.Market
            });
            ordreEnAttenteDepuis = Maintenant();
            if (r.Status == TradingOperationResultStatus.Failure)
                Dire($"ERREUR d'ordre ({(ecart > 0 ? "achat" : "vente")} {Math.Abs(ecart)} MNQ) : {r.Message}", true);
            else
                Dire($"ordre envoye : {(ecart > 0 ? "achat" : "vente")} {Math.Abs(ecart)} MNQ (position {reel} -> {voulu})");
        }

        void ToutFermer(string raison)
        {
            int reel = PositionReelle();
            if (reel != 0 && (Maintenant() - ordreEnAttenteDepuis).TotalSeconds >= 15)
            {
                Core.Instance.PlaceOrder(new PlaceOrderRequestParameters
                {
                    Account = Compte, Symbol = SymboleMNQ, Side = reel > 0 ? Side.Sell : Side.Buy,
                    Quantity = Math.Abs(reel), OrderTypeId = OrderType.Market
                });
                ordreEnAttenteDepuis = Maintenant();
                Dire($"tout ferme : {raison}", true);
            }
        }

        // ------------------------------------------------------------------ etat et messages
        class Etat { public string Jour { get; set; } public bool RsiTenu { get; set; } public double EntreeRsi { get; set; } }

        Etat LireEtat()
        {
            var f = Path.Combine(Dossier, "etat.json");
            try { return File.Exists(f) ? JsonSerializer.Deserialize<Etat>(File.ReadAllText(f)) : null; } catch { return null; }
        }

        void SauverEtat()
        {
            if (bot == null) return;
            var e = new Etat { Jour = jour.ToString("yyyy-MM-dd"), RsiTenu = bot.Rsi == 1, EntreeRsi = bot.EntreeRsi };
            File.WriteAllText(Path.Combine(Dossier, "etat.json"), JsonSerializer.Serialize(e));
        }

        string EtatTexte() => bot == null ? "" :
            $"Position voulue {bot.PositionNette} MNQ (zone {bot.ZoneTenue}, RSI(2) {bot.Rsi}){(bot.Rsi == 1 ? $", RSI(2) achete a {bot.EntreeRsi:F2}" : "")}" +
            $"{(bot.ZoneActive ? "" : " ; zone inactive aujourd'hui")}";

        void Dire(string texte, bool erreur = false)
        {
            Log(texte, erreur ? StrategyLoggingLevel.Error : StrategyLoggingLevel.Info);
            try { File.AppendAllText(Path.Combine(Dossier, "journal.txt"), $"{Maintenant():yyyy-MM-dd HH:mm:ss} UTC {texte}{Environment.NewLine}"); } catch { }
            if (string.IsNullOrWhiteSpace(JetonTelegram) || string.IsNullOrWhiteSpace(ChatTelegram)) return;
            try
            {
                var contenu = new FormUrlEncodedContent(new Dictionary<string, string> { ["chat_id"] = ChatTelegram, ["text"] = "Bot 3 en 1 : " + texte });
                http.PostAsync($"https://api.telegram.org/bot{JetonTelegram}/sendMessage", contenu);
            }
            catch { }
        }
    }
}
