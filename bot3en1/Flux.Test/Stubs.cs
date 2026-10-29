// Imitation minimale de l'API Quantower (TradingPlatform.BusinessLayer) pour FluxNQ : celle du test du bot 3 en 1, plus un
// carnet (DepthOfMarket, NewLevel2) aux noms de l'API reelle, que FluxNQ lit par reflexion. Ce n'est PAS l'API reelle.
using System;
using System.Collections.Generic;
using System.Linq;

namespace TradingPlatform.BusinessLayer
{
    public enum StrategyLoggingLevel { Info, Trading, Error }
    public enum AggressorFlag { NotSet, None, Buy, Sell }
    public enum Side { Buy, Sell }
    public enum HistoryType { Last, Bid, Ask, Mark }
    public enum SeekOriginHistory { Begin, End }
    public enum TradingOperationResultStatus { Success, Failure }

    [AttributeUsage(AttributeTargets.Field | AttributeTargets.Property)]
    public class InputParameterAttribute : Attribute
    {
        public InputParameterAttribute(string name, int sortIndex = 0) { }
        public InputParameterAttribute(string name, int sortIndex, double minimum, double maximum, double increment, int decimalPlaces) { }
    }

    public class Account { public string Name = "SIM"; public double Balance { get; set; } }   // Balance : lu par reflexion (mode a plat)
    public class Last { public DateTime Time; public double Price, Size; public AggressorFlag AggressorFlag; }
    public enum AggregateMethod { None, ByPriceLVL }
    public class Level2Item { public double Price { get; set; } public double Size { get; set; } }
    public class GetLevel2ItemsParameters { public AggregateMethod AggregateMethod { get; set; } public int LevelsCount { get; set; } public bool CalculateCumulative { get; set; } }
    public class GetDepthOfMarketParameters { public GetLevel2ItemsParameters GetLevel2ItemsParameters { get; set; } }
    public class DepthOfMarketAggregatedCollections { public Level2Item[] Bids { get; set; } public Level2Item[] Asks { get; set; } }
    public class DepthOfMarket
    {
        public Func<DepthOfMarketAggregatedCollections> Source;
        public GetDepthOfMarketParameters Derniers;
        public DepthOfMarketAggregatedCollections GetDepthOfMarketAggregatedCollections(GetDepthOfMarketParameters p) { Derniers = p; return Source(); }
    }
    public class Level2Quote { }
    public class DOMQuote { }
    public delegate void Level2Handler(Symbol symbol, Level2Quote level2, DOMQuote dom);
    public class Symbol
    {
        public string Name;
        public event Action<Symbol, Last> NewLast;
        public void Emettre(Last l) => NewLast?.Invoke(this, l);
        public DepthOfMarket DepthOfMarket { get; } = new DepthOfMarket();
        public event Level2Handler NewLevel2;
        public void EmettreL2() => NewLevel2?.Invoke(this, null, null);
        public int AbonnesL2 => NewLevel2?.GetInvocationList().Length ?? 0;
        public Func<HistoryRequestParameters, HistoricalData> Histoire;
        public HistoricalData GetHistory(HistoryRequestParameters p) => Histoire != null ? Histoire(p) : throw new Exception("pas d'historique dans le test");
    }
    public class HistoryAggregationTick { public HistoryAggregationTick(HistoryType type) { } }   // comme Quantower 1.146
    public class HistoryRequestParameters { public Symbol Symbol; public DateTime FromTime, ToTime; public object Aggregation; }
    public interface IHistoryItem { }
    public class HistoryItemLast : IHistoryItem { public DateTime TimeLeft; public double Price, Volume; public AggressorFlag AggressorFlag; }
    public class HistoricalData
    {
        public List<IHistoryItem> Items = new List<IHistoryItem>();
        public int Count => Items.Count;
        public IHistoryItem this[int i, SeekOriginHistory o] => Items[i];
    }
    public class PnLItem { public double Value { get; set; } }
    public class Position { public Account Account; public Symbol Symbol; public Side Side; public double Quantity; public PnLItem GrossPnL { get; set; } }
    public static class OrderType { public const string Market = "Market"; }
    public class PlaceOrderRequestParameters { public Account Account; public Symbol Symbol; public Side Side; public double Quantity; public string OrderTypeId; }
    public class TradingOperationResult { public TradingOperationResultStatus Status; public string Message = ""; }
    public class TimeUtils { public DateTime DateTimeUtcNow; }
    public class Core
    {
        public static Core Instance = new Core();
        public TimeUtils TimeUtils = new TimeUtils();
        public List<Position> Liste = new List<Position>();
        public Position[] Positions => Liste.ToArray();
        public List<string> Ordres = new List<string>();
        public TradingOperationResult PlaceOrder(PlaceOrderRequestParameters p)
        {
            // remplissage immediat au dernier prix connu (test)
            int q = (p.Side == Side.Buy ? 1 : -1) * (int)p.Quantity;
            var pos = Liste.FirstOrDefault(x => x.Account == p.Account && x.Symbol == p.Symbol);
            int avant = pos == null ? 0 : (pos.Side == Side.Buy ? 1 : -1) * (int)pos.Quantity;
            int apres = avant + q;
            Liste.RemoveAll(x => x.Account == p.Account && x.Symbol == p.Symbol);
            if (apres != 0) Liste.Add(new Position { Account = p.Account, Symbol = p.Symbol, Side = apres > 0 ? Side.Buy : Side.Sell, Quantity = Math.Abs(apres) });
            Ordres.Add($"{TimeUtils.DateTimeUtcNow:yyyy-MM-dd HH:mm:ss} {p.Side} {p.Quantity} {p.Symbol?.Name} -> position {apres}");
            return new TradingOperationResult { Status = TradingOperationResultStatus.Success };
        }
    }
    public abstract class Strategy
    {
        public string Name, Description;
        public List<string> Logs = new List<string>();
        public bool Arretee;
        protected abstract void OnRun();
        protected abstract void OnStop();
        protected void Log(string m, StrategyLoggingLevel l) => Logs.Add($"[{l}] {m}");
        public void Stop() { Arretee = true; }
        public void Lancer() => OnRun();
        public void Arreter() => OnStop();
    }
}
