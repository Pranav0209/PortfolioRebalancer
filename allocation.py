"""
Allocation analysis and drift detection.
Compares source and target portfolios.
"""

import pandas as pd
import numpy as np


def calculate_drift_analysis(source_df, target_df):
    """
    Calculate drift between source and target portfolios.
    
    Args:
        source_df: Normalized source portfolio (with weight_pct)
        target_df: Normalized target portfolio (with weight_pct)
        
    Returns:
        DataFrame with comprehensive drift analysis
    """
    # Create lookup dicts
    source_weights = dict(zip(source_df['symbol'], source_df['weight_pct']))
    target_weights = dict(zip(target_df['symbol'], target_df['weight_pct']))
    source_qtys = dict(zip(source_df['symbol'], source_df['quantity']))
    target_qtys = dict(zip(target_df['symbol'], target_df['quantity']))
    
    # Get all symbols
    all_symbols = sorted(set(source_weights.keys()) | set(target_weights.keys()))
    
    # Build analysis
    analysis = []
    for symbol in all_symbols:
        source_pct = source_weights.get(symbol, 0)
        target_pct = target_weights.get(symbol, 0)
        source_qty = source_qtys.get(symbol, 0)
        target_qty = target_qtys.get(symbol, 0)
        
        drift = target_pct - source_pct
        
        # Classify status
        if symbol in source_weights and symbol not in target_weights:
            status = '❌ Missing'
        elif symbol not in source_weights:
            status = '⚠️ Extra'
        elif abs(drift) < 0.01:  # Within 0.01%
            status = '✅ Aligned'
        elif drift > 0:
            status = '🔺 Overweight'
        else:
            status = '🔻 Underweight'
        
        analysis.append({
            'Symbol': symbol,
            'Source %': round(source_pct, 2),
            'Target %': round(target_pct, 2),
            'Drift %': round(drift, 2),
            'Status': status,
            'Source Qty': int(source_qty) if source_qty > 0 else 0,
            'Target Qty': int(target_qty) if target_qty > 0 else 0,
        })
    
    return pd.DataFrame(analysis)


def calculate_tracking_error(drift_series):
    """
    Calculate tracking error as sum of squared drifts.
    
    Args:
        drift_series: Series of drift percentages
        
    Returns:
        Float: tracking error value
    """
    return round(float((drift_series ** 2).sum()), 2)


def get_status_summary(analysis_df):
    """
    Get count summary by status.
    
    Args:
        analysis_df: Drift analysis DataFrame
        
    Returns:
        Dictionary with status counts
    """
    status_counts = analysis_df['Status'].value_counts().to_dict()
    return {
        'Aligned': status_counts.get('✅ Aligned', 0),
        'Overweight': status_counts.get('🔺 Overweight', 0),
        'Underweight': status_counts.get('🔻 Underweight', 0),
        'Missing': status_counts.get('❌ Missing', 0),
        'Extra': status_counts.get('⚠️ Extra', 0),
    }
