import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { useQuery } from 'react-query';
import axios from 'axios';

// Enhanced API base URL for Williams Capital Management
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8081';

// Trading context
const TradingContext = createContext();

// Initial state
const initialState = {
  isConnected: false,
  wallet: {
    address: '',
    balance: 0,
    balanceUSD: 0,
  },
  trading: {
    isActive: false,
    totalTrades: 0,
    successfulTrades: 0,
    totalPnL: 0,
    totalPnLUSD: 0,
    winRate: 0,
  },
  system: {
    health: 'unknown',
    uptime: 0,
    lastUpdate: null,
  },
  market: {
    solPrice: 0,
    solChange24h: 0,
  },
  recentTrades: [],
  alerts: [],
};

// Reducer
function tradingReducer(state, action) {
  switch (action.type) {
    case 'SET_CONNECTION_STATUS':
      return { ...state, isConnected: action.payload };
    
    case 'UPDATE_WALLET':
      return { ...state, wallet: { ...state.wallet, ...action.payload } };
    
    case 'UPDATE_TRADING_METRICS':
      return { ...state, trading: { ...state.trading, ...action.payload } };
    
    case 'UPDATE_SYSTEM_HEALTH':
      return { ...state, system: { ...state.system, ...action.payload } };
    
    case 'UPDATE_MARKET_DATA':
      return { ...state, market: { ...state.market, ...action.payload } };
    
    case 'ADD_TRADE':
      return {
        ...state,
        recentTrades: [action.payload, ...state.recentTrades.slice(0, 9)], // Keep last 10 trades
      };
    
    case 'ADD_ALERT':
      return {
        ...state,
        alerts: [action.payload, ...state.alerts.slice(0, 19)], // Keep last 20 alerts
      };
    
    case 'SET_FULL_STATE':
      return { ...state, ...action.payload };
    
    default:
      return state;
  }
}

// Enhanced API functions for live trading integration
const api = {
  getHealth: () => axios.get(`${API_BASE_URL}/health`),
  getMetrics: () => axios.get(`${API_BASE_URL}/metrics`),
  getLiveStatus: () => axios.get(`${API_BASE_URL}/live-status`),
  getWalletInfo: () => axios.get(`${API_BASE_URL}/wallet-info`),
  getTradingSession: () => axios.get(`${API_BASE_URL}/trading-session`),
  getRecentTrades: () => axios.get(`${API_BASE_URL}/trading-session`), // Get trades from session
  getSystemStatus: () => axios.get(`${API_BASE_URL}/system/status`),
};

// Provider component
export function TradingProvider({ children }) {
  const [state, dispatch] = useReducer(tradingReducer, initialState);

  // Health check query - every 30 seconds
  const { data: healthData, isError: healthError } = useQuery(
    'health',
    () => api.getHealth(),
    {
      refetchInterval: 30000, // 30 seconds
      onSuccess: (response) => {
        dispatch({ type: 'SET_CONNECTION_STATUS', payload: true });
        dispatch({
          type: 'UPDATE_SYSTEM_HEALTH',
          payload: {
            health: response.data.overall_health ? 'healthy' : 'unhealthy',
            lastUpdate: new Date().toISOString(),
          },
        });
      },
      onError: () => {
        dispatch({ type: 'SET_CONNECTION_STATUS', payload: false });
        dispatch({
          type: 'UPDATE_SYSTEM_HEALTH',
          payload: { health: 'disconnected' },
        });
      },
    }
  );

  // Enhanced metrics query - every 30 seconds aligned with live trading system
  const { data: metricsData } = useQuery(
    'metrics',
    () => api.getMetrics(),
    {
      refetchInterval: 30000, // 30 seconds to match live trading system
      enabled: state.isConnected,
      onSuccess: (response) => {
        const metrics = response.data;

        // Update wallet data from new API structure
        if (metrics.wallet) {
          dispatch({
            type: 'UPDATE_WALLET',
            payload: {
              address: metrics.wallet.address || '',
              balance: metrics.wallet.balance || 0,
              balanceUSD: metrics.wallet.balanceUSD || 0,
            },
          });
        }

        // Update trading metrics from new API structure
        if (metrics.trading) {
          dispatch({
            type: 'UPDATE_TRADING_METRICS',
            payload: {
              isActive: metrics.trading.isActive || false,
              totalTrades: metrics.trading.totalTrades || 0,
              successfulTrades: metrics.trading.successfulTrades || 0,
              totalPnL: metrics.trading.totalPnL || 0,
              totalPnLUSD: metrics.trading.totalPnLUSD || 0,
              winRate: metrics.trading.winRate || 0,
            },
          });
        }

        // Update market data from new API structure
        if (metrics.market) {
          dispatch({
            type: 'UPDATE_MARKET_DATA',
            payload: {
              solPrice: metrics.market.solPrice || 0,
              solChange24h: metrics.market.solChange24h || 0,
            },
          });
        }

        // Update system health from new API structure
        if (metrics.system) {
          dispatch({
            type: 'UPDATE_SYSTEM_HEALTH',
            payload: {
              health: metrics.system.health === 'online' ? 'healthy' : 'unhealthy',
              uptime: metrics.system.uptime || 0,
              lastUpdate: metrics.system.lastUpdate || new Date().toISOString(),
            },
          });
        }
      },
    }
  );

  // Recent trades query - every 30 seconds aligned with live trading system
  const { data: tradesData } = useQuery(
    'recentTrades',
    () => api.getTradingSession(),
    {
      refetchInterval: 30000, // 30 seconds to match live trading system
      enabled: state.isConnected,
      onSuccess: (response) => {
        if (response.data && response.data.recent_trades && Array.isArray(response.data.recent_trades)) {
          // Update recent trades from trading session data
          dispatch({
            type: 'SET_FULL_STATE',
            payload: { recentTrades: response.data.recent_trades.slice(0, 10) },
          });
        }
      },
    }
  );

  // Calculate derived values
  const derivedState = {
    ...state,
    trading: {
      ...state.trading,
      winRate: state.trading.totalTrades > 0 
        ? (state.trading.successfulTrades / state.trading.totalTrades) * 100 
        : 0,
    },
  };

  const contextValue = {
    state: derivedState,
    dispatch,
    api,
    isLoading: !state.isConnected,
  };

  return (
    <TradingContext.Provider value={contextValue}>
      {children}
    </TradingContext.Provider>
  );
}

// Hook to use trading context
export function useTrading() {
  const context = useContext(TradingContext);
  if (!context) {
    throw new Error('useTrading must be used within a TradingProvider');
  }
  return context;
}
