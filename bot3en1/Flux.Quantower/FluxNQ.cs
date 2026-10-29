using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Linq.Expressions;
using System.Net.Http;
using System.Reflection;
using System.Threading;
using Bot3en1.Flux;
using TradingPlatform.BusinessLayer;

namespace Bot3en1
{
    /// <summary>Bot order flow du NQ (flux/README.md, « Le bot FluxNQ ») :
    /// - lit chaque transaction du NQ (prix, taille, cote agresseur) et le DOM (10 niveaux, une photo par seconde) ;
    /// - construit minutes, footprint, profil de volume, VWAP, delta ; lecture sur Telegram ;
    /// - enregistre tout dans Dossier\flux\AAAA-MM-JJ\ (tape, DOM, minutes, footprint, trades virtuels, ordres passifs) ;
    /// - suit S1, S2, S2b et C1 dans des carnets virtuels ;
    /// - passe des ordres MNQ seulement pour la regle choisie (aucune par defaut).</summary>
    public class FluxNQ : Strategy
    {
        [InputParameter("Compte (ordres MNQ seulement si une regle est choisie plus bas)", 10)] public Account Compte;
        [InputParameter("NQ : contrat du moment, pour lire le flux (tape et DOM), ex. NQZ6", 20)] public Symbol SymboleNQ;
        [InputParameter("MNQ : meme echeance, pour les ordres, ex. MNQZ6", 30)] public Symbol SymboleMNQ;
        [InputParameter("Dossier des donnees (enregistrements dans le sous-dossier flux)", 40)] public string Dossier = @"C:\Bot3en1";
        [InputParameter("Regle qui passe les ordres : 0 = aucune (lecture, enregistrement, carnets virtuels), 1 = S1, 2 = S2, 3 = S2b, 4 = C1. Aucune regle n'a encore franchi la barre fixee (40 trades en direct et t au moins 2,24) - flux/README.md", 50, 0, 4, 1, 0)]
        public int RegleOrdres = 0;
        [InputParameter("MNQ par trade (ordres reels)", 60, 1, 10, 1, 0)] public int Taille = 1;
        [InputParameter("Limite de perte du jour en $ pour les ordres reels (0 = aucune)", 70, 0, 5000, 50, 0)] public double LimitePerteJour = 300;
        [InputParameter("Trades reels au plus par jour", 80, 1, 20, 1, 0)] public int MaxTradesJour = 4;
        [InputParameter("Lecture du flux sur Telegram toutes les X minutes (0 = jamais)", 90, 0, 120, 5, 0)] public int PeriodeLecture = 30;
        [InputParameter("Gros lot : transaction d'au moins X contrats NQ (lecture)", 95, 1, 500, 1, 0)] public int GrosLot = 20;
        [InputParameter("Telegram : jeton du bot (facultatif)", 100)] public string JetonTelegram = "";
        [InputParameter("Telegram : numero de conversation (facultatif)", 110)] public string ChatTelegram = "";

        const string Version = "29 octobre 2026 (S1, S2, S2b, C1 ; enregistrement du tape et du DOM)";
        const double TICK = 0.25;
        static readonly HttpClient http = new HttpClient { Timeout = TimeSpan.FromSeconds(20) };
        static readonly CultureInfo inv = CultureInfo.InvariantCulture;

        MoteurFlux moteur;
        TimeZoneInfo ny;
        Timer horloge;
        readonly object verrou = new object();
        DateTime jour = DateTime.MinValue;
        bool seanceFinie = true, jouable;
        int prochaineMinute;
        BarreFlux[] barres = new BarreFlux[MoteurFlux.N];
        double dernierPrix;
        DateTime dernierTick = DateTime.MinValue, derniereLecture = DateTime.MinValue, dernierePhoto = DateTime.MinValue;
        bool alerteSilence;
        string derniereErreurTelegram = "";
        // DOM
        LecteurDom lecteurDom;
        PhotoDom photo;
        Delegate abonnementL2;
        long majL2;
        // enregistrement
        string dossierJour;
        StreamWriter wTape, wDom, wMinutes, wFootprint, wVirtuel, wPassif, wReel;
        // lecture : gros lots des 30 dernieres minutes (heure UTC, prix, taille, sens)
        readonly List<(DateTime t, double prix, double taille, int sens)> gros = new List<(DateTime, double, double, int)>();
        // ordres passifs a verifier : regle, sens, limite, fin de l'attente, minute du signal
        readonly List<Passif> passifs = new List<Passif>();
        // ordres reels
        int? voulu;                       // position MNQ voulue par le bot (null : le bot ne gere rien)
        Reel reel;
        DateTime ordreEnvoye = DateTime.MinValue, alerteEtrangere = DateTime.MinValue;
        double realiseJour;
        int tradesJour;
        bool arretJour;

        class Passif { public string Regle; public int Sens, Signal; public double Limite; public DateTime Fin; public bool Rempli; public DateTime Quand; }
        class Reel { public string Regle; public int Sens, FinMinute, Signal; public double Entree, Stop, Objectif; }

        public FluxNQ() : base()
        {
            Name = "FluxNQ order flow (tape DOM footprint)";     // sans deux-points ni virgule, comme les strategies qui marchent
            Description = "Lit le tape, le DOM et le footprint du NQ et enregistre tout. Suit S1 S2 S2b et C1 en virtuel. Ordres MNQ seulement pour la regle choisie.";
        }

