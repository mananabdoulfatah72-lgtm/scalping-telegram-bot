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
    /// A tester d'abord sur un compte de simulation (voir GUIDE.md).
    /// Mode a plat (Bulenox, FundedNext, vagues 10-11) : RSI(2) de nuit seulement sur MES (achat a 18 h, vente a 9 h 30), zone
    /// sur MES quand le compte est trop pres de son plancher (frein), pas de zone les jours d'annonce de la Fed, plafond du jour
    /// (a mettre seulement sur le compte finance) verifie sur la valeur reelle du compte.</summary>
    public class Bot3en1Strategy : Strategy
    {
        [InputParameter("Compte", 10)] public Account Compte;
        [InputParameter("Mode a plat chaque jour (Bulenox, FundedNext) : RSI(2) de nuit sur MES, frein, pas de zone les jours de la Fed", 12)]
        public bool ModeAPlat = false;
        [InputParameter("NQ (barres et delta), contrat du moment, ex. NQZ6", 20)] public Symbol SymboleNQ;
        [InputParameter("MNQ (ordres), meme echeance, ex. MNQZ6", 30)] public Symbol SymboleMNQ;
        [InputParameter("MES (mode a plat : RSI(2) de nuit et zone freinee), meme echeance, ex. MESZ6", 35)] public Symbol SymboleMES;
        [InputParameter("Dossier des donnees du bot", 40)] public string Dossier = @"C:\Bot3en1";
        [InputParameter("MNQ par source", 50, 1, 5, 1, 0)] public int Taille = 1;
        [InputParameter("Plafond de gain du jour en $ (0 = aucun ; Bulenox : 500 sur le compte Master seulement, 0 pendant le challenge ; Static : 500 sur le compte Pro)", 60, 0, 5000, 50, 0)] public double PlafondJour = 0;
        [InputParameter("Mode a plat : limite de perte du jour en $ (0 = aucune ; Bulenox option 2 : 1050, juste avant la limite de 1 100 $ de la firme)", 61, 0, 5000, 50, 0)] public double LimitePerteJour = 0;
        [InputParameter("Mode a plat : frein, zone sur MES quand le compte est a X $ ou plus sous son plus haut de fin de journee (0 = jamais ; Bulenox : 750)", 62, 0, 5000, 50, 0)] public double Frein = 750;
        [InputParameter("Mode a plat : solde de depart du compte (ex. 50000)", 63, 0, 1000000, 1000, 0)] public double SoldeDepart = 50000;
        [InputParameter("Mode a plat : perte max suivie en fin de journee (Bulenox 50K : 2500)", 64, 0, 100000, 100, 0)] public double PerteMax = 2500;
        [InputParameter("Mode a plat : le plancher s'arrete a solde de depart + X (Bulenox : 100)", 65, 0, 10000, 50, 0)] public double Blocage = 100;
        [InputParameter("Mode a plat : jours de la Fed en plus (AAAA-MM-JJ separes par des virgules)", 66)] public string JoursFedEnPlus = "";
        [InputParameter("Mode a plat : plus haut de fin de journee deja atteint par ce compte (0 = inconnu ; compte neuf : 0)", 67, 0, 1000000, 100, 0)] public double PlusHautConnu = 0;
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
        double dernierPrix, prixAvantPause;          // dernier prix du NQ, et dernier prix avant la pause de 17 h
        DateTime journeeTrading;                     // journee de trading de la firme (de 18 h la veille a 17 h)
        bool fermerHorsSeance;                       // plafond atteint la nuit : aligner la position meme hors seance
        bool plafondANoter;                          // plafond atteint dans une transaction de nuit : message et etat au prochain tic
        bool etatASauver;                            // nouvelle journee de trading : etat a enregistrer au prochain tic
        bool alerteSilence;
        // mode a plat
        double dernierPrixES;                        // dernier prix de l'ES (flux du MES)
        DateTime dernierTickES = DateTime.MinValue;
        DateTime ordreMESEnAttenteDepuis = DateTime.MinValue;
        string nuitJournee = "";                     // journee de trading du dernier RSI(2) de nuit achete
        double picFinJour, soldeEstime, equiteDebut; // plus haut de fin de journee, solde estime par le bot, equite a 18 h
        string freinJournee = "";                    // journee de trading pour laquelle le frein a ete decide
        bool freinActif;
        DateTime depassementDepuis = DateTime.MinValue;   // plafond ou limite constate depuis (confirmation sur 3 s)
        string alerteNuit = "";                      // journee de trading deja signalee (achat de nuit impossible)
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
                if (ModeAPlat && SymboleMES == null)
                    throw new Exception("mode a plat : choisis aussi le symbole MES dans les reglages");
                ny = TrouverFuseau();
                Directory.CreateDirectory(Dossier);
                var maintenant = HeureNY();
                jour = maintenant.Date;
                VerifierEcheance();
                PreparerMoteur();
                DemarrerSeance(maintenant);
                SymboleNQ.NewLast += SurTransaction;
                if (ModeAPlat) SymboleMES.NewLast += SurTransactionES;
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
            if (ModeAPlat && SymboleMES != null) SymboleMES.NewLast -= SurTransactionES;
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
            foreach (var s in ModeAPlat ? new[] { SymboleNQ, SymboleMNQ, SymboleMES } : new[] { SymboleNQ, SymboleMNQ })
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
            bot.PlafondJour = ModeAPlat ? 0 : PlafondJour;     // mode a plat : plafond gere ici, sur la valeur reelle du compte
            bot.ModeAPlat = ModeAPlat;
            if (ModeAPlat)
            {
                bot.JoursFed = new HashSet<DateTime>(Calendrier.JoursFed);
                foreach (var x in (JoursFedEnPlus ?? "").Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries))
                    if (DateTime.TryParseExact(x.Trim(), "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out var dj)) bot.JoursFed.Add(dj);
                    else Dire($"ATTENTION : jour de la Fed illisible dans les reglages : {x}", true);
            }
            bot.ContratSuivant = (j, c) => Calendrier.Contrat(Calendrier.SeanceSuivante(j));
            var etat = LireEtat();
            if (etat != null && etat.RsiTenu) bot.RestaurerRsi(true, etat.EntreeRsi);
            // journee de trading en cours (de 18 h la veille a 17 h) :
            // - meme journee que le fichier d'etat : gain deja realise, reference du RSI(2) et plafond repris tels quels ;
            // - sinon, nouvelle journee : reference du RSI(2) = dernier prix avant 17 h enregistre, a defaut la derniere
            //   cloture de l'historique.
            journeeTrading = JourneeTrading(HeureNY());
            string jt = journeeTrading.ToString("yyyy-MM-dd");
            if (etat != null && etat.PrixAvantPause > 0) prixAvantPause = etat.PrixAvantPause;
            if (etat?.JourneeTrading == jt)
                bot.RestaurerJournee(etat.RealiseJour, etat.RefRsi, etat.PlafondJournee == jt);
            else
                bot.NouvelleJournee(prixAvantPause > 0 ? prixAvantPause : (bot.Historique.Count > 0 ? bot.Historique[^1].Cloture : 0));
            if (ModeAPlat) PreparerModeAPlat(etat, jt);
        }

        /// <summary>Mode a plat : etat du compte (plus haut de fin de journee, solde estime, frein) et RSI(2) de nuit en cours,
        /// repris de etat.json s'il s'agit du meme compte.</summary>
        void PreparerModeAPlat(Etat etat, string jt)
        {
            double? reel = SoldeReel();
            if (etat != null && etat.CompteNom == (Compte.Name ?? ""))
            {
                picFinJour = etat.PicFinJour; soldeEstime = etat.SoldeEstime > 0 ? etat.SoldeEstime : SoldeDepart;
                nuitJournee = etat.NuitJournee ?? "";
                if (DateTime.TryParseExact(etat.JourDecisionNuit ?? "", "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out var jd))
                    bot.RestaurerDecisionNuit(etat.NuitVoulue, jd);
                if (etat.NuitTenue) bot.RestaurerNuit(true, etat.EntreeNuitES > 0 ? etat.EntreeNuitES : double.NaN);
                if (etat.JourneeTrading == jt) { bot.RestaurerRealiseAPlat(etat.RealiseAPlat); equiteDebut = etat.EquiteDebut; }
                if (etat.FreinJournee != null) { freinJournee = etat.FreinJournee; freinActif = etat.FreinActif; }
            }
            else
            {
                soldeEstime = reel ?? SoldeDepart;
                picFinJour = Math.Max(SoldeDepart, Math.Max(soldeEstime, PlusHautConnu));
                if (etat != null && !string.IsNullOrEmpty(etat.CompteNom))
                    Dire($"nouveau compte ({Compte.Name}) : plus haut de fin de journee repris a {picFinJour:F0} $");
            }
            if (reel.HasValue) soldeEstime = reel.Value;
            if (PlusHautConnu > picFinJour) picFinJour = PlusHautConnu;
            double solde = reel ?? soldeEstime;
            Dire($"mode a plat : solde {(reel.HasValue ? "" : "estime ")}{solde:F0} $, plus haut de fin de journee {picFinJour:F0} $, plancher"
                 + $" {RegleCompte.Plancher(picFinJour, SoldeDepart, PerteMax, Blocage):F0} $"
                 + $"{(reel.HasValue ? "" : " (solde du compte illisible : estimation du bot)")}");
        }

        // ------------------------------------------------------------------ mode a plat : compte
        static double? LireDouble(object o, string propriete)
        {
            try
            {
                var v = o?.GetType().GetProperty(propriete)?.GetValue(o);
                return v switch { double d => d, float f => f, decimal m => (double)m, int i => i, long l => l, _ => (double?)null };
            }
            catch { return null; }
        }

        /// <summary>Solde du compte donne par la plateforme (Account.Balance), lu sans en dependre a la compilation.</summary>
        double? SoldeReel()
        {
            var b = LireDouble(Compte, "Balance");
            return b.HasValue && b.Value > 0 && !double.IsNaN(b.Value) ? b : null;
        }

        /// <summary>Equite du compte : solde + gains latents des positions MNQ et MES (Position.GrossPnL.Value). null si illisible.</summary>
        double? EquiteReelle()
        {
            var b = SoldeReel();
            if (b == null) return null;
            double ouvert = 0;
            foreach (var p in Core.Instance.Positions)
            {
                if (p.Account != Compte || (p.Symbol != SymboleMNQ && p.Symbol != SymboleMES)) continue;
                object g;
                try { g = p.GetType().GetProperty("GrossPnL")?.GetValue(p); } catch { return null; }
                var v = LireDouble(g, "Value");
                if (v == null) return null;
                ouvert += v.Value;
            }
            return b + ouvert;
        }

        /// <summary>Gain de la journee de trading (depuis 18 h) selon la plateforme : equite reelle - equite de 18 h (null si illisible).</summary>
        double? ValeurJourReelle()
        {
            var e = EquiteReelle();
            return e.HasValue && equiteDebut > 0 ? e.Value - equiteDebut : (double?)null;
        }

        /// <summary>Gain de la journee de trading selon les comptes du bot (prix du NQ et de l'ES, frais du backtest).</summary>
        double ValeurJourEstimee()
        {
            bot.PrixES = dernierPrixES > 0 ? dernierPrixES : double.NaN;
            return bot.ValeurJourAPlat(dernierPrix);
        }

        /// <summary>Seance dont la decision du RSI(2) (15 h 50) commande la nuit de la journee jt : la derniere seance avant jt
        /// qui n'est ni fermee ni feriee (pas de decision les jours feries de la Bourse).</summary>
        static DateTime DecisionAttendue(DateTime jt)
        {
            var d = jt.Date.AddDays(-1);
            while (Calendrier.JourFerme(d) || Calendrier.Ferie(d)) d = d.AddDays(-1);
            return d;
        }

        /// <summary>18 h : la journee qui se termine est close (positions a plat) ; solde, plus haut de fin de journee et frein
        /// pour la seance suivante.</summary>
        void FinDeJourneeAPlat(string jt)
        {
            soldeEstime += bot.RealiseAPlat;
            double? reel = SoldeReel();
            if (reel.HasValue) soldeEstime = reel.Value;             // recale l'estimation sur le vrai solde
            double solde = reel ?? soldeEstime;
            if (solde > picFinJour) picFinJour = solde;
            equiteDebut = reel ?? 0;
            bool avant = freinActif;
            freinActif = RegleCompte.Frein(solde, picFinJour, SoldeDepart, PerteMax, Blocage, Frein);
            freinJournee = jt;
            double coussin = RegleCompte.Coussin(solde, picFinJour, SoldeDepart, PerteMax, Blocage);
            if (freinActif != avant || freinActif)
                Dire($"journee du {jt} : solde {(reel.HasValue ? "" : "estime ")}{solde:F0} $, coussin {coussin:F0} $ -> "
                     + (freinActif ? $"FREIN : zone sur MES (compte a {picFinJour - solde:F0} $ sous son plus haut)" : "zone sur MNQ"));
        }

        /// <summary>18 h (New York) : nouvelle journee de trading de la firme (gain du jour remis a zero, plafond leve, RSI(2)
        /// compte depuis le dernier prix avant 17 h). Appelee par l'horloge et par chaque transaction.</summary>
        void PasserJournee(DateTime ny)
        {
            var jt = JourneeTrading(ny);
            if (jt == journeeTrading || ny.TimeOfDay < TimeSpan.FromHours(18)) return;
            journeeTrading = jt;
            if (ModeAPlat && bot != null) FinDeJourneeAPlat(jt.ToString("yyyy-MM-dd"));
            bot?.NouvelleJournee(prixAvantPause > 0 ? prixAvantPause : dernierPrix);
            etatASauver = true;
        }

        /// <summary>Journee de trading de la firme : de 18 h (New York) la veille a 17 h ; designee par le jour ou elle finit.</summary>
        static DateTime JourneeTrading(DateTime ny) => ny.TimeOfDay >= TimeSpan.FromHours(18) ? ny.Date.AddDays(1) : ny.Date;

        void DemarrerSeance(DateTime maintenant)
        {
            derniereMinute = Calendrier.JourCourt(jour) ? (Calendrier.Ferie(jour) ? 209 : 224) : Moteur.N - 1;
            if (Calendrier.JourFerme(jour)) { seanceFinie = true; return; }
            for (int i = 0; i < Moteur.N; i++) barres[i] = new Barre();
            if (ModeAPlat)
            {
                string js = jour.ToString("yyyy-MM-dd");
                if (freinJournee != js)                  // frein pas encore decide a 18 h (demarrage du bot) : decide maintenant
                {
                    double solde = SoldeReel() ?? soldeEstime;
                    freinActif = RegleCompte.Frein(solde, picFinJour, SoldeDepart, PerteMax, Blocage, Frein);
                    freinJournee = js;
                }
                bot.ZoneSurMES = freinActif;
            }
            bot.DebutSeance(jour, Calendrier.Contrat(jour), derniereMinute);
            if (ModeAPlat && bot.JourFed) Dire("jour d'annonce de la Fed : pas de zone aujourd'hui (le RSI(2) de nuit continue)");
            if (ModeAPlat && bot.ZoneSurMES && bot.ZoneActive) Dire("frein actif : la zone trade sur MES aujourd'hui");
            decisionRsiFaite = seanceFinie = false;
            prochaineMinute = 0;
            int m = Minute(maintenant);
            if (m > 0)
            {
                // demarrage apres 9 h 30 : barres et delta deja passes rejoues sans ordre ; aucune entree de zone au milieu d'un trade
                double realiseAvant = bot.RealiseAPlat;
                Rattraper(Math.Min(m, derniereMinute + 1));
                bot.OublierZoneTenue();
                if (ModeAPlat) bot.RestaurerRealiseAPlat(realiseAvant);   // les trades rejoues n'ont pas ete pris (ou sont deja comptes)
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
                dernierPrix = last.Price;
                if (t.TimeOfDay < TimeSpan.FromHours(17)) prixAvantPause = last.Price;
                PasserJournee(t);                        // une transaction de 18 h peut arriver avant le tic de l'horloge
                // hors seance (apres la fin de la seance, ou avant 9 h 30) : plafond du jour verifie a chaque transaction
                bool horsSeance = seanceFinie || t.Date != jour || Minute(t) < 0;
                if (horsSeance && !ModeAPlat && PlafondJour > 0 && bot != null && bot.VerifierPlafondHorsSeance(last.Price))
                    fermerHorsSeance = plafondANoter = true;
                if (t.Date == jour) Ajouter(t, last.Price, last.Size, last.AggressorFlag);
            }
        }

        void SurTransactionES(Symbol s, Last last)
        {
            lock (verrou) { dernierPrixES = last.Price; dernierTickES = Maintenant(); }
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
                    PasserJournee(maintenant);
                    if (etatASauver) { etatASauver = false; SauverEtat(); }
                    // plafond du jour atteint hors seance (verifie a chaque transaction, voir SurTransaction)
                    if (plafondANoter)
                    {
                        plafondANoter = false;
                        Dire($"plafond du jour atteint hors seance ({PlafondJour:F0} $) a {dernierPrix:F2} : RSI(2) ferme, plus de trade jusqu'a 18 h");
                        SauverEtat();
                    }
                    if (fermerHorsSeance && bot != null)
                    {
                        if (PositionReelle(SymboleMNQ) == bot.PositionNette) fermerHorsSeance = false;
                        else Aligner();
                    }
                    if (ModeAPlat && bot != null)
                    {
                        if (TicAPlat(maintenant)) return;        // fichier STOP : tout ferme, aucun realignement
                        if (seanceFinie) { Aligner(); return; }
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

        /// <summary>Mode a plat, a chaque tic : RSI(2) de nuit (achat a 18 h, vente a 9 h 30), plafond et limite de perte du jour.
        /// Renvoie vrai si le fichier STOP est present (tout est ferme, l'appelant ne doit plus aligner les positions).</summary>
        bool TicAPlat(DateTime maintenant)
        {
            var tod = maintenant.TimeOfDay;
            bot.PrixES = dernierPrixES > 0 ? dernierPrixES : double.NaN;
            if (File.Exists(Path.Combine(Dossier, "STOP"))) { ToutFermer("fichier STOP present"); return true; }
            // vente du RSI(2) de nuit a 9 h 30
            if (bot.RsiNuit != 0 && tod >= TimeSpan.FromMinutes(570) && tod < TimeSpan.FromHours(18))
            {
                foreach (var s in bot.FermerNuit(dernierPrix)) Dire(s.Texte);
                SauverEtat();
            }
            // achat du RSI(2) de nuit : de 18 h a 9 h 25, si la seance qui suit existe et que le MES cote
            string jt = journeeTrading.ToString("yyyy-MM-dd");
            bool nuit = tod >= TimeSpan.FromHours(18) || tod < TimeSpan.FromMinutes(565);
            bool esVivant = dernierPrixES > 0 && (Maintenant() - dernierTickES).TotalMinutes < 5;
            if (bot.NuitVoulue && bot.RsiNuit == 0 && !bot.Arret && nuit && nuitJournee != jt && !Calendrier.JourFerme(journeeTrading))
            {
                var attendue = DecisionAttendue(journeeTrading);
                string empeche = bot.JourDecision != attendue
                    ? $"decision du RSI(2) du {attendue:yyyy-MM-dd} absente (derniere : {bot.JourDecision:yyyy-MM-dd})"
                    : !esVivant && (tod >= TimeSpan.FromMinutes(18 * 60 + 5) || tod < TimeSpan.FromMinutes(565)) ? "flux du MES absent depuis 5 minutes" : null;
                if (empeche == null && esVivant)
                {
                    foreach (var s in bot.OuvrirNuit(dernierPrix)) Dire(s.Texte);
                    nuitJournee = jt;
                    SauverEtat();
                }
                else if (empeche != null && alerteNuit != jt)
                {
                    alerteNuit = jt;
                    Dire($"ALERTE : RSI(2) de nuit voulu mais pas achete ({empeche})", true);
                }
            }
            // plafond (compte finance) et limite de perte du jour : la valeur reelle du compte (si lisible) et l'estimation du bot
            // doivent etre d'accord, 3 secondes de suite, sans ordre envoye dans les 10 dernieres secondes (evite une lecture
            // fausse pendant qu'une position se ferme)
            if (!bot.Arret && (PlafondJour > 0 || LimitePerteJour > 0) && (bot.ZoneTenue != 0 || bot.RsiNuit != 0 || bot.RealiseAPlat != 0))
            {
                double? vr = ValeurJourReelle();
                double ve = ValeurJourEstimee();
                bool plafond = PlafondJour > 0 && ve >= PlafondJour && (vr == null || vr >= PlafondJour);
                bool limite = LimitePerteJour > 0 && ve <= -LimitePerteJour && (vr == null || vr <= -LimitePerteJour);
                bool ordreRecent = (Maintenant() - ordreEnAttenteDepuis).TotalSeconds < 10 || (Maintenant() - ordreMESEnAttenteDepuis).TotalSeconds < 10;
                if ((plafond || limite) && !ordreRecent)
                {
                    if (depassementDepuis == DateTime.MinValue) depassementDepuis = Maintenant();
                    else if ((Maintenant() - depassementDepuis).TotalSeconds >= 3)
                    {
                        string v = $"{(vr.HasValue ? $"compte {vr.Value:F0} $, " : "")}estimation {ve:F0} $";
                        string raison = plafond ? $"plafond du jour atteint ({v})" : $"limite de perte du jour atteinte ({v})";
                        foreach (var s in bot.ArreterJournee(dernierPrix, raison)) Dire(s.Texte, limite);
                        depassementDepuis = DateTime.MinValue;
                        SauverEtat();
                    }
                }
                else depassementDepuis = DateTime.MinValue;
            }
            return false;
        }

        void FermerMinute(int m, bool executer)
        {
            if (ModeAPlat) bot.PrixES = dernierPrixES > 0 ? dernierPrixES : double.NaN;
            var signaux = bot.MinuteFermee(m, barres[m]);
            foreach (var s in signaux)
                if (executer) Dire(s.Texte);
            if (executer && signaux.Count > 0) SauverEtat();            // gain du jour realise : garde en cas de redemarrage
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
            if (!ModeAPlat) { AlignerSymbole(SymboleMNQ, "MNQ", bot.PositionNette, ref ordreEnAttenteDepuis); return; }
            AlignerSymbole(SymboleMNQ, "MNQ", bot.PositionMNQ, ref ordreEnAttenteDepuis);
            AlignerSymbole(SymboleMES, "MES", bot.PositionMES, ref ordreMESEnAttenteDepuis);
        }

        void AlignerSymbole(Symbol symbole, string nom, int voulu, ref DateTime attente)
        {
            if ((Maintenant() - attente).TotalSeconds < 15) return;     // laisser le temps a l'ordre precedent
            int reel = PositionReelle(symbole), ecart = voulu - reel;
            if (ecart == 0) return;
            var r = Core.Instance.PlaceOrder(new PlaceOrderRequestParameters
            {
                Account = Compte, Symbol = symbole, Side = ecart > 0 ? Side.Buy : Side.Sell,
                Quantity = Math.Abs(ecart), OrderTypeId = OrderType.Market
            });
            attente = Maintenant();
            if (r.Status == TradingOperationResultStatus.Failure)
                Dire($"ERREUR d'ordre ({(ecart > 0 ? "achat" : "vente")} {Math.Abs(ecart)} {nom}) : {r.Message}", true);
            else
                Dire($"ordre envoye : {(ecart > 0 ? "achat" : "vente")} {Math.Abs(ecart)} {nom} (position {reel} -> {voulu})");
        }

        void ToutFermer(string raison)
        {
            FermerSymbole(SymboleMNQ, ref ordreEnAttenteDepuis, raison);
            if (ModeAPlat) FermerSymbole(SymboleMES, ref ordreMESEnAttenteDepuis, raison);
        }

        void FermerSymbole(Symbol symbole, ref DateTime attente, string raison)
        {
            int reel = PositionReelle(symbole);
            if (reel != 0 && (Maintenant() - attente).TotalSeconds >= 15)
            {
                Core.Instance.PlaceOrder(new PlaceOrderRequestParameters
                {
                    Account = Compte, Symbol = symbole, Side = reel > 0 ? Side.Sell : Side.Buy,
                    Quantity = Math.Abs(reel), OrderTypeId = OrderType.Market
                });
                attente = Maintenant();
                Dire($"tout ferme : {raison}", true);
            }
        }

        // ------------------------------------------------------------------ etat et messages
        class Etat
        {
            public string Jour { get; set; }
            public bool RsiTenu { get; set; }
            public double EntreeRsi { get; set; }
            public string PlafondJournee { get; set; }      // journee de trading ou le plafond du jour a ete atteint
            public string JourneeTrading { get; set; }      // journee de trading de l'enregistrement (de 18 h la veille a 17 h)
            public double RealiseJour { get; set; }         // gain deja realise dans cette journee de trading
            public double RefRsi { get; set; }              // reference du RSI(2) pour le gain du jour
            public double PrixAvantPause { get; set; }      // dernier prix du NQ avant 17 h
            // mode a plat
            public string CompteNom { get; set; }
            public bool NuitTenue { get; set; }
            public double EntreeNuitES { get; set; }
            public string NuitJournee { get; set; }
            public double PicFinJour { get; set; }
            public double SoldeEstime { get; set; }
            public double EquiteDebut { get; set; }
            public double RealiseAPlat { get; set; }
            public string FreinJournee { get; set; }
            public bool FreinActif { get; set; }
            public bool NuitVoulue { get; set; }
            public string JourDecisionNuit { get; set; }
        }

        /// <summary>Fichier d'etat : etat.json (ancien mode) ; en mode a plat, un fichier par compte (challenge et Master peuvent
        /// tourner en meme temps sans s'ecraser).</summary>
        string FichierEtat()
        {
            if (!ModeAPlat) return Path.Combine(Dossier, "etat.json");
            var nom = new string((Compte?.Name ?? "compte").Select(c => char.IsLetterOrDigit(c) || c == '-' || c == '_' ? c : '_').ToArray());
            return Path.Combine(Dossier, $"etat_{nom}.json");
        }

        Etat LireEtat()
        {
            var f = FichierEtat();
            try { return File.Exists(f) ? JsonSerializer.Deserialize<Etat>(File.ReadAllText(f)) : null; } catch { return null; }
        }

        void SauverEtat()
        {
            if (bot == null) return;
            var e = new Etat { Jour = jour.ToString("yyyy-MM-dd"), RsiTenu = bot.Rsi == 1, EntreeRsi = bot.EntreeRsi,
                               PlafondJournee = bot.Arret ? journeeTrading.ToString("yyyy-MM-dd") : null,
                               JourneeTrading = journeeTrading.ToString("yyyy-MM-dd"), RealiseJour = bot.RealiseJour,
                               RefRsi = bot.RefRsi, PrixAvantPause = prixAvantPause,
                               CompteNom = Compte?.Name ?? "", NuitTenue = bot.RsiNuit == 1, EntreeNuitES = Fini(bot.EntreeNuitES),
                               NuitJournee = nuitJournee, PicFinJour = picFinJour, SoldeEstime = soldeEstime, EquiteDebut = equiteDebut,
                               RealiseAPlat = Fini(bot.RealiseAPlat), FreinJournee = freinJournee, FreinActif = freinActif,
                               NuitVoulue = bot.NuitVoulue, JourDecisionNuit = bot.JourDecision == default ? null : bot.JourDecision.ToString("yyyy-MM-dd") };
            File.WriteAllText(FichierEtat(), JsonSerializer.Serialize(e));
        }

        static double Fini(double v) => double.IsNaN(v) || double.IsInfinity(v) ? 0 : v;      // JSON : pas de NaN

        string EtatTexte() => bot == null ? "" : ModeAPlat ?
            $"Positions voulues : MNQ {bot.PositionMNQ}, MES {bot.PositionMES} (zone {bot.ZoneTenue}{(bot.ZoneSurMES ? " sur MES, frein" : "")},"
            + $" RSI(2) de nuit {bot.RsiNuit}{(bot.NuitVoulue ? ", achat de nuit voulu" : "")})"
            + $"{(bot.ZoneActive ? "" : bot.JourFed ? " ; jour de la Fed, pas de zone" : " ; zone inactive aujourd'hui")}"
            + $"{(bot.Arret ? " ; plafond ou limite du jour atteint, plus de trade jusqu'a 18 h" : "")}" :
            $"Position voulue {bot.PositionNette} MNQ (zone {bot.ZoneTenue}, RSI(2) {bot.Rsi}){(bot.Rsi == 1 ? $", RSI(2) achete a {bot.EntreeRsi:F2}" : "")}" +
            $"{(bot.ZoneActive ? "" : " ; zone inactive aujourd'hui")}" +
            $"{(bot.Arret ? " ; plafond du jour atteint, plus de trade jusqu'a 18 h" : "")}";

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
