import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Stock Analysis Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50;
        color: white;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("📊 Navigation")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Select Page:",
    ["🏠 Home", "📈 Daily Signals", "🏆 Top Stocks Analysis", "ℹ️ About"],
    index=0
)

# Add timestamp of last update
st.sidebar.markdown("---")
st.sidebar.markdown("### ⏰ Last Update")
try:
    if os.path.exists('daily_signals_with_all_data.csv'):
        last_modified = os.path.getmtime('daily_signals_with_all_data.csv')
        last_update = datetime.fromtimestamp(last_modified).strftime('%Y-%m-%d %H:%M:%S')
        st.sidebar.success(f"📅 {last_update}")
    else:
        st.sidebar.warning("⚠️ No data available")
except Exception as e:
    st.sidebar.error("❌ Error checking update time")

# GitHub Repository Link
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 Repository")
st.sidebar.markdown("[View on GitHub](https://github.com/saimuralichitturi-bit/portfolio_streamlit_v1)")

# Page: Home Dashboard
if page == "🏠 Home":
    st.markdown('<p class="main-header">📊 Stock Analysis Dashboard</p>', unsafe_allow_html=True)
    
    st.markdown("""
    ### Welcome to the Automated Stock Analysis System
    
    This dashboard provides real-time insights into NSE stock market data with automated daily updates.
    """)
    
    # Quick Stats Overview
    col1, col2, col3 = st.columns(3)
    
    try:
        # Load signals data
        if os.path.exists('daily_signals_with_all_data.csv'):
            df_signals = pd.read_csv('daily_signals_with_all_data.csv')
            
            with col1:
                st.info("### 📈 Daily Signals")
                st.metric("Total Signals", len(df_signals))
                if "signal" in df_signals.columns:
                    buy_count = len(df_signals[df_signals["signal"] == 1])
                    sell_count = len(df_signals[df_signals["signal"] == 0])
        
                    st.write(f"🟢 Buy: {buy_count} | 🔴 Sell: {sell_count}")
        
        # Load top stocks data
        if os.path.exists('output/top30_stocks.csv'):
            df_top30 = pd.read_csv('output/top30_stocks.csv')
            
            with col2:
                st.success("### 🏆 Top Stocks")
                st.metric("Top 30 Stocks", len(df_top30))
                if 'volume' in df_top30.columns:
                    total_vol = df_top30['volume'].sum()
                    st.write(f"📊 Total Volume: {total_vol:,.0f}")
        
        with col3:
            st.warning("### 🕐 Next Update")
            st.write("**3:00 PM IST**")
            st.write("Monday - Friday")
            st.write("(Trading Days Only)")
    
    except Exception as e:
        st.error(f"Error loading overview data: {str(e)}")
    
    # Recent Activity
    st.markdown("---")
    st.subheader("📋 Recent Activity")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📁 Available Files")
        files_status = []
        
        files_to_check = [
            ('daily_signals_with_all_data.csv', 'Daily Signals'),
            ('output/top30_stocks.csv', 'Top 30 Stocks'),
            ('output/top20_stocks.csv', 'Top 20 Stocks'),
            ('output/top10_stocks.csv', 'Top 10 Stocks'),
            ('output/top5_stocks.csv', 'Top 5 Stocks'),
        ]
        
        for file_path, file_name in files_to_check:
            if os.path.exists(file_path):
                files_status.append(f"✅ {file_name}")
            else:
                files_status.append(f"❌ {file_name}")
        
        for status in files_status:
            st.write(status)
    
    with col2:
        st.markdown("#### 🔄 Pipeline Status")
        st.write("✅ GitHub Actions: Active")
        st.write("✅ Auto-commit: Enabled")
        st.write("✅ Scheduled: 3:00 PM IST")
        st.write("✅ Manual Trigger: Available")
    
    # Quick Links
    st.markdown("---")
    st.subheader("🚀 Quick Links")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📈 View Daily Signals", use_container_width=True):
            st.session_state.page = "📈 Daily Signals"
            st.rerun()
    
    with col2:
        if st.button("🏆 View Top Stocks", use_container_width=True):
            st.session_state.page = "🏆 Top Stocks Analysis"
            st.rerun()
    
    with col3:
        if st.button("ℹ️ About System", use_container_width=True):
            st.session_state.page = "ℹ️ About"
            st.rerun()

