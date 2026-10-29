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
    /// (a mettre seulement sur le compte finance) verifie sur la valeur reelle du compte.
    /// Challenge de 30 jours (vague 13, version D) : arret a l'objectif (tout ferme des que le compte atteint l'objectif + 50 $,
    /// plus aucun trade ensuite) et taille de fin de course (6 MNQ par source les 5 dernieres seances si l'objectif n'est pas
    /// atteint).</summary>
    public class Bot3en1Strategy : Strategy
    {
        [InputParameter("Compte", 10)] public Account Compte;
        [InputParameter("Mode a plat chaque jour (Bulenox, FundedNext) : frein, pas de zone les jours de la Fed, a plat avant 16 h 59 (New York)", 12)]
        public bool ModeAPlat = false;
        [InputParameter("Mode a plat : RSI(2) de nuit sur MES, achat 18 h - vente 9 h 30 (Bulenox interdit de garder une position la nuit : laisser decoche)", 13)]
        public bool RsiDeNuit = false;
        [InputParameter("NQ (barres et delta), contrat du moment, ex. NQZ6", 20)] public Symbol SymboleNQ;
        [InputParameter("MNQ (ordres), meme echeance, ex. MNQZ6", 30)] public Symbol SymboleMNQ;
        [InputParameter("MES (mode a plat : RSI(2) de nuit et zone freinee), meme echeance, ex. MESZ6", 35)] public Symbol SymboleMES;
        [InputParameter("Dossier des donnees du bot", 40)] public string Dossier = @"C:\Bot3en1";
        [InputParameter("MNQ par source (Bulenox : 4 pendant le challenge de 30 jours, 1 sur le compte Master)", 50, 1, 6, 1, 0)] public int Taille = 1;
        [InputParameter("Zone : entree a la cassure, cochee par defaut depuis le 26 octobre 2026 a la demande de l'utilisateur (entre deux controles, des qu'une minute cloture au-dela des niveaux du dernier controle, le bot entre tout de suite ; controles, niveaux et sorties inchanges ; decoche = entree seulement aux controles de 30 minutes)", 51)]
        public bool EntreeCassure = true;
        [InputParameter("Zone : entree a la cassure confirmee par le volume, cochee par defaut depuis le 26 octobre 2026 a la demande de l'utilisateur (la minute de la cassure doit avoir un volume d'au moins 2 fois la moyenne des 30 minutes d'avant ; sans effet aux controles)", 52)]
        public bool ConfirmationVolume = true;
        [InputParameter("Zone : multiple du volume pour confirmer la cassure, 1 par defaut depuis le 26 octobre 2026 au soir a la demande de l'utilisateur (1 = la minute de la cassure a au moins le volume moyen des 30 minutes d'avant ; 2 = au moins le double)", 53, 0.5, 5, 0.5, 1)]
        public double MultipleVolume = 1.0;
        [InputParameter("Zone : pas d'entree tardive, cochee par defaut depuis le 26 octobre 2026 au soir a la demande de l'utilisateur (entree seulement a la minute ou le prix franchit le niveau, avec le volume, aux controles comme entre eux ; une cassure ratee n'est pas rattrapee plus haut ou plus bas)", 54)]
        public bool SansEntreeTardive = true;
        [InputParameter("Zone : fenetre de confirmation en minutes, 5 par defaut depuis le 26 octobre 2026 au soir a la demande de l'utilisateur (si la minute de la cassure n'a pas le volume, une des minutes suivantes peut confirmer tant que le prix reste au-dela du niveau ; 0 = seulement la minute de la cassure)", 56, 0, 30, 1, 0)]
        public int FenetreConfirmation = 5;
        [InputParameter("Zone : filtre Q1, sens de l'ouverture, decoche par defaut (achat seulement si l'ouverture de 9 h 30 est au-dessus ou au niveau de la cloture de la veille, vente seulement si elle est en dessous ou au niveau ; scalping/README.md partie Q)", 57)]
        public bool FiltreOuverture = false;
        [InputParameter("Zone : filtre Q2, tendance de fond, decoche par defaut (achat seulement si la veille a cloture au-dessus de la moyenne des 20 dernieres clotures, vente seulement en dessous ; scalping/README.md partie Q)", 58)]
        public bool FiltreTendance = false;
        [InputParameter("Zone : une seule entree par seance et sortie seulement au retour sous le niveau casse, cochee par defaut depuis le 26 octobre 2026 au soir a la demande de l'utilisateur (sortie a un controle de 30 minutes si le prix est repasse de l'autre cote du niveau casse a l'entree, au lieu de la limite du controle ou du VWAP ; sinon a 16 h ; limite de perte du jour inchangee)", 55)]
        public bool LaisserCourir = true;
        [InputParameter("Zone : pas de sortie aux controles, cochee par defaut depuis le 27 octobre 2026 a la demande de l'utilisateur (le trade est garde jusqu'a 16 h, ou jusqu'a la limite de perte du jour ; decoche = sortie a un controle au retour sous le niveau casse)", 59)]
        public bool SortieFinDeJour = true;
        [InputParameter("Zone : stop en points au-dela du niveau casse, 70 par defaut depuis le 27 octobre 2026 a la demande de l'utilisateur (achat : niveau casse - 70 ; vente : niveau casse + 70 ; verifie a chaque prix recu ; 0 = aucun stop)", 47, 0, 1000, 5, 0)]
        public double StopPoints = 70;
        [InputParameter("Filtre delta de la zone : decoche par defaut depuis le 26 octobre 2026 = la zone seule, chaque cassure verifiee a un controle est prise quel que soit le delta (coche = ancien bot, cassure ecartee si le delta 30 min va contre elle)", 48)]
        public bool FiltreDeltaActif = false;
        [InputParameter("Filtre delta : relance, decochee par defaut depuis le 20 octobre 2026 (un trade ecarte encore en cours est pris a un controle suivant si le delta va alors dans son sens, donc plus tard et plus loin de sa sortie ; relance/README.md)", 49)]
        public bool RelanceFiltre = false;
        [InputParameter("Plafond de gain du jour en $ (0 = aucun ; Bulenox : 500 sur le compte Master seulement, 0 pendant le challenge ; Static : 500 sur le compte Pro)", 60, 0, 5000, 50, 0)] public double PlafondJour = 0;
        [InputParameter("Mode a plat : limite de perte du jour en $ (0 = aucune ; Bulenox option 2 : 1000, 100 $ de marge avant la limite de 1 100 $ de la firme)", 61, 0, 5000, 50, 0)] public double LimitePerteJour = 0;
        [InputParameter("Mode a plat : frein, zone sur MES quand le compte est a X $ ou plus sous son plus haut de fin de journee (0 = jamais ; Bulenox : 750)", 62, 0, 5000, 50, 0)] public double Frein = 750;
        [InputParameter("Mode a plat : solde de depart du compte (ex. 50000)", 63, 0, 1000000, 1000, 0)] public double SoldeDepart = 50000;
        [InputParameter("Mode a plat : perte max suivie en fin de journee (Bulenox 50K : 2500)", 64, 0, 100000, 100, 0)] public double PerteMax = 2500;
        [InputParameter("Mode a plat : le plancher s'arrete a solde de depart + X (Bulenox : 100)", 65, 0, 10000, 50, 0)] public double Blocage = 100;
        [InputParameter("Mode a plat : jours de la Fed en plus (AAAA-MM-JJ separes par des virgules)", 66)] public string JoursFedEnPlus = "";
        [InputParameter("Mode a plat : plus haut de fin de journee deja atteint par ce compte (0 = inconnu ; compte neuf : 0)", 67, 0, 1000000, 1, 0)] public double PlusHautConnu = 0;
        [InputParameter("Mode a plat : solde actuel du compte, seulement si le journal dit « solde du compte illisible » (0 = rien ; repris une seule fois par valeur, le bot le suit ensuite)", 70, 0, 1000000, 1, 0)]
        public double SoldeManuel = 0;
        [InputParameter("Challenge : objectif, solde du compte a atteindre (Bulenox 50K : 53000). Des que le compte atteint l'objectif + 50 $, le bot ferme tout et ne trade plus (0 = aucun ; compte Master : 0)", 68, 0, 10000000, 500, 0)]
        public double ObjectifChallenge = 0;
        [InputParameter("Challenge : dernier jour ou le compte peut trader, AAAA-MM-JJ (date de fin donnee par Bulenox ; vide = aucune ; compte Master : vide)", 69)]
        public string DateFinChallenge = "";
        [InputParameter("Challenge : MNQ par source pendant les dernieres seances si l'objectif n'est pas atteint (0 = jamais ; version 30 jours : 6 ; compte Master : 0)", 71, 0, 6, 1, 0)]
        public int TailleFin = 0;
        [InputParameter("Challenge : nombre de dernieres seances jouees avec cette taille (version 30 jours : 5)", 72, 1, 20, 1, 0)]
        public int SeancesFin = 5;
        [InputParameter("Telegram : jeton du bot (facultatif)", 75)] public string JetonTelegram = "";
        [InputParameter("Telegram : numero de conversation (facultatif)", 80)] public string ChatTelegram = "";
        [InputParameter("Historique : adresse des barres du robot", 90)]
        public string AdresseHistorique = "https://raw.githubusercontent.com/mananabdoulfatah72-lgtm/scalping-telegram-bot/main/zone/robot/nq_1min.csv.gz";

        const string Version = "27 octobre 2026 (regle de l'utilisateur : entree a la cassure avec volume, fenetre de confirmation, une entree par seance, stop au niveau casse +/- 70 points, sinon 16 h ou limite du jour)";     // ecrite au lancement : verifie que la mise a jour est bien chargee
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
        DateTime demarrageUtc;                       // heure du lancement du bot (UTC)
        DateTime alerteAveugle = DateTime.MinValue;  // derniere alerte « aucune transaction NQ depuis le demarrage »
        bool premierPrixANoter;                      // premiere transaction NQ depuis le lancement : confirmation au prochain tic
        bool erreurHeureNotee;                       // heure d'une transaction illisible : notee une seule fois
        bool soldeIllisible;                         // solde du compte illisible au lancement : relu chaque minute
        DateTime derniereLectureSolde = DateTime.MinValue;
        double soldeManuelApplique;                  // dernier SoldeManuel deja repris (garde dans l'etat : repris une seule fois)
        string derniereErreurTelegram = "";          // derniere erreur d'envoi Telegram notee dans le journal
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
        DateTime finChallenge = DateTime.MinValue;   // dernier jour du challenge (DateFinChallenge), MinValue si aucun
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
                // symboles et compte restaures depuis les reglages : on reprend les objets de la connexion active
                // (modele de strategie Quantower : Core.GetSymbol(symbole.CreateInfo())), sinon ils peuvent ne recevoir aucun prix
                ReprendreObjetsVivants(false);
                var maintenant = HeureNY();
                jour = maintenant.Date;
                demarrageUtc = Maintenant();
                VerifierEcheance();
                PreparerMoteur();
                DemarrerSeance(maintenant);
                SymboleNQ.NewLast += SurTransaction;
                if (ModeAPlat) SymboleMES.NewLast += SurTransactionES;
                horloge = new Timer(_ => Tic(), null, 500, 500);
                Dire($"demarre le {jour:yyyy-MM-dd} a {maintenant:HH:mm} (New York), version du {Version}, entree {(EntreeCassure ? "A LA CASSURE (entre deux controles)" + (ConfirmationVolume ? $" CONFIRMEE PAR LE VOLUME (x{MultipleVolume.ToString("0.#", CultureInfo.InvariantCulture)})" : " sans confirmation par le volume") : "aux controles de 30 minutes seulement")}, {(SansEntreeTardive ? $"SANS ENTREE TARDIVE (confirmation dans les {Math.Max(0, FenetreConfirmation)} minutes apres la cassure)" : "entree tardive possible aux controles")}, {(LaisserCourir ? "UNE ENTREE PAR SEANCE" : "plusieurs entrees par seance")}, {(StopPoints > 0 ? $"STOP A {StopPoints.ToString("0.##", CultureInfo.InvariantCulture)} POINTS AU-DELA DU NIVEAU CASSE, " : "aucun stop, ")}{(SortieFinDeJour ? "PAS DE SORTIE AUX CONTROLES : SORTIE SEULEMENT A 16 H OU A LA LIMITE DE PERTE DU JOUR" : LaisserCourir ? "sortie a un controle au retour sous le niveau casse, ou a 16 h" : "sorties d'origine (aux controles, limite de la zone ou VWAP, et 16 h)")}, filtres Q1 (sens de l'ouverture) {(FiltreOuverture ? "COCHE" : "decoche")} et Q2 (tendance de fond) {(FiltreTendance ? "COCHE" : "decoche")}, filtre delta {(FiltreDeltaActif ? "COCHE (cassures ecartees si le delta va contre)" : "decoche (zone seule)")}, relance du filtre {(RelanceFiltre ? "COCHEE" : "decochee")}. {EtatTexte()}");
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
            if (ModeAPlat && Compte != null && SymboleMNQ != null && SymboleMES != null)
            {
                // mode a plat : rien ne doit rester ouvert quand le bot ne tourne plus (la firme interdit les positions de nuit)
                try
                {
                    lock (verrou)
                    {
                        ordreEnAttenteDepuis = ordreMESEnAttenteDepuis = DateTime.MinValue;
                        ToutFermer("arret du bot : positions fermees (mode a plat)");
                    }
                }
                catch (Exception e) { Dire($"ERREUR en fermant les positions a l'arret : {e.Message}", true); }
                SauverEtat();
                Dire("arrete. Mode a plat : les positions ont ete fermees.");
                return;
            }
            SauverEtat();
            Dire("arrete. Les positions ouvertes restent ouvertes (le RSI(2) peut tenir la nuit).");
        }

        /// <summary>Heure de Paris d'une minute de la seance du jour (9 h 30 New York + m minutes), ex. "16h00".</summary>
        string HeureDeParis(int m)
        {
            try
            {
                TimeZoneInfo paris = null;
                foreach (var id in new[] { "Romance Standard Time", "Europe/Paris" })
                    try { paris = TimeZoneInfo.FindSystemTimeZoneById(id); break; } catch { }
                if (paris == null) return null;
                var utc = TimeZoneInfo.ConvertTimeToUtc(jour.AddMinutes(570 + m), ny);
                var t = TimeZoneInfo.ConvertTimeFromUtc(utc, paris);
                return $"{t.Hour}h{t.Minute:00}";
            }
            catch { return null; }
        }

        /// <summary>Heure UTC d'une transaction, quel que soit le genre de DateTime donne par la plateforme.</summary>
        static DateTime EnUtc(DateTime d) => d.Kind == DateTimeKind.Local ? d.ToUniversalTime()
            : d.Kind == DateTimeKind.Unspecified ? DateTime.SpecifyKind(d, DateTimeKind.Utc) : d;

        /// <summary>Remplace les symboles et le compte des reglages par les objets de la connexion active (Core.GetSymbol(info),
        /// compte de meme Id dans Core.Accounts), puis refait l'abonnement aux transactions si on reabonne. Tout par reflexion :
        /// rien ne depend du nom exact de ces methodes a la compilation.</summary>
        void ReprendreObjetsVivants(bool reabonner)
        {
            try
            {
                if (reabonner)
                {
                    SymboleNQ.NewLast -= SurTransaction;
                    if (ModeAPlat && SymboleMES != null) SymboleMES.NewLast -= SurTransactionES;
                }
                var avant = SymboleNQ;
                SymboleNQ = Vivant(SymboleNQ);
                SymboleMNQ = Vivant(SymboleMNQ);
                if (SymboleMES != null) SymboleMES = Vivant(SymboleMES);
                var compteAvant = Compte;
                Compte = CompteVivant(Compte);
                if (reabonner)
                {
                    SymboleNQ.NewLast += SurTransaction;
                    if (ModeAPlat && SymboleMES != null) SymboleMES.NewLast += SurTransactionES;
                }
                Dire($"symboles {(reabonner ? "repris et abonnement refait" : "verifies")} : NQ {SymboleNQ.Name}"
                     + $"{(ReferenceEquals(avant, SymboleNQ) ? "" : " (objet de la connexion active)")}, MNQ {SymboleMNQ.Name}"
                     + $"{(SymboleMES != null ? $", MES {SymboleMES.Name}" : "")} ; compte"
                     + $"{(ReferenceEquals(compteAvant, Compte) ? " inchange" : " repris de la connexion active")}");
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
            bot.FiltreDelta = FiltreDeltaActif;
            bot.EntreeCassure = EntreeCassure;
            bot.ConfirmationVolume = ConfirmationVolume;
            bot.VolumeMultiple = MultipleVolume;
            bot.SansEntreeTardive = SansEntreeTardive;
            bot.FenetreConfirmation = Math.Max(0, FenetreConfirmation);
            bot.FiltreOuverture = FiltreOuverture;
            bot.FiltreTendance = FiltreTendance;
            bot.LaisserCourir = LaisserCourir;
            bot.SortieFinDeJour = SortieFinDeJour;
            bot.StopPoints = Math.Max(0, StopPoints);
            bot.Relance = RelanceFiltre;
            bot.MessageControle = true;
            bot.HeureParis = m => HeureDeParis(m);
            bot.PlafondJour = ModeAPlat ? 0 : PlafondJour;     // mode a plat : plafond gere ici, sur la valeur reelle du compte
            bot.ModeAPlat = ModeAPlat;
            if (ModeAPlat)
            {
                bot.JoursFed = new HashSet<DateTime>(Calendrier.JoursFed);
                foreach (var x in (JoursFedEnPlus ?? "").Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries))
                    if (DateTime.TryParseExact(x.Trim(), "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out var dj)) bot.JoursFed.Add(dj);
                    else Dire($"ATTENTION : jour de la Fed illisible dans les reglages : {x}", true);
                finChallenge = DateTime.MinValue;
                if (!string.IsNullOrWhiteSpace(DateFinChallenge))
                {
                    if (DateTime.TryParseExact(DateFinChallenge.Trim(), "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out var df)) finChallenge = df;
                    else Dire($"ATTENTION : date de fin du challenge illisible ({DateFinChallenge}) : ecris-la AAAA-MM-JJ, ex. 2026-11-11", true);
                }
                if (TailleFin > 0 && finChallenge == DateTime.MinValue)
                    Dire($"ATTENTION : {TailleFin} MNQ en fin de challenge demande, mais sans date de fin lisible : la taille reste a {Taille}", true);
                if (ObjectifChallenge > 0 && ObjectifChallenge <= SoldeDepart)
                    Dire($"ATTENTION : objectif du challenge ({ObjectifChallenge:F0} $) pas au-dessus du solde de depart ({SoldeDepart:F0} $) :"
                         + " il faut le solde a atteindre (Bulenox 50K : 53000). Le bot ne tradera pas.", true);
            }
            else if (ObjectifChallenge > 0 || TailleFin > 0 || !string.IsNullOrWhiteSpace(DateFinChallenge))
                Dire("ATTENTION : reglages du challenge ignores, ils ne marchent qu'avec le mode a plat coche", true);
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
            // solde illisible : solde donne dans les reglages, repris une seule fois par valeur (le bot le suit ensuite a 18 h)
            soldeManuelApplique = etat != null && etat.CompteNom == (Compte.Name ?? "") ? etat.SoldeManuel : 0;
            if (!reel.HasValue && SoldeManuel > 0 && Math.Abs(SoldeManuel - soldeManuelApplique) > 0.005)
            {
                soldeEstime = SoldeManuel;
                if (SoldeManuel > picFinJour) picFinJour = SoldeManuel;
                soldeManuelApplique = SoldeManuel;
                Dire($"solde du compte repris des reglages : {SoldeManuel:F0} $ (le bot le suit ensuite avec ses propres trades)");
            }
            if (reel.HasValue) soldeEstime = reel.Value;
            if (PlusHautConnu > picFinJour) picFinJour = PlusHautConnu;
            double solde = reel ?? soldeEstime;
            Dire($"mode a plat : solde {(reel.HasValue ? "" : "estime ")}{solde:F0} $, plus haut de fin de journee {picFinJour:F0} $, plancher"
                 + $" {RegleCompte.Plancher(picFinJour, SoldeDepart, PerteMax, Blocage):F0} $"
                 + $"{(reel.HasValue ? "" : " (ATTENTION : solde du compte illisible, estimation du bot. Verifie la connexion Rithmic :"
                       + " objectif, limite de perte et plancher sont calcules sur cette estimation)")}", !reel.HasValue);
            soldeIllisible = !reel.HasValue;
            if (soldeIllisible) Dire($"diagnostic du solde : {DiagnosticSolde()}");
            // taille de la journee : celle du RSI(2) de nuit deja achete s'il y en a un (comptes du bot = position reelle),
            // sinon celle du calendrier du challenge
            bot.Taille = bot.RsiNuit != 0 && etat != null && etat.CompteNom == (Compte.Name ?? "") && etat.TailleTenue > 0
                ? etat.TailleTenue : TailleJournee(journeeTrading);
            if (ObjectifChallenge > 0 || finChallenge != DateTime.MinValue)
            {
                int reste = finChallenge == DateTime.MinValue ? -1 : RegleCompte.SeancesRestantes(journeeTrading, finChallenge);
                Dire("challenge : " + (ObjectifChallenge > 0
                         ? $"objectif {ObjectifChallenge:F0} $ (tout ferme a {ObjectifChallenge + RegleCompte.MargeObjectif:F0} $, puis plus de trade)"
                         : "pas d'objectif")
                     + (reste >= 0 ? $", dernier jour le {finChallenge:yyyy-MM-dd} ({reste} seance(s) restante(s), aujourd'hui compris)" : "")
                     + (TailleFin > 0 && reste >= 0 ? $", {TailleFin} MNQ par source les {SeancesFin} dernieres seances" : "")
                     + $" ; taille aujourd'hui : {bot.Taille} MNQ par source");
                if (reste == 0) Dire($"ATTENTION : la date de fin du challenge ({finChallenge:yyyy-MM-dd}) est passee", true);
            }
        }

        /// <summary>Solde du compte au debut de la journee de trading : equite lue a 18 h, a defaut l'estimation du bot.</summary>
        double SoldeDebutJour() => equiteDebut > 0 ? equiteDebut : soldeEstime;

        /// <summary>MNQ par source pour la journee de trading jt : taille de fin de course pendant les SeancesFin dernieres seances
        /// avant DateFinChallenge (vague 13), taille normale sinon.</summary>
        int TailleJournee(DateTime jt) => Math.Max(1, finChallenge == DateTime.MinValue ? Taille
            : RegleCompte.TailleDuJour(Taille, TailleFin, SeancesFin, RegleCompte.SeancesRestantes(jt, finChallenge)));

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

        /// <summary>Ce que la plateforme donne quand le solde est illisible : valeur brute de Account.Balance et champs du compte
        /// qui ressemblent a un solde (noms et valeurs seulement), pour adapter la lecture.</summary>
        string DiagnosticSolde()
        {
            string brut;
            try
            {
                var p = Compte?.GetType().GetProperty("Balance");
                brut = p == null ? "propriete Balance absente" : $"Balance = {Convert.ToString(p.GetValue(Compte), CultureInfo.InvariantCulture)}";
            }
            catch (Exception e) { brut = $"Balance illisible ({e.GetType().Name})"; }
            var champs = new List<string>();
            try
            {
                if (Compte?.GetType().GetProperty("AdditionalInfo")?.GetValue(Compte) is System.Collections.IEnumerable infos)
                    foreach (var x in infos)
                    {
                        if (x == null) continue;
                        var t = x.GetType();
                        string nom = Convert.ToString(t.GetProperty("NameKey")?.GetValue(x) ?? t.GetProperty("Name")?.GetValue(x)
                                                      ?? t.GetProperty("Id")?.GetValue(x), CultureInfo.InvariantCulture) ?? "";
                        object v = t.GetProperty("Value")?.GetValue(x);
                        string n = nom.ToLowerInvariant();
                        if (v != null && (n.Contains("balance") || n.Contains("cash") || n.Contains("equity") || n.Contains("liquid")
                                          || n.Contains("p&l") || n.Contains("pnl")))
                            champs.Add($"{nom} = {Convert.ToString(v, CultureInfo.InvariantCulture)}");
                        if (champs.Count >= 12) break;
                    }
            }
            catch { }
            return brut + (champs.Count > 0 ? " ; autres champs : " + string.Join(", ", champs) : " ; aucun autre champ de solde trouve");
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
            bot.ZoneAutorisee = true;                    // coupee seulement pour la seance d'un rattrapage impossible
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
                Dire($"demarrage en cours de seance : la zone ne prendra que les nouveaux signaux apres {maintenant:HH:mm}"
                     + (bot.Relance ? " (relance cochee : un trade deja en cours peut aussi etre pris a un controle si le delta passe de son cote)" : ""));
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
                        Ajouter(TimeZoneInfo.ConvertTimeFromUtc(EnUtc(t.TimeLeft), ny), t.Price, t.Volume, t.AggressorFlag);
            }
            catch (Exception e) { Dire($"rattrapage des transactions impossible ({e.Message}) : la zone est coupee pour aujourd'hui", true); bot.ZoneAutorisee = false; }
            for (int m = 0; m < jusqua; m++) FermerMinute(m, executer: false);
            prochaineMinute = jusqua;
        }

        // ------------------------------------------------------------------ marche
        void SurTransaction(Symbol s, Last last)
        {
            lock (verrou)
            {
                if (dernierTick == DateTime.MinValue) premierPrixANoter = true;
                dernierTick = Maintenant();
                dernierPrix = last.Price;
                DateTime t;
                try { t = TimeZoneInfo.ConvertTimeFromUtc(EnUtc(last.Time), ny); }
                catch (Exception e)
                {
                    if (!erreurHeureNotee) { erreurHeureNotee = true; Dire($"ERREUR : heure d'une transaction NQ illisible ({e.Message})", true); }
                    return;
                }
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
                    if (premierPrixANoter) { premierPrixANoter = false; Dire($"flux NQ recu ({dernierPrix:F2}) : le bot voit le marche"); }
                    if (soldeIllisible && (Maintenant() - derniereLectureSolde).TotalSeconds >= 60)
                    {
                        derniereLectureSolde = Maintenant();
                        var lu = SoldeReel();
                        if (lu.HasValue) { soldeIllisible = false; Dire($"solde du compte lu : {lu.Value:F0} $ (le bot utilise maintenant le vrai solde)"); }
                    }
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
                        ReprendreObjetsVivants(true);
                    }
                    if (alerteSilence && (Maintenant() - dernierTick).TotalMinutes < 1)
                    {
                        alerteSilence = false;
                        Dire($"flux NQ revenu ({dernierPrix:F2})");
                    }
                    // aucune transaction NQ depuis le lancement (16 octobre 2026 : bot aveugle toute la seance, sans aucune
                    // alerte) : alerte 3 minutes apres le lancement (des 8 h, le NQ s'echange avant l'ouverture) ou apres
                    // l'ouverture, puis toutes les 15 minutes
                    bool avantOuverture = m < 0 && maintenant.TimeOfDay >= TimeSpan.FromHours(8) && !Calendrier.JourFerme(jour);
                    if (dernierTick == DateTime.MinValue && ((m >= 0 && m <= derniereMinute) || avantOuverture))
                    {
                        var ouverture = TimeZoneInfo.ConvertTimeToUtc(jour.AddMinutes(570), ny);
                        var depuis = m >= 0 && ouverture > demarrageUtc ? ouverture : demarrageUtc;
                        if ((Maintenant() - depuis).TotalMinutes > 3 && (Maintenant() - alerteAveugle).TotalMinutes >= 15)
                        {
                            alerteAveugle = Maintenant();
                            Dire("ALERTE : aucune transaction NQ recue depuis le lancement : le bot ne voit pas le marche et ne peut pas"
                                 + " trader. Verifie que la connexion Rithmic est verte et que le symbole NQ des reglages recoit des prix,"
                                 + " puis relance le bot.", true);
                            ReprendreObjetsVivants(true);
                        }
                    }
                    if (bot.StopPoints > 0 && m >= 0 && m <= derniereMinute && dernierPrix > 0)
                    {
                        var arrets = bot.VerifierStop(dernierPrix, m);
                        foreach (var x in arrets) Dire(x.Texte);
                        if (arrets.Count > 0) SauverEtat();
                    }
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
            // filet de 16 h 30 a 18 h : la firme exige d'etre a plat avant 16 h 59 (New York) ; toute position encore ouverte
            // (ordre de sortie refuse, position prise a la main...) est fermee, quoi que pense le moteur
            if (tod >= TimeSpan.FromMinutes(16 * 60 + 30) && tod < TimeSpan.FromHours(18)
                && (PositionReelle(SymboleMNQ) != 0 || PositionReelle(SymboleMES) != 0))
            {
                ToutFermer("filet de 16 h 30 : position encore ouverte apres la seance (a plat obligatoire avant 16 h 59)");
                return true;
            }
            // vente du RSI(2) de nuit a 9 h 30
            if (bot.RsiNuit != 0 && tod >= TimeSpan.FromMinutes(570) && tod < TimeSpan.FromHours(18))
            {
                foreach (var s in bot.FermerNuit(dernierPrix)) Dire(s.Texte);
                SauverEtat();
            }
            string jt = journeeTrading.ToString("yyyy-MM-dd");
            // taille de la journee (challenge : fin de course), changee seulement a plat (comptes du bot = positions reelles)
            int tj = TailleJournee(journeeTrading);
            if (bot.Taille != tj && bot.ZoneTenue == 0 && bot.RsiNuit == 0)
            {
                int avant = bot.Taille;
                bot.Taille = tj;
                bool finCourse = TailleFin > 0 && tj == TailleFin && tj != Taille;
                Dire($"journee du {jt} : {tj} MNQ par source (avant {avant})"
                     + (finCourse ? $", fin de course du challenge ({RegleCompte.SeancesRestantes(journeeTrading, finChallenge)} seance(s) restante(s))" : ""));
                SauverEtat();
            }
            // objectif du challenge deja atteint au debut de la journee : plus aucun trade sur ce compte
            if (!bot.Arret && RegleCompte.ObjectifAtteint(ObjectifChallenge, SoldeDebutJour()))
            {
                bot.ArreterJournee(dernierPrix, "objectif du challenge atteint");
                Dire($"OBJECTIF DU CHALLENGE ATTEINT (solde {SoldeDebutJour():F0} $, objectif {ObjectifChallenge:F0} $) : le bot ne trade plus sur ce"
                     + " compte. Compte Master : MNQ par source 1, frein 750, plafond du jour 500, objectif 0, date de fin vide, MNQ en fin de challenge 0.");
                SauverEtat();
            }
            // achat du RSI(2) de nuit : de 18 h a 9 h 25, si la seance qui suit existe et que le MES cote
            bool nuit = tod >= TimeSpan.FromHours(18) || tod < TimeSpan.FromMinutes(565);
            bool esVivant = dernierPrixES > 0 && (Maintenant() - dernierTickES).TotalMinutes < 5;
            if (RsiDeNuit && bot.NuitVoulue && bot.RsiNuit == 0 && !bot.Arret && nuit && nuitJournee != jt && !Calendrier.JourFerme(journeeTrading))
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
            // plafond (compte finance), arret a l'objectif (challenge : plafond = objectif + 50 $ - solde de 18 h) et limite de perte
            // du jour : la valeur reelle du compte (si lisible) et l'estimation du bot doivent etre d'accord, 3 secondes de suite,
            // sans ordre envoye dans les 10 dernieres secondes (evite une lecture fausse pendant qu'une position se ferme)
            double cap = RegleCompte.PlafondEffectif(PlafondJour, ObjectifChallenge, SoldeDebutJour());
            if (!bot.Arret && (cap > 0 || LimitePerteJour > 0) && (bot.ZoneTenue != 0 || bot.RsiNuit != 0 || bot.RealiseAPlat != 0))
            {
                double? vr = ValeurJourReelle();
                double ve = ValeurJourEstimee();
                bool plafond = cap > 0 && ve >= cap && (vr == null || vr >= cap);
                bool parObjectif = ObjectifChallenge > 0 && (PlafondJour <= 0 || cap < PlafondJour);
                bool limite = LimitePerteJour > 0 && ve <= -LimitePerteJour && (vr == null || vr <= -LimitePerteJour);
                bool ordreRecent = (Maintenant() - ordreEnAttenteDepuis).TotalSeconds < 10 || (Maintenant() - ordreMESEnAttenteDepuis).TotalSeconds < 10;
                if ((plafond || limite) && !ordreRecent)
                {
                    if (depassementDepuis == DateTime.MinValue) depassementDepuis = Maintenant();
                    else if ((Maintenant() - depassementDepuis).TotalSeconds >= 3)
                    {
                        string v = $"{(vr.HasValue ? $"compte {vr.Value:F0} $, " : "")}estimation {ve:F0} $";
                        string raison = !plafond ? $"limite de perte du jour atteinte ({v})"
                            : parObjectif ? $"OBJECTIF DU CHALLENGE ATTEINT ({v}, solde vise {ObjectifChallenge + RegleCompte.MargeObjectif:F0} $)"
                            : $"plafond du jour atteint ({v})";
                        foreach (var s in bot.ArreterJournee(dernierPrix, raison)) Dire(s.Texte, limite && !plafond);
                        if (plafond && parObjectif)
                            Dire("challenge : si Bulenox confirme la reussite, passe au compte Master avec ses reglages (MNQ par source 1, frein 750,"
                                 + " plafond du jour 500, objectif 0, date de fin vide, MNQ en fin de challenge 0). Sur ce compte, plus aucun trade"
                                 + " tant que le solde de 18 h est a l'objectif.");
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
            public int TailleTenue { get; set; }            // MNQ par source des positions en cours (challenge : fin de course)
            public double SoldeManuel { get; set; }         // dernier solde des reglages deja repris (solde illisible)
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
                               NuitVoulue = bot.NuitVoulue, JourDecisionNuit = bot.JourDecision == default ? null : bot.JourDecision.ToString("yyyy-MM-dd"),
                               TailleTenue = bot.Taille, SoldeManuel = soldeManuelApplique };
            File.WriteAllText(FichierEtat(), JsonSerializer.Serialize(e));
        }

        static double Fini(double v) => double.IsNaN(v) || double.IsInfinity(v) ? 0 : v;      // JSON : pas de NaN

        string EtatTexte() => bot == null ? "" : ModeAPlat ?
            $"Positions voulues : MNQ {bot.PositionMNQ}, MES {bot.PositionMES} (zone {bot.ZoneTenue}{(bot.ZoneSurMES ? " sur MES, frein" : "")},"
            + $" RSI(2) de nuit {(RsiDeNuit ? $"{bot.RsiNuit}{(bot.NuitVoulue ? ", achat de nuit voulu" : "")}" : "decoche")})"
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
            // un jeton ou un numero Telegram n'a jamais d'espace : ceux colles par erreur (ex. apres les deux-points) sont retires
            string jeton = System.Text.RegularExpressions.Regex.Replace(JetonTelegram, "\\s", ""),
                   chat = System.Text.RegularExpressions.Regex.Replace(ChatTelegram, "\\s", "");
            if (jeton.StartsWith("bot", StringComparison.OrdinalIgnoreCase)) jeton = jeton.Substring(3);
            try
            {
                var contenu = new FormUrlEncodedContent(new Dictionary<string, string> { ["chat_id"] = chat, ["text"] = "Bot 3 en 1 : " + texte });
                http.PostAsync($"https://api.telegram.org/bot{jeton}/sendMessage", contenu).ContinueWith(t => NoterTelegram(t, jeton));
            }
            catch (Exception e) { NoterErreurTelegram(e.Message.Replace(jeton, "***"), 0); }
        }

        /// <summary>Resultat d'un envoi Telegram : une erreur est ecrite dans le journal (jamais sur Telegram, jamais le jeton),
        /// une seule fois tant qu'elle ne change pas.</summary>
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
