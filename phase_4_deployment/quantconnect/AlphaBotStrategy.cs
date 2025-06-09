/*
 * AlphaBotStrategy.cs
 * Q5 System QuantConnect Deployment
 * 
 * This C# implementation of the Q5 Alpha Bot strategy is designed for deployment
 * on the QuantConnect platform. It implements the core wallet-following logic
 * with appropriate risk management for live trading.
 */

using System;
using System.Collections.Generic;
using System.Linq;
using QuantConnect;
using QuantConnect.Algorithm;
using QuantConnect.Data;
using QuantConnect.Indicators;
using QuantConnect.Orders;
using QuantConnect.Securities;

namespace Q5System
{
    public class AlphaBotStrategy : QCAlgorithm
    {
        // Configuration parameters
        private decimal _minScore = 0.41m;
        private decimal _minAlphaCount = 1.5m;
        private decimal _stopLossPct = 0.034m;
        private decimal _takeProfitPct = 0.092m;
        private decimal _trailingStopPct = 0.016m;
        private decimal _maxPositionPct = 0.026m;
        private int _maxActivePositions = 15;
        
        // Trading state
        private Dictionary<Symbol, TradeInfo> _activePositions;
        private Dictionary<string, decimal> _walletScores;
        private List<string> _alphaWallets;
        
        // Custom data sources
        private AlphaWalletDataSource _alphaWalletData;
        private TokenSignalDataSource _tokenSignalData;
        
        public override void Initialize()
        {
            SetStartDate(2025, 5, 1);
            SetCash(1000);
            
            // Set brokerage model for Solana
            SetBrokerageModel(BrokerageName.Coinbase, AccountType.Cash);
            
            // Initialize collections
            _activePositions = new Dictionary<Symbol, TradeInfo>();
            _walletScores = new Dictionary<string, decimal>();
            _alphaWallets = new List<string>();
            
            // Add Solana tokens from config
            var symbols = LoadSymbolsFromConfig();
            foreach (var symbol in symbols)
            {
                AddCrypto(symbol, Resolution.Minute);
            }
            
            // Add custom data sources
            _alphaWalletData = new AlphaWalletDataSource();
            _tokenSignalData = new TokenSignalDataSource();
            AddData<AlphaWalletData>("alpha_wallets");
            AddData<TokenSignalData>("token_signals");
            
            // Schedule functions
            Schedule.On(DateRules.EveryDay(), TimeRules.Every(TimeSpan.FromMinutes(5)), CheckForSignals);
            Schedule.On(DateRules.EveryDay(), TimeRules.Every(TimeSpan.FromMinutes(1)), ManagePositions);
        }
        
        public override void OnData(Slice data)
        {
            // Process custom data
            if (data.ContainsKey("alpha_wallets"))
            {
                var walletData = data["alpha_wallets"] as AlphaWalletData;
                UpdateWalletScores(walletData);
            }
            
            if (data.ContainsKey("token_signals"))
            {
                var signalData = data["token_signals"] as TokenSignalData;
                ProcessSignals(signalData);
            }
        }
        
        private void CheckForSignals()
        {
            if (_activePositions.Count >= _maxActivePositions)
            {
                Log("Maximum active positions reached. Skipping signal check.");
                return;
            }
            
            // Check for new signals based on wallet activity
            foreach (var wallet in _alphaWallets)
            {
                var walletScore = _walletScores.GetValueOrDefault(wallet, 0);
                if (walletScore < _minScore) continue;
                
                // Get tokens recently purchased by this wallet
                var tokens = _tokenSignalData.GetRecentTokens(wallet);
                foreach (var token in tokens)
                {
                    if (ShouldEnterPosition(token, walletScore))
                    {
                        EnterPosition(token);
                    }
                }
            }
        }
        
