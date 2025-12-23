"""
Normalize portfolio data.
Handles symbol cleaning and weight calculations.
"""

import pandas as pd


def normalize_portfolio(df):
    """
    Calculate normalized weights for a portfolio.
    
    Args:
        df: DataFrame with columns: symbol, quantity
        
    Returns:
        DataFrame with columns: symbol, quantity, weight_pct
    """
    result = df.copy()
    total_qty = result['quantity'].sum()
    result['weight_pct'] = (result['quantity'] / total_qty * 100).round(2)
    return result.sort_values('weight_pct', ascending=False).reset_index(drop=True)


def get_all_symbols(source_df, target_df):
    """
    Get union of all symbols across portfolios.
    
    Args:
        source_df: Normalized source portfolio
        target_df: Normalized target portfolio
        
    Returns:
        Sorted list of unique symbols
    """
    symbols = set(source_df['symbol'].unique()) | set(target_df['symbol'].unique())
    return sorted(list(symbols))


def clean_symbol(symbol):
    """Clean and normalize a symbol string."""
    return str(symbol).strip().upper()
