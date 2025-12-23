"""
Portfolio Rebalancer - Streamlit App
Quantity-based portfolio replication and drift analysis.
"""

import streamlit as st
import pandas as pd
from loaders import load_csv_from_upload, parse_portfolio_data
from normalize import normalize_portfolio, get_all_symbols
from allocation import calculate_drift_analysis, calculate_tracking_error, get_status_summary
from rebalance import calculate_scale_factor, calculate_rebalance_actions, get_rebalance_summary, calculate_fresh_investment
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

# ============================================================================
# NAVIGATION
# ============================================================================

def home_page():
    st.title("🏠 Portfolio Rebalancer")
    st.markdown(
        """
        Choose your investment scenario:
        
        - **Rebalance Existing Account**: Compare your current holdings against a target allocation and get rebalancing recommendations.
        - **Fresh Investment**: Start a new portfolio based on a model allocation and specify your investment amount.
        """
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Rebalance Existing Account", use_container_width=True):
            st.session_state.page = "rebalance"
            st.rerun()
    
    with col2:
        if st.button("💰 Fresh Investment", use_container_width=True):
            st.session_state.page = "fresh"
            st.rerun()

def rebalance_existing_page():
    st.title("📊 Rebalance Existing Account")
    st.markdown("Compare a source portfolio against target holdings to identify rebalancing opportunities.")
    
    # Back button
    if st.button("← Back to Home"):
        st.session_state.page = "home"
        st.rerun()
    
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
            help="Current holdings (Zerodha or any broker)",
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
                    
                    # Display rebalance table
                    rebalance_table = create_rebalance_table(rebalance_actions)
                    st.dataframe(
                        rebalance_table,
                        use_container_width=True,
                        hide_index=True,
                    )
                    
                    # Rebalance summary
                    st.subheader("Rebalance Summary")
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("Buy Actions", rebalance_summary['Buy Count'])
                    with col2:
                        st.metric("Sell Actions", rebalance_summary['Sell Count'])
                    with col3:
                        st.metric("Hold Actions", rebalance_summary['Hold Count'])
                    with col4:
                        st.metric("Total Buy Qty", f"{rebalance_summary['Total Buy Qty']:,}")
                    with col5:
                        st.metric("Total Sell Qty", f"{rebalance_summary['Total Sell Qty']:,}")
                    
                    # Download rebalance actions
                    csv_rebalance = rebalance_table.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Rebalance Actions (CSV)",
                        data=csv_rebalance,
                        file_name="rebalance_actions.csv",
                        mime="text/csv",
                    )
                
                # ====================================================================
                # TAB 3: VISUALIZATIONS
                # ====================================================================
                with tab3:
                    st.subheader("Portfolio Visualizations")
                    
                    # Allocation comparison
                    st.markdown("**Allocation Comparison**")
                    fig_allocation = plot_allocation_comparison(drift_analysis)
                    st.plotly_chart(fig_allocation, use_container_width=True)
                    
                    # Drift distribution
                    st.markdown("**Drift Distribution**")
                    fig_drift = plot_drift_distribution(drift_analysis)
                    st.plotly_chart(fig_drift, use_container_width=True)
                    
                    # Status pie chart
                    st.markdown("**Status Breakdown**")
                    fig_status = plot_status_pie(status_summary)
                    st.plotly_chart(fig_status, use_container_width=True)
            
            except Exception as e:
                st.error(f"Error processing portfolios: {str(e)}")
                st.info("💡 Check that your CSV files have the expected columns (symbol, quantity)")

