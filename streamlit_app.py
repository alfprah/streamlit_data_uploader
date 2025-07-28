# Streamlit App: Universal Data File Uploader to Snowflake

import streamlit as st

import pandas as pd
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.exceptions import SnowparkSQLException
from io import BytesIO
import logging
import re
import os
from typing import Dict, List, Tuple, Optional

# Check for Excel support
try:
    import openpyxl
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False

try:
    import xlrd
    XLS_SUPPORT = True
except ImportError:
    XLS_SUPPORT = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
SUPPORTED_FILE_TYPES = {
    "csv": {"extensions": [".csv"], "description": "Comma Separated Values"},
    "txt": {"extensions": [".txt"], "description": "Text Files (assumed CSV format)"},
}

# Add Excel support only if packages are available
if EXCEL_SUPPORT or XLS_SUPPORT:
    excel_extensions = []
    excel_desc = "Excel Files ("
    
    if EXCEL_SUPPORT:
        excel_extensions.append(".xlsx")
        excel_desc += ".xlsx"
    
    if XLS_SUPPORT:
        if excel_extensions:
            excel_extensions.append(", .xls")
        else:
            excel_extensions.append(".xls")
        excel_desc += ".xls"
    
    excel_desc += ")"
    SUPPORTED_FILE_TYPES["excel"] = {"extensions": excel_extensions, "description": excel_desc}

DEFAULT_CSV_OPTIONS = {
    "field_delimiter": ",",
    "skip_header": 1,
    "empty_field_as_null": True,
    "field_optionally_enclosed_by": '"',
    "trim_space": True
}

# --- Helper Functions ---
def clean_column_name(name: str) -> str:
    """Converts a column name to Snowflake-friendly identifier."""
    if not isinstance(name, str):
        name = str(name)
    name = name.strip()
    name = name.upper()
    name = re.sub(r'\s+|-', '_', name)
    name = re.sub(r'[()\[\]{}.?/\\\'\":;,!@#$%^&*`~]', '', name)
    
    if name and name[0].isdigit():
        name = '_' + name
    
    # Handle empty names
    if not name:
        name = 'UNNAMED_COLUMN'
    
    return name

def clean_table_name(name: str) -> str:
    """Converts a table name to Snowflake-friendly identifier."""
    if not isinstance(name, str):
        name = str(name)
    name = name.strip()
    name = name.upper()
    name = re.sub(r'[^A-Z0-9_]', '_', name)
    
    if name and name[0].isdigit():
        name = '_' + name
    
    if not name:
        name = 'UNNAMED_TABLE'
    
    return name

def get_file_type(filename: str) -> Optional[str]:
    """Determine file type based on extension."""
    _, ext = os.path.splitext(filename.lower())
    for file_type, config in SUPPORTED_FILE_TYPES.items():
        if ext in config["extensions"]:
            return file_type
    return None

def read_file_to_dataframe(uploaded_file, file_type: str, csv_options: Dict = None) -> pd.DataFrame:
    """Read uploaded file into pandas DataFrame based on file type."""
    if csv_options is None:
        csv_options = DEFAULT_CSV_OPTIONS
    
    file_bytes = uploaded_file.getvalue()
    file_size_mb = len(file_bytes) / 1024 / 1024
    input_stream = BytesIO(file_bytes)
    
    # Show progress for larger files
    if file_size_mb > 50:
        st.info(f"📊 Processing {file_size_mb:.1f}MB file...")
    
    if file_type == "excel":
        filename = uploaded_file.name.lower()
        if filename.endswith('.xlsx') and EXCEL_SUPPORT:
            df = pd.read_excel(input_stream, engine='openpyxl')
        elif filename.endswith('.xls') and XLS_SUPPORT:
            df = pd.read_excel(input_stream, engine='xlrd')
        else:
            raise ValueError("Excel file type not supported in this environment. Please add the required packages (openpyxl for .xlsx, xlrd for .xls) to your Streamlit app in Snowsight.")
    elif file_type in ["csv", "txt"]:
        # Read CSV/TXT file
        pandas_args = {
            "delimiter": csv_options.get("field_delimiter", ","),
            "header": 0 if csv_options.get("skip_header", 1) == 1 else None,
            "quotechar": csv_options.get("field_optionally_enclosed_by", '"'),
            "escapechar": '\\',
            "skipinitialspace": csv_options.get("trim_space", True)
        }
        df = pd.read_csv(input_stream, **pandas_args)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
    
    return df

