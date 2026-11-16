using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;
using SupertrendNQ;

// Rejoue le moteur Supertrend sur un fichier de minutes (t,o,h,l,c,...) : toutes les seances du fichier alimentent
// l'indicateur ; seules les seances completes (premiere et derniere minute presentes, au moins 370 minutes) sont tradees,
// comme le test sur 15 ans. Minutes absentes : cloture recopiee (vers l'avant, puis vers l'arriere en debut de seance).
// Usage : Supertrend.Replay <minutes.csv[.gz]> [sortie.csv]
class Program
{
    static int Main(string[] a)
    {
        var inv = CultureInfo.InvariantCulture;
        var bot = new MoteurST();
        Rejeu.Jouer(bot, Rejeu.LireJours(Rejeu.Lignes(a[0]), DateTime.MaxValue));
        var sortie = a.Length > 1 ? a[1] : null;
        var lignes = new List<string> { "jour,sens,m_in,m_out,entree,sortie" };
        lignes.AddRange(bot.Trades.Select(t => $"{t.Jour:yyyy-MM-dd},{t.Sens},{t.MinuteEntree},{t.MinuteSortie},{t.Entree.ToString("R", inv)},{t.Sortie.ToString("R", inv)}"));
        if (sortie != null) File.WriteAllLines(sortie, lignes);
        double total = bot.Trades.Sum(t => 2 * t.Sens * (t.Sortie - t.Entree) - 3.0);
        Console.WriteLine($"{bot.Trades.Count} trades, {bot.Trades.Select(t => t.Jour).Distinct().Count()} seances, total {total:F0} $ pour 1 MNQ (prix bruts)");
        return 0;
    }
}