# Page: Daily Signals
elif page == "📈 Daily Signals":
    st.markdown('<p class="main-header">📈 Daily Trading Signals</p>', unsafe_allow_html=True)
    
    try:
        # Load the signals CSV
        df_signals = pd.read_csv('daily_signals_with_all_data.csv')
        
        # Check for required columns
        if df_signals.empty:
            st.warning("⚠️ The signals file is empty. Please wait for data generation.")
            st.stop()
        
        # Handle column names - try to identify signal column
        signal_col = None
        for col in df_signals.columns:
            if 'signal' in col.lower():
                signal_col = col
                break
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Signals", len(df_signals))
        with col2:
            if signal_col and signal_col in df_signals.columns:
                buy_signals = len(df_signals[df_signals[signal_col] == 1])
                st.metric("🟢 Buy Signals", buy_signals)
            else:
                st.metric("🟢 Buy Signals", "N/A")
        with col3:
            if signal_col and signal_col in df_signals.columns:
                sell_signals = len(df_signals[df_signals[signal_col] == 0])
                st.metric("🔴 Sell Signals", sell_signals)
            else:
                st.metric("🔴 Sell Signals", "N/A")
        with col4:
            symbol_col = 'symbol' if 'symbol' in df_signals.columns else df_signals.columns[0]
            unique_stocks = df_signals[symbol_col].nunique()
            st.metric("🎯 Unique Stocks", unique_stocks)
        
        st.markdown("---")
        
        # Visualization: Signal Distribution
        if signal_col and signal_col in df_signals.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                try:
                    signal_counts = df_signals[signal_col].astype(str).str.upper().value_counts()
                    fig = px.pie(
                        values=signal_counts.values,
                        names=signal_counts.index,
                        title="Signal Distribution",
                        color_discrete_sequence=['#00CC96', '#EF553B', '#636EFA']
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.info("📊 Signal distribution chart unavailable")
            
            with col2:
                volume_col = None
                for col in df_signals.columns:
                    if 'volume' in col.lower():
                        volume_col = col
                        break
                
                if volume_col and symbol_col:
                    try:
                        top_volume = df_signals.nlargest(10, volume_col)[[symbol_col, volume_col]]
                        fig = px.bar(
                            top_volume,
                            x=symbol_col,
                            y=volume_col,
                            title="Top 10 Stocks by Volume",
                            color=volume_col,
                            color_continuous_scale='Blues'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.info("📊 Volume chart unavailable")
        
        # Filters
        st.subheader("🔍 Filter Options")
        col1, col2, col3 = st.columns(3)
        
        filtered_df = df_signals.copy()
        
        with col1:
            if signal_col and signal_col in df_signals.columns:
                try:
                    signal_options = df_signals[signal_col].astype(str).str.upper().unique()
                    signal_filter = st.multiselect(
                        "Filter by Signal Type:",
                        options=signal_options,
                        default=signal_options
                    )
                    if signal_filter:
                        filtered_df = filtered_df[filtered_df[signal_col].astype(str).str.upper().isin(signal_filter)]
                except Exception as e:
                    st.info("Filter unavailable")
        
        with col2:
            if symbol_col:
                search_stock = st.text_input("🔎 Search Stock Symbol:", "")
                if search_stock:
                    try:
                        filtered_df = filtered_df[filtered_df[symbol_col].astype(str).str.contains(search_stock, case=False, na=False)]
                    except Exception as e:
                        st.warning("Search unavailable")
        
        with col3:
            sort_by = st.selectbox(
                "Sort by:",
                options=filtered_df.columns.tolist(),
                index=0
            )
            sort_order = st.radio("Order:", ["Descending", "Ascending"], horizontal=True)
            try:
                filtered_df = filtered_df.sort_values(
                    by=sort_by,
                    ascending=(sort_order == "Ascending")
                )
            except Exception as e:
                st.info("Sorting unavailable for this column")
        
        # Display the dataframe
        st.subheader("📋 Signals Data Table")
        
        # Create column config dynamically
        column_config = {}
        for col in filtered_df.columns:
            col_lower = col.lower()
            if 'symbol' in col_lower:
                column_config[col] = st.column_config.TextColumn(col, width="medium")
            elif 'signal' in col_lower:
                column_config[col] = st.column_config.TextColumn(col, width="small")
            elif 'price' in col_lower or 'close' in col_lower:
                column_config[col] = st.column_config.NumberColumn(col, format="₹%.2f")
            elif 'volume' in col_lower:
                column_config[col] = st.column_config.NumberColumn(col, format="%d")
        
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=500,
            column_config=column_config if column_config else None
        )
        
        # Download button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Filtered CSV",
                data=csv,
                file_name=f"daily_signals_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col2:
            st.metric("Filtered Results", len(filtered_df))
        
    except FileNotFoundError:
        st.error("❌ Daily signals file not found. Please run the analysis first.")
        st.info("💡 The file should be generated automatically at 3:00 PM IST on trading days.")
    except pd.errors.EmptyDataError:
        st.error("❌ The signals file is empty or corrupted.")
        st.info("💡 Please wait for the next data generation cycle.")
    except Exception as e:
        st.error(f"❌ Error loading signals: {str(e)}")
        st.info("💡 Please check if the CSV file format is correct.")
        st.code(str(e))

# Page: Top Stocks Analysis
elif page == "🏆 Top Stocks Analysis":
    st.markdown('<p class="main-header">🏆 Top Stocks Analysis</p>', unsafe_allow_html=True)
    
    # Check if output directory exists
    if not os.path.exists('output'):
        st.warning("⚠️ Output folder not found. The analysis will create it automatically.")
        st.info("💡 Files will be available after the first run at 3:00 PM IST.")
        st.stop()
    
    # Tabs for different top stocks
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Top 30 Stocks", "📈 Top 20 Stocks", "⭐ Top 10 Stocks", "🥇 Top 5 Stocks"])
    
    def display_stock_data(file_path, title, tab_key):
        try:
            df = pd.read_csv(file_path)
            
            if df.empty:
                st.warning(f"⚠️ {title} file is empty.")
                return
            
            # Identify columns dynamically
            symbol_col = None
            price_col = None
            volume_col = None
            change_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                if 'symbol' in col_lower and not symbol_col:
                    symbol_col = col
                elif ('close' in col_lower or 'price' in col_lower) and not price_col:
                    price_col = col
                elif 'volume' in col_lower and not volume_col:
                    volume_col = col
                elif 'change' in col_lower and 'percent' in col_lower and not change_col:
                    change_col = col
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total Stocks", len(df))
            with col2:
                if price_col:
                    try:
                        avg_price = df[price_col].mean()
                        st.metric("💰 Avg Price", f"₹{avg_price:.2f}")
                    except:
                        st.metric("💰 Avg Price", "N/A")
                else:
                    st.metric("💰 Avg Price", "N/A")
            with col3:
                if volume_col:
                    try:
                        total_volume = df[volume_col].sum()
                        st.metric("📈 Total Volume", f"{total_volume:,.0f}")
                    except:
                        st.metric("📈 Total Volume", "N/A")
                else:
                    st.metric("📈 Total Volume", "N/A")
            with col4:
                if change_col:
                    try:
                        avg_change = df[change_col].mean()
                        st.metric("📊 Avg Change %", f"{avg_change:.2f}%")
                    except:
                        st.metric("📊 Avg Change %", "N/A")
                else:
                    st.metric("📊 Avg Change %", "N/A")
            
            st.markdown("---")
            
            # Visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                if symbol_col and price_col:
                    try:
                        top_10 = df.head(10)
                        fig = px.bar(
                            top_10,
                            x=symbol_col,
                            y=price_col,
                            title=f"Top 10 by Price - {title}",
                            color=price_col,
                            color_continuous_scale='Viridis',
                            labels={price_col: 'Price (₹)', symbol_col: 'Stock Symbol'}
                        )
                        fig.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.info("📊 Price chart unavailable")
                else:
                    st.info("📊 Price data not available")
            
            with col2:
                if symbol_col and volume_col:
                    try:
                        top_10_vol = df.nlargest(10, volume_col)
                        fig = px.bar(
                            top_10_vol,
                            x=symbol_col,
                            y=volume_col,
                            title=f"Top 10 by Volume - {title}",
                            color=volume_col,
                            color_continuous_scale='Blues',
                            labels={volume_col: 'Volume', symbol_col: 'Stock Symbol'}
                        )
                        fig.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.info("📊 Volume chart unavailable")
                else:
                    st.info("📊 Volume data not available")
            
            # Additional visualization: Price vs Volume scatter
            if symbol_col and price_col and volume_col:
                try:
                    fig = px.scatter(
                        df.head(20),
                        x=volume_col,
                        y=price_col,
                        text=symbol_col,
                        title=f"Price vs Volume Analysis - {title}",
                        color=price_col,
                        size=volume_col,
                        color_continuous_scale='Turbo',
                        labels={price_col: 'Price (₹)', volume_col: 'Volume'}
                    )
                    fig.update_traces(textposition='top center')
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    pass
            
            st.markdown("---")
            
            # Search and filter
            col1, col2 = st.columns(2)
            
            filtered_df = df.copy()
            
            with col1:
                if symbol_col:
                    search = st.text_input(f"🔎 Search in {title}:", key=f"search_{tab_key}")
                    if search:
                        try:
                            filtered_df = filtered_df[filtered_df[symbol_col].astype(str).str.contains(search, case=False, na=False)]
                        except:
                            pass
            
            with col2:
                if len(df.columns) > 1:
                    sort_col = st.selectbox(
                        "Sort by:",
                        options=df.columns.tolist(),
                        key=f"sort_{tab_key}"
                    )
                    try:
                        filtered_df = filtered_df.sort_values(by=sort_col, ascending=False)
                    except:
                        pass
            
            # Display dataframe
            st.subheader(f"📋 {title} Data Table")
            
            # Create column config dynamically
            column_config = {}
            for col in filtered_df.columns:
                col_lower = col.lower()
                if 'symbol' in col_lower:
                    column_config[col] = st.column_config.TextColumn(col, width="medium")
                elif 'close' in col_lower or 'price' in col_lower:
                    column_config[col] = st.column_config.NumberColumn(col, format="₹%.2f")
                elif 'volume' in col_lower:
                    column_config[col] = st.column_config.NumberColumn(col, format="%d")
                elif 'change' in col_lower and 'percent' in col_lower:
                    column_config[col] = st.column_config.NumberColumn(col, format="%.2f%%")
            
            st.dataframe(
                filtered_df,
                use_container_width=True,
                height=400,
                column_config=column_config if column_config else None
            )
            
            # Download button and stats
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label=f"📥 Download CSV",
                    data=csv,
                    file_name=f"{title.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key=f"download_{tab_key}",
                    use_container_width=True
                )
            with col2:
                st.metric("Filtered Results", len(filtered_df))
            
        except FileNotFoundError:
            st.warning(f"⚠️ {title} file not found in output folder.")
            st.info("💡 The file will be generated automatically at 3:00 PM IST on trading days.")
        except pd.errors.EmptyDataError:
            st.error(f"❌ {title} file is empty or corrupted.")
        except Exception as e:
            st.error(f"❌ Error loading {title}: {str(e)}")
            with st.expander("🔍 View Error Details"):
                st.code(str(e))
    
    with tab1:
        display_stock_data('output/top30_stocks.csv', 'Top 30 Stocks', 'top30')
    
    with tab2:
        display_stock_data('output/top20_stocks.csv', 'Top 20 Stocks', 'top20')
    
    with tab3:
        display_stock_data('output/top10_stocks.csv', 'Top 10 Stocks', 'top10')
    
    with tab4:
        display_stock_data('output/top5_stocks.csv', 'Top 5 Stocks', 'top5')

