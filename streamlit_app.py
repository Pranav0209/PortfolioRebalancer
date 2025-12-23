"""
Portfolio Rebalancer - Streamlit App
Quantity-based portfolio replication and drift analysis.
"""

import streamlit as st
import pandas as pd
from loaders import load_csv_from_upload, parse_portfolio_data
from normalize import normalize_portfolio, get_all_symbols
from allocation import calculate_drift_analysis, calculate_tracking_error, get_status_summary
from rebalance import calculate_scale_factor, calculate_rebalance_actions, get_rebalance_summary
from visuals import (
    plot_allocation_comparison,
    plot_drift_distribution,
    plot_status_pie,
    create_drift_table,
    create_rebalance_table,
)
import config

# Page config
st.set_page_config(
    page_title="Portfolio Rebalancer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 Portfolio Rebalancer")
st.markdown(
    """
    Quantity-based portfolio replication and drift analysis.
    Compare a source portfolio against target holdings to identify rebalancing opportunities.
    """
)

# ============================================================================
# SIDEBAR - CONFIGURATION & FILE UPLOADS
# ============================================================================
st.sidebar.header("⚙️ Configuration")

with st.sidebar:
    # Groq API Key management
    st.subheader("🔑 Groq API Key")
    
    # Load saved API key
    saved_api_key = config.get_groq_api_key()
    
    if saved_api_key:
        st.success("✅ API key saved")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text("••••••••••••••••")
        with col2:
            if st.button("Clear", key="clear_api"):
                config.clear_groq_api_key()
                st.rerun()
        groq_api_key = saved_api_key
    else:
        # Input for new API key
        api_key_input = st.text_input(
            "Enter API Key",
            type="password",
            help="Get from https://console.groq.com/keys",
            key="api_key_input"
        )
        
        if api_key_input:
            if st.button("💾 Save API Key"):
                if config.set_groq_api_key(api_key_input):
                    st.success("API key saved!")
                    st.rerun()
                else:
                    st.error("Failed to save API key")
            groq_api_key = api_key_input
        else:
            st.warning("⚠️ API key required for auto-column detection")
            groq_api_key = None
    
    st.divider()
    st.header("📤 Upload Portfolios")
    
    st.subheader("Step 1: Source Portfolio")
    source_file = st.file_uploader(
        "Upload source portfolio (CSV/Excel)",
        type=["csv", "xlsx", "xls"],
        key="source_file",
        help="Bio Growth model, target allocation, or any format",
    )
    
    st.subheader("Step 2: Target Portfolio")
    target_file = st.file_uploader(
        "Upload target portfolio (CSV/Excel)",
        type=["csv", "xlsx", "xls"],
        key="target_file",
        help="Current holdings (Zerodha, DVC809, or any broker)",
    )
    
    st.divider()
    
    if source_file and target_file:
        if groq_api_key:
            st.success("✅ Files ready. Processing...")
        else:
            st.error("❌ Add Groq API key to process files")
    else:
        st.info("📌 Upload both files to begin analysis")

# ============================================================================
# MAIN LOGIC
# ============================================================================

