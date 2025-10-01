import streamlit as st
import pandas as pd
import os
from pathlib import Path
import time
from datetime import datetime
import json
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Check for required dependencies
try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    import xlrd
    XLRD_AVAILABLE = True
except ImportError:
    XLRD_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

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
    .card, .glass-card, .stat-card {
        background: #1a1f2e;
        border: 1px solid #2d3347;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    /* Inputs and buttons */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {
        background: #1a1f2e !important;
        border: 1px solid #2d3347 !important;
        border-radius: 6px !important;
        color: #ffffff !important;
        padding: 0.5rem 1rem !important;
    }
    
    .stSelectbox > div > div {
        background: #1a1f2e !important;
        border: 1px solid #2d3347 !important;
        border-radius: 6px !important;
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
    
    .stat-label {
        color: #a3a3a3;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stat-number {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    
    .main-title {
        font-size: 2.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
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
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* PDF Viewer */
    .pdf-container {
        background: #1a1f2e;
        border: 1px solid #2d3347;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    
    .pdf-page {
        max-width: 100%;
        height: auto;
        border-radius: 4px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Add custom CSS to make selectbox text white
st.markdown("""
<style>
.stSelectbox > div > div > select {
    color: #fff !important;
}
.stSelectbox label {
    color: #fff !important;
}
</style>
""", unsafe_allow_html=True)

# Improved custom CSS for selectbox
st.markdown("""
<style>
.stSelectbox > div > div > select {
    color: #fff !important;
    background: #fff !important;
}
.stSelectbox label {
    color: #fff !important;
}
.stSelectbox > div > div {
    background: #fff !important;
    color: #222 !important;
}
.stSelectbox > div[data-baseweb="select"] > div {
    background: #fff !important;
    color: #222 !important;
}
.stSelectbox [data-baseweb="select"] span {
    color: #222 !important;
}
.stSelectbox [data-baseweb="select"] div[role="option"] {
    color: #222 !important;
    background: #fff !important;
}
.stSelectbox [data-baseweb="select"] div[aria-selected="true"] {
    color: #fff !important;
    background: #3b5bdb !important;
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
if 'file_type' not in st.session_state:
    st.session_state.file_type = None
if 'pdf_page' not in st.session_state:
    st.session_state.pdf_page = 1

def authenticate(email):
    """Authenticate user with @in.ey.com email"""
    if not email:
        return False
    return email.strip().lower().endswith('@in.ey.com')

def get_files():
    """Get all Excel and PDF files in the current directory"""
    files = []
    try:
        # Check for Excel files
        if OPENPYXL_AVAILABLE:
            for file in Path('.').glob('*.xlsx'):
                if not file.name.startswith('~') and not file.name.startswith('.'):
                    files.append(file.name)
        
        if XLRD_AVAILABLE:
            for file in Path('.').glob('*.xls'):
                if not file.name.startswith('~') and not file.name.startswith('.'):
                    files.append(file.name)
        
        # Check for PDF files
        for file in Path('.').glob('*.pdf'):
            if not file.name.startswith('~') and not file.name.startswith('.'):
                files.append(file.name)
        
        if not OPENPYXL_AVAILABLE and not XLRD_AVAILABLE:
            st.error("⚠️ No Excel libraries found. Please install 'openpyxl' for .xlsx files or 'xlrd' for .xls files.")
            st.code("pip install openpyxl", language="bash")
            
    except Exception as e:
        st.error(f"Error scanning for files: {str(e)}")
    return sorted(files)

def load_excel_file(filename):
    """Load Excel file with all sheets"""
    file_ext = Path(filename).suffix.lower()
    
    if file_ext == '.xlsx' and not OPENPYXL_AVAILABLE:
        st.error("⚠️ Missing dependency: 'openpyxl' is required to read .xlsx files.")
        st.info("📦 Install it using: `pip install openpyxl`")
        return None
    
    if file_ext == '.xls' and not XLRD_AVAILABLE:
        st.error("⚠️ Missing dependency: 'xlrd' is required to read .xls files.")
        st.info("📦 Install it using: `pip install xlrd`")
        return None
    
    try:
        engine = 'openpyxl' if file_ext == '.xlsx' else 'xlrd'
        excel_file = pd.ExcelFile(filename, engine=engine)
        data = {}
        
        for sheet_name in excel_file.sheet_names:
            try:
                df = pd.read_excel(filename, sheet_name=sheet_name, engine=engine)
                if df.empty:
                    st.warning(f"Sheet '{sheet_name}' is empty")
                    continue
                data[sheet_name] = df
            except Exception as e:
                st.warning(f"Could not load sheet '{sheet_name}': {str(e)}")
                continue
        
        if not data:
            st.error("No valid sheets found in the Excel file")
            return None
        return data
    except Exception as e:
        st.error(f"⚠️ Error loading file: {str(e)}")
        return None

def calculate_insights(data):
    """Calculate data insights for visualization"""
    insights = {}
    for sheet_name, df in data.items():
        try:
            insights[sheet_name] = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'numeric_columns': len(df.select_dtypes(include=['number']).columns),
                'text_columns': len(df.select_dtypes(include=['object']).columns),
                'missing_values': int(df.isnull().sum().sum()),
                'memory_usage': df.memory_usage(deep=True).sum() / 1024 / 1024
            }
        except Exception as e:
            st.warning(f"Could not calculate insights for '{sheet_name}': {str(e)}")
            insights[sheet_name] = {
                'total_rows': 0,
                'total_columns': 0,
                'numeric_columns': 0,
                'text_columns': 0,
                'missing_values': 0,
                'memory_usage': 0
            }
    return insights

def create_overview_summary(insights):
    """Create an overview summary of all sheets"""
    if not insights:
        return "No data available"
    
    sheet_names = list(insights.keys())
    rows = [insights[sheet]['total_rows'] for sheet in sheet_names]
    cols = [insights[sheet]['total_columns'] for sheet in sheet_names]
    
    summary_parts = []
    for i, sheet in enumerate(sheet_names):
        summary_parts.append(f"**{sheet}**: {rows[i]:,} rows × {cols[i]} columns")
    
    return " | ".join(summary_parts)

def apply_filter(df, column, filter_values):
    """Apply filter to dataframe"""
    if not filter_values or len(filter_values) == 0:
        return df
    try:
        return df[df[column].isin(filter_values)]
    except Exception as e:
        st.warning(f"Could not apply filter on column '{column}': {str(e)}")
        return df

def get_color_palette(n):
    """Generate distinct colors for graphs"""
    colors = [
        '#667eea', '#764ba2', '#f093fb', '#4facfe',
        '#43e97b', '#fa709a', '#fee140', '#30cfd0',
        '#a8edea', '#fed6e3', '#c471f5', '#fa71cd',
        '#f38181', '#ffc75f', '#d8b5ff', '#1dd1a1',
        '#ee5a6f', '#f0932b', '#6c5ce7', '#00b894'
    ]
    return colors[:n] if n <= len(colors) else colors * (n // len(colors) + 1)

def create_visualization(df, time_col, category_col, value_cols, chart_type, selected_categories=None):
    """Create visualization based on user selections"""
    try:
        # Filter by selected categories if specified
        if selected_categories and len(selected_categories) > 0:
            df_filtered = df[df[category_col].isin(selected_categories)].copy()
        else:
            df_filtered = df.copy()
        
        if df_filtered.empty:
            st.warning("No data available for selected categories")
            return None
        
        # Sort by time column
        df_filtered = df_filtered.sort_values(time_col)
        
        # Create figure
        fig = go.Figure()
        
        # Get colors
        categories = df_filtered[category_col].unique()
        colors = get_color_palette(len(categories))
        color_map = dict(zip(categories, colors))
        
        if chart_type == "Line Chart":
            for category in categories:
                cat_data = df_filtered[df_filtered[category_col] == category]
                for value_col in value_cols:
                    fig.add_trace(go.Scatter(
                        x=cat_data[time_col],
                        y=cat_data[value_col],
                        mode='lines+markers',
                        name=f"{category} - {value_col}",
                        line=dict(color=color_map[category], width=2),
                        marker=dict(size=6)
                    ))
        
        elif chart_type == "Bar Chart":
            for i, value_col in enumerate(value_cols):
                for category in categories:
                    cat_data = df_filtered[df_filtered[category_col] == category]
                    fig.add_trace(go.Bar(
                        x=cat_data[time_col],
                        y=cat_data[value_col],
                        name=f"{category} - {value_col}",
                        marker_color=color_map[category]
                    ))
        
        elif chart_type == "Area Chart":
            for category in categories:
                cat_data = df_filtered[df_filtered[category_col] == category]
                for value_col in value_cols:
                    fig.add_trace(go.Scatter(
                        x=cat_data[time_col],
                        y=cat_data[value_col],
                        mode='lines',
                        name=f"{category} - {value_col}",
                        fill='tonexty',
                        line=dict(color=color_map[category], width=2)
                    ))
        
        elif chart_type == "Scatter Plot":
            for category in categories:
                cat_data = df_filtered[df_filtered[category_col] == category]
                for value_col in value_cols:
                    fig.add_trace(go.Scatter(
                        x=cat_data[time_col],
                        y=cat_data[value_col],
                        mode='markers',
                        name=f"{category} - {value_col}",
                        marker=dict(
                            color=color_map[category],
                            size=10,
                            line=dict(width=1, color='white')
                        )
                    ))
        
        # Update layout for dark theme
        fig.update_layout(
            plot_bgcolor='#0f1117',
            paper_bgcolor='#1a1f2e',
            font=dict(color='#e6e6e6'),
            xaxis=dict(
                gridcolor='#2d3347',
                showgrid=True,
                title=time_col
            ),
            yaxis=dict(
                gridcolor='#2d3347',
                showgrid=True,
                title='Value'
            ),
            hovermode='x unified',
            legend=dict(
                bgcolor='rgba(26, 31, 46, 0.8)',
                bordercolor='#2d3347',
                borderwidth=1
            ),
            margin=dict(l=50, r=50, t=50, b=50),
            height=500
        )
        
        return fig
    
    except Exception as e:
        st.error(f"Error creating visualization: {str(e)}")
        return None

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
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h1 class='main-title'>📚 Research Library</h1>", unsafe_allow_html=True)
        st.markdown("<p class='subtitle'>Select your dataset to begin exploration</p>", unsafe_allow_html=True)
    with col2:
        if st.session_state.user_email:
            user_display = st.session_state.user_email.split('@')[0]
            st.markdown(
                f"<div style='text-align: right; color: #48dbfb; margin-top: 2rem;'>"
                f"👤 {user_display}"
                f"</div>",
                unsafe_allow_html=True
            )
    
    files = get_files()
    
    if not files:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.warning("⚠️ No files found in the current directory. Please add .xlsx, .xls, or .pdf files.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='stat-label'>AVAILABLE DATASETS</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='stat-number'>{len(files)}</div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        selected_file = st.selectbox(
            "Choose your research file",
            files,
            key="file_selector"
        )
        
        if selected_file:
            try:
                file_path = Path(selected_file)
                file_size = file_path.stat().st_size / 1024 / 1024
                file_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("FILE SIZE", f"{file_size:.2f} MB")
                with col2:
                    st.metric("LAST MODIFIED", file_modified.strftime('%d %b'))
                with col3:
                    file_ext = file_path.suffix.upper().replace('.', '')
                    st.metric("FORMAT", file_ext)
            except Exception as e:
                st.error(f"Error reading file information: {str(e)}")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("🔍 EXPLORE DATA", use_container_width=True):
                st.session_state.selected_file = selected_file
                file_ext = Path(selected_file).suffix.lower()
                st.session_state.file_type = file_ext
                
                if file_ext == '.pdf':
                    st.session_state.stage = 'pdf_view'
                else:
                    st.session_state.stage = 'filter_setup'
                
                time.sleep(0.3)
                st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================================
# PDF VIEW PAGE
# ============================================================================
elif st.session_state.stage == 'pdf_view':
    st.markdown("<div class='fade-in'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("<h1 class='main-title'>📄 PDF Viewer</h1>", unsafe_allow_html=True)
        st.markdown(f"<p class='subtitle'><code>{st.session_state.selected_file}</code></p>", unsafe_allow_html=True)
    with col2:
        if st.button("◀ Back", use_container_width=True):
            st.session_state.stage = 'file_selection'
            st.session_state.selected_file = None
            st.session_state.pdf_page = 1
            st.rerun()
    
    try:
        # Display PDF using iframe
        with open(st.session_state.selected_file, "rb") as f:
            base64_pdf = __import__('base64').b64encode(f.read()).decode('utf-8')
        
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
        
        st.markdown("<div class='pdf-container'>", unsafe_allow_html=True)
        st.markdown(pdf_display, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Download option
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            with open(st.session_state.selected_file, "rb") as pdf_file:
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_file,
                    file_name=st.session_state.selected_file,
                    mime="application/pdf",
                    use_container_width=True
                )
    
    except Exception as e:
        st.error(f"Error loading PDF: {str(e)}")
        st.info("Your browser may not support embedded PDF viewing. Please use the download button to view the file.")
    
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
    
    if st.session_state.excel_data is None:
        with st.spinner("🔄 Loading data..."):
            st.session_state.excel_data = load_excel_file(st.session_state.selected_file)
            if st.session_state.excel_data:
                st.session_state.data_insights = calculate_insights(st.session_state.excel_data)
            else:
                st.error("Failed to load Excel file. Please go back and try again.")
                if st.button("◀ Back to File Selection"):
                    st.session_state.stage = 'file_selection'
                    st.session_state.selected_file = None
                    st.rerun()
    
    if st.session_state.excel_data:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        
        st.markdown("### 📊 Data Overview")
        
        summary = create_overview_summary(st.session_state.data_insights)
        st.markdown(summary)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        total_rows = sum(insight['total_rows'] for insight in st.session_state.data_insights.values())
        total_sheets = len(st.session_state.excel_data)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Sheets", total_sheets)
        with col2:
            st.metric("Total Rows", f"{total_rows:,}")
        with col3:
            total_cols = sum(insight['total_columns'] for insight in st.session_state.data_insights.values())
            st.metric("Total Columns", total_cols)
        with col4:
            total_memory = sum(insight['memory_usage'] for insight in st.session_state.data_insights.values())
            st.metric("MB in Memory", f"{total_memory:.1f}")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
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
                with st.expander(f"📄 {sheet_name} ({len(df):,} rows)", expanded=False):
                    columns = df.columns.tolist()
                    if not columns:
                        st.warning(f"No columns found in {sheet_name}")
                        continue
                    
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
        
        # Create tabs - add Visualizations tab
        tab_labels = [f"📄 {name}" for name in sheet_names] + ["📈 Visualizations"]
        tabs = st.tabs(tab_labels)
        
        # Data tabs
        for idx, sheet_name in enumerate(sheet_names):
            with tabs[idx]:
                df = st.session_state.excel_data[sheet_name].copy()
                original_count = len(df)
                
                if sheet_name in st.session_state.filters_config:
                    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                    st.markdown("### 🔍 Active Filters")
                    
                    filter_columns = st.session_state.filters_config[sheet_name]
                    
                    if sheet_name not in st.session_state.active_filters:
                        st.session_state.active_filters[sheet_name] = {}
                    
                    num_filters = len(filter_columns)
                    filter_cols = st.columns(min(num_filters, 3))
                    
                    for col_idx, filter_col in enumerate(filter_columns):
                        with filter_cols[col_idx % 3]:
                            try:
                                unique_values = sorted(df[filter_col].dropna().unique().tolist())
                                
                                if len(unique_values) > 1000:
                                    st.warning(f"⚠️ Column '{filter_col}' has {len(unique_values)} unique values. Filter may be slow.")
                                
                                selected_values = st.multiselect(
                                    filter_col,
                                    unique_values,
                                    key=f"active_filter_{sheet_name}_{filter_col}",
                                    default=st.session_state.active_filters[sheet_name].get(filter_col, [])
                                )
                                
                                st.session_state.active_filters[sheet_name][filter_col] = selected_values
                                
                                if selected_values:
                                    df = apply_filter(df, filter_col, selected_values)
                            except Exception as e:
                                st.error(f"Error creating filter for '{filter_col}': {str(e)}")
                    
                    if any(st.session_state.active_filters[sheet_name].values()):
                        if st.button("🔄 Clear All Filters", key=f"clear_{sheet_name}"):
                            st.session_state.active_filters[sheet_name] = {}
                            st.rerun()
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Rows Displayed", f"{len(df):,}")
                
                with col2:
                    filtered_pct = (len(df) / original_count * 100) if original_count > 0 else 0
                    st.metric("Data Shown", f"{filtered_pct:.1f}%")
                
                with col3:
                    active_filter_count = sum(
                        1 for filters in st.session_state.active_filters.get(sheet_name, {}).values() 
                        if filters
                    )
                    st.metric("Active Filters", active_filter_count)
                
                with col4:
                    st.metric("Columns", len(df.columns))
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                st.markdown("### 📋 Data Table")
                
                search_term = st.text_input(
                    "🔍 Search in table",
                    key=f"search_{sheet_name}",
                    placeholder="Type to search..."
                )
                
                display_df = df.copy()
                
                if search_term:
                    try:
                        mask = display_df.astype(str).apply(
                            lambda x: x.str.contains(search_term, case=False, na=False, regex=False)
                        ).any(axis=1)
                        display_df = display_df[mask]
                        st.info(f"Found {len(display_df):,} matching rows")
                    except Exception as e:
                        st.error(f"Search error: {str(e)}")
                        display_df = df.copy()
                
                try:
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        height=500
                    )
                except Exception as e:
                    st.error(f"Error displaying data: {str(e)}")
                    st.write("Attempting to display first 1000 rows...")
                    st.dataframe(
                        display_df.head(1000),
                        use_container_width=True,
                        height=500
                    )
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([2, 1, 2])
                with col2:
                    try:
                        csv = display_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download Filtered Data",
                            data=csv,
                            file_name=f"{sheet_name}_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True,
                            key=f"download_{sheet_name}"
                        )
                    except Exception as e:
                        st.error(f"Error preparing download: {str(e)}")
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Visualizations tab
        with tabs[-1]:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("### 📊 Trend-Based Analysis")
            st.markdown("Create custom visualizations to analyze trends across your data")
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Sheet selection for visualization
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("#### 1️⃣ Select Data Source")
            
            viz_sheet = st.selectbox(
                "Choose sheet for visualization",
                sheet_names,
                key="viz_sheet_select"
            )
            
            if viz_sheet:
                df_viz = st.session_state.excel_data[viz_sheet].copy()
                
                # Apply active filters if any
                if viz_sheet in st.session_state.active_filters:
                    for filter_col, filter_vals in st.session_state.active_filters[viz_sheet].items():
                        if filter_vals:
                            df_viz = apply_filter(df_viz, filter_col, filter_vals)
                
                st.info(f"📊 Working with {len(df_viz):,} rows from '{viz_sheet}'")
                
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Column configuration
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.markdown("#### 2️⃣ Configure Chart Parameters")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Time/X-axis column
                    all_columns = df_viz.columns.tolist()
                    time_col = st.selectbox(
                        "📅 Select Time/X-axis Column",
                        all_columns,
                        key="time_column",
                        help="Select the column to use for the X-axis (usually time, date, or sequence)"
                    )
                
                with col2:
                    # Category column
                    category_col = st.selectbox(
                        "🏷️ Select Category Column",
                        all_columns,
                        key="category_column",
                        help="Select the column to group data by (e.g., product, region, type)"
                    )
                
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                
                if time_col and category_col:
                    # Category selection
                    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                    st.markdown("#### 3️⃣ Select Categories to Display")
                    
                    try:
                        available_categories = sorted(df_viz[category_col].dropna().unique().tolist())
                        
                        if len(available_categories) > 50:
                            st.warning(f"⚠️ {len(available_categories)} categories available. Consider selecting a subset for better visualization.")
                        
                        selected_categories = st.multiselect(
                            f"Choose categories from '{category_col}'",
                            available_categories,
                            default=available_categories[:min(5, len(available_categories))],
                            key="selected_categories",
                            help="Select which categories you want to see in the chart"
                        )
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        if selected_categories:
                            # Value columns selection
                            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                            st.markdown("#### 4️⃣ Select Values to Plot")
                            
                            # Get numeric columns
                            numeric_columns = df_viz.select_dtypes(include=['number']).columns.tolist()
                            
                            if not numeric_columns:
                                st.warning("⚠️ No numeric columns found for plotting. Please select a different sheet.")
                            else:
                                value_cols = st.multiselect(
                                    "📈 Select value columns to plot",
                                    numeric_columns,
                                    default=[numeric_columns[0]] if numeric_columns else [],
                                    key="value_columns",
                                    help="Select one or more numeric columns to visualize"
                                )
                                
                                st.markdown("</div>", unsafe_allow_html=True)
                                st.markdown("<br>", unsafe_allow_html=True)
                                
                                if value_cols:
                                    # Chart type selection
                                    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                                    st.markdown("#### 5️⃣ Select Chart Type")
                                    
                                    col1, col2, col3, col4 = st.columns(4)
                                    
                                    with col1:
                                        if st.button("📈 Line Chart", use_container_width=True):
                                            st.session_state.chart_type = "Line Chart"
                                    
                                    with col2:
                                        if st.button("📊 Bar Chart", use_container_width=True):
                                            st.session_state.chart_type = "Bar Chart"
                                    
                                    with col3:
                                        if st.button("📉 Area Chart", use_container_width=True):
                                            st.session_state.chart_type = "Area Chart"
                                    
                                    with col4:
                                        if st.button("⚫ Scatter Plot", use_container_width=True):
                                            st.session_state.chart_type = "Scatter Plot"
                                    
                                    st.markdown("</div>", unsafe_allow_html=True)
                                    st.markdown("<br>", unsafe_allow_html=True)
                                    
                                    # Display chart
                                    if 'chart_type' in st.session_state:
                                        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                                        st.markdown(f"### {st.session_state.chart_type}")
                                        
                                        with st.spinner("🎨 Creating visualization..."):
                                            fig = create_visualization(
                                                df_viz,
                                                time_col,
                                                category_col,
                                                value_cols,
                                                st.session_state.chart_type,
                                                selected_categories
                                            )
                                            
                                            if fig:
                                                st.plotly_chart(fig, use_container_width=True)
                                                
                                                # Download chart
                                                st.markdown("<br>", unsafe_allow_html=True)
                                                col1, col2, col3 = st.columns([2, 1, 2])
                                                with col2:
                                                    try:
                                                        img_bytes = fig.to_image(format="png")
                                                        st.download_button(
                                                            label="📥 Download Chart",
                                                            data=img_bytes,
                                                            file_name=f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                                                            mime="image/png",
                                                            use_container_width=True
                                                        )
                                                    except:
                                                        st.info("💡 Tip: Right-click on the chart to download it")
                                        
                                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    except Exception as e:
                        st.error(f"Error in visualization setup: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Footer
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='text-align: center; color: #7C7C8C; font-size: 0.85rem;'>"
        f"Last updated: {datetime.now().strftime('%d %B %Y, %H:%M:%S')} | "
        f"<span class='status-dot'></span>Session active"
        f"</div>",
        unsafe_allow_html=True
    )