def fresh_investment_page():
    st.title("💰 Fresh Investment")
    st.markdown("Start a new portfolio based on a model allocation.")
    
    # Back button
    if st.button("← Back to Home"):
        st.session_state.page = "home"
        st.rerun()
    
    # ============================================================================
    # SIDEBAR - CONFIGURATION
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
                if st.button("Clear", key="clear_api_fresh"):
                    config.clear_groq_api_key()
                    st.rerun()
            groq_api_key = saved_api_key
        else:
            # Input for new API key
            api_key_input = st.text_input(
                "Enter API Key",
                type="password",
                help="Get from https://console.groq.com/keys",
                key="api_key_input_fresh"
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
        st.header("📤 Upload Model Portfolio")
        
        model_file = st.file_uploader(
            "Upload model portfolio (CSV/Excel)",
            type=["csv", "xlsx", "xls"],
            key="model_file",
            help="Model allocation (prices optional - can enter manually)",
        )
        
        st.divider()
        st.header("💰 Investment Amount")
        
        investment_amount = st.number_input(
            "Enter investment amount (₹)",
            min_value=1000.0,
            value=100000.0,
            step=1000.0,
            help="Total amount you want to invest",
        )
        
        if model_file and groq_api_key:
            st.success("✅ Ready to calculate investment")
        elif not model_file:
            st.info("📌 Upload model portfolio to begin")
        elif not groq_api_key:
            st.error("❌ Add Groq API key to process file")
    
    # ============================================================================
    # MAIN LOGIC
    # ============================================================================
    
    if model_file and groq_api_key:
        try:
            # Load and parse model portfolio
            model_raw = load_csv_from_upload(model_file)
            
            with st.spinner("Analyzing model portfolio..."):
                model_df = parse_portfolio_data(model_raw, groq_api_key=groq_api_key)
            
            # Check if prices are available - prefer Invested Price for fresh investment
            price_col = None
            if 'price' in model_df.columns and not model_df['price'].isna().all():
                price_col = 'price'
            elif 'Invested Price' in model_df.columns and not model_df['Invested Price'].isna().all():
                # For fresh investment, prefer invested price to maintain original allocation design
                price_col = 'Invested Price'
                model_df = model_df.rename(columns={'Invested Price': 'price'})
            elif 'Market Price' in model_df.columns and not model_df['Market Price'].isna().all():
                price_col = 'Market Price'
                model_df = model_df.rename(columns={'Market Price': 'price'})
            
            has_prices = price_col is not None
            
            if has_prices:
                st.success(f"✅ Price data detected from '{price_col}' column")
                if price_col == 'Invested Price':
                    st.info("💡 Using invested prices to preserve your original portfolio allocation design")
            
            # Normalize to get weights for price input help text
            model_norm = normalize_portfolio(model_df)
            
            if not has_prices:
                st.warning("⚠️ Price column not detected in your CSV file.")
                st.info("💡 You can either:\n1. Add a 'Price' column to your CSV\n2. Enter prices manually below")
                
                # Manual price input section
                st.subheader("📝 Enter Stock Prices")
                st.markdown("Enter current market prices for each stock (in ₹):")
                
                # Create a form for price input
                with st.form("price_input_form"):
                    price_inputs = {}
                    for _, row in model_norm.iterrows():
                        symbol = row['symbol']
                        weight_pct = row['weight_pct']
                        estimated_amount = (weight_pct / 100) * investment_amount
                        price_inputs[symbol] = st.number_input(
                            f"{symbol} Price (₹)",
                            min_value=0.01,
                            value=100.0,
                            step=0.01,
                            key=f"price_{symbol}",
                            help=f"Current market price for {symbol} in rupees (est. allocation: ₹{estimated_amount:.0f})"
                        )
                    
                    submitted = st.form_submit_button("✅ Calculate Investment Plan")
                
                if submitted:
                    # Add prices to dataframe
                    model_norm = model_norm.copy()
                    model_norm['price'] = model_norm['symbol'].map(price_inputs)
                    has_prices = True
                else:
                    return
            
            # Use normalized dataframe for calculations
            model_norm = normalize_portfolio(model_df) if has_prices and 'price' not in model_df.columns else model_norm
            
            # Calculate fresh investment
            with st.spinner("Calculating investment quantities..."):
                investment_actions = calculate_fresh_investment(model_norm, investment_amount)
            
            # ====================================================================
            # RESULTS
            # ====================================================================
            st.subheader("💰 Investment Plan")
            
            total_invested = investment_actions['Adjusted Amount'].sum() if 'Adjusted Amount' in investment_actions.columns else investment_actions['Amount'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Investment", f"₹{investment_amount:,.0f}")
            with col2:
                st.metric("Actual Allocated", f"₹{total_invested:,.0f}")
            with col3:
                st.metric("Stocks", len(investment_actions))
            
            st.divider()
            
            # Display investment table
            st.subheader("Stock Allocation")
            display_cols = ['Symbol', 'Weight %', 'Price', 'Calculated Qty', 'Adjusted Qty', 'Adjusted Amount']
            if all(col in investment_actions.columns for col in display_cols):
                display_table = investment_actions[display_cols].copy()
                display_table.columns = ['Symbol', 'Weight %', 'Price (₹)', 'Calc Qty', 'Quantity', 'Amount (₹)']
            else:
                display_table = investment_actions.copy()
            
            st.dataframe(
                display_table,
                use_container_width=True,
                hide_index=True,
            )
            
            # Download investment plan
            csv_investment = display_table.to_csv(index=False)
            st.download_button(
                label="📥 Download Investment Plan (CSV)",
                data=csv_investment,
                file_name="fresh_investment_plan.csv",
                mime="text/csv",
            )
            
            st.info("💡 Quantities are rounded to whole shares. 'Calc Qty' shows exact calculated amounts. Stocks with Calc Qty < 1 show as 0 Quantity (cannot buy fractional shares).")
            
        except Exception as e:
            st.error(f"Error processing model portfolio: {str(e)}")
            st.info("💡 Ensure your CSV has symbol and quantity columns. Price column is optional - you can enter prices manually if not detected.")

# ============================================================================
# MAIN APP LOGIC
# ============================================================================

if 'page' not in st.session_state:
    st.session_state.page = 'home'

if st.session_state.page == 'home':
    home_page()
elif st.session_state.page == 'rebalance':
    rebalance_existing_page()
elif st.session_state.page == 'fresh':
    fresh_investment_page()
