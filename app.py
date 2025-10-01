import streamlit as st
import pandas as pd
import os
from pathlib import Path
import time
from datetime import datetime
import json

# Page configuration
st.set_page_config(
    page_title="Research Portal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Clean, modern dark theme CSS
st.markdown("""
<style>
    /* Global styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
        transition: all 0.2s ease;
    }
    
    /* Hide Streamlit elements */
    #MainMenu, footer, header {display: none;}
    
    /* Dark theme base */
    .main {
        background-color: #0f1117;
        color: #e6e6e6;
    }
    
    /* Typography */
    h1, h2, h3 {
        color: #ffffff;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    .subtitle {
        color: #a3a3a3;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    
    /* Cards */
    .card {
        background: #1a1f2e;
        border: 1px solid #2d3347;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    /* Inputs and buttons */
    .stTextInput > div > div > input,
    .stSelectbox > div > div {
        background: #1a1f2e;
        border: 1px solid #2d3347;
        border-radius: 6px;
        color: #ffffff;
        padding: 0.5rem 1rem;
    }
    
    .stButton > button {
        background: #3b5bdb;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background: #4c6ef5;
        box-shadow: 0 2px 6px rgba(59, 91, 219, 0.2);
    }
    
    /* Tables */
    .dataframe {
        background: #1a1f2e !important;
        border: 1px solid #2d3347 !important;
        border-radius: 6px !important;
    }
    
    /* Metrics */
    .metric-card {
        background: #1a1f2e;
        border: 1px solid #2d3347;
        border-radius: 6px;
        padding: 1rem;
        text-align: center;
    }
    
    .metric-value {
        color: #ffffff;
        font-size: 1.5rem;
        font-weight: 600;
    }
    
    .metric-label {
        color: #a3a3a3;
        font-size: 0.85rem;
        margin-top: 0.25rem;
    }
    
    /* Charts */
    .js-plotly-plot {
        background: #1a1f2e !important;
        border: 1px solid #2d3347 !important;
        border-radius: 6px !important;
        padding: 1rem !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #1a1f2e;
        border-radius: 6px;
        padding: 0.5rem;
        gap: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 4px;
        color: #a3a3a3;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: #3b5bdb;
        color: white;
    }
    
    /* Status indicator */
    .status {
        color: #a3a3a3;
        font-size: 0.85rem;
        text-align: center;
        margin-top: 2rem;
    }
    
    .status-dot {
        display: inline-block;
        width: 6px;
        height: 6px;
        background: #4ade80;
        border-radius: 50%;
        margin-right: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'selected_file' not in st.session_state:
    st.session_state.selected_file = None
if 'excel_data' not in st.session_state:
    st.session_state.excel_data = None
if 'filters_config' not in st.session_state:
    st.session_state.filters_config = {}
if 'stage' not in st.session_state:
    st.session_state.stage = 'login'
if 'active_filters' not in st.session_state:
    st.session_state.active_filters = {}
if 'data_insights' not in st.session_state:
    st.session_state.data_insights = {}
if 'user_email' not in st.session_state:
    st.session_state.user_email = None

def authenticate(email):
    """Authenticate user with @ey.com email"""
    return email.strip().lower().endswith('@in.ey.com')

def get_excel_files():
    """Get all Excel files in the current directory"""
    excel_files = []
    for file in Path('.').glob('*.xlsx'):
        if not file.name.startswith('~'):
            excel_files.append(file.name)
    return sorted(excel_files)

def load_excel_file(filename):
    """Load Excel file with all sheets"""
    try:
        excel_file = pd.ExcelFile(filename)
        data = {}
        for sheet_name in excel_file.sheet_names:
            data[sheet_name] = pd.read_excel(filename, sheet_name=sheet_name)
        return data
    except Exception as e:
        st.error(f"⚠️ Error loading file: {str(e)}")
        return None

def calculate_insights(data):
    """Calculate data insights for visualization"""
    insights = {}
    for sheet_name, df in data.items():
        insights[sheet_name] = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'numeric_columns': len(df.select_dtypes(include=['number']).columns),
            'text_columns': len(df.select_dtypes(include=['object']).columns),
            'missing_values': df.isnull().sum().sum(),
            'memory_usage': df.memory_usage(deep=True).sum() / 1024 / 1024  # MB
        }
    return insights

def create_overview_chart(insights):
    """Create an overview visualization of all sheets"""
    sheet_names = list(insights.keys())
    rows = [insights[sheet]['total_rows'] for sheet in sheet_names]
    cols = [insights[sheet]['total_columns'] for sheet in sheet_names]
    # Instead of chart, return a summary string
    summary = f"Sheets: {', '.join(sheet_names)}\nRows: {rows}\nColumns: {cols}"
    return summary

def apply_filter(df, column, filter_values):
    """Apply filter to dataframe"""
    if filter_values and len(filter_values) > 0:
        return df[df[column].isin(filter_values)]
    return df

# ============================================================================
# LOGIN PAGE
# ============================================================================
if not st.session_state.authenticated:
    st.markdown("<div class='fade-in'>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        
        st.markdown("<h1 class='main-title'>🔬 Research Portal</h1>", unsafe_allow_html=True)
        st.markdown("<p class='subtitle'>Next-generation data exploration platform</p>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        email = st.text_input(
            "Email Address",
            placeholder="your.name@in.ey.com",
            key="email_input",
            label_visibility="collapsed"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 ACCESS PORTAL", use_container_width=True):
            if authenticate(email):
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.session_state.stage = 'file_selection'
                st.success(f"✨ Welcome aboard, {email.split('@')[0]}!")
                time.sleep(0.8)
                st.rerun()
            else:
                st.error("⚠️ Access denied. Please use your @in.ey.com email address.")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Status indicator
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<div style='text-align: center; color: #a0a0b0;'>"
            "<span class='status-dot'></span>All systems operational"
            "</div>",
            unsafe_allow_html=True
        )
    
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================================
# FILE SELECTION PAGE
# ============================================================================
elif st.session_state.stage == 'file_selection':
    st.markdown("<div class='fade-in'>", unsafe_allow_html=True)
    
    # Header with user info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h1 class='main-title'>📚 Research Library</h1>", unsafe_allow_html=True)
        st.markdown("<p class='subtitle'>Select your dataset to begin exploration</p>", unsafe_allow_html=True)
    with col2:
        if st.session_state.user_email:
            st.markdown(
                f"<div style='text-align: right; color: #48dbfb; margin-top: 2rem;'>"
                f"👤 {st.session_state.user_email.split('@')[0]}"
                f"</div>",
                unsafe_allow_html=True
            )
    
    excel_files = get_excel_files()
    
    if not excel_files:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.warning("⚠️ No Excel files found in the repository.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        
        # File stats
        st.markdown(f"<div class='stat-label'>AVAILABLE DATASETS</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='stat-number'>{len(excel_files)}</div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        selected_file = st.selectbox(
            "Choose your research file",
            excel_files,
            key="file_selector"
        )
        
        # Show file info
        if selected_file:
            file_path = Path(selected_file)
            file_size = file_path.stat().st_size / 1024 / 1024  # MB
            file_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(
                    f"<div class='stat-card'>"
                    f"<div style='color: #a0a0b0; font-size: 0.9rem;'>FILE SIZE</div>"
                    f"<div style='color: white; font-size: 1.5rem; font-weight: 600; margin-top: 0.5rem;'>"
                    f"{file_size:.2f} MB</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            with col2:
                st.markdown(
                    f"<div class='stat-card'>"
                    f"<div style='color: #a0a0b0; font-size: 0.9rem;'>LAST MODIFIED</div>"
                    f"<div style='color: white; font-size: 1.5rem; font-weight: 600; margin-top: 0.5rem;'>"
                    f"{file_modified.strftime('%d %b')}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            with col3:
                st.markdown(
                    f"<div class='stat-card'>"
                    f"<div style='color: #a0a0b0; font-size: 0.9rem;'>FORMAT</div>"
                    f"<div style='color: white; font-size: 1.5rem; font-weight: 600; margin-top: 0.5rem;'>"
                    f"XLSX</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("🔍 EXPLORE DATA", use_container_width=True):
                st.session_state.selected_file = selected_file
                st.session_state.stage = 'filter_setup'
                time.sleep(0.3)
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================================
# FILTER SETUP PAGE
# ============================================================================
elif st.session_state.stage == 'filter_setup':
    st.markdown("<div class='fade-in'>", unsafe_allow_html=True)
    
    st.markdown("<h1 class='main-title'>⚙️ Configure Filters</h1>", unsafe_allow_html=True)
    st.markdown(
        f"<p class='subtitle'>Customizing view for: <code>{st.session_state.selected_file}</code></p>",
        unsafe_allow_html=True
    )
    
    # Load Excel data
    if st.session_state.excel_data is None:
        with st.spinner("🔄 Loading data..."):
            st.session_state.excel_data = load_excel_file(st.session_state.selected_file)
            if st.session_state.excel_data:
                st.session_state.data_insights = calculate_insights(st.session_state.excel_data)
    
    if st.session_state.excel_data:
        # Show data overview
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        
        st.markdown("### 📊 Data Overview")
        
        # Create visualization
        summary = create_overview_chart(st.session_state.data_insights)
        st.write(summary)
        
        # Summary stats
        total_rows = sum(insight['total_rows'] for insight in st.session_state.data_insights.values())
        total_sheets = len(st.session_state.excel_data)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(
                f"<div class='stat-card'>"
                f"<div class='stat-number'>{total_sheets}</div>"
                f"<div class='stat-label'>Sheets</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                f"<div class='stat-card'>"
                f"<div class='stat-number'>{total_rows:,}</div>"
                f"<div class='stat-label'>Total Rows</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        with col3:
            total_cols = sum(insight['total_columns'] for insight in st.session_state.data_insights.values())
            st.markdown(
                f"<div class='stat-card'>"
                f"<div class='stat-number'>{total_cols}</div>"
                f"<div class='stat-label'>Total Columns</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        with col4:
            total_memory = sum(insight['memory_usage'] for insight in st.session_state.data_insights.values())
            st.markdown(
                f"<div class='stat-card'>"
                f"<div class='stat-number'>{total_memory:.1f}</div>"
                f"<div class='stat-label'>MB in Memory</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Filter configuration
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        
        st.markdown("### 🎯 Filter Configuration")
        
        apply_filters = st.radio(
            "Would you like to apply filters to the data?",
            ["No filters - show all data", "Yes - configure custom filters"],
            key="filter_choice"
        )
        
        if apply_filters == "Yes - configure custom filters":
            st.markdown("<br>", unsafe_allow_html=True)
            
            filters_config = {}
            
            for sheet_name, df in st.session_state.excel_data.items():
                with st.expander(f"📄 {sheet_name} ({len(df)} rows)", expanded=False):
                    columns = df.columns.tolist()
                    selected_columns = st.multiselect(
                        f"Select filter columns for {sheet_name}",
                        columns,
                        key=f"filter_{sheet_name}"
                    )
                    if selected_columns:
                        filters_config[sheet_name] = selected_columns
            
            st.session_state.filters_config = filters_config
        else:
            st.session_state.filters_config = {}
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("📈 VIEW DATA", use_container_width=True):
                st.session_state.stage = 'data_view'
                time.sleep(0.3)
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================================
# DATA VIEW PAGE
# ============================================================================
elif st.session_state.stage == 'data_view':
    st.markdown("<div class='fade-in'>", unsafe_allow_html=True)
    
    # Header with navigation
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("<h1 class='main-title'>📊 Data Explorer</h1>", unsafe_allow_html=True)
        st.markdown(f"<p class='subtitle'><code>{st.session_state.selected_file}</code></p>", unsafe_allow_html=True)
    with col2:
        if st.button("◀ Back", use_container_width=True):
            st.session_state.stage = 'file_selection'
            st.session_state.selected_file = None
            st.session_state.excel_data = None
            st.session_state.filters_config = {}
            st.session_state.active_filters = {}
            st.session_state.data_insights = {}
            st.rerun()
    
    if st.session_state.excel_data:
        sheet_names = list(st.session_state.excel_data.keys())
        
        # Create tabs for sheets
        tabs = st.tabs([f"📄 {name}" for name in sheet_names])
        
        for idx, (tab, sheet_name) in enumerate(zip(tabs, sheet_names)):
            with tab:
                df = st.session_state.excel_data[sheet_name].copy()
                original_count = len(df)
                
                # Show filters for this sheet if configured
                if sheet_name in st.session_state.filters_config:
                    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                    st.markdown("### 🔍 Active Filters")
                    
                    filter_columns = st.session_state.filters_config[sheet_name]
                    
                    # Initialize active filters for this sheet if not exists
                    if sheet_name not in st.session_state.active_filters:
                        st.session_state.active_filters[sheet_name] = {}
                    
                    # Create filter columns
                    num_filters = len(filter_columns)
                    filter_cols = st.columns(min(num_filters, 3))
                    
                    for col_idx, filter_col in enumerate(filter_columns):
                        with filter_cols[col_idx % 3]:
                            unique_values = df[filter_col].dropna().unique().tolist()
                            
                            selected_values = st.multiselect(
                                filter_col,
                                unique_values,
                                key=f"active_filter_{sheet_name}_{filter_col}",
                                default=st.session_state.active_filters[sheet_name].get(filter_col, [])
                            )
                            
                            st.session_state.active_filters[sheet_name][filter_col] = selected_values
                            
                            # Apply filter
                            if selected_values:
                                df = apply_filter(df, filter_col, selected_values)
                    
                    # Clear filters button
                    if any(st.session_state.active_filters[sheet_name].values()):
                        if st.button("🔄 Clear All Filters", key=f"clear_{sheet_name}"):
                            st.session_state.active_filters[sheet_name] = {}
                            st.rerun()
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                
                # Data statistics card
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(
                        f"<div class='stat-card'>"
                        f"<div class='stat-number'>{len(df):,}</div>"
                        f"<div class='stat-label'>Rows Displayed</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                
                with col2:
                    filtered_pct = (len(df) / original_count * 100) if original_count > 0 else 0
                    st.markdown(
                        f"<div class='stat-card'>"
                        f"<div class='stat-number'>{filtered_pct:.1f}%</div>"
                        f"<div class='stat-label'>Data Shown</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                
                with col3:
                    active_filter_count = sum(
                        1 for filters in st.session_state.active_filters.get(sheet_name, {}).values() 
                        if filters
                    )
                    st.markdown(
                        f"<div class='stat-card'>"
                        f"<div class='stat-number'>{active_filter_count}</div>"
                        f"<div class='stat-label'>Active Filters</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                
                with col4:
                    st.markdown(
                        f"<div class='stat-card'>"
                        f"<div class='stat-number'>{len(df.columns)}</div>"
                        f"<div class='stat-label'>Columns</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Quick insights
                if len(df) > 0:
                    st.markdown("### 📈 Quick Insights")
                    
                    # Find numeric columns for insights
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    
                    if numeric_cols:
                        insight_cols = st.columns(min(len(numeric_cols), 4))
                        
                        for i, col in enumerate(numeric_cols[:4]):
                            with insight_cols[i]:
                                avg_val = df[col].mean()
                                st.markdown(
                                    f"<div style='background: rgba(120, 119, 198, 0.1); "
                                    f"padding: 1rem; border-radius: 12px; "
                                    f"border: 1px solid rgba(120, 119, 198, 0.3);'>"
                                    f"<div style='color: #a0a0b0; font-size: 0.8rem;'>{col}</div>"
                                    f"<div style='color: white; font-size: 1.3rem; font-weight: 600; margin-top: 0.5rem;'>"
                                    f"{avg_val:,.2f}</div>"
                                    f"<div style='color: #48dbfb; font-size: 0.8rem;'>Average</div>"
                                    f"</div>",
                                    unsafe_allow_html=True
                                )
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Data table
                st.markdown("### 📋 Data Table")
                
                # Search functionality
                search_term = st.text_input(
                    "🔍 Search in table",
                    key=f"search_{sheet_name}",
                    placeholder="Type to search..."
                )
                
                if search_term:
                    # Search across all columns
                    mask = df.astype(str).apply(
                        lambda x: x.str.contains(search_term, case=False, na=False)
                    ).any(axis=1)
                    df = df[mask]
                    st.info(f"Found {len(df)} matching rows")
                
                st.dataframe(
                    df,
                    use_container_width=True,
                    height=500
                )
                
                # Download button
                st.markdown("<br>", unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([2, 1, 2])
                with col2:
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Filtered Data",
                        data=csv,
                        file_name=f"{sheet_name}_filtered.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Footer with timestamp
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='text-align: center; color: #7C7C8C; font-size: 0.85rem;'>"
        f"Last updated: {datetime.now().strftime('%d %B %Y, %H:%M:%S')} | "
        f"<span class='status-dot'></span>Session active"
        f"</div>",
        unsafe_allow_html=True
    )