        // ------------------------------------------------------------------ demarrage et arret
        protected override void OnRun()
        {
            try
            {
                if (SymboleNQ == null) throw new Exception("aucun symbole NQ choisi : ouvre les reglages de FluxNQ et choisis NQZ6 dans « NQ : contrat du moment »");
                if (RegleOrdres > 0 && (Compte == null || SymboleMNQ == null))
                    throw new Exception("une regle passe les ordres : choisis aussi le compte et le symbole MNQ");
                ny = TrouverFuseau();
                Directory.CreateDirectory(Path.Combine(Dossier, "flux"));
                SymboleNQ = Vivant(SymboleNQ);
                if (SymboleMNQ != null) SymboleMNQ = Vivant(SymboleMNQ);
                Compte = CompteVivant(Compte);
                moteur = new MoteurFlux();
                lock (verrou)
                {
                    var maintenant = HeureNY();
                    VerifierEcheance(maintenant.Date);
                    PreparerSeance(maintenant);
                }
                SymboleNQ.NewLast += SurTransaction;
                AbonnerDom();
                horloge = new Timer(_ => Tic(), null, 250, 250);
                string regle = RegleOrdres == 0 ? "AUCUNE (lecture, enregistrement et carnets virtuels seulement)" : $"{NomRegle(RegleOrdres)} sur {Compte?.Name}, {Taille} MNQ, limite du jour {LimitePerteJour:F0} $, {MaxTradesJour} trades au plus";
                Dire($"demarre (version du {Version}). Regle qui passe les ordres : {regle}. Enregistrement dans {Path.Combine(Dossier, "flux")}.");
                if (RegleOrdres > 0)
                    Dire($"ATTENTION : {NomRegle(RegleOrdres)} n'a pas encore franchi la barre fixee pour le reel (40 trades en direct, gain moyen > 0, t >= 2,24). Ce sont des ordres d'essai.", true);
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
            DesabonnerDom();
            lock (verrou)
            {
                try
                {
                    if (voulu != null && SymboleMNQ != null && PositionReelle() != 0)
                    {
                        voulu = 0;
                        EnvoyerOrdre(-PositionReelle(), "arret du bot : position fermee");
                    }
                }
                catch (Exception e) { Dire($"ERREUR en fermant la position a l'arret : {e.Message}", true); }
                FermerFichiers(false);
            }
            Dire("arrete.");
        }

        static string NomRegle(int r) => r switch { 1 => "S1", 2 => "S2", 3 => "S2b", 4 => "C1", _ => "aucune" };

        static TimeZoneInfo TrouverFuseau()
        {
            foreach (var id in new[] { "Eastern Standard Time", "America/New_York" })
                try { return TimeZoneInfo.FindSystemTimeZoneById(id); } catch { }
            throw new Exception("fuseau horaire de New York introuvable");
        }

        static DateTime Maintenant() => Core.Instance.TimeUtils.DateTimeUtcNow;
        DateTime HeureNY() => TimeZoneInfo.ConvertTimeFromUtc(Maintenant(), ny);
        static DateTime EnUtc(DateTime d) => d.Kind == DateTimeKind.Local ? d.ToUniversalTime()
            : d.Kind == DateTimeKind.Unspecified ? DateTime.SpecifyKind(d, DateTimeKind.Utc) : d;
        static int Minute(DateTime nyt) => nyt.Hour * 60 + nyt.Minute - 570;

        void VerifierEcheance(DateTime j)
        {
            string attendu = Calendrier.Contrat(j), court = $"{attendu[0]}{attendu[^1]}";
            foreach (var s in new[] { SymboleNQ, SymboleMNQ })
                if (s != null && !(s.Name ?? "").ToUpperInvariant().Contains(court) && !(s.Name ?? "").ToUpperInvariant().Contains(attendu))
                    Dire($"ATTENTION : le symbole {s.Name} ne semble pas etre l'echeance du jour ({court}). Change-le dans les reglages.", true);
        }

        static T Vivant<T>(T objet) where T : class
        {
            if (objet == null) return null;
            try
            {
                var info = objet.GetType().GetMethod("CreateInfo", Type.EmptyTypes)?.Invoke(objet, null);
                if (info == null) return objet;
                foreach (var m in Core.Instance.GetType().GetMethods())
                {
                    if (m.Name != "GetSymbol") continue;
                    var ps = m.GetParameters();
                    if (ps.Length == 0 || !ps[0].ParameterType.IsInstanceOfType(info)) continue;
                    var args = new object[ps.Length];
                    args[0] = info;
                    for (int i = 1; i < ps.Length; i++)
                        args[i] = ps[i].HasDefaultValue ? ps[i].DefaultValue : ps[i].ParameterType.IsValueType ? Activator.CreateInstance(ps[i].ParameterType) : null;
                    if (m.Invoke(Core.Instance, args) is T vivant) return vivant;
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

        // ------------------------------------------------------------------ seance
        string DossierDu(DateTime j) => Path.Combine(Dossier, "flux", j.ToString("yyyy-MM-dd"));

        /// <summary>Seances precedentes (5) depuis les enregistrements, sinon depuis l'historique Rithmic ; seance du jour
        /// rattrapee si le bot demarre apres 9 h 30.</summary>
        void PreparerSeance(DateTime maintenant)
        {
            jour = maintenant.Date;
            barres = new BarreFlux[MoteurFlux.N];
            prochaineMinute = 0;
            realiseJour = 0; tradesJour = 0; arretJour = false;
            passifs.Clear();
            seanceFinie = Calendrier.JourFerme(jour) || Calendrier.JourCourt(jour) || maintenant.TimeOfDay >= TimeSpan.FromHours(16);
            if (seanceFinie) return;
            var prec = new List<BarreFlux[]>();
            Dictionary<long, double> profilVeille = null;
            DateTime veille = DateTime.MinValue;
            var d = jour.AddDays(-1);
            for (int essais = 0; prec.Count < 5 && essais < 15; essais++, d = d.AddDays(-1))
            {
                if (Calendrier.JourFerme(d) || Calendrier.JourCourt(d)) continue;
                var (b, profil) = ChargerSeance(d);
                if (b == null) continue;
                if (prec.Count == 0) { profilVeille = profil; veille = d; }
                prec.Insert(0, b);
            }
            // pas de trade le jour d'un changement de contrat (comme l'historique)
            jouable = prec.Count >= 5 && veille != DateTime.MinValue && Calendrier.Contrat(veille) == Calendrier.Contrat(jour);
            moteur.DebutSeance(jour, prec, profilVeille, jouable);
            OuvrirFichiers();
            Dire($"seance du {jour:yyyy-MM-dd} : {prec.Count} seance(s) precedente(s) chargee(s)"
                 + (jouable ? ", regles actives" : " : PAS DE TRADE aujourd'hui (seances precedentes incompletes ou changement de contrat), lecture et enregistrement seulement"));
            int m = Minute(maintenant);
            if (m > 0) Rattraper(Math.Min(m, MoteurFlux.N));
        }

        /// <summary>Minutes et profil d'une seance passee : fichiers enregistres, sinon transactions de l'historique Rithmic
        /// (enregistrees ensuite pour la prochaine fois).</summary>
        (BarreFlux[] barres, Dictionary<long, double> profil) ChargerSeance(DateTime d)
        {
            string dos = DossierDu(d), fm = Path.Combine(dos, "minutes.csv"), ff = Path.Combine(dos, "footprint.csv");
            try
            {
                if (File.Exists(fm) && File.Exists(ff))
                {
                    var b = new BarreFlux[MoteurFlux.N];
                    foreach (var l in File.ReadLines(fm).Skip(1))
                    {
                        var c = l.Split(',');
                        int t = int.Parse(c[1], inv);
                        if (t < 0 || t >= MoteurFlux.N) continue;
                        b[t] = new BarreFlux { O = D(c[2]), H = D(c[3]), L = D(c[4]), C = D(c[5]), Achats = D(c[7]), Ventes = D(c[8]), Presente = D(c[6]) > 0,
                                               ParPrix = new Dictionary<long, double[]>() };
                    }
                    var profil = new Dictionary<long, double>();
                    foreach (var l in File.ReadLines(ff).Skip(1))
                    {
                        var c = l.Split(',');
                        int t = Minute(DateTime.ParseExact(c[0], "yyyy-MM-dd HH:mm", inv));
                        long k = (long)Math.Round(D(c[1]) / TICK);
                        double a = D(c[2]), v = D(c[3]);
                        if (t >= 0 && t < MoteurFlux.N && b[t] != null) b[t].ParPrix[k] = new[] { a, v };
                        profil[k] = (profil.TryGetValue(k, out var x) ? x : 0) + a + v;
                    }
                    if (b.Count(x => x != null) >= MoteurFlux.N - 20)
                    {
                        Completer(b);
                        return (b, profil);
                    }
                }
                // historique Rithmic : transactions de 9 h 30 a 16 h
                var debutUtc = TimeZoneInfo.ConvertTimeToUtc(d.AddMinutes(570), ny);
                var finUtc = TimeZoneInfo.ConvertTimeToUtc(d.AddMinutes(960), ny);
                var h = SymboleNQ.GetHistory(new HistoryRequestParameters
                {
                    Symbol = SymboleNQ, FromTime = debutUtc, ToTime = finUtc,
                    Aggregation = new HistoryAggregationTick(HistoryType.Last)
                });
                var bb = new BarreFlux[MoteurFlux.N];
                int n = 0;
                for (int i = 0; i < h.Count; i++)
                    if (h[i, SeekOriginHistory.Begin] is HistoryItemLast tk)
                    {
                        var tn = TimeZoneInfo.ConvertTimeFromUtc(EnUtc(tk.TimeLeft), ny);
                        if (tn.Date != d) continue;
                        Ajouter(bb, Minute(tn), tk.Price, tk.Volume, tk.AggressorFlag);
                        n++;
                    }
                if (n == 0 || bb.Count(x => x != null) < MoteurFlux.N - 20) return (null, null);
                Directory.CreateDirectory(dos);
                using (var w1 = new StreamWriter(fm, false)) EcrireMinutes(w1, d, bb, true);
                using (var w2 = new StreamWriter(ff, false)) EcrireFootprint(w2, d, bb, true);
                Completer(bb);
                var pr = new Dictionary<long, double>();
                foreach (var x in bb)
                    if (x?.ParPrix != null) foreach (var kv in x.ParPrix) pr[kv.Key] = (pr.TryGetValue(kv.Key, out var y) ? y : 0) + kv.Value[0] + kv.Value[1];
                return (bb, pr);
            }
            catch (Exception e)
            {
                Dire($"seance du {d:yyyy-MM-dd} illisible ({e.Message})", true);
                return (null, null);
            }
        }

        static double D(string x) => string.IsNullOrEmpty(x) ? double.NaN : double.Parse(x, inv);

        /// <summary>Minutes sans transaction recopiees a plat (volume nul), footprint calcule.</summary>
        static void Completer(BarreFlux[] b)
        {
            double p = b.FirstOrDefault(x => x != null)?.O ?? 0;
            for (int t = 0; t < b.Length; t++)
            {
                if (b[t] == null) b[t] = new BarreFlux { O = p, H = p, L = p, C = p, VentesBas2 = 0, AchatsHaut2 = 0 };
                else b[t].CalculerFootprint();
                if (b[t].ParPrix == null || b[t].ParPrix.Count == 0) { b[t].VentesBas2 = 0; b[t].AchatsHaut2 = 0; }
                p = b[t].C;
            }
        }

        static void Ajouter(BarreFlux[] b, int m, double prix, double taille, AggressorFlag cote)
        {
            if (m < 0 || m >= b.Length) return;
            var x = b[m];
            if (x == null) b[m] = x = new BarreFlux { O = prix, H = prix, L = prix, C = prix, Presente = true, ParPrix = new Dictionary<long, double[]>() };
            x.H = Math.Max(x.H, prix); x.L = Math.Min(x.L, prix); x.C = prix;
            long k = (long)Math.Round(prix / TICK);
            if (!x.ParPrix.TryGetValue(k, out var pp)) x.ParPrix[k] = pp = new double[2];
            if (cote == AggressorFlag.Buy) { x.Achats += taille; pp[0] += taille; }
            else if (cote == AggressorFlag.Sell) { x.Ventes += taille; pp[1] += taille; }
        }

        /// <summary>Demarrage apres 9 h 30 : transactions de la seance rejouees (aucun ordre reel pour un signal passe).</summary>
        void Rattraper(int jusqua)
        {
            try
            {
                var h = SymboleNQ.GetHistory(new HistoryRequestParameters
                {
                    Symbol = SymboleNQ, FromTime = TimeZoneInfo.ConvertTimeToUtc(jour.AddMinutes(570), ny),
                    ToTime = TimeZoneInfo.ConvertTimeToUtc(jour.AddMinutes(570 + jusqua), ny),
                    Aggregation = new HistoryAggregationTick(HistoryType.Last)
                });
                for (int i = 0; i < h.Count; i++)
                    if (h[i, SeekOriginHistory.Begin] is HistoryItemLast tk)
                    {
                        var tu = EnUtc(tk.TimeLeft);
                        var tn = TimeZoneInfo.ConvertTimeFromUtc(tu, ny);
                        int m = Minute(tn);
                        if (tn.Date != jour || m < 0 || m >= jusqua) continue;
                        Ajouter(barres, m, tk.Price, tk.Volume, tk.AggressorFlag);
                        EcrireTape(tu, tk.Price, tk.Volume, tk.AggressorFlag);
                    }
            }
            catch (Exception e) { Dire($"rattrapage de la seance impossible ({e.Message}) : les minutes passees sont a plat", true); }
            for (int m = 0; m < jusqua; m++) FermerMinute(m, executer: false);
            prochaineMinute = jusqua;
            Dire($"demarrage en cours de seance : {jusqua} minute(s) rattrapee(s) (aucun ordre reel pour un signal passe)");
        }

        // ------------------------------------------------------------------ fichiers
        void OuvrirFichiers()
        {
            FermerFichiers(false);
            dossierJour = DossierDu(jour);
            Directory.CreateDirectory(dossierJour);
            StreamWriter W(string nom, string entete, bool ajout)
            {
                string f = Path.Combine(dossierJour, nom);
                bool existe = ajout && File.Exists(f) && new FileInfo(f).Length > 0;
                var w = new StreamWriter(f, ajout) { AutoFlush = false };
                if (!existe) w.WriteLine(entete);
                return w;
            }
            // minutes, footprint et tape sont reecrits (rattrapage depuis 9 h 30) ; DOM et journaux sont completes
            wTape = W("tape.csv", "t_utc,prix,taille,cote", false);
            wMinutes = W("minutes.csv", "jour,minute,o,h,l,c,v,achats,ventes,sans_cote,contrat", false);
            wFootprint = W("footprint.csv", "m,prix,achat,vente", false);
            var entDom = "t_utc," + string.Join(",", Enumerable.Range(1, 10).Select(i => $"pa{i},qa{i}")) + "," + string.Join(",", Enumerable.Range(1, 10).Select(i => $"pv{i},qv{i}"));
            wDom = W("dom.csv", entDom, true);
            wVirtuel = W("virtuel.csv", "regle,jour,signal,entree_minute,sens,entree,stop,objectif,R,sortie_minute,sortie,motif,net,raison", true);
            wPassif = W("passif.csv", "regle,jour,signal,sens,limite,rempli,seconde", true);
            wReel = W("reel.csv", "regle,jour,signal,sens,taille,entree_estimee,stop,objectif,sortie_estimee,motif,gain_estime_dollars", true);
        }

        void FermerFichiers(bool compresser)
        {
            foreach (var w in new[] { wTape, wDom, wMinutes, wFootprint, wVirtuel, wPassif, wReel })
                try { w?.Flush(); w?.Dispose(); } catch { }
            wTape = wDom = wMinutes = wFootprint = wVirtuel = wPassif = wReel = null;
            if (!compresser || dossierJour == null) return;
            foreach (var nom in new[] { "tape.csv", "dom.csv" })
            {
                string f = Path.Combine(dossierJour, nom);
                try
                {
                    if (!File.Exists(f)) continue;
                    using (var src = File.OpenRead(f))
                    using (var dst = new GZipStream(File.Create(f + ".gz"), CompressionLevel.Optimal))
                        src.CopyTo(dst);
                    File.Delete(f);
                }
                catch (Exception e) { Dire($"compression de {nom} impossible ({e.Message})", true); }
            }
        }

        void EcrireTape(DateTime tu, double prix, double taille, AggressorFlag cote)
        {
            int c = cote == AggressorFlag.Buy ? 1 : cote == AggressorFlag.Sell ? -1 : 0;
            wTape?.WriteLine($"{tu:yyyy-MM-dd HH:mm:ss.fff},{prix.ToString("R", inv)},{taille.ToString("R", inv)},{c}");
        }

        static void EcrireMinutes(StreamWriter w, DateTime d, BarreFlux[] b, bool entete, int seule = -1)
        {
            if (entete) w.WriteLine("jour,minute,o,h,l,c,v,achats,ventes,sans_cote,contrat");
            for (int t = 0; t < b.Length; t++)
            {
                if (seule >= 0 && t != seule) continue;
                var x = b[t];
                if (x == null || !x.Presente) continue;
                double tot = x.ParPrix?.Values.Sum(p => p[0] + p[1]) ?? x.Achats + x.Ventes;
                w.WriteLine(string.Join(",", d.ToString("yyyy-MM-dd"), t.ToString(inv), x.O.ToString("R", inv), x.H.ToString("R", inv),
                    x.L.ToString("R", inv), x.C.ToString("R", inv), (x.Achats + x.Ventes).ToString("R", inv), x.Achats.ToString("R", inv),
                    x.Ventes.ToString("R", inv), "0", Calendrier.Contrat(d)));
            }
        }

        static void EcrireFootprint(StreamWriter w, DateTime d, BarreFlux[] b, bool entete, int seule = -1)
        {
            if (entete) w.WriteLine("m,prix,achat,vente");
            for (int t = 0; t < b.Length; t++)
            {
                if (seule >= 0 && t != seule) continue;
                var x = b[t];
                if (x?.ParPrix == null) continue;
                string m = d.AddMinutes(570 + t).ToString("yyyy-MM-dd HH:mm");
                foreach (var kv in x.ParPrix.OrderBy(k => k.Key))
                    w.WriteLine($"{m},{(kv.Key * TICK).ToString("R", inv)},{kv.Value[0].ToString("R", inv)},{kv.Value[1].ToString("R", inv)}");
            }
        }

        // ------------------------------------------------------------------ DOM (par reflexion : rien ne depend des noms exacts a la compilation)
        void AbonnerDom()
        {
            lecteurDom = new LecteurDom();
            if (!lecteurDom.Init(SymboleNQ)) Dire($"DOM indisponible ({lecteurDom.Erreur}) : C1 ne pourra pas trader, le reste fonctionne", true);
            try
            {
                var ev = SymboleNQ.GetType().GetEvent("NewLevel2");
                if (ev == null) { Dire("abonnement au DOM : evenement NewLevel2 absent (photo du carnet lue quand meme)", true); return; }
                var ps = ev.EventHandlerType.GetMethod("Invoke").GetParameters().Select(p => Expression.Parameter(p.ParameterType)).ToArray();
                var corps = Expression.Call(Expression.Constant(this), typeof(FluxNQ).GetMethod(nameof(SurNiveau2), BindingFlags.Instance | BindingFlags.NonPublic));
                abonnementL2 = Expression.Lambda(ev.EventHandlerType, corps, ps).Compile();
                ev.AddEventHandler(SymboleNQ, abonnementL2);
            }
            catch (Exception e) { Dire($"abonnement au DOM impossible ({e.Message})", true); }
        }

        void DesabonnerDom()
        {
            try { if (abonnementL2 != null) SymboleNQ?.GetType().GetEvent("NewLevel2")?.RemoveEventHandler(SymboleNQ, abonnementL2); } catch { }
        }

        void SurNiveau2() => Interlocked.Increment(ref majL2);

        void PhotoDuCarnet(DateTime tu)
        {
            if (lecteurDom == null || !lecteurDom.Pret) return;
            var p = lecteurDom.Lire();
            if (p == null) return;
            photo = p;
            var cols = new List<string> { tu.ToString("yyyy-MM-dd HH:mm:ss.fff") };
            for (int i = 0; i < 10; i++) cols.Add(i < p.PrixAchat.Length ? $"{p.PrixAchat[i].ToString("R", inv)},{p.QteAchat[i].ToString("R", inv)}" : ",");
            for (int i = 0; i < 10; i++) cols.Add(i < p.PrixVente.Length ? $"{p.PrixVente[i].ToString("R", inv)},{p.QteVente[i].ToString("R", inv)}" : ",");
            wDom?.WriteLine(string.Join(",", cols));
        }

        // ------------------------------------------------------------------ marche
        void SurTransaction(Symbol s, Last last)
        {
            lock (verrou)
            {
                try
                {
                    var tu = EnUtc(last.Time);
                    var tn = TimeZoneInfo.ConvertTimeFromUtc(tu, ny);
                    dernierTick = Maintenant();
                    dernierPrix = last.Price;
                    if (seanceFinie || tn.Date != jour) return;
                    int m = Minute(tn);
                    if (m < 0 || m >= MoteurFlux.N) return;
                    EcrireTape(tu, last.Price, last.Size, last.AggressorFlag);
                    if (m >= prochaineMinute) Ajouter(barres, m, last.Price, last.Size, last.AggressorFlag);
                    if (last.Size >= GrosLot)
                        gros.Add((tu, last.Price, last.Size, last.AggressorFlag == AggressorFlag.Buy ? 1 : last.AggressorFlag == AggressorFlag.Sell ? -1 : 0));
                    // ordres passifs : rempli si une transaction passe au moins un tick au-dela de la limite
                    foreach (var p in passifs)
                        if (!p.Rempli && tu <= p.Fin && (p.Sens > 0 ? last.Price <= p.Limite - TICK : last.Price >= p.Limite + TICK))
                        {
                            p.Rempli = true;
                            p.Quand = tu;
                        }
                    // ordres reels : stop et objectif verifies a chaque transaction
                    if (reel != null)
                    {
                        if (reel.Sens > 0 ? last.Price <= reel.Stop : last.Price >= reel.Stop) FermerReel("stop", last.Price);
                        else if (reel.Sens > 0 ? last.Price >= reel.Objectif + TICK : last.Price <= reel.Objectif - TICK) FermerReel("objectif", reel.Objectif);
                    }
                }
                catch (Exception e) { Dire($"ERREUR sur une transaction : {e.Message}", true); }
            }
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
                        FermerFichiers(true);
                        VerifierEcheance(maintenant.Date);
                        PreparerSeance(maintenant);
                    }
                    if (File.Exists(Path.Combine(Dossier, "STOP")))
                    {
                        if (!arretJour) Dire("fichier STOP present : plus aucun ordre reel, position fermee", true);
                        arretJour = true;
                        if (reel != null) FermerReel("fichier STOP", dernierPrix);
                    }
                    // filet : position du bot encore ouverte apres 16 h 30 (a plat obligatoire avant 16 h 59)
                    if (voulu != null && voulu != 0 && maintenant.TimeOfDay >= TimeSpan.FromMinutes(990) && reel == null) voulu = 0;
                    Aligner();
                    if (seanceFinie) return;
                    var tu = Maintenant();
                    int m = Minute(maintenant);
                    if (m >= 0 && m < MoteurFlux.N && (tu - dernierePhoto).TotalMilliseconds >= 1000)
                    {
                        dernierePhoto = tu;
                        PhotoDuCarnet(tu);
                    }
                    // une minute est fermee quand l'horloge a passe la minute suivante (+2 s pour les dernieres transactions)
                    while (prochaineMinute < MoteurFlux.N && maintenant >= jour.AddMinutes(570 + prochaineMinute + 1).AddSeconds(2))
                    {
                        FermerMinute(prochaineMinute, executer: true);
                        prochaineMinute++;
                    }
                    if (prochaineMinute >= MoteurFlux.N) { FinDeSeance(); return; }
                    if (m >= 0 && dernierTick != DateTime.MinValue && (Maintenant() - dernierTick).TotalMinutes > 3 && !alerteSilence)
                    {
                        alerteSilence = true;
                        Dire("ALERTE : aucune transaction NQ depuis 3 minutes (connexion Rithmic ?)", true);
                    }
                    if (alerteSilence && (Maintenant() - dernierTick).TotalMinutes < 1) { alerteSilence = false; Dire($"flux NQ revenu ({dernierPrix:F2})"); }
                }
            }
            catch (Exception e) { Dire($"ERREUR : {e.Message}", true); }
        }

        void FermerMinute(int m, bool executer)
        {
            var x = barres[m];
            if (x != null) x.CalculerFootprint();
            var dom = executer ? photo : null;
            var evs = moteur.FermerMinute(m, x, dom);
            if (x != null && x.Presente)
            {
                EcrireMinutes(wMinutes, jour, barres, false, m);
                EcrireFootprint(wFootprint, jour, barres, false, m);
            }
            foreach (var e in evs)
            {
                var tr = e.Trade;
                if (e.Sortie)
                    wVirtuel?.WriteLine(string.Join(",", tr.Regle.Nom, jour.ToString("yyyy-MM-dd"), tr.Signal, tr.EntreeMinute, tr.Sens,
                        tr.Entree.ToString("R", inv), tr.Stop.ToString("R", inv), tr.Objectif.ToString("R", inv), tr.R.ToString("R", inv),
                        tr.SortieMinute, tr.Sortie.ToString("R", inv), tr.Motif, tr.Net.ToString("R", inv), "\"" + tr.Raison.Replace("\"", "'") + "\""));
                if (!executer) continue;
                Dire(e.Texte + (e.Signal ? " [virtuel]" : ""));
                if (e.Signal)
                {
                    // ordre passif equivalent : limite au meilleur prix acheteur (achat) ou vendeur (vente), 60 secondes
                    double lim = tr.Sens > 0 ? (photo != null && photo.PrixAchat.Length > 0 ? photo.PrixAchat[0] : dernierPrix - TICK)
                                             : (photo != null && photo.PrixVente.Length > 0 ? photo.PrixVente[0] : dernierPrix + TICK);
                    passifs.Add(new Passif { Regle = tr.Regle.Nom, Sens = tr.Sens, Signal = tr.Signal, Limite = lim, Fin = Maintenant().AddSeconds(60) });
                    if (RegleOrdres > 0 && tr.Regle.Nom == NomRegle(RegleOrdres)) OuvrirReel(tr);
                }
            }
            // passifs dont l'attente est finie : journal
            foreach (var p in passifs.Where(p => Maintenant() > p.Fin).ToList())
            {
                wPassif?.WriteLine(string.Join(",", p.Regle, jour.ToString("yyyy-MM-dd"), p.Signal, p.Sens, p.Limite.ToString("R", inv), p.Rempli ? 1 : 0,
                    p.Rempli ? (p.Quand - (p.Fin.AddSeconds(-60))).TotalSeconds.ToString("0.0", inv) : ""));
                passifs.Remove(p);
            }
            if (executer)
            {
                if (reel != null && (m >= reel.FinMinute || m >= MoteurFlux.N - 2)) FermerReel(m >= reel.FinMinute ? "temps" : "fin de seance", dernierPrix);
                foreach (var w in new[] { wTape, wDom, wMinutes, wFootprint, wVirtuel, wPassif, wReel }) try { w?.Flush(); } catch { }
                if (PeriodeLecture > 0 && m >= 29 && (m + 1) % PeriodeLecture == 0) Dire(Lecture(m));
            }
        }

        void FinDeSeance()
        {
            if (seanceFinie) return;
            seanceFinie = true;
            if (reel != null) FermerReel("fin de seance", dernierPrix);
            var t = moteur.Trades.Where(x => x.SortieMinute >= 0).ToList();
            string res = string.Join(" ; ", moteur.Regles.Select(r =>
            {
                var tr = t.Where(x => x.Regle == r).ToList();
                return $"{r.Nom} {tr.Count} trade(s) {tr.Sum(x => x.Net):+0.0;-0.0} pt";
            }));
            Dire($"seance du {jour:yyyy-MM-dd} terminee. Carnets virtuels : {res}. Ordres reels : {tradesJour} trade(s), {realiseJour:+0;-0} $ estimes. "
                 + $"Enregistrements : {dossierJour}");
            FermerFichiers(true);
        }

        // ------------------------------------------------------------------ lecture
        string Lecture(int m)
        {
            var x = moteur.Barre(m);
            if (x == null) return "lecture : pas de donnees";
            double vw = moteur.Vwap(m), s = moteur.SigmaV(m);
            var (q10, _, _, q90) = moteur.Seuils;
            var (pdh, pdl, poc, val, vah) = moteur.Veille;
            string profilJour = "";
            if (moteur.ProfilSeance.Count > 0)
            {
                var (p, l, h) = MoteurFlux.ZoneValeur(moteur.ProfilSeance);
                profilJour = $"profil du jour POC {p:F2} (zone de valeur {l:F2} - {h:F2})";
            }
            var limite = Maintenant().AddMinutes(-30);
            gros.RemoveAll(g => g.t < limite);
            string lots = gros.Count == 0 ? $"aucun lot de {GrosLot}+ contrats en 30 min"
                : $"{gros.Count} lot(s) de {GrosLot}+ en 30 min (achats {gros.Where(g => g.sens > 0).Sum(g => g.taille):0}, ventes {gros.Where(g => g.sens < 0).Sum(g => g.taille):0}), le plus gros {gros.OrderByDescending(g => g.taille).First().taille:0} a {gros.OrderByDescending(g => g.taille).First().prix:F2}";
            string carnet = photo == null || photo.Vide ? "carnet indisponible"
                : $"carnet 10 niveaux : {photo.SommeAchat:0} a l'achat / {photo.SommeVente:0} a la vente (ratio {photo.SommeAchat / Math.Max(1, photo.SommeVente):0.00}), plus grosse offre {Max(photo.QteAchat, photo.PrixAchat)} a l'achat, {Max(photo.QteVente, photo.PrixVente)} a la vente";
            string virt = string.Join(", ", moteur.Regles.Select(r => $"{r.Nom} {moteur.Trades.Where(t => t.Regle == r && t.SortieMinute >= 0).Sum(t => t.Net):+0;-0} pt"));
            return $"lecture de {jour.AddMinutes(570 + m + 1):HH:mm} (New York) : NQ {x.C:F2}, VWAP {vw:F2} ({(x.C >= vw ? "au-dessus" : "en dessous")}, bandes {vw - s:F2} / {vw + s:F2}) ; "
                   + $"delta 30 min {moteur.D30(m):+0;-0}, CVD du jour {moteur.Cvd(m):+0;-0}, desequilibre de la minute {moteur.Desequilibre(m):+0.00;-0.00} (seuils {q10:+0.00;-0.00} / {q90:+0.00;-0.00}) ; "
                   + $"{profilJour} ; veille : haut {pdh:F2}, bas {pdl:F2}, POC {poc:F2}, zone de valeur {val:F2} - {vah:F2} ; {lots} ; {carnet} ; "
                   + $"carnets virtuels du jour : {virt}{(RegleOrdres > 0 ? $" ; ordres reels : {tradesJour} trade(s), {realiseJour:+0;-0} $" : "")}";
        }

        static string Max(double[] q, double[] p)
        {
            if (q.Length == 0) return "-";
            int i = Array.IndexOf(q, q.Max());
            return $"{q[i]:0} a {p[i]:F2}";
        }

        // ------------------------------------------------------------------ ordres reels
        int PositionReelle()
        {
            int q = 0;
            foreach (var p in Core.Instance.Positions)
                if (p.Account == Compte && p.Symbol == SymboleMNQ)
                    q += (p.Side == Side.Buy ? 1 : -1) * (int)Math.Round(p.Quantity);
            return q;
        }

        void OuvrirReel(TradeFlux tr)
        {
            string refus = arretJour ? "limite du jour atteinte ou fichier STOP"
                : tradesJour >= MaxTradesJour ? $"{MaxTradesJour} trades reels deja pris aujourd'hui"
                : reel != null || voulu != null ? "un trade reel est deja en cours"
                : PositionReelle() != 0 ? "une position MNQ que le bot n'a pas ouverte existe sur ce compte (bot 3 en 1 ou position a la main ?)"
                : dernierPrix <= 0 ? "aucun prix recu" : null;
            if (refus != null) { Dire($"{tr.Regle.Nom} : pas d'ordre reel ({refus})", refus.Contains("n'a pas ouverte")); return; }
            var r = tr.Regle;
            double ent = dernierPrix + tr.Sens * TICK;
            double st = tr.Sens > 0 ? Math.Floor(Math.Min(tr.StopStructure, ent - r.StopMin) / TICK) * TICK
                                    : Math.Ceiling(Math.Max(tr.StopStructure, ent + r.StopMin) / TICK) * TICK;
            double R = Math.Abs(ent - st);
            if (R > 0.0012 * ent) { Dire($"{r.Nom} : pas d'ordre reel (risque de {R:F2} points, au-dela de 0,12 % du prix)"); return; }
            double ob = ent + tr.Sens * r.Objectif * R;
            ob = tr.Sens > 0 ? Math.Ceiling(ob / TICK) * TICK : Math.Floor(ob / TICK) * TICK;
            reel = new Reel { Regle = r.Nom, Sens = tr.Sens, Entree = ent, Stop = st, Objectif = ob, Signal = tr.Signal,
                              FinMinute = Math.Min(tr.Signal + r.Duree, MoteurFlux.N - 2) };
            tradesJour++;
            voulu = tr.Sens * Taille;
            Dire($"{r.Nom} : ORDRE REEL {(tr.Sens > 0 ? "achat" : "vente")} {Taille} MNQ vers {ent:F2}, stop {st:F2} ({R * 2 * Taille:F0} $), objectif {ob:F2}");
            Aligner();
        }

        void FermerReel(string motif, double prix)
        {
            if (reel == null) return;
            double gain = reel.Sens * (prix - reel.Entree) * 2 * Taille - 2.0 * Taille;
            realiseJour += gain;
            wReel?.WriteLine(string.Join(",", reel.Regle, jour.ToString("yyyy-MM-dd"), reel.Signal, reel.Sens, Taille, reel.Entree.ToString("R", inv),
                reel.Stop.ToString("R", inv), reel.Objectif.ToString("R", inv), prix.ToString("R", inv), motif, gain.ToString("0.00", inv)));
            Dire($"{reel.Regle} : SORTIE REELLE ({motif}) vers {prix:F2}, {gain:+0;-0} $ estimes ; jour {realiseJour:+0;-0} $");
            reel = null;
            voulu = 0;
            if (LimitePerteJour > 0 && realiseJour <= -LimitePerteJour && !arretJour)
            {
                arretJour = true;
                Dire($"limite de perte du jour atteinte ({realiseJour:F0} $) : plus d'ordre reel aujourd'hui", true);
            }
            Aligner();
        }

        void Aligner()
        {
            if (voulu == null || SymboleMNQ == null || Compte == null) return;
            int r = PositionReelle();
            if (r == voulu.Value)
            {
                if (voulu.Value == 0) voulu = null;
                return;
            }
            if ((Maintenant() - ordreEnvoye).TotalSeconds < 10) return;
            EnvoyerOrdre(voulu.Value - r, $"position {r} -> {voulu.Value}");
        }

        void EnvoyerOrdre(int q, string raison)
        {
            if (q == 0) return;
            var res = Core.Instance.PlaceOrder(new PlaceOrderRequestParameters
            {
                Account = Compte, Symbol = SymboleMNQ, Side = q > 0 ? Side.Buy : Side.Sell, Quantity = Math.Abs(q), OrderTypeId = OrderType.Market
            });
            ordreEnvoye = Maintenant();
            if (res.Status == TradingOperationResultStatus.Failure) Dire($"ERREUR d'ordre ({(q > 0 ? "achat" : "vente")} {Math.Abs(q)} MNQ) : {res.Message}", true);
            else Dire($"ordre envoye : {(q > 0 ? "achat" : "vente")} {Math.Abs(q)} MNQ ({raison})");
        }

        // ------------------------------------------------------------------ messages
        void Dire(string texte, bool erreur = false)
        {
            Log(texte, erreur ? StrategyLoggingLevel.Error : StrategyLoggingLevel.Info);
            try
            {
                Directory.CreateDirectory(Path.Combine(Dossier, "flux"));       // le message d'une erreur au demarrage n'est pas perdu
                File.AppendAllText(Path.Combine(Dossier, "flux", "journal.txt"), $"{Maintenant():yyyy-MM-dd HH:mm:ss} UTC {texte}{Environment.NewLine}");
            }
            catch { }
            if (string.IsNullOrWhiteSpace(JetonTelegram) || string.IsNullOrWhiteSpace(ChatTelegram)) return;
            string jeton = System.Text.RegularExpressions.Regex.Replace(JetonTelegram, "\\s", ""),
                   chat = System.Text.RegularExpressions.Regex.Replace(ChatTelegram, "\\s", "");
            if (jeton.StartsWith("bot", StringComparison.OrdinalIgnoreCase)) jeton = jeton.Substring(3);
            try
            {
                var contenu = new FormUrlEncodedContent(new Dictionary<string, string> { ["chat_id"] = chat, ["text"] = "FluxNQ : " + texte });
                http.PostAsync($"https://api.telegram.org/bot{jeton}/sendMessage", contenu).ContinueWith(t =>
                {
                    try
                    {
                        string err = t.IsFaulted ? (t.Exception?.GetBaseException().Message ?? "erreur") : t.IsCanceled ? "pas de reponse en 20 s"
                            : t.Result.IsSuccessStatusCode ? "" : $"code {(int)t.Result.StatusCode}";
                        if (err == "" || err == derniereErreurTelegram) { if (err == "") derniereErreurTelegram = ""; return; }
                        derniereErreurTelegram = err;
                        Log($"Telegram : message non envoye ({err.Replace(jeton, "***")})", StrategyLoggingLevel.Error);
                    }
                    catch { }
                });
            }
            catch { }
        }
    }