# --- Initialize Session State ---
if 'file_configs' not in st.session_state:
    st.session_state.file_configs = {}

# --- Get Snowpark Session ---
try:
    session = get_active_session()
    db = session.get_current_database().replace('"', '')
    schema = session.get_current_schema().replace('"', '')
    role = session.get_current_role().replace('"', '')
    warehouse = session.get_current_warehouse().replace('"', '')
    logger.info(f"Snowpark session active. Role: {role}, DB: {db}, Schema: {schema}, WH: {warehouse}")
except Exception as e:
    st.error(f"Error getting Snowflake session: {e}")
    logger.error(f"Error getting Snowflake session: {e}", exc_info=True)
    st.stop()

# --- Streamlit App UI ---
st.set_page_config(
    layout="wide", 
    page_title="Universal Data Uploader", 
    page_icon="❄️",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern Snowflake-themed design
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 1rem;
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    
    .main-title {
        font-size: clamp(2rem, 5vw, 3rem);
        font-weight: 700;
        margin: 0;
        background: linear-gradient(135deg, #29B5E8 0%, #1E88E5 50%, #0D47A1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1.1;
        text-align: center;
        width: 100%;
    }
    
    .subtitle {
        font-size: clamp(1rem, 2.5vw, 1.1rem);
        color: #64748B;
        margin: 1rem auto 0 auto;
        max-width: 650px;
        line-height: 1.5;
        text-align: center;
        width: 100%;
        padding: 0 2rem;
        display: block;
        box-sizing: border-box;
    }
    
    .connection-badge {
        display: inline-block;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 0.4rem 0.8rem;
        margin: 0.2rem;
        font-size: 0.8rem;
        color: #475569;
        white-space: nowrap;
    }
    
    .connection-badges {
        text-align: center;
        margin: 1.5rem 0;
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 0.5rem;
        width: 100%;
    }
    
    .upload-section {
        max-width: 900px;
        margin: 2rem auto;
        padding: 2rem;
        background: white;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border: 1px solid #E2E8F0;
    }
    
    .section-title {
        font-size: clamp(1.2rem, 3vw, 1.4rem);
        font-weight: 600;
        color: #1E293B;
        margin-bottom: 1.5rem;
        text-align: center;
        width: 100%;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #29B5E8 0%, #1E88E5 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(41, 181, 232, 0.4) !important;
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1.5rem;
        margin: 2rem 0;
        padding: 0 1rem;
        width: 100%;
        max-width: 1200px;
        margin-left: auto;
        margin-right: auto;
    }
    
    .feature-card {
        background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%);
        padding: 2rem 1.5rem;
        border-radius: 16px;
        border: 1px solid #E2E8F0;
        text-align: center;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        min-width: 0;
    }
    
    .feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(135deg, #29B5E8 0%, #1E88E5 100%);
    }
    
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(41, 181, 232, 0.15);
        border-color: #29B5E8;
    }
    
    .feature-title {
        font-weight: 600;
        color: #1E293B;
        margin: 1rem 0 0.5rem 0;
        font-size: 1.1rem;
        text-align: center;
        word-break: break-word;
    }
    
    .feature-desc {
        color: #64748B;
        font-size: 0.9rem;
        margin: 0;
        line-height: 1.4;
        text-align: center;
        word-break: break-word;
        hyphens: auto;
    }
    
    .stExpander {
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        margin: 1rem 0 !important;
        background: white !important;
    }
    
    .stExpander > div:first-child {
        background: #F8FAFC !important;
        border-radius: 12px 12px 0 0 !important;
    }
    
    .stProgress .stProgress-bar {
        background: linear-gradient(135deg, #29B5E8 0%, #1E88E5 100%) !important;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .block-container {
        padding-top: 2rem;
        max-width: 100%;
    }
    
    /* Remove any blank containers */
    .element-container:empty {
        display: none !important;
    }
    
    /* Remove excessive spacing between main sections */
    .main .block-container .element-container {
        margin-bottom: 0 !important;
    }
    
    /* Tight spacing for connection badges area */
    .connection-badges + .element-container {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Ensure upload section has minimal top margin */
    .upload-section {
        margin-top: 1rem !important;
    }
    
    /* Responsive improvements */
    @media (max-width: 1024px) {
        .feature-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 1.5rem;
            max-width: 800px;
        }
    }
    
    @media (max-width: 768px) {
        .connection-badges {
            flex-direction: column;
            align-items: center;
        }
        
        .feature-grid {
            grid-template-columns: 1fr;
            gap: 1rem;
            max-width: 400px;
        }
        
        .upload-section {
            margin: 1rem;
            padding: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Compact Excel support status
excel_warning = None
if not EXCEL_SUPPORT and not XLS_SUPPORT:
    excel_warning = "Excel files not supported. Add 'openpyxl' and 'xlrd' to packages or convert to CSV."
elif not EXCEL_SUPPORT:
    excel_warning = ".xlsx files not supported. Add 'openpyxl' to packages or convert to CSV."
elif not XLS_SUPPORT:
    excel_warning = ".xls files not supported. Add 'xlrd' to packages or convert to CSV."

if excel_warning:
    st.info(f"ℹ️ {excel_warning}")

# Modern header
st.markdown("""
<div class="main-header">
    <h1 class="main-title">Universal Data Uploader</h1>
    <p class="subtitle">Seamlessly upload CSV, TXT, and Excel files directly to Snowflake with intelligent column mapping and data processing</p>
</div>
""", unsafe_allow_html=True)

# Database and Schema selection in sidebar
with st.sidebar:
    st.markdown("### Target Location")
    
    # Get available databases and schemas
    try:
        databases_result = session.sql("SHOW DATABASES").collect()
        available_databases = [row['name'] for row in databases_result]
        
        # Database selection
        current_db_index = available_databases.index(db) if db in available_databases else 0
        selected_db = st.selectbox(
            "Database", 
            available_databases, 
            index=current_db_index,
            help="Select target database for uploads"
        )
        
        # Get schemas for selected database
        schemas_result = session.sql(f"SHOW SCHEMAS IN DATABASE {selected_db}").collect()
        available_schemas = [row['name'] for row in schemas_result]
        
        # Schema selection
        current_schema_index = available_schemas.index(schema) if schema in available_schemas else 0
        selected_schema = st.selectbox(
            "Schema", 
            available_schemas, 
            index=current_schema_index,
            help="Select target schema for uploads"
        )
        
    except Exception as e:
        st.error(f"Error fetching databases/schemas: {str(e)}")
        selected_db = db
        selected_schema = schema
    
    st.divider()
    
    st.markdown("### CSV Options")
    csv_delimiter = st.selectbox("Delimiter", [",", ";", "|", "\t"], index=0)
    csv_has_header = st.checkbox("Has Header Row", value=True)
    csv_quote_char = st.selectbox("Quote Character", ['"', "'", "None"], index=0)
    
    # Build CSV options here to keep it contained
    current_csv_options = {
        "field_delimiter": "\t" if csv_delimiter == "\\t" else csv_delimiter,
        "skip_header": 1 if csv_has_header else 0,
        "empty_field_as_null": True,
        "field_optionally_enclosed_by": csv_quote_char if csv_quote_char != "None" else None,
        "trim_space": True
    }

# Connection info and upload section combined
st.markdown(f"""
<div class="connection-badges">
    <span class="connection-badge">Database: {selected_db}</span>
    <span class="connection-badge">Schema: {selected_schema}</span>
    <span class="connection-badge">Role: {role}</span>
    <span class="connection-badge">Warehouse: {warehouse}</span>
</div>
""", unsafe_allow_html=True)

# Build supported file extensions list (keeping it minimal)
supported_extensions = [ext[1:] for config in SUPPORTED_FILE_TYPES.values() for ext in config['extensions']]

# Upload section header as Streamlit component
st.markdown('<div class="section-title" style="margin-top: 2rem;">Upload Your Files</div>', unsafe_allow_html=True)

# File uploader immediately after title
uploaded_files = st.file_uploader(
    "Drag and drop files here or click to browse",
    type=supported_extensions,
    accept_multiple_files=True,
    key="universal_file_uploader",
    label_visibility="collapsed"
)

if not uploaded_files:
    # Show features in a clean container
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-card">
            <div class="feature-title">Multiple Formats</div>
            <div class="feature-desc">Support for CSV, TXT, and Excel files (.xlsx, .xls)</div>
        </div>
        <div class="feature-card">
            <div class="feature-title">Column Mapping</div>
            <div class="feature-desc">Interactive column renaming with real-time preview</div>
        </div>
        <div class="feature-card">
            <div class="feature-title">Batch Upload</div>
            <div class="feature-desc">Process multiple files simultaneously with progress tracking</div>
        </div>
        <div class="feature-card">
            <div class="feature-title">Auto-Cleaning</div>
            <div class="feature-desc">Automatic Snowflake-compatible column name formatting</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

if uploaded_files:
    # File configuration section with automatic preview loading
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Configure Your Files</div>', unsafe_allow_html=True)
    
    # Configure each file
    for i, uploaded_file in enumerate(uploaded_files):
        file_name = uploaded_file.name
        file_type = get_file_type(file_name)
        
        if not file_type:
            st.error(f"Unsupported file type: {file_name}")
            continue
        
        with st.expander(f"{file_name} ({SUPPORTED_FILE_TYPES[file_type]['description']})", expanded=True):
            # Store configuration
            if file_name not in st.session_state.file_configs:
                st.session_state.file_configs[file_name] = {}
            config = st.session_state.file_configs[file_name]
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Table name configuration
                default_table_name = clean_table_name(os.path.splitext(file_name)[0])
                table_name = st.text_input(
                    f"Table Name:",
                    value=default_table_name,
                    key=f"table_name_{i}",
                    help="Table name will be cleaned for Snowflake compatibility"
                )
                table_name = clean_table_name(table_name)
                st.caption(f"Final table name: `{table_name}`")
                
                config['table_name'] = table_name
                config['file_type'] = file_type
                config['csv_options'] = current_csv_options if file_type in ['csv', 'txt'] else None
            
            with col2:
                st.markdown("**File Details**")
                st.caption(f"Size: {uploaded_file.size:,} bytes")
                st.caption(f"Type: {file_type.upper()}")
                st.caption(f"Target: `{selected_db}.{selected_schema}.{table_name}`")
            
            # Automatic preview loading (combined with column editing)
            if 'original_columns' not in config:
                with st.spinner(f"Loading preview for {file_name}..."):
                    try:
                        df = read_file_to_dataframe(
                            uploaded_file, 
                            file_type, 
                            current_csv_options if file_type in ['csv', 'txt'] else None
                        )
                        config['original_columns'] = df.columns.tolist()
                        config['cleaned_columns'] = [clean_column_name(col) for col in config['original_columns']]
                        if 'custom_columns' not in config:
                            config['custom_columns'] = config['cleaned_columns'].copy()
                        config['num_rows'] = len(df)
                        config['preview_head'] = df.head(10)
                        st.rerun()  # Refresh to show the loaded data
                    except Exception as e:
                        st.error(f"Error loading file: {str(e)}")
            
            # Display preview and editor if loaded
            if 'original_columns' in config:
                st.success(f"Loaded {config['num_rows']} rows × {len(config['original_columns'])} columns")
                
                if config['num_rows'] == 0:
                    st.warning("File appears to be empty")
                else:
                    # Show preview and column mapping together
                    col_preview, col_mapping = st.columns([1, 1])
                    
                    with col_preview:
                        st.markdown("**Data Preview** (first 10 rows)")
                        st.dataframe(config['preview_head'], use_container_width=True, height=300)
                    
                    with col_mapping:
                        st.markdown("**Column Mapping**")
                        renaming_df = pd.DataFrame({
                            'Original': config['original_columns'],
                            'Rename To': config['custom_columns']
                        })
                        edited_df = st.data_editor(
                            renaming_df,
                            column_config={
                                'Rename To': st.column_config.TextColumn(
                                    'Rename To',
                                    help='Edit to rename columns. Names will be cleaned for Snowflake.',
                                    required=True,
                                )
                            },
                            disabled=['Original'],
                            hide_index=True,
                            use_container_width=True,
                            height=300,
                            key=f"column_editor_{i}"
                        )
                        # Update custom columns from edits
                        config['custom_columns'] = edited_df['Rename To'].tolist()

    st.markdown('</div>', unsafe_allow_html=True)
    
    # Upload section
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Ready to Upload</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        upload_button = st.button("Upload All Files", type="primary", use_container_width=True)

    if upload_button:
        st.markdown('<div class="section-title">Upload Progress</div>', unsafe_allow_html=True)
        
        progress_bar = st.progress(0)
        status_container = st.container()
        
        total_files = len(uploaded_files)
        successful_uploads = 0
        
        for i, uploaded_file in enumerate(uploaded_files):
            file_name = uploaded_file.name
            
            if file_name not in st.session_state.file_configs:
                with status_container:
                    st.error(f"Configuration missing for {file_name}")
                continue
            
            config = st.session_state.file_configs[file_name]
            table_name = config['table_name']
            file_type = config['file_type']
            # Use selected database and schema instead of session defaults
            full_table_name = f"{selected_db}.{selected_schema}.{table_name}"
            
            with status_container:
                status_msg = st.empty()
                status_msg.info(f"Processing {file_name} → {table_name}")
            
            try:
                # Read file into DataFrame
                df = read_file_to_dataframe(uploaded_file, file_type, config.get('csv_options'))
                logger.info(f"Read {len(df)} rows from {file_name}")
                
                if df.empty:
                    status_msg.warning(f"Skipped empty file: {file_name}")
                    continue
                
                # Apply custom column names if available, else clean original
                if 'custom_columns' in config and len(config['custom_columns']) == len(df.columns):
                    custom_names = config['custom_columns']
                else:
                    custom_names = [clean_column_name(col) for col in df.columns]
                
                # Clean the (custom) names for Snowflake
                df.columns = [clean_column_name(col) for col in custom_names]
                logger.info(f"Applied columns for {file_name}: {df.columns.tolist()}")
                
                # Convert to string and handle NaN values
                df = df.astype(str)
                df.replace({'<NA>': None, 'nan': None, 'NaN': None, 'None': None}, inplace=True)
                
                # Create Snowpark DataFrame and upload to selected database/schema
                snowpark_df = session.create_dataframe(df)
                snowpark_df.write.mode("overwrite").option("copy_options", {'on_error': 'continue'}).save_as_table(full_table_name)
                
                status_msg.success(f"Successfully uploaded {file_name} to {table_name} ({len(df)} rows)")
                successful_uploads += 1
                logger.info(f"Successfully uploaded {file_name} to {full_table_name}")
                
            except SnowparkSQLException as e:
                status_msg.error(f"Snowflake error for {file_name}: {e.message}")
                logger.error(f"Snowflake error for {file_name}: {e}", exc_info=True)
            except Exception as e:
                status_msg.error(f"Error processing {file_name}: {str(e)}")
                logger.error(f"Error processing {file_name}: {e}", exc_info=True)
            
            # Update progress
            progress_bar.progress((i + 1) / total_files)
        
        # Final status
        if successful_uploads == total_files:
            st.success(f"All {total_files} files uploaded successfully!")
        elif successful_uploads > 0:
            st.warning(f"{successful_uploads}/{total_files} files uploaded successfully.")
        else:
            st.error("No files were uploaded successfully.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Modern footer
st.markdown("""
<div style="text-align: center; margin: 4rem 0 2rem 0; padding: 2rem; border-top: 1px solid #E2E8F0;">
    <p style="color: #64748B; font-size: 0.875rem; margin: 0;">
        Connected as <strong>{}</strong> • Target: <strong>{}.{}</strong>
    </p>
</div>
""".format(role, selected_db, selected_schema), unsafe_allow_html=True)