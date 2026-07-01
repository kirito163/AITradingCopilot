"""
Calcoli avanzati di metriche di portafoglio: ROI, Drawdown, Sharpe, Sortino, ecc.
"""

import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger


@dataclass
class MetricsResult:
    """Risultato metriche calcolate"""
    total_return: float = 0.0
    annualized_return: float = 0.0
    annualized_volatility: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    calmar_ratio: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_trade_return: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    best_trade: float = 0.0
    worst_trade: float = 0.0
    expectancy: float = 0.0


class PortfolioMetrics:
    """Calcolatore metriche di performance"""

    @staticmethod
    def calculate_returns(equity_curve: List[float]) -> np.ndarray:
        """Calcola rendimenti giornalieri da curva equity"""
        if len(equity_curve) < 2:
            return np.array([])
        arr = np.array(equity_curve)
        return (arr[1:] - arr[:-1]) / arr[:-1]

    @staticmethod
    def calculate_drawdown(equity_curve: List[float]) -> tuple:
        """
        Calcola massimo drawdown e durata

        Returns:
            (max_drawdown_percent, max_drawdown_days)
        """
        if len(equity_curve) < 2:
            return 0.0, 0
        arr = np.array(equity_curve)
        peak = np.maximum.accumulate(arr)
        drawdown = (arr - peak) / peak
        max_dd = float(np.min(drawdown))

        # Durata
        drawdown_periods = 0
        max_periods = 0
        for dd in drawdown:
            if dd < 0:
                drawdown_periods += 1
                max_periods = max(max_periods, drawdown_periods)
            else:
                drawdown_periods = 0
        return max_dd * 100, max_periods

    @staticmethod
    def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.02, periods_per_year: int = 252) -> float:
        """Calcola Sharpe Ratio annualizzato"""
        if len(returns) < 2:
            return 0.0
        excess = returns - (risk_free_rate / periods_per_year)
        if np.std(returns) == 0:
            return 0.0
        return float(np.sqrt(periods_per_year) * np.mean(excess) / np.std(returns))

    @staticmethod
    def calculate_sortino_ratio(returns: np.ndarray, risk_free_rate: float = 0.02, periods_per_year: int = 252) -> float:
        """Calcola Sortino Ratio (usa solo deviazione standard negativa)"""
        if len(returns) < 2:
            return 0.0
        excess = returns - (risk_free_rate / periods_per_year)
        downside = np.minimum(0, returns)
        downside_std = np.std(downside)
        if downside_std == 0:
            return 0.0
        return float(np.sqrt(periods_per_year) * np.mean(excess) / downside_std)

    @staticmethod
    def calculate_profit_factor(trades_pnl: List[float]) -> float:
        """Fattore di profitto: profitti lordi / perdite lorde"""
        if not trades_pnl:
            return 0.0
        gross_profit = sum(p for p in trades_pnl if p > 0)
        gross_loss = abs(sum(p for p in trades_pnl if p < 0))
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        return gross_profit / gross_loss

    @staticmethod
    def calculate_win_rate(trades_pnl: List[float]) -> float:
        """Percentuale di trade vincenti"""
        if not trades_pnl:
            return 0.0
        winners = sum(1 for p in trades_pnl if p > 0)
        return (winners / len(trades_pnl)) * 100

    @staticmethod
    def calculate_expectancy(trades_pnl: List[float]) -> float:
        """Expectancy: guadagno medio per trade"""
        if not trades_pnl:
            return 0.0
        return np.mean(trades_pnl)

    @classmethod
    def compute_all(cls, equity_curve: List[float], trades_pnl: List[float] = None,
                    risk_free_rate: float = 0.02) -> MetricsResult:
        """Calcola tutte le metriche principali"""
        returns = cls.calculate_returns(equity_curve)
        max_dd, dd_duration = cls.calculate_drawdown(equity_curve)

        sharpe = cls.calculate_sharpe_ratio(returns, risk_free_rate)
        sortino = cls.calculate_sortino_ratio(returns, risk_free_rate)

        if trades_pnl is None:
            trades_pnl = []

        win_rate = cls.calculate_win_rate(trades_pnl)
        profit_factor = cls.calculate_profit_factor(trades_pnl)
        expectancy = cls.calculate_expectancy(trades_pnl)

        annual_vol = float(np.std(returns) * np.sqrt(252)) if len(returns) > 0 else 0.0
        total_return = (equity_curve[-1] / equity_curve[0] - 1) * 100 if equity_curve and equity_curve[0] != 0 else 0.0
        annual_return = ((1 + total_return/100) ** (252/len(equity_curve)) - 1) * 100 if len(equity_curve) > 1 else 0.0

        # Calmar ratio
        calmar = annual_return / abs(max_dd) if max_dd != 0 else 0.0

        avg_win = np.mean([p for p in trades_pnl if p > 0]) if any(p > 0 for p in trades_pnl) else 0.0
        avg_loss = np.mean([p for p in trades_pnl if p < 0]) if any(p < 0 for p in trades_pnl) else 0.0
        best = max(trades_pnl) if trades_pnl else 0.0
        worst = min(trades_pnl) if trades_pnl else 0.0

        return MetricsResult(
            total_return=total_return,
            annualized_return=annual_return,
            annualized_volatility=annual_vol,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_dd,
            max_drawdown_duration=dd_duration,
            calmar_ratio=calmar,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_trade_return=expectancy,
            avg_win=avg_win,
            avg_loss=avg_loss,
            best_trade=best,
            worst_trade=worst,
            expectancy=expectancy
        )