    /// <summary>Lecture du carnet par reflexion (DepthOfMarket.GetDepthOfMarketAggregatedCollections) : 10 meilleurs prix de
    /// chaque cote. Si la plateforme n'a pas ces noms, Pret reste faux et le bot continue sans DOM.</summary>
    public class LecteurDom
    {
        object dom, parametres;
        MethodInfo methode;
        public string Erreur = "";
        public bool Pret;

        public bool Init(object symbole)
        {
            try
            {
                dom = Valeur(symbole, "DepthOfMarket");
                if (dom == null) { Erreur = "propriete DepthOfMarket absente"; return false; }
                methode = dom.GetType().GetMethods().FirstOrDefault(m => m.Name == "GetDepthOfMarketAggregatedCollections" && m.GetParameters().Length == 1);
                if (methode == null) { Erreur = "methode GetDepthOfMarketAggregatedCollections absente"; return false; }
                var tp = methode.GetParameters()[0].ParameterType;
                parametres = Activator.CreateInstance(tp);
                var pl = tp.GetProperty("GetLevel2ItemsParameters");
                object l2 = pl != null ? Activator.CreateInstance(pl.PropertyType) : parametres;
                Fixer(l2, "LevelsCount", 10);
                Fixer(l2, "CalculateCumulative", false);
                var am = l2.GetType().GetProperty("AggregateMethod");
                if (am != null && am.PropertyType.IsEnum && Enum.GetNames(am.PropertyType).Contains("ByPriceLVL"))
                    am.SetValue(l2, Enum.Parse(am.PropertyType, "ByPriceLVL"));
                if (pl != null) pl.SetValue(parametres, l2);
                Pret = true;
                return true;
            }
            catch (Exception e) { Erreur = e.GetBaseException().Message; return false; }
        }