# Page: About
elif page == "ℹ️ About":
    st.markdown('<p class="main-header">ℹ️ About This Dashboard</p>', unsafe_allow_html=True)
    
    # System Overview
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## 📊 Stock Analysis Pipeline
        
        This dashboard provides automated stock analysis with daily updates from the NSE market.
        The system runs completely automated through GitHub Actions.
        
        ### 🎯 Key Features
        
        - **📈 Daily Signals**: Real-time trading signals with comprehensive data
        - **🏆 Top Stocks Analysis**: Curated lists of top performing stocks (30/20/10/5)
        - **🤖 Automated Updates**: Data refreshed daily at 3:00 PM IST
        - **🔄 GitHub Integration**: All results committed to repository automatically
        - **📊 Interactive Visualizations**: Charts and graphs for better insights
        - **🔍 Advanced Filtering**: Search and filter capabilities
        - **📥 Export Data**: Download any dataset as CSV
        """)
    
    with col2:
        st.info("""
        ### 📈 Statistics
        
        **Update Frequency**  
        Daily (Mon-Fri)
        
        **Update Time**  
        3:00 PM IST
        
        **Data Source**  
        NSE via Kite API
        
        **Automation**  
        GitHub Actions
        
        **Tech Stack**  
        Python, Streamlit, Pandas
        """)
    
    st.markdown("---")
    
    # Data Pipeline Flow
    st.subheader("🔄 Data Pipeline Flow")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### Step 1: Data Collection
        **`stock_pred.py`**
        - 🔌 Connects to Kite API
        - 📥 Fetches NSE market data
        - 💾 Updates `nse_complete_data.pickle`
        - 📊 Generates `daily_signals_with_all_data.csv`
        - ✅ Commits to GitHub
        """)
    
    with col2:
        st.markdown("""
        #### Step 2: Analysis & Processing
        **`main.py`**
        - 📖 Reads daily signals CSV
        - 🔍 Analyzes and processes data
        - 📁 Creates output folder
        - 📈 Generates top stocks files
        - ✅ Commits results to GitHub
        """)
    
    st.markdown("---")
    
    # Schedule Information
    st.subheader("⏰ Automation Schedule")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.success("""
        **🕐 Execution Time**
        
        3:00 PM IST  
        (9:30 AM UTC)
        """)
    
    with col2:
        st.info("""
        **📅 Frequency**
        
        Monday - Friday  
        (Trading Days Only)
        """)
    
    with col3:
        st.warning("""
        **🔄 Trigger Type**
        
        Automatic via Cron  
        Manual option available
        """)
    
    st.markdown("---")
    
    # Technical Details
    st.subheader("🛠️ Technical Stack")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **Frontend**
        - Streamlit
        - Plotly
        - Pandas
        """)
    
    with col2:
        st.markdown("""
        **Backend**
        - Python 3.10
        - Kite Connect API
        - GitHub Actions
        """)
    
    with col3:
        st.markdown("""
        **Data Storage**
        - CSV Files
        - Pickle Files
        - GitHub Repository
        """)
    
    st.markdown("---")
    
    # Future Enhancements
    st.subheader("🚀 Future Enhancements")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### Planned Features
        - [ ] Real-time price updates
        - [ ] Historical performance tracking
        - [ ] Advanced technical indicators
        - [ ] Email/SMS alerts
        - [ ] Portfolio management
        - [ ] Backtesting capabilities
        """)
    
    with col2:
        st.markdown("""
        #### Additional Pages
        - [ ] Market Overview
        - [ ] Sector Analysis
        - [ ] Watchlist Manager
        - [ ] Performance Metrics
        - [ ] Settings & Configuration
        - [ ] User Preferences
        """)
    
    st.markdown("---")
    
    # Links and Resources
    st.subheader("🔗 Links & Resources")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **📚 Documentation**
        - [GitHub Repository](https://github.com/saimuralichitturi-bit/portfolio_streamlit_v1)
        - [Kite API Docs](https://kite.trade/docs/connect/v3/)
        - [Streamlit Docs](https://docs.streamlit.io/)
        """)
    
    with col2:
        st.markdown("""
        **🔧 Tools**
        - [GitHub Actions](https://github.com/features/actions)
        - [Streamlit Cloud](https://streamlit.io/cloud)
        - [Python.org](https://www.python.org/)
        """)
    
    with col3:
        st.markdown("""
        **💬 Support**
        - Report Issues on GitHub
        - Check Actions Logs
        - Review Documentation
        """)
    
    st.markdown("---")
    
    # Disclaimer
    st.warning("""
    ⚠️ **Disclaimer**: This tool is for educational and informational purposes only. 
    Always do your own research before making investment decisions. 
    Past performance does not guarantee future results.
    """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Made with ❤️ using Streamlit | Automated with GitHub Actions</p>
        <p>© 2024 Stock Analysis Pipeline | All Rights Reserved</p>
    </div>
    """, unsafe_allow_html=True)

# Footer in Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 Quick Actions")
if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("💡 Tip: Data updates automatically at 3:00 PM IST on trading days")