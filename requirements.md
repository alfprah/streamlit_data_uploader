# Universal Data Uploader to Snowflake - Requirements & Setup Guide

> **Open Source Project**: This is a community-driven tool for Snowflake users. Contributions and feedback welcome!

## Overview
*Disclaimer: This app is provided as a sample resource for your convenience. It is not officially supported by Snowflake and is provided "as is," without warranty or liability. Please review the code and validate it for your use case before deploying in a production environment.* This Streamlit application provides a universal file uploader that can handle various file formats (.csv, .txt, .xlsx, .xls) and upload them directly to Snowflake tables with automatic column name cleaning and data type standardization.

## Features

- **Universal File Support**: CSV, TXT, and Excel files (.xlsx, .xls) - all formats fully supported
- **Interactive Column Renaming**: Edit column names using built-in data editor before upload
- **File Preview**: Preview data structure and content before uploading
- **Custom Table Naming**: Rename tables before upload with automatic name sanitization
- **Batch Upload**: Upload multiple files simultaneously with progress tracking
- **Smart Column Cleaning**: Automatic conversion to Snowflake-friendly column names
- **Configurable CSV Options**: Customizable delimiters, headers, and quote characters
- **Session Management**: Persistent configuration across file interactions
- **Real-time Status**: Live upload progress and error reporting

## Prerequisites

### 1. Python Environment
- Python 3.8 or higher
- Required packages (see Installation section)

### 2. Snowflake Setup
- Active Snowflake account
- Appropriate role with required permissions (see Permissions section)
- Database and schema access for table creation/modification

### 3. Snowpark Configuration
- The app runs exclusively in Snowflake's Streamlit environment
- Uses `get_active_session()` to automatically connect to your Snowflake account
- No manual connection configuration required

## Installation

### Snowflake Streamlit Deployment
1. **Create Streamlit App**: In Snowflake, create a new Streamlit app
2. **Upload Files**: Upload all project files to your Streamlit app:
   - `streamlit_app.py` (main application)
   - `environment.yml` (dependencies)
3. **Configure Environment**: Ensure the `environment.yml` file is recognized
4. **Reboot**: Click "Reboot" in Snowflake Streamlit interface to install dependencies
5. **Universal Support**: All file formats (CSV, TXT, Excel) are fully supported

### Required Dependencies
- `streamlit` - Web application framework (version 1.28+ recommended for data editor)
- `pandas` - Data manipulation and analysis (includes Excel support)
- `snowflake-snowpark-python` - Snowflake connection and operations

### Component Requirements
- **Interactive Data Editor**: Requires Streamlit 1.23+ for `st.data_editor` functionality
- **Session State**: Uses Streamlit's built-in session state for configuration persistence

## Snowflake Permissions Required

### Minimum Role Permissions
Your Snowflake role must have the following permissions:

#### Database Level
```sql
GRANT USAGE ON DATABASE <your_database> TO ROLE <your_role>;
```

#### Schema Level
```sql
GRANT USAGE ON SCHEMA <your_database>.<your_schema> TO ROLE <your_role>;
GRANT CREATE TABLE ON SCHEMA <your_database>.<your_schema> TO ROLE <your_role>;
```

#### Table Level (for existing tables)
```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA <your_database>.<your_schema> TO ROLE <your_role>;
-- Or for specific tables:
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE <your_database>.<your_schema>.<table_name> TO ROLE <your_role>;
```

#### Warehouse Access
```sql
GRANT USAGE ON WAREHOUSE <your_warehouse> TO ROLE <your_role>;
```

### Example Permission Setup Script
```sql
-- Replace with your actual values
USE ROLE ACCOUNTADMIN; -- Or appropriate admin role

-- Grant database access
GRANT USAGE ON DATABASE MY_DATABASE TO ROLE DATA_LOADER_ROLE;

-- Grant schema access and table creation
GRANT USAGE ON SCHEMA MY_DATABASE.PUBLIC TO ROLE DATA_LOADER_ROLE;
GRANT CREATE TABLE ON SCHEMA MY_DATABASE.PUBLIC TO ROLE DATA_LOADER_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA MY_DATABASE.PUBLIC TO ROLE DATA_LOADER_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA MY_DATABASE.PUBLIC TO ROLE DATA_LOADER_ROLE;

-- Grant warehouse access
GRANT USAGE ON WAREHOUSE MY_WAREHOUSE TO ROLE DATA_LOADER_ROLE;

-- Assign role to user
GRANT ROLE DATA_LOADER_ROLE TO USER MY_USER;
```

## Configuration for New Users

### 1. Update Database Connection
When deploying for a new user/environment, ensure the Snowpark session connects to the correct:

- **Database**: Target database name
- **Schema**: Target schema name  
- **Warehouse**: Compute warehouse to use
- **Role**: Role with appropriate permissions

### 2. Snowflake Context Configuration
The app automatically uses Snowflake's session context when running in Streamlit:
```python
# Automatic session detection in Snowflake Streamlit
session = get_active_session()
db = session.get_current_database()
schema = session.get_current_schema()
role = session.get_current_role()
warehouse = session.get_current_warehouse()
```