        static object Valeur(object o, string nom)
        {
            if (o == null) return null;
            var t = o.GetType();
            var p = t.GetProperty(nom);
            if (p != null) return p.GetValue(o);
            return t.GetField(nom)?.GetValue(o);
        }

        static void Fixer(object o, string nom, object v)
        {
            var p = o.GetType().GetProperty(nom);
            if (p != null && p.CanWrite) p.SetValue(o, Convert.ChangeType(v, p.PropertyType, CultureInfo.InvariantCulture));
        }

        static double Nombre(object o, string nom)
        {
            var v = Valeur(o, nom);
            return v == null ? double.NaN : Convert.ToDouble(v, CultureInfo.InvariantCulture);
        }

        public PhotoDom Lire()
        {
            try
            {
                var r = methode.Invoke(dom, new[] { parametres });
                var achats = Niveaux(Valeur(r, "Bids")).Where(x => x.q > 0).OrderByDescending(x => x.p).Take(10).ToArray();
                var ventes = Niveaux(Valeur(r, "Asks")).Where(x => x.q > 0).OrderBy(x => x.p).Take(10).ToArray();
                return new PhotoDom { PrixAchat = achats.Select(x => x.p).ToArray(), QteAchat = achats.Select(x => x.q).ToArray(),
                                      PrixVente = ventes.Select(x => x.p).ToArray(), QteVente = ventes.Select(x => x.q).ToArray() };
            }
            catch (Exception e) { Erreur = e.GetBaseException().Message; return null; }
        }

        static IEnumerable<(double p, double q)> Niveaux(object liste)
        {
            if (liste is System.Collections.IEnumerable e)
                foreach (var x in e)
                    if (x != null) yield return (Nombre(x, "Price"), Nombre(x, "Size"));
        }
    }
}
