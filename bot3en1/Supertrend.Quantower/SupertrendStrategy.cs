using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using Bot3en1;
using TradingPlatform.BusinessLayer;

namespace SupertrendNQ
{
    /// <summary>Supertrend NQ pour Quantower (compte Rithmic, Bulenox par exemple). Les decisions viennent du moteur verifie
    /// (Supertrend.Core, rejeu identique au test sur 15 ans : 9 628 trades) ; cette classe lit le marche (transactions du NQ),
    /// construit les minutes, appelle le moteur et aligne la position sur MNQ. Elle ajoute ce que le compte exige : limite de
    /// perte du jour, objectif du challenge, a plat avant la fin de la journee, fichier STOP, reprise apres une relance,
    /// position fermee a la main jamais rouverte, messages Telegram.</summary>
    public class SupertrendStrategy : Strategy
    {
        [InputParameter("Compte", 10)] public Account Compte;
        [InputParameter("NQ (prix et barres), contrat du moment, ex. NQZ6", 20)] public Symbol SymboleNQ;
        [InputParameter("MNQ (ordres), meme echeance, ex. MNQZ6", 30)] public Symbol SymboleMNQ;
        [InputParameter("MNQ par trade", 40, 1, 20, 1, 0)] public int Taille = 1;
        [InputParameter("Limite de perte du jour en $ (tout ferme, plus de trade jusqu'au lendemain ; 0 = aucune)", 50, 0, 100000, 50, 0)]
        public double LimiteJour = 500;
        [InputParameter("Objectif : solde du compte a atteindre (tout ferme a l'objectif + 50 $, plus aucun trade ensuite ; 0 = aucun)", 55, 0, 10000000, 100, 0)]
        public double Objectif = 0;
        [InputParameter("Supertrend : ATR sur combien de barres de 5 min (teste : 10)", 60, 2, 100, 1, 0)] public int Periode = 10;
        [InputParameter("Supertrend : multiple de l'ATR (teste : 3)", 61, 0.5, 10, 0.1, 1)] public double Multiple = 3;
        [InputParameter("Dossier des donnees de la strategie", 70)] public string Dossier = @"C:\SupertrendNQ";
        [InputParameter("Telegram : jeton du bot (facultatif)", 75)] public string JetonTelegram = "";
        [InputParameter("Telegram : numero de conversation (facultatif)", 80)] public string ChatTelegram = "";
        [InputParameter("Historique : adresse des barres du robot", 90)]
        public string AdresseHistorique = "https://raw.githubusercontent.com/mananabdoulfatah72-lgtm/scalping-telegram-bot/main/zone/robot/nq_1min.csv.gz";

        const string Version = "2 novembre 2026 (Supertrend 10-3 sur barres de 5 min, regle du test sur 15 ans)";
        const int N = MoteurST.N;

        readonly object verrou = new object();
        static readonly HttpClient http = new HttpClient { Timeout = TimeSpan.FromSeconds(20) };
        MoteurST bot;
        TimeZoneInfo ny;
        Timer horloge;
        DateTime jour, demarrageUtc, dernierTick = DateTime.MinValue, ordreEnAttenteDepuis = DateTime.MinValue;
        DateTime repriseAttendueJusqua = DateTime.MinValue, zeroVuDepuis = DateTime.MinValue, limiteVueDepuis = DateTime.MinValue;
        DateTime alerteAveugle = DateTime.MinValue;
        BarreMin[] barres = new BarreMin[N];
        int prochaineMinute, derniereMinute = N - 1, dernierMNQ, tradesDuJour;
        double dernierPrix, realiseHors;                 // realiseHors : sorties forcees (limite, main, objectif), en $
        bool seanceFinie, arretJour, objectifAtteint, alerteSilence, premierPrix, erreurHeure, soldeIllisibleNote, resumeEnvoye;
        string objectifCle = "", derniereErreurTelegram = "";