        private bool ShouldEnterPosition(TokenInfo token, decimal walletScore)
        {
            // Check if we already have a position
            if (_activePositions.ContainsKey(token.Symbol)) return false;
            
            // Check alpha count
            if (token.AlphaCount < _minAlphaCount) return false;
            
            // Check confidence score
            if (token.Confidence < _minScore) return false;
            
            return true;
        }
        
        private void EnterPosition(TokenInfo token)
        {
            // Calculate position size
            var positionSize = Portfolio.TotalPortfolioValue * _maxPositionPct;
            
            // Place market order
            var ticket = MarketOrder(token.Symbol, positionSize);
            if (ticket.Status == OrderStatus.Filled)
            {
                // Add to active positions
                _activePositions[token.Symbol] = new TradeInfo
                {
                    EntryPrice = ticket.AverageFillPrice,
                    StopLossPrice = ticket.AverageFillPrice * (1 - _stopLossPct),
                    TakeProfitPrice = ticket.AverageFillPrice * (1 + _takeProfitPct),
                    TrailingStopPrice = ticket.AverageFillPrice * (1 - _trailingStopPct),
                    HighestPrice = ticket.AverageFillPrice
                };
                
                Log($"Entered position in {token.Symbol} at {ticket.AverageFillPrice}");
            }
        }
        
        private void ManagePositions()
        {
            foreach (var position in _activePositions.ToList())
            {
                var symbol = position.Key;
                var info = position.Value;
                var currentPrice = Securities[symbol].Price;
                
                // Update highest price for trailing stop
                if (currentPrice > info.HighestPrice)
                {
                    info.HighestPrice = currentPrice;
                    info.TrailingStopPrice = info.HighestPrice * (1 - _trailingStopPct);
                }
                
                // Check exit conditions
                if (currentPrice <= info.StopLossPrice || 
                    currentPrice <= info.TrailingStopPrice || 
                    currentPrice >= info.TakeProfitPrice)
                {
                    ExitPosition(symbol);
                }
            }
        }
        
        private void ExitPosition(Symbol symbol)
        {
            Liquidate(symbol);
            _activePositions.Remove(symbol);
            Log($"Exited position in {symbol}");
        }
        
        private List<string> LoadSymbolsFromConfig()
        {
            // In a real implementation, this would load from config.json
            return new List<string> { "SOLUSDT", "BTCUSDT" };
        }
        
        private void UpdateWalletScores(AlphaWalletData data)
        {
            foreach (var wallet in data.Wallets)
            {
                _walletScores[wallet.Address] = wallet.Score;
                if (wallet.Score >= _minScore && !_alphaWallets.Contains(wallet.Address))
                {
                    _alphaWallets.Add(wallet.Address);
                }
            }
        }
        
        private void ProcessSignals(TokenSignalData data)
        {
            // Process incoming token signals
            foreach (var signal in data.Signals)
            {
                if (signal.SignalType == "BUY" && signal.Confidence >= _minScore)
                {
                    var token = new TokenInfo
                    {
                        Symbol = SymbolFromMint(signal.TokenMint),
                        AlphaCount = signal.AlphaCount,
                        Confidence = signal.Confidence
                    };
                    
                    if (ShouldEnterPosition(token, signal.WalletScore))
                    {
                        EnterPosition(token);
                    }
                }
            }
        }
        
        private Symbol SymbolFromMint(string mint)
        {
            // In a real implementation, this would convert a token mint address to a Symbol
            return Symbol.Create("SOLUSDT", SecurityType.Crypto, Market.Coinbase);
        }
    }
    
    // Helper classes
    public class TradeInfo
    {
        public decimal EntryPrice { get; set; }
        public decimal StopLossPrice { get; set; }
        public decimal TakeProfitPrice { get; set; }
        public decimal TrailingStopPrice { get; set; }
        public decimal HighestPrice { get; set; }
    }
    
    public class TokenInfo
    {
        public Symbol Symbol { get; set; }
        public decimal AlphaCount { get; set; }
        public decimal Confidence { get; set; }
    }
}
