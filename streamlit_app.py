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
    input_stream = BytesIO(file_bytes)
    
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
st.set_page_config(layout="wide", page_title="Universal Data Uploader")

# Show Excel support status
if not EXCEL_SUPPORT and not XLS_SUPPORT:
    st.warning("📊 **Excel files not supported in this environment.** Please add 'openpyxl' (for .xlsx) and/or 'xlrd' (for .xls) to your Streamlit app's packages in Snowsight, or convert Excel files to CSV format before uploading.")
    
    with st.expander("💡 How to Convert Excel to CSV", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Method 1: Excel Application")
            st.write("1. Open your Excel file")
            st.write("2. **File → Save As**")
            st.write("3. Choose **CSV (Comma delimited)**")
            st.write("4. Save and upload the CSV file")
        
        with col2:
            st.markdown("### Method 2: Google Sheets")
            st.write("1. Upload Excel to Google Sheets")
            st.write("2. **File → Download → CSV**")
            st.write("3. Upload the downloaded CSV")
elif not EXCEL_SUPPORT:
    st.info("📊 **.xlsx files not supported.** Please add 'openpyxl' to your Streamlit app's packages in Snowsight, or convert to CSV.")
elif not XLS_SUPPORT:
    st.info("📊 **.xls files not supported.** Please add 'xlrd' to your Streamlit app's packages in Snowsight, or convert to CSV.")

st.title("🚀 Universal Data Uploader to Snowflake")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    st.write(f"**Current Target:**")
    st.code(f"Database: {db}\nSchema: {schema}")
    st.write(f"**Connection:**")
    st.code(f"Role: {role}\nWarehouse: {warehouse}")
    
    st.markdown("---")
    st.header("CSV Options")
    csv_delimiter = st.selectbox("Delimiter", [",", ";", "|", "\t"], index=0)
    csv_has_header = st.checkbox("Has Header Row", value=True)
    csv_quote_char = st.selectbox("Quote Character", ['"', "'", "None"], index=0)

# Main content
supported_extensions_str = ', '.join(['.' + ext for config in SUPPORTED_FILE_TYPES.values() for ext in config['extensions']])
st.markdown(f"""
**Instructions:** 
- Upload files ({supported_extensions_str})
- Preview and configure each file, including renaming columns
- Customize table names
- Batch upload to Snowflake

**Target Location:** `{db}.{schema}`
""")

# Build CSV options from sidebar
current_csv_options = {
    "field_delimiter": "\t" if csv_delimiter == "\\t" else csv_delimiter,
    "skip_header": 1 if csv_has_header else 0,
    "empty_field_as_null": True,
    "field_optionally_enclosed_by": csv_quote_char if csv_quote_char != "None" else None,
    "trim_space": True
}

st.markdown("---")

# Build supported file extensions list
supported_extensions = [ext[1:] for config in SUPPORTED_FILE_TYPES.values() for ext in config['extensions']]

# File uploader
uploaded_files = st.file_uploader(
    "Select files to upload",
    type=supported_extensions,
    accept_multiple_files=True,
    key="universal_file_uploader"
)

if uploaded_files:
    st.markdown("---")
    st.subheader("📋 File Configuration & Preview")
    
    # Configure each file
    for i, uploaded_file in enumerate(uploaded_files):
        file_name = uploaded_file.name
        file_type = get_file_type(file_name)
        
        if not file_type:
            st.error(f"❌ Unsupported file type for: {file_name}")
            continue
        
        with st.expander(f"📄 {file_name} ({SUPPORTED_FILE_TYPES[file_type]['description']})", expanded=True):
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Table name configuration
                default_table_name = clean_table_name(os.path.splitext(file_name)[0])
                table_name = st.text_input(
                    f"Table Name for {file_name}:",
                    value=default_table_name,
                    key=f"table_name_{i}"
                )
                table_name = clean_table_name(table_name)
                st.write(f"**Cleaned Table Name:** `{table_name}`")
                
                # Store configuration
                if file_name not in st.session_state.file_configs:
                    st.session_state.file_configs[file_name] = {}
                config = st.session_state.file_configs[file_name]
                config['table_name'] = table_name
                config['file_type'] = file_type
                config['csv_options'] = current_csv_options if file_type in ['csv', 'txt'] else None
            
            with col2:
                st.write("**File Info:**")
                st.write(f"- Size: {uploaded_file.size:,} bytes")
                st.write(f"- Type: {file_type.upper()}")
                st.write(f"- Target: `{db}.{schema}.{table_name}`")
            
            # Preview and rename section
            if st.button(f"👀 Load Preview for {file_name}", key=f"load_preview_{i}"):
                with st.spinner(f"Loading data for {file_name}..."):
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
                        st.success("Data loaded successfully!")
                    except Exception as e:
                        st.error(f"❌ Error loading {file_name}: {str(e)}")
            
            # Display preview and editor if loaded
            if 'original_columns' in config:
                st.write(f"**Shape:** {config['num_rows']} rows × {len(config['original_columns'])} columns")
                
                if config['num_rows'] == 0:
                    st.warning("⚠️ File appears to be empty")
                else:
                    st.write("**Data Preview (first 10 rows):**")
                    st.dataframe(config['preview_head'], use_container_width=True)
                    
                    st.write("**Rename Columns (will be cleaned for Snowflake):**")
                    renaming_df = pd.DataFrame({
                        'Original': config['original_columns'],
                        'Rename To': config['custom_columns']
                    })
                    edited_df = st.data_editor(
                        renaming_df,
                        column_config={
                            'Rename To': st.column_config.TextColumn(
                                'Rename To',
                                help='Edit to rename the column. Final name will be cleaned for Snowflake compatibility.',
                                required=True,
                            )
                        },
                        disabled=['Original'],
                        hide_index=False,
                        use_container_width=True,
                        key=f"column_editor_{i}"
                    )
                    # Update custom columns from edits
                    config['custom_columns'] = edited_df['Rename To'].tolist()

    # Upload section
    st.markdown("---")
    st.subheader("🚀 Upload to Snowflake")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        upload_button = st.button("🚀 Upload All Files", type="primary", use_container_width=True)
    
    if upload_button:
        st.markdown("---")
        st.subheader("📊 Upload Progress")
        
        progress_bar = st.progress(0)
        status_container = st.container()
        
        total_files = len(uploaded_files)
        successful_uploads = 0
        
        for i, uploaded_file in enumerate(uploaded_files):
            file_name = uploaded_file.name
            
            if file_name not in st.session_state.file_configs:
                with status_container:
                    st.error(f"❌ Configuration missing for {file_name}")
                continue
            
            config = st.session_state.file_configs[file_name]
            table_name = config['table_name']
            file_type = config['file_type']
            full_table_name = f"{db}.{schema}.{table_name}"
            
            with status_container:
                status_msg = st.empty()
                status_msg.info(f"⏳ Processing {file_name} → {table_name}...")
            
            try:
                # Read file into DataFrame
                df = read_file_to_dataframe(uploaded_file, file_type, config.get('csv_options'))
                logger.info(f"Read {len(df)} rows from {file_name}")
                
                if df.empty:
                    status_msg.warning(f"⚠️ Skipped empty file: {file_name}")
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
                
                # Create Snowpark DataFrame and upload
                snowpark_df = session.create_dataframe(df)
                snowpark_df.write.mode("overwrite").option("copy_options", {'on_error': 'continue'}).save_as_table(full_table_name)
                
                status_msg.success(f"✅ Successfully uploaded {file_name} to {table_name} ({len(df)} rows)")
                successful_uploads += 1
                logger.info(f"Successfully uploaded {file_name} to {full_table_name}")
                
            except SnowparkSQLException as e:
                status_msg.error(f"❌ Snowflake error for {file_name}: {e.message}")
                logger.error(f"Snowflake error for {file_name}: {e}", exc_info=True)
            except Exception as e:
                status_msg.error(f"❌ Error processing {file_name}: {str(e)}")
                logger.error(f"Error processing {file_name}: {e}", exc_info=True)
            
            # Update progress
            progress_bar.progress((i + 1) / total_files)
        
        # Final status
        st.markdown("---")
        if successful_uploads == total_files:
            st.success(f"🎉 All {total_files} files uploaded successfully!")
        elif successful_uploads > 0:
            st.warning(f"⚠️ {successful_uploads}/{total_files} files uploaded successfully.")
        else:
            st.error("❌ No files were uploaded successfully.")

else:
    st.info("📤 Upload files to get started...")

# Footer
st.markdown("---")
st.caption(f"Connected as: {role} | Warehouse: {warehouse} | Target: {db}.{schema}")

# Supported formats info
with st.expander("ℹ️ Supported File Formats"):
    for file_type, config in SUPPORTED_FILE_TYPES.items():
        st.write(f"**{file_type.upper()}:** {config['description']} - {', '.join(config['extensions'])}")