if source_file and target_file:
    if not groq_api_key:
        st.error("ERROR: Please provide Groq API key in the sidebar to process files")
    else:
        try:
            # Load files
            source_raw = load_csv_from_upload(source_file)
            target_raw = load_csv_from_upload(target_file)
            
            # Parse portfolios with LLM-based column detection
            with st.spinner("Analyzing column structure..."):
                source_df = parse_portfolio_data(source_raw, groq_api_key=groq_api_key)
                target_df = parse_portfolio_data(target_raw, groq_api_key=groq_api_key)
            
            # Normalize
            source_norm = normalize_portfolio(source_df)
            target_norm = normalize_portfolio(target_df)
            
            # Analysis
            drift_analysis = calculate_drift_analysis(source_norm, target_norm)
            status_summary = get_status_summary(drift_analysis)
            tracking_error = calculate_tracking_error(drift_analysis['Drift %'])
            scale_factor = calculate_scale_factor(source_norm, target_norm)
            rebalance_actions = calculate_rebalance_actions(source_norm, target_norm, scale_factor)
            rebalance_summary = get_rebalance_summary(rebalance_actions)
            
            # ====================================================================
            # TOP METRICS
            # ====================================================================
            st.subheader("📈 Portfolio Health Metrics")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric(label="Tracking Error", value=f"{tracking_error}%")
            with col2:
                st.metric(label="Scale Factor", value=f"{scale_factor:.4f}")
            with col3:
                st.metric(label="Aligned Stocks", value=status_summary['Aligned'])
            with col4:
                st.metric(label="Overweight", value=status_summary['Overweight'])
            with col5:
                st.metric(label="Underweight", value=status_summary['Underweight'])
            
            if status_summary['Missing'] > 0 or status_summary['Extra'] > 0:
                col6, col7 = st.columns(2)
                with col6:
                    st.metric(label="Missing Stocks", value=status_summary['Missing'])
                with col7:
                    st.metric(label="Extra Stocks", value=status_summary['Extra'])
            
            st.divider()
            
            # ====================================================================
            # TAB LAYOUT
            # ====================================================================
            tab1, tab2, tab3 = st.tabs(["🔍 Drift Analysis", "🔄 Rebalance Actions", "📊 Visualizations"])
            
            # ====================================================================
            # TAB 1: DRIFT ANALYSIS
            # ====================================================================
            with tab1:
                st.subheader("Drift Analysis - Symbol by Symbol")
                st.markdown(
                    """
                    - **Status**: Alignment classification
                    - **Source %**: Target weight in source portfolio
                    - **Target %**: Current weight in target portfolio
                    - **Drift %**: Difference (Target - Source)
                    """
                )
                
                # Display drift table
                display_table = create_drift_table(drift_analysis)
                st.dataframe(
                    display_table,
                    use_container_width=True,
                    hide_index=True,
                )
                
                # Summary by status
                st.subheader("Status Breakdown")
                
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("✅ Aligned", status_summary['Aligned'])
                with col2:
                    st.metric("🔺 Overweight", status_summary['Overweight'])
                with col3:
                    st.metric("🔻 Underweight", status_summary['Underweight'])
                with col4:
                    st.metric("❌ Missing", status_summary['Missing'])
                with col5:
                    st.metric("⚠️ Extra", status_summary['Extra'])
                
                # Download drift analysis
                csv_drift = display_table.to_csv(index=False)
                st.download_button(
                    label="📥 Download Drift Analysis (CSV)",
                    data=csv_drift,
                    file_name="drift_analysis.csv",
                    mime="text/csv",
                )
            
            # ====================================================================
            # TAB 2: REBALANCE ACTIONS
            # ====================================================================
            with tab2:
                st.subheader("Rebalance Actions")
                st.markdown(
                    f"""
                    **Scale Factor**: {scale_factor:.4f}
                    
                    This means target portfolio is {scale_factor:.1%} the size of source portfolio.
                    
                    - **Current Qty**: Shares currently held
                    - **Target Qty**: Shares needed for alignment
                    - **Action**: BUY / SELL / HOLD
                    - **Qty Change**: Number of shares to trade
                    """
                )
                
                # Action summary
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Buy Actions", rebalance_summary['Buy Count'])
                with col2:
                    st.metric("Sell Actions", rebalance_summary['Sell Count'])
                with col3:
                    st.metric("Hold Actions", rebalance_summary['Hold Count'])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Buy Qty", rebalance_summary['Total Buy Qty'])
                with col2:
                    st.metric("Total Sell Qty", rebalance_summary['Total Sell Qty'])
                
                st.divider()
                
                # Display rebalance table
                st.subheader("Detailed Actions")
                display_actions = create_rebalance_table(rebalance_actions)
                st.dataframe(
                    display_actions,
                    use_container_width=True,
                    hide_index=True,
                )
                
                # Download rebalance actions
                csv_actions = display_actions.to_csv(index=False)
                st.download_button(
                    label="📥 Download Rebalance Actions (CSV)",
                    data=csv_actions,
                    file_name="rebalance_actions.csv",
                    mime="text/csv",
                )
            
            # ====================================================================
            # TAB 3: VISUALIZATIONS
            # ====================================================================
            with tab3:
                st.subheader("Allocation Comparison")
                st.plotly_chart(
                    plot_allocation_comparison(drift_analysis),
                    use_container_width=True,
                )
                
                st.divider()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Drift Distribution")
                    st.plotly_chart(
                        plot_drift_distribution(drift_analysis),
                        use_container_width=True,
                    )
                
                with col2:
                    st.subheader("Portfolio Health")
                    st.plotly_chart(
                        plot_status_pie(status_summary),
                        use_container_width=True,
                    )
            
            # ====================================================================
            # SOURCE PORTFOLIOS (Expandable)
            # ====================================================================
            with st.expander("📂 Source Portfolio Details"):
                st.subheader("Source Portfolio (Normalized)")
                st.dataframe(
                    source_norm[['symbol', 'quantity', 'weight_pct']],
                    use_container_width=True,
                    hide_index=True,
                )
            
            with st.expander("📂 Target Portfolio Details"):
                st.subheader("Target Portfolio (Normalized)")
                st.dataframe(
                    target_norm[['symbol', 'quantity', 'weight_pct']],
                    use_container_width=True,
                    hide_index=True,
                )
        
        except Exception as e:
            st.error(f"ERROR processing files: {str(e)}")

else:
    # Welcome screen
    st.info("Add Groq API key and upload both source/target portfolios in the sidebar to begin.")
    
    st.divider()
    
    st.subheader("Getting Groq API Key (Free)")
    st.markdown("""
    1. Visit https://console.groq.com/keys
    2. Create free account (takes 1 minute)
    3. Copy API key
    4. Paste in sidebar
    5. Upload your files
    """)
    
    st.divider()
    
    st.subheader("Supported Formats")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Bio Growth Format**
        - Scrip Name: INFY, TCS, etc.
        - Net Qty: 100, 50, etc.
        """)
    
    with col2:
        st.markdown("""
        **DVC809/Zerodha Format**
        - Symbol: INFY, TCS, etc.
        - Quantity Available: 100, 50, etc.
        """)
    
    st.markdown("""
    Any format works! LLM intelligently detects:
    - Symbol/ticker columns
    - Quantity/holdings columns
    - Ignores: ISIN, Sector, Pledged, Discrepant, Long Term, etc.
    """)
