# 🚀 Universal Data Uploader to Snowflake

A powerful Streamlit application that enables seamless uploading of various file formats (.csv, .txt, .xlsx, .xls) directly to Snowflake tables with intelligent column name cleaning and data processing.

## ✨ Key Features

- **Universal File Support**: CSV, TXT, Excel (.xlsx, .xls) - all formats fully supported
- **Interactive Column Renaming**: Edit column names with built-in data editor
- **Smart Column Cleaning**: Automatic Snowflake-friendly column naming
- **File Preview**: Preview data structure and content before upload
- **Custom Table Naming**: Rename tables with automatic sanitization
- **Batch Processing**: Upload multiple files simultaneously
- **Progress Tracking**: Real-time upload status and error reporting
- **Configurable CSV Options**: Customize delimiters, headers, and quote characters

## 🚀 Quick Start

1. **Deploy to Snowflake**
   - Upload all project files to your Snowflake Streamlit app
   - Include the `environment.yml` file for dependencies
   - Click "Reboot" to install packages

2. **Start Using**
   - Drag & drop or browse for files
   - Configure table names and CSV options
   - Load preview and rename columns interactively
   - Click "Upload All Files"

## 📁 Supported File Formats

| Format | Extensions | Status |
|--------|------------|--------|
| CSV | `.csv` | ✅ Fully supported |
| Text | `.txt` | ✅ Fully supported |
| Excel | `.xlsx, .xls` | ✅ Fully supported |

## ⚙️ Configuration

### Snowflake Requirements
- Snowflake account with Streamlit enabled
- Active Snowpark session
- Database and schema access
- Table creation permissions
- Appropriate warehouse access

### CSV Options (Configurable)
- **Delimiter**: Comma, semicolon, pipe, or tab
- **Headers**: First row contains column names
- **Quote Character**: Text field enclosure

## 📊 Data Processing

### Interactive Column Renaming
1. **Load Preview** - Click to load data and see first 10 rows
2. **Edit Column Names** - Use interactive data editor to rename columns
3. **Auto-Cleaning** - Final names are cleaned for Snowflake compatibility

### Column Name Cleaning Examples
Original columns are automatically converted:
- `Product Name` → `PRODUCT_NAME`
- `SKU-ID` → `SKU_ID`
- `Price ($)` → `PRICE`
- `123ABC` → `_123ABC`

### Data Handling
- All data converted to string type for consistency
- NULL values properly handled (`NaN`, `<NA>`, `None` → `NULL`)
- Empty fields become NULL based on CSV options

## 🔧 Testing the App

1. **Upload any supported file** - CSV, TXT, Excel files all work immediately
2. **Test column renaming** - Load preview and edit column names
3. **Test different delimiters** - Try semicolon, tab, pipe separators
4. **Preview functionality** - Test the data preview and interactive editor
5. **Multi-format batch** - Upload mixed file types together

## 📚 Documentation

For detailed setup instructions, permissions, and troubleshooting, see [requirements.md](requirements.md).

## 🏗️ Architecture

```
User Files → Streamlit UI → Pandas → Column Cleaning → Snowpark → Snowflake Tables
```

## 💡 Advanced Features

- **Interactive UI**: Modern data editor for column renaming
- **Session Management**: Persistent configuration across interactions
- **Simple & Reliable**: Clean code that lets pandas handle Excel support naturally
- **Runtime Detection**: Excel works if pandas supports it, clear errors if not
- **Error Handling**: Continue processing on individual row errors  
- **Memory Efficient**: Processes files in memory without disk storage
- **Security**: Inherits user's Snowflake permissions
- **Logging**: Comprehensive logging for troubleshooting

## 🤝 Contributing

This application can be easily extended to support:
- Additional file formats
- Custom data transformations
- Different upload modes (append, merge)
- Advanced column type inference
- Custom validation rules

---

**Note**: This app requires a Snowflake environment with appropriate permissions. See `requirements.md` for detailed setup instructions. 