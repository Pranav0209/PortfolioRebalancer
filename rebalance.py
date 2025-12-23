"""
Rebalancing logic and quantity guidance.
"""

import pandas as pd
import numpy as np


def calculate_scale_factor(source_df, target_df):
    """
    Calculate global quantity scaling factor.
    
    Args:
        source_df: Source portfolio with quantity column
        target_df: Target portfolio with quantity column
        
    Returns:
        Float: scale factor (target_total / source_total)
    """
    source_total = source_df['quantity'].sum()
    target_total = target_df['quantity'].sum()
    
    if source_total == 0:
        return 1.0
    
    return round(target_total / source_total, 4)


def calculate_rebalance_actions(source_df, target_df, scale_factor=None):
    """
    Calculate buy/sell quantities to align target with source.
    
    Args:
        source_df: Source portfolio with quantity
        target_df: Target portfolio with quantity
        scale_factor: Override calculated scale factor (optional)
        
    Returns:
        DataFrame with rebalance actions
    """
    if scale_factor is None:
        scale_factor = calculate_scale_factor(source_df, target_df)
    
    # Create lookups
    source_map = dict(zip(source_df['symbol'], source_df['quantity']))
    target_map = dict(zip(target_df['symbol'], target_df['quantity']))
    
    all_symbols = sorted(set(source_map.keys()) | set(target_map.keys()))
    
    actions = []
    for symbol in all_symbols:
        source_qty = source_map.get(symbol, 0)
        target_qty = target_map.get(symbol, 0)
        
        # Target quantity based on scale factor
        target_qty_ideal = source_qty * scale_factor
        
        # Action required
        action_qty = target_qty_ideal - target_qty
        
        if action_qty > 0.5:
            action_type = 'BUY'
        elif action_qty < -0.5:
            action_type = 'SELL'
        else:
            action_type = 'HOLD'
        
        actions.append({
            'Symbol': symbol,
            'Current Qty': int(target_qty) if target_qty > 0 else 0,
            'Target Qty': int(round(target_qty_ideal)),
            'Action': action_type,
            'Qty Change': int(round(action_qty)),
        })
    
    result = pd.DataFrame(actions)
    
    # Sort: BUY first, then SELL, then HOLD
    order_map = {'BUY': 0, 'SELL': 1, 'HOLD': 2}
    result['sort_key'] = result['Action'].map(order_map)
    result = result.sort_values(['sort_key', 'Qty Change'], ascending=[True, False])
    return result.drop('sort_key', axis=1).reset_index(drop=True)


def get_rebalance_summary(actions_df):
    """
    Get summary of rebalance actions.
    
    Args:
        actions_df: Rebalance actions DataFrame
        
    Returns:
        Dictionary with action counts and totals
    """
    buy_qty = actions_df[actions_df['Action'] == 'BUY']['Qty Change'].sum()
    sell_qty = abs(actions_df[actions_df['Action'] == 'SELL']['Qty Change'].sum())
    
    return {
        'Buy Count': len(actions_df[actions_df['Action'] == 'BUY']),
        'Sell Count': len(actions_df[actions_df['Action'] == 'SELL']),
        'Hold Count': len(actions_df[actions_df['Action'] == 'HOLD']),
        'Total Buy Qty': int(buy_qty),
        'Total Sell Qty': int(sell_qty),
    }


def calculate_fresh_investment(source_df, investment_amount):
    """
    Calculate quantities to buy for fresh investment based on source portfolio weights.
    
    Args:
        source_df: Source portfolio with symbol, quantity, weight_pct, price
        investment_amount: Total amount to invest
        
    Returns:
        DataFrame with investment actions
    """
    if 'price' not in source_df.columns or source_df['price'].isna().all():
        raise ValueError("Price column required for fresh investment calculation")
    
    # Ensure we have weights
    if 'weight_pct' not in source_df.columns:
        raise ValueError("weight_pct column required. Run normalize_portfolio first.")
    
    actions = []
    total_invested = 0
    
    for _, row in source_df.iterrows():
        symbol = row['symbol']
        weight_pct = row['weight_pct']
        price = row['price']
        
        if pd.isna(price) or price <= 0:
            continue  # Skip if no valid price
        
        # Calculate amount to invest in this stock
        amount = (weight_pct / 100) * investment_amount
        
        # Calculate quantity to buy
        quantity = amount / price
        
        # Round to whole shares, but ensure minimum 1 share if allocation is meaningful
        if quantity >= 0.5:
            quantity_rounded = max(1, int(round(quantity)))
        else:
            quantity_rounded = 0
        
        # Actual amount invested
        actual_amount = quantity_rounded * price
        
        total_invested += actual_amount
        
        actions.append({
            'Symbol': symbol,
            'Weight %': weight_pct,
            'Price': price,
            'Calculated Qty': round(quantity, 3),
            'Target Qty': quantity_rounded,
            'Amount': actual_amount,
        })
    
    result = pd.DataFrame(actions)
    
    # Adjust for rounding errors to match total investment
    if len(result) > 0:
        adjustment_factor = investment_amount / total_invested if total_invested > 0 else 1
        result['Adjusted Qty'] = (result['Calculated Qty'] * adjustment_factor).round().astype(int)
        result['Adjusted Amount'] = result['Adjusted Qty'] * result['Price']
    
    return result
