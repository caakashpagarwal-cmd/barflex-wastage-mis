"""
BARFLEX POLYFILMS - WASTAGE MIS DASHBOARD
Streamlit-based interactive dashboard for real-time wastage monitoring
Author: CA Akash Agarwal | Maars & Associates
Platform: Streamlit Cloud (https://streamlit.io)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Barflex Wastage MIS",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .status-critical {
        color: #dc3545;
        font-weight: bold;
    }
    .status-warning {
        color: #ff9800;
        font-weight: bold;
    }
    .status-compliant {
        color: #28a745;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Title and header
st.title("🏭 Barflex Polyfilms - Wastage MIS Dashboard")
st.markdown("**Real-Time Wastage Monitoring & Analysis**")
st.markdown(f"*Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Prepared by: CA Akash Agarwal, Maars & Associates*")

# Load data function
@st.cache_data
def load_data():
    """Load and process Barflex wastage data"""
    try:
        file_path = st.file_uploader("📁 Upload Wastage Data (XLSX)", type="xlsx")
        if file_path:
            excel_file = pd.ExcelFile(file_path)
            return excel_file.sheet_names, file_path
    except:
        pass
    return None, None

# Sidebar for file upload
st.sidebar.header("📊 Data Upload & Settings")
uploaded_file = st.sidebar.file_uploader("Upload Wastage Data File", type="xlsx", key="data_upload")

if uploaded_file:
    excel_file = pd.ExcelFile(uploaded_file)
    sheets = excel_file.sheet_names
    
    # Department selector
    st.sidebar.header("🔍 Department Filter")
    selected_dept = st.sidebar.multiselect(
        "Select Department(s)",
        sheets,
        default=sheets
    )
    
    # Load selected departments
    dept_data = {}
    for sheet in selected_dept:
        df = pd.read_excel(uploaded_file, sheet_name=sheet)
        df['DATE'] = pd.to_datetime(df['DATE'])
        df = df.sort_values('DATE').reset_index(drop=True)
        dept_data[sheet] = df
    
    # Main dashboard
    st.header("📈 Dashboard Overview")
    
    # Create summary metrics for each department
    metric_cols = st.columns(min(3, len(selected_dept)))
    
    for idx, (sheet_name, df) in enumerate(dept_data.items()):
        with metric_cols[idx % 3]:
            # Get wastage column dynamically
            wastage_cols = [col for col in df.columns if 'WASTAGE %' in col and 'MAX' not in col and 'VARIANCE' not in col]
            if wastage_cols:
                wastage_col = wastage_cols[0]
                wastage_pct = pd.to_numeric(df[wastage_col], errors='coerce')
                
                # Variance columns
                var_cols = [col for col in df.columns if 'VARIANCE' in col]
                var_col = var_cols[0] if var_cols else None
                
                if var_col:
                    variance = pd.to_numeric(df[var_col], errors='coerce')
                    breaches = (variance > 0).sum()
                    status = 'CRITICAL' if (breaches/len(df)*100) > 50 else ('WARNING' if (breaches/len(df)*100) > 25 else 'COMPLIANT')
                    color_class = 'status-critical' if status == 'CRITICAL' else ('status-warning' if status == 'WARNING' else 'status-compliant')
                    
                    st.metric(
                        label=sheet_name.replace('WASTAGE - ', '').replace('WASTAGE- ', ''),
                        value=f"{wastage_pct.mean():.2f}%",
                        delta=f"{status}",
                        delta_color="inverse" if status == "CRITICAL" else "off"
                    )
    
    # Detailed analysis by department
    st.header("🔬 Detailed Department Analysis")
    
    for sheet_name in selected_dept:
        with st.expander(f"📊 {sheet_name.replace('WASTAGE - ', '').replace('WASTAGE- ', '')} - Details"):
            df = dept_data[sheet_name]
            
            # Get column names
            wastage_cols = [col for col in df.columns if 'WASTAGE %' in col and 'MAX' not in col and 'VARIANCE' not in col]
            var_cols = [col for col in df.columns if 'VARIANCE' in col]
            max_allowed_cols = [col for col in df.columns if 'MAX' in col and 'WASTAGE' in col]
            
            if wastage_cols:
                wastage_col = wastage_cols[0]
                var_col = var_cols[0] if var_cols else None
                max_col = max_allowed_cols[0] if max_allowed_cols else None
                
                df[wastage_col] = pd.to_numeric(df[wastage_col], errors='coerce')
                clean_df = df[df[wastage_col].notna()].copy()
                
                # Create columns for metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Average Wastage", f"{clean_df[wastage_col].mean():.4f}%")
                with col2:
                    st.metric("Max Wastage", f"{clean_df[wastage_col].max():.4f}%")
                with col3:
                    st.metric("Min Wastage", f"{clean_df[wastage_col].min():.4f}%")
                with col4:
                    st.metric("Std Dev", f"{clean_df[wastage_col].std():.4f}%")
                
                # Trend chart
                fig = px.line(
                    clean_df,
                    x='DATE',
                    y=wastage_col,
                    title=f"Wastage Trend - {sheet_name}",
                    markers=True
                )
                
                if max_col:
                    fig.add_hline(
                        y=clean_df[max_col].mean(),
                        line_dash="dash",
                        line_color="red",
                        annotation_text=f"Max Allowed: {clean_df[max_col].mean():.2f}%"
                    )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Distribution chart
                fig_dist = px.histogram(
                    clean_df,
                    x=wastage_col,
                    nbins=20,
                    title=f"Wastage Distribution",
                    labels={wastage_col: "Wastage %"}
                )
                st.plotly_chart(fig_dist, use_container_width=True)
                
                # Worst and best days
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🚨 Worst 5 Days")
                    worst_days = clean_df.nlargest(5, wastage_col)[['DATE', wastage_col]]
                    st.dataframe(worst_days, use_container_width=True)
                
                with col2:
                    st.subheader("✅ Best 5 Days")
                    best_days = clean_df.nsmallest(5, wastage_col)[['DATE', wastage_col]]
                    st.dataframe(best_days, use_container_width=True)
    
    # Data download section
    st.header("📥 Download Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Download Summary as CSV"):
            summary_data = []
            for sheet_name, df in dept_data.items():
                wastage_cols = [col for col in df.columns if 'WASTAGE %' in col and 'MAX' not in col and 'VARIANCE' not in col]
                if wastage_cols:
                    wastage_col = wastage_cols[0]
                    wastage_pct = pd.to_numeric(df[wastage_col], errors='coerce')
                    summary_data.append({
                        'Department': sheet_name,
                        'Avg Wastage %': wastage_pct.mean(),
                        'Max Wastage %': wastage_pct.max(),
                        'Min Wastage %': wastage_pct.min()
                    })
            
            summary_df = pd.DataFrame(summary_data)
            st.download_button(
                label="Download CSV",
                data=summary_df.to_csv(index=False),
                file_name=f"barflex_summary_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col2:
        st.info("💡 **How to use this dashboard:**\n1. Upload your Wastage Data XLSX file\n2. Select departments to view\n3. Analyze trends and identify issues\n4. Download summaries for reporting")

else:
    st.info("📁 **Please upload a Wastage Data file to begin analysis**")
    st.markdown("""
    ### Features:
    - 📊 Real-time wastage monitoring
    - 📈 Interactive trend charts
    - 🎯 Department-wise comparison
    - 🚨 Alert system for breaches
    - 📥 Export capabilities
    
    ### How it works:
    1. Upload your XLSX file with wastage data
    2. Select departments to analyze
    3. View interactive dashboards
    4. Download reports for client advisory
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 12px;">
    <p>Barflex Polyfilms Wastage MIS Dashboard | CA Akash Agarwal | Maars & Associates</p>
    <p>Deployment: Streamlit Cloud | Last Updated: May 2026</p>
</div>
""", unsafe_allow_html=True)