### 3. File Size Considerations
- **Snowflake Streamlit**: Default upload limit is 200MB per file
- **Warehouse Size**: Choose appropriate warehouse size for your data volume
- **Processing**: Large files are processed efficiently within Snowflake's environment

## Usage Instructions

### 1. Access Your Snowflake Streamlit App
Navigate to your deployed Streamlit app in Snowflake and ensure all files are uploaded with the correct environment configuration.

### 2. Configure Upload Settings
- Use the sidebar to configure CSV parsing options:
  - **Delimiter**: Choose between comma, semicolon, pipe, or tab
  - **Header Row**: Specify if first row contains column names
  - **Quote Character**: Set quote character for text fields

### 3. Upload Files
1. Click "Browse files" or drag and drop files
2. All formats supported: .csv, .txt, .xlsx, .xls
3. Multiple files can be selected simultaneously

### 4. Configure Each File
For each uploaded file:
- **Table Name**: Customize the target table name (auto-cleaned for Snowflake compatibility)
- **Load Preview**: Click "👀 Load Preview" to see data structure and load column editor
- **Rename Columns**: Use the interactive data editor to rename columns before upload
- **Verify**: Check the target location shows correct database.schema.table

### 5. Execute Upload
- Click "Upload All Files" to process all configured files
- Monitor progress bar and individual file status
- Review final upload summary

## Data Processing Details

### Interactive Column Renaming
The app provides an interactive workflow for column management:
- **Load Preview**: Click to load data and display the first 10 rows
- **Data Editor**: Interactive table showing original column names vs rename options
- **Custom Names**: Edit the "Rename To" column to specify custom column names
- **Auto-Cleaning**: Final column names are automatically cleaned for Snowflake compatibility

### Column Name Cleaning Rules
All column names (custom or original) are converted to Snowflake-friendly format:
- **Uppercase**: All column names converted to uppercase
- **Spaces/Hyphens**: Replaced with underscores
- **Special Characters**: Removed (parentheses, brackets, punctuation)
- **Leading Numbers**: Prefixed with underscore
- **Empty Names**: Replaced with "UNNAMED_COLUMN"

### Data Type Handling
- All data is converted to string type for consistent Snowflake loading
- NULL values are properly handled (NaN, <NA>, 'None' → NULL)
- Empty fields become NULL based on CSV options

### Table Operations
- **Mode**: Overwrite (existing table data is replaced)
- **Error Handling**: Continue on error (bad rows logged but don't stop process)
- **Table Creation**: Tables are created automatically if they don't exist

## Troubleshooting

### Common Issues

#### 1. Permission Errors
```
Error: does not exist or not authorized
```
**Solution**: Verify role has required permissions on database, schema, and tables

#### 2. Column Mismatch Errors
```
Error: column mismatch
```
**Solution**: 
- Use the column renaming feature to match existing table schema
- Ensure target table columns match cleaned column names
- Allow app to create new table with auto-generated schema

#### 3. File Format Errors
```
Error: Unsupported file type
```
**Solution**: Ensure file has supported extension (.csv, .txt, .xlsx, .xls) and is properly formatted

#### 4. Memory Issues
```
Error: Memory error during file processing
```
**Solution**: 
- Process smaller files
- Increase available system memory
- Use more powerful Snowflake warehouse

#### 5. Connection Issues
```
Error: Error getting Snowflake session
```
**Solution**: 
- Ensure app is running in Snowflake Streamlit environment
- Verify your Snowflake role has necessary permissions
- Check that Streamlit is properly configured in your Snowflake account

### Performance Optimization

#### For Large Files
- Use larger Snowflake warehouse (M, L, XL, etc.)
- Process files individually rather than batch upload
- Consider file splitting for extremely large datasets

#### For Many Small Files
- Batch upload is efficient for multiple small files
- Use appropriate warehouse size for total data volume

## Security Considerations

### Data Privacy
- Files are processed in memory and not stored permanently on the app server
- Data is transmitted directly to Snowflake using encrypted connections
- No intermediate file storage on local system

### Access Control
- App inherits permissions from the user's Snowflake role
- No elevation of privileges beyond user's existing access
- All operations logged through Snowflake's audit trail

### Sensitive Data
- Avoid uploading files with PII/PHI without proper governance
- Ensure target schema has appropriate access controls
- Consider data masking for sensitive columns

## Support and Maintenance

### Regular Maintenance
- Monitor Snowflake warehouse usage and costs
- Review and update role permissions as needed
- Update Python dependencies periodically

### Logging
- Application logs available in Snowflake Streamlit interface
- Snowflake operation logs available in Snowflake query history
- Error details captured for troubleshooting

### Customization Options
The app can be easily extended to support:
- Additional file formats
- Enhanced column editing features (data type selection, validation rules)
- Custom data transformations
- Different upload modes (append, merge)
- Advanced column type inference
- Custom validation rules
- Column mapping templates for common file structures

---

## Support

For technical support or feature requests:
- **Issues**: Open an issue on the GitHub repository
- **Contributions**: Pull requests welcome!
- **Community**: Share your experiences and improvements

This is an open-source project - community contributions and feedback are encouraged!

## License

This project is provided as-is for the Snowflake community. Feel free to use, modify, and distribute according to your needs. 