        public SupertrendStrategy() : base()
        {
            Name = "Supertrend NQ (10-3, 5 min)";
            Description = "Supertrend 10-3 sur les barres de 5 minutes du NQ, ordres sur MNQ, a plat a 15 h 55 (New York).";
        }

        // ------------------------------------------------------------------ demarrage et arret
        protected override void OnRun()
        {
            try
            {
                if (Compte == null || SymboleNQ == null || SymboleMNQ == null)
                    throw new Exception("choisis le compte, le symbole NQ et le symbole MNQ dans les reglages");
                if (Taille < 1) throw new Exception("MNQ par trade : au moins 1");
                ny = TrouverFuseau();
                Directory.CreateDirectory(Dossier);
                ReprendreObjetsVivants(false);
                var maintenant = HeureNY();
                jour = maintenant.Date;
                demarrageUtc = Maintenant();
                VerifierEcheance();
                PreparerMoteur();
                LireEtat();
                DemarrerSeance(maintenant);
                SymboleNQ.NewLast += SurTransaction;
                horloge = new Timer(_ => Tic(), null, 500, 500);
                Dire($"demarre le {jour:yyyy-MM-dd} a {maintenant:HH:mm} (New York), version du {Version} ; {Taille} MNQ par trade,"
                     + $" limite du jour {(LimiteJour > 0 ? $"{LimiteJour:F0} $" : "AUCUNE")}, objectif {(Objectif > 0 ? $"{Objectif:F0} $" : "aucun")},"
                     + $" Supertrend {Periode}-{Multiple.ToString("0.#", CultureInfo.InvariantCulture)}"
                     + (Periode != 10 || Math.Abs(Multiple - 3) > 1e-9 ? " (ATTENTION : seul le 10-3 a ete teste)" : "")
                     + $". {EtatTexte()}");
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
            if (Compte != null && SymboleMNQ != null && bot != null)
            {
                try { lock (verrou) { ordreEnAttenteDepuis = DateTime.MinValue; ToutFermer("arret de la strategie : position fermee"); } }
                catch (Exception e) { Dire($"ERREUR en fermant la position a l'arret : {e.Message}", true); }
                SauverEtat();
            }
            Dire("arretee. Rien ne reste ouvert sur MNQ.");
        }

        static TimeZoneInfo TrouverFuseau()
        {
            foreach (var id in new[] { "Eastern Standard Time", "America/New_York" })
                try { return TimeZoneInfo.FindSystemTimeZoneById(id); } catch { }
            throw new Exception("fuseau horaire de New York introuvable");
        }

        static DateTime Maintenant() => Core.Instance.TimeUtils.DateTimeUtcNow;
        DateTime HeureNY() => TimeZoneInfo.ConvertTimeFromUtc(Maintenant(), ny);
        static int Minute(DateTime t) => t.Hour * 60 + t.Minute - 570;
        static DateTime EnUtc(DateTime d) => d.Kind == DateTimeKind.Local ? d.ToUniversalTime()
            : d.Kind == DateTimeKind.Unspecified ? DateTime.SpecifyKind(d, DateTimeKind.Utc) : d;

        void VerifierEcheance()
        {
            string attendu = Calendrier.Contrat(jour), court = $"{attendu[0]}{attendu[^1]}";
            foreach (var s in new[] { SymboleNQ, SymboleMNQ })
                if (!(s.Name ?? "").ToUpperInvariant().Contains(court) && !(s.Name ?? "").ToUpperInvariant().Contains(attendu))
                    Dire($"ATTENTION : le symbole {s.Name} ne semble pas etre l'echeance du jour ({court}). Change-le dans les reglages.", true);
        }

        /// <summary>Indicateur continu : les barres du robot (GitHub) sont rejouees jusqu'a hier ; s'il ne repond pas, la copie
        /// locale sert.</summary>
        void PreparerMoteur()
        {
            string local = Path.Combine(Dossier, "nq_1min.csv.gz");
            try { File.WriteAllBytes(local, http.GetByteArrayAsync(AdresseHistorique).GetAwaiter().GetResult()); }
            catch (Exception e)
            {
                if (!File.Exists(local)) throw new Exception($"historique impossible a telecharger ({e.Message}) et aucune copie locale");
                Dire($"historique non telecharge ({e.Message}) : copie locale utilisee");
            }
            var jours = Rejeu.LireJours(Rejeu.Lignes(local), jour.AddDays(-1));
            if (jours.Count < 5) throw new Exception($"historique trop court ({jours.Count} seances)");
            bot = new MoteurST { Periode = Math.Max(2, Periode), Multiple = Multiple };
            Rejeu.Jouer(bot, jours);
            bot.Trades.Clear();
            var derniere = jours.Keys.Last();
            if (Calendrier.SeanceSuivante(derniere) < jour)
                Dire($"ATTENTION : l'historique s'arrete le {derniere:yyyy-MM-dd} (robot en retard ?) : le Supertrend part d'un etat un peu ancien.", true);
        }

        // ------------------------------------------------------------------ seance
        void DemarrerSeance(DateTime maintenant)
        {
            seanceFinie = false; resumeEnvoye = false; tradesDuJour = 0; prochaineMinute = 0;
            for (int i = 0; i < N; i++) barres[i] = new BarreMin();
            string js = jour.ToString("yyyy-MM-dd");
            if (etatLu == null || etatLu.Jour != js) { realiseHors = 0; arretJour = false; }
            bool court = Calendrier.JourCourt(jour), ferme = Calendrier.JourFerme(jour);
            derniereMinute = court ? (Calendrier.Ferie(jour) ? 209 : 224) : N - 1;
            if (ferme) { seanceFinie = true; return; }
            bot.DebutSeance(jour, !court && !arretJour && !objectifAtteint);
            if (court) Dire("seance courte aujourd'hui : pas de trade (le test ne joue que les seances completes)");
            repriseAttendueJusqua = DateTime.MinValue; zeroVuDepuis = DateTime.MinValue;
            int m = Minute(maintenant);
            if (m > 0)
            {
                // lancement apres 9 h 30 : minutes deja passees rejouees sans ordre
                Rattraper(Math.Min(m, derniereMinute + 1));
                int voulue = bot.Position * Taille, compte = PositionReelle(SymboleMNQ);
                if (bot.Position != 0 && compte == voulue)
                    Dire($"lancement en cours de seance : la position du Supertrend ({Sens(bot.Position)} {compte} MNQ, entree a {bot.Entree:F2}) est deja sur le compte : elle est reprise");
                else if (bot.Position != 0 && compte == 0)
                {
                    repriseAttendueJusqua = Maintenant().AddSeconds(60);
                    Dire($"lancement en cours de seance : le Supertrend est {(bot.Position > 0 ? "haussier" : "baissier")} ; si le compte ne montre pas"
                         + " cette position dans 60 s, pas d'entree au milieu de la tendance : prochaine position au prochain retournement");
                }
                else if (bot.Position == 0)
                    Dire("lancement en cours de seance : aucune position voulue pour l'instant");
                dernierMNQ = compte;
            }
        }

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
                    Aggregation = new HistoryAggregationTick(HistoryType.Last)
                });
                for (int i = 0; i < ticks.Count; i++)
                    if (ticks[i, SeekOriginHistory.Begin] is HistoryItemLast t)
                        Ajouter(TimeZoneInfo.ConvertTimeFromUtc(EnUtc(t.TimeLeft), ny), t.Price);
            }
            catch (Exception e)
            {
                Dire($"rattrapage des minutes impossible ({e.Message}) : pas de trade aujourd'hui (le Supertrend serait faux)", true);
                bot.Arreter();
            }
            double avant = bot.RealiseJour;
            for (int m = 0; m < jusqua; m++) FermerMinute(m, false);
            realiseHors -= (bot.RealiseJour - avant) * Taille;      // trades rejoues sans ordre : pas dans le resultat du jour
            prochaineMinute = jusqua;
        }

        void SurTransaction(Symbol s, Last last)
        {
            lock (verrou)
            {
                if (dernierTick == DateTime.MinValue) premierPrix = true;
                dernierTick = Maintenant();
                dernierPrix = last.Price;
                DateTime t;
                try { t = TimeZoneInfo.ConvertTimeFromUtc(EnUtc(last.Time), ny); }
                catch (Exception e)
                {
                    if (!erreurHeure) { erreurHeure = true; Dire($"ERREUR : heure d'une transaction NQ illisible ({e.Message})", true); }
                    return;
                }
                if (t.Date == jour) Ajouter(t, last.Price);
            }
        }

        void Ajouter(DateTime t, double prix)
        {
            int m = Minute(t);
            if (m < 0 || m >= N || m < prochaineMinute) return;
            var b = barres[m];
            if (!b.Presente) { b.O = b.H = b.L = prix; b.Presente = true; }
            b.H = Math.Max(b.H, prix); b.L = Math.Min(b.L, prix); b.C = prix;
        }

        void FermerMinute(int m, bool executer)
        {
            var signaux = bot.MinuteFermee(m, barres[m]);
            if (!executer) return;
            foreach (var x in signaux)
            {
                Dire(x.Texte);
                if (x.Texte.StartsWith("achat") || x.Texte.StartsWith("vente")) tradesDuJour++;
            }
            if (signaux.Count > 0) SauverEtat();
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
                        SauverEtat();
                    }
                    if (premierPrix) { premierPrix = false; Dire($"flux NQ recu ({dernierPrix:F2}) : la strategie voit le marche"); }
                    if (File.Exists(Path.Combine(Dossier, "STOP")))
                    {
                        if (bot != null && bot.Position != 0) { realiseHors += Latent(); bot.Abandonner(); SauverEtat(); }
                        ToutFermer("fichier STOP present : position fermee ; apres le retrait du fichier, prochaine position au prochain retournement");
                        return;
                    }
                    int m = Minute(maintenant);
                    if (!seanceFinie)
                    {
                        while (prochaineMinute <= derniereMinute && maintenant >= jour.AddMinutes(570 + prochaineMinute + 1).AddSeconds(2))
                        {
                            FermerMinute(prochaineMinute, true);
                            prochaineMinute++;
                        }
                        if (prochaineMinute > derniereMinute) FinDeSeance();
                        Surveiller(m, maintenant);
                    }
                    Risques(maintenant);
                    // filet : rien d'ouvert apres 15 h 56 (New York), quoi que pense le moteur (la firme exige d'etre a plat)
                    if (maintenant.TimeOfDay >= TimeSpan.FromMinutes(15 * 60 + 56) && maintenant.TimeOfDay < TimeSpan.FromHours(18))
                    {
                        if (PositionReelle(SymboleMNQ) != 0) ToutFermer("filet de fin de seance : position encore ouverte apres 15 h 56");
                        return;
                    }
                    Aligner();
                }
            }
            catch (Exception e) { Dire($"ERREUR : {e.Message}", true); }
        }

        void FinDeSeance()
        {
            seanceFinie = true;
            for (int m = derniereMinute + 1; m < N; m++) bot.MinuteFermee(m, new BarreMin());   // seance courte : comme le test
            if (!resumeEnvoye)
            {
                resumeEnvoye = true;
                double total = bot.RealiseJour * Taille + realiseHors;
                Dire($"fin de seance : {tradesDuJour} entree(s), resultat estime {total:+0;-0} $ ({Taille} MNQ, frais compris)");
                SauverEtat();
            }
        }

        void Surveiller(int m, DateTime maintenant)
        {
            if (m >= 0 && m <= derniereMinute && dernierTick != DateTime.MinValue && (Maintenant() - dernierTick).TotalMinutes > 3 && !alerteSilence)
            {
                alerteSilence = true;
                Dire("ALERTE : plus aucune transaction NQ recue depuis 3 minutes (connexion Rithmic ?)", true);
                ReprendreObjetsVivants(true);
            }
            if (alerteSilence && (Maintenant() - dernierTick).TotalMinutes < 1) { alerteSilence = false; Dire($"flux NQ revenu ({dernierPrix:F2})"); }
            if (dernierTick == DateTime.MinValue && m >= 0 && m <= derniereMinute)
            {
                var ouverture = TimeZoneInfo.ConvertTimeToUtc(jour.AddMinutes(570), ny);
                var depuis = ouverture > demarrageUtc ? ouverture : demarrageUtc;
                if ((Maintenant() - depuis).TotalMinutes > 3 && (Maintenant() - alerteAveugle).TotalMinutes >= 15)
                {
                    alerteAveugle = Maintenant();
                    Dire("ALERTE : aucune transaction NQ recue depuis le lancement : la strategie ne voit pas le marche. Verifie la connexion"
                         + " Rithmic et le symbole NQ des reglages, puis relance-la.", true);
                    ReprendreObjetsVivants(true);
                }
            }
        }

        // ------------------------------------------------------------------ risques du compte
        double Latent()
        {
            if (bot == null || bot.Position == 0 || double.IsNaN(bot.Entree) || dernierPrix <= 0) return 0;
            return Taille * (2 * bot.Position * (dernierPrix - bot.Entree) - 3.0);
        }

        void Risques(DateTime maintenant)
        {
            if (bot == null) return;
            // limite de perte du jour : resultat realise + latent, confirme 3 s (un prix aberrant ne declenche rien)
            double valeur = bot.RealiseJour * Taille + realiseHors + Latent();
            if (LimiteJour > 0 && !arretJour && valeur <= -LimiteJour)
            {
                if (limiteVueDepuis == DateTime.MinValue) limiteVueDepuis = Maintenant();
                else if ((Maintenant() - limiteVueDepuis).TotalSeconds >= 3)
                {
                    realiseHors += Latent();
                    arretJour = true;
                    bot.Arreter();
                    ordreEnAttenteDepuis = DateTime.MinValue;
                    ToutFermer($"limite de perte du jour atteinte ({valeur:F0} $ pour une limite de {LimiteJour:F0} $) : tout est ferme, plus de trade aujourd'hui", true);
                    SauverEtat();
                }
            }
            else limiteVueDepuis = DateTime.MinValue;
            // objectif du challenge : solde du compte + latent
            if (Objectif > 0 && !objectifAtteint)
            {
                double? solde = SoldeReel();
                if (!solde.HasValue)
                {
                    if (!soldeIllisibleNote) { soldeIllisibleNote = true; Dire("ATTENTION : solde du compte illisible : l'arret a l'objectif ne peut pas marcher. Verifie la connexion Rithmic.", true); }
                }
                else if (solde.Value + Latent() >= Objectif + 50)
                {
                    double compteVu = solde.Value + Latent();
                    realiseHors += Latent();
                    objectifAtteint = true;
                    bot.Arreter();
                    ordreEnAttenteDepuis = DateTime.MinValue;
                    ToutFermer($"OBJECTIF ATTEINT : compte a {compteVu:F0} $ (objectif {Objectif:F0} $) : tout est ferme, plus aucun trade", true);
                    SauverEtat();
                }
            }
        }

        // ------------------------------------------------------------------ ordres
        int PositionReelle(Symbol symbole)
        {
            int q = 0;
            foreach (var p in Core.Instance.Positions)
                if (p.Account == Compte && p.Symbol == symbole)
                    q += (p.Side == Side.Buy ? 1 : -1) * (int)Math.Round(p.Quantity);
            return q;
        }

        void Aligner()
        {
            if (bot == null) return;
            int voulu = bot.Position * Taille, reel = PositionReelle(SymboleMNQ);
            if (voulu != 0 && reel == voulu) dernierMNQ = reel;
            if (repriseAttendueJusqua != DateTime.MinValue)
            {
                if (voulu != 0 && reel == voulu) { repriseAttendueJusqua = DateTime.MinValue; Dire($"position lue sur le compte ({reel} MNQ) : elle est reprise"); }
                else if (voulu != 0 && reel == 0 && Maintenant() < repriseAttendueJusqua) return;
                else
                {
                    repriseAttendueJusqua = DateTime.MinValue;
                    if (voulu != 0 && reel == 0)
                    {
                        bot.Abandonner();
                        Dire("pas de position sur le compte apres 60 s : pas d'entree au milieu de la tendance, prochaine position au prochain retournement");
                        return;
                    }
                }
            }
            if ((Maintenant() - ordreEnAttenteDepuis).TotalSeconds < 15) return;     // laisser le temps a l'ordre precedent
            // position voulue en place puis revenue a zero sans ordre de la strategie : fermee a la main (ou par le courtier).
            // Retenue seulement si elle reste a zero 30 s alors que des transactions arrivent (une coupure vide aussi la liste).
            if (reel == 0 && voulu != 0 && dernierMNQ == voulu)
            {
                if (zeroVuDepuis == DateTime.MinValue) { zeroVuDepuis = Maintenant(); return; }
                if ((Maintenant() - zeroVuDepuis).TotalSeconds < 30 || dernierTick <= zeroVuDepuis) return;
                realiseHors += Latent();
                bot.Abandonner();
                dernierMNQ = 0;
                zeroVuDepuis = DateTime.MinValue;
                SauverEtat();
                Dire($"position MNQ fermee hors de la strategie (vers {dernierPrix:F2}) : elle n'est pas rouverte ; prochaine position au prochain retournement du Supertrend", true);
                return;
            }
            zeroVuDepuis = DateTime.MinValue;
            if (reel != 0 || voulu == 0) dernierMNQ = reel;
            int ecart = voulu - reel;
            if (ecart == 0) return;
            Passer(ecart > 0 ? Side.Buy : Side.Sell, Math.Abs(ecart), reel, voulu);
        }

        void Passer(Side cote, int quantite, int avant, int apres)
        {
            var r = Core.Instance.PlaceOrder(new PlaceOrderRequestParameters
            {
                Account = Compte, Symbol = SymboleMNQ, Side = cote, Quantity = quantite, OrderTypeId = OrderType.Market
            });
            ordreEnAttenteDepuis = Maintenant();
            if (r.Status == TradingOperationResultStatus.Failure)
                Dire($"ERREUR d'ordre ({(cote == Side.Buy ? "achat" : "vente")} {quantite} MNQ) : {r.Message}", true);
            else
                Dire($"ordre envoye : {(cote == Side.Buy ? "achat" : "vente")} {quantite} MNQ (position {avant} -> {apres})");
        }

        /// <summary>Ferme la position MNQ (si aucun ordre n'est parti dans les 15 s). `annoncer` : la raison est ecrite meme sans
        /// position (evenement unique : limite du jour, objectif) ; sinon seulement quand un ordre part.</summary>
        void ToutFermer(string raison, bool annoncer = false)
        {
            int reel = PositionReelle(SymboleMNQ);
            bool ordre = reel != 0 && (Maintenant() - ordreEnAttenteDepuis).TotalSeconds >= 15;
            if (ordre) Passer(reel > 0 ? Side.Sell : Side.Buy, Math.Abs(reel), reel, 0);
            if (ordre || annoncer) Dire(raison, true);
            dernierMNQ = 0;
        }

        // ------------------------------------------------------------------ compte
        static double? LireDouble(object o, string propriete)
        {
            try
            {
                var v = o?.GetType().GetProperty(propriete)?.GetValue(o);
                return v switch { double d => d, float f => f, decimal m => (double)m, int i => i, long l => l, _ => (double?)null };
            }
            catch { return null; }
        }

        double? SoldeReel()
        {
            var b = LireDouble(Compte, "Balance");
            return b.HasValue && b.Value > 0 && !double.IsNaN(b.Value) ? b : null;
        }

        void ReprendreObjetsVivants(bool reabonner)
        {
            try
            {
                if (reabonner) SymboleNQ.NewLast -= SurTransaction;
                SymboleNQ = Vivant(SymboleNQ);
                SymboleMNQ = Vivant(SymboleMNQ);
                Compte = CompteVivant(Compte);
                if (reabonner) SymboleNQ.NewLast += SurTransaction;
            }
            catch (Exception e) { Dire($"ERREUR en reprenant les symboles ({e.Message})", true); }
        }

        static T Vivant<T>(T objet) where T : class
        {
            if (objet == null) return null;
            try
            {
                var info = objet.GetType().GetMethod("CreateInfo", Type.EmptyTypes)?.Invoke(objet, null);
                if (info == null) return objet;
                var core = Core.Instance;
                foreach (var m in core.GetType().GetMethods())
                {
                    if (m.Name != "GetSymbol") continue;
                    var ps = m.GetParameters();
                    if (ps.Length == 0 || !ps[0].ParameterType.IsInstanceOfType(info)) continue;
                    var args = new object[ps.Length];
                    args[0] = info;
                    for (int i = 1; i < ps.Length; i++)
                        args[i] = ps[i].HasDefaultValue ? ps[i].DefaultValue : ps[i].ParameterType.IsValueType ? Activator.CreateInstance(ps[i].ParameterType) : null;
                    if (m.Invoke(core, args) is T vivant) return vivant;
                }
            }
            catch { }
            return objet;
        }

        static Account CompteVivant(Account compte)
        {
            if (compte == null) return null;
            try
            {
                var id = compte.GetType().GetProperty("Id")?.GetValue(compte);
                if (Core.Instance.GetType().GetProperty("Accounts")?.GetValue(Core.Instance) is System.Collections.IEnumerable comptes && id != null)
                    foreach (var c in comptes)
                        if (c is Account a && Equals(a.GetType().GetProperty("Id")?.GetValue(a), id)) return a;
            }
            catch { }
            return compte;
        }

        // ------------------------------------------------------------------ etat (survit a une relance)
        public class Etat
        {
            public string Jour { get; set; }
            public double RealiseJour { get; set; }
            public double RealiseHors { get; set; }
            public bool ArretJour { get; set; }
            public string ObjectifCle { get; set; }
            public bool ObjectifAtteint { get; set; }
        }

        Etat etatLu;
        string FichierEtat() => Path.Combine(Dossier, "etat.json");

        void LireEtat()
        {
            try { etatLu = File.Exists(FichierEtat()) ? JsonSerializer.Deserialize<Etat>(File.ReadAllText(FichierEtat())) : null; } catch { etatLu = null; }
            objectifCle = $"{Compte?.Name}|{Objectif.ToString(CultureInfo.InvariantCulture)}";
            objectifAtteint = etatLu != null && etatLu.ObjectifAtteint && etatLu.ObjectifCle == objectifCle && Objectif > 0;
            if (etatLu != null && etatLu.Jour == jour.ToString("yyyy-MM-dd"))
            {
                arretJour = etatLu.ArretJour;
                realiseHors = etatLu.RealiseHors + etatLu.RealiseJour;      // trades deja faits aujourd'hui avant la relance
            }
            if (objectifAtteint) Dire("objectif deja atteint sur ce compte (etat.json) : la strategie ne tradera plus. Mets un autre objectif ou 0 pour un nouveau compte.");
            if (arretJour) Dire("limite du jour deja atteinte aujourd'hui (etat.json) : pas de trade avant demain");
        }

        void SauverEtat()
        {
            if (bot == null) return;
            try
            {
                var e = new Etat { Jour = jour.ToString("yyyy-MM-dd"), RealiseJour = bot.RealiseJour * Taille, RealiseHors = realiseHors,
                                   ArretJour = arretJour, ObjectifCle = objectifCle, ObjectifAtteint = objectifAtteint };
                File.WriteAllText(FichierEtat(), JsonSerializer.Serialize(e));
                etatLu = e;
            }
            catch { }
        }

        string EtatTexte() => bot == null ? "" :
            $"Supertrend {(bot.Sens > 0 ? "haussier" : bot.Sens < 0 ? "baissier" : "pas encore pret")}, ligne a {bot.Ligne:F2} ;"
            + $" position voulue {bot.Position * Taille} MNQ"
            + (arretJour ? " ; limite du jour atteinte, pas de trade aujourd'hui" : "")
            + (objectifAtteint ? " ; objectif atteint, plus aucun trade" : "");

        static string Sens(int s) => s > 0 ? "achat" : "vente";

        // ------------------------------------------------------------------ messages
        void Dire(string texte, bool erreur = false)
        {
            Log(texte, erreur ? StrategyLoggingLevel.Error : StrategyLoggingLevel.Info);
            try { File.AppendAllText(Path.Combine(Dossier, "journal.txt"), $"{Maintenant():yyyy-MM-dd HH:mm:ss} UTC {texte}{Environment.NewLine}"); } catch { }
            if (string.IsNullOrWhiteSpace(JetonTelegram) || string.IsNullOrWhiteSpace(ChatTelegram)) return;
            string jeton = System.Text.RegularExpressions.Regex.Replace(JetonTelegram, "\\s", ""),
                   chat = System.Text.RegularExpressions.Regex.Replace(ChatTelegram, "\\s", "");
            if (jeton.StartsWith("bot", StringComparison.OrdinalIgnoreCase)) jeton = jeton.Substring(3);
            try
            {
                var contenu = new FormUrlEncodedContent(new Dictionary<string, string> { ["chat_id"] = chat, ["text"] = "Supertrend NQ : " + texte });
                http.PostAsync($"https://api.telegram.org/bot{jeton}/sendMessage", contenu).ContinueWith(t => NoterTelegram(t, jeton));
            }
            catch (Exception e) { NoterErreurTelegram(e.Message.Replace(jeton, "***"), 0); }
        }

        void NoterTelegram(System.Threading.Tasks.Task<HttpResponseMessage> t, string jeton)
        {
            try
            {
                if (t.IsFaulted) { NoterErreurTelegram((t.Exception?.GetBaseException().Message ?? "erreur").Replace(jeton, "***"), 0); return; }
                if (t.IsCanceled) { NoterErreurTelegram("pas de reponse de Telegram en 20 s", 0); return; }
                using var r = t.Result;
                if (r.IsSuccessStatusCode) { derniereErreurTelegram = ""; return; }
                string corps = "";
                try { corps = r.Content.ReadAsStringAsync().GetAwaiter().GetResult(); } catch { }
                var d = System.Text.RegularExpressions.Regex.Match(corps, "\"description\"\\s*:\\s*\"([^\"]*)\"");
                NoterErreurTelegram($"code {(int)r.StatusCode}{(d.Success ? $", {d.Groups[1].Value}" : "")}", (int)r.StatusCode);
            }
            catch { }
        }

        void NoterErreurTelegram(string erreur, int code)
        {
            if (erreur == derniereErreurTelegram) return;
            derniereErreurTelegram = erreur;
            string conseil = code == 401 || code == 404 ? "jeton faux ou incomplet : recopie-le en entier depuis BotFather"
                : code == 400 && erreur.Contains("chat not found") ? "numero de conversation faux, ou tu n'as pas appuye sur Demarrer dans ton bot"
                : code == 403 ? "ouvre ton bot dans Telegram et appuie sur Demarrer (ou debloque-le)"
                : "verifie la connexion internet du PC";
            string texte = $"Telegram : message non envoye ({erreur}) : {conseil}";
            Log(texte, StrategyLoggingLevel.Error);
            try { File.AppendAllText(Path.Combine(Dossier, "journal.txt"), $"{Maintenant():yyyy-MM-dd HH:mm:ss} UTC {texte}{Environment.NewLine}"); } catch { }
        }
    }
}
