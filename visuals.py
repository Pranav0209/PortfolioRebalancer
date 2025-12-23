"""
Visualization functions for Streamlit app.
Charts and tables for drift analysis and rebalancing.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def plot_allocation_comparison(analysis_df):
    """
    Create side-by-side bar chart comparing source vs target allocations.
    
    Args:
        analysis_df: Drift analysis DataFrame
        
    Returns:
        Plotly figure
    """
    df = analysis_df[['Symbol', 'Source %', 'Target %']].copy()
    df = df.sort_values('Source %', ascending=True)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['Source %'],
        y=df['Symbol'],
        name='Source %',
        orientation='h',
        marker_color='rgba(99, 110, 250, 0.7)',
    ))
    
    fig.add_trace(go.Bar(
        x=df['Target %'],
        y=df['Symbol'],
        name='Target %',
        orientation='h',
        marker_color='rgba(239, 85, 59, 0.7)',
    ))
    
    fig.update_layout(
        barmode='group',
        title='Source vs Target Allocation %',
        xaxis_title='Allocation %',
        yaxis_title='Symbol',
        height=400 + len(df) * 15,
        showlegend=True,
        hovermode='closest',
    )
    
    return fig


def plot_drift_distribution(analysis_df):
    """
    Create bar chart showing drift by symbol.
    
    Args:
        analysis_df: Drift analysis DataFrame
        
    Returns:
        Plotly figure
    """
    df = analysis_df[['Symbol', 'Drift %']].copy()
    df = df.sort_values('Drift %', ascending=False)
    
    # Color based on drift direction
    colors = ['red' if x < 0 else 'green' for x in df['Drift %']]
    
    fig = go.Figure(
        data=[go.Bar(x=df['Symbol'], y=df['Drift %'], marker_color=colors)]
    )
    
    fig.update_layout(
        title='Drift % by Stock (Positive = Overweight, Negative = Underweight)',
        xaxis_title='Symbol',
        yaxis_title='Drift %',
        height=400,
        showlegend=False,
        hovermode='x',
    )
    
    fig.add_hline(y=0, line_dash='dash', line_color='black', opacity=0.5)
    
    return fig


def plot_status_pie(status_summary):
    """
    Create pie chart of status distribution.
    
    Args:
        status_summary: Dictionary from allocation.get_status_summary()
        
    Returns:
        Plotly figure
    """
    # Filter out zeros
    data = {k: v for k, v in status_summary.items() if v > 0}
    
    colors = {
        'Aligned': '#2ecc71',      # Green
        'Overweight': '#e74c3c',   # Red
        'Underweight': '#3498db',  # Blue
        'Missing': '#95a5a6',      # Gray
        'Extra': '#f39c12',        # Orange
    }
    
    fig = px.pie(
        values=list(data.values()),
        names=list(data.keys()),
        color_discrete_map=colors,
        title='Portfolio Health by Stock Status',
    )
    
    fig.update_layout(height=400)
    
    return fig


def create_drift_table(analysis_df):
    """
    Create styled drift analysis table.
    
    Args:
        analysis_df: Drift analysis DataFrame
        
    Returns:
        Formatted DataFrame for display
    """
    display_df = analysis_df.copy()
    
    # Sort by absolute drift descending
    display_df['abs_drift'] = display_df['Drift %'].abs()
    display_df = display_df.sort_values('abs_drift', ascending=False)
    display_df = display_df.drop('abs_drift', axis=1)
    
    return display_df


def create_rebalance_table(actions_df):
    """
    Create styled rebalance actions table.
    
    Args:
        actions_df: Rebalance actions DataFrame
        
    Returns:
        Formatted DataFrame for display
    """
    return actions_df.copy()
