# H5 to SAS Converter

This tool converts HDF5 (.h5) files to SAS-compatible formats, preserving data structure and types as much as possible.

## Features

- **NEW: Automatic multi-dataset conversion** - Converts all datasets when none specified
- Convert single H5 files to SAS XPORT format (.xpt)
- Batch convert multiple H5 files in a directory
- Inspect H5 file structure before conversion
- List all datasets in an H5 file
- Handle various data types and shapes (1D, 2D, multi-dimensional arrays)
- Multiple output formats with automatic fallback
- Automatic SAS-compatible column naming
- Command-line interface with multiple options

## Quick Start

```bash
# Clone or navigate to the project directory
cd /Users/davidparry/code/github/hd5-7bdat

# Setup and run
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 Converter.py PatientData_1755638164371998322.h5
```

Your converted file will be saved as `PatientData_1755638164371998322.xpt` (SAS XPORT format).

## Quick Test with Sample Data

Want to see the converter in action with a small test file? We've included `test.h5`, a minimal test file with just 2 rows per dataset:

### Step 1: Run a quick test conversion
```bash
# Basic conversion
python3 Converter.py test.h5

# Expected output:
# 2025-08-25 17:44:40,962 - INFO - Converting test.h5 to test.sas7bdat
# 2025-08-25 17:44:40,964 - INFO - No dataset specified, using: Trends/ART_Dias
# 2025-08-25 17:44:40,966 - INFO - Converted dataset shape: (2, 1)
# 2025-08-25 17:44:40,966 - INFO - Columns: ['ART_Dias']
# 2025-08-25 17:44:40,993 - INFO - Successfully saved using pyreadstat (XPORT format) to: test.xpt
```

### Step 2: Verify the conversion
```bash
# Check the converted data
python3 -c "import pyreadstat; df, meta = pyreadstat.read_xport('test.xpt'); print('✓ Success! Data:', df.values.tolist())"
# Output: ✓ Success! Data: [[80.0], [82.0]]
```

### More test examples
```bash
# Inspect test file structure
python3 Converter.py test.h5 --inspect

# Convert a specific dataset (e.g., ECG data)
python3 Converter.py test.h5 -d "Waveforms/ECG_II" -o test_ecg.xpt

# Convert heart rate data
python3 Converter.py test.h5 -d "Trends/HR_na" -o test_hr.xpt
```

The test file contains the same structure as the full patient data but with minimal data (2 rows) for quick testing and verification.

## Installation

### Prerequisites

- Python 3.7 or higher
- pip package manager

### Setup Steps

1. **Create and activate a virtual environment:**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. **Install required packages:**
```bash
pip install -r requirements.txt
```

3. **Verify installation:**
```bash
python3 -c "import h5py, pandas, numpy, pyreadstat; print('✓ All packages installed successfully')"
```

If you see the success message, you're ready to convert files!

## Usage

### Basic Usage

Convert the sample H5 file to SAS format:
```bash
python3 Converter.py PatientData_1755638164371998322.h5
```

**Expected output (NEW - converts all datasets):**
```
2025-08-25 16:57:10,842 - INFO - Converting PatientData_1755638164371998322.h5 to PatientData_1755638164371998322.sas7bdat
2025-08-25 16:57:10,849 - INFO - No dataset specified. Found 15 dataset(s) in H5 file:
2025-08-25 16:57:10,849 - INFO -   - Trends/ART_Dias
2025-08-25 16:57:10,849 - INFO -   - Trends/ART_Mean
2025-08-25 16:57:10,849 - INFO -   - Trends/HR_na
2025-08-25 16:57:10,849 - INFO -   - Waveforms/ECG_II
2025-08-25 16:57:10,849 - INFO -   - ... (and more)
2025-08-25 16:57:10,849 - INFO - Converting all 15 dataset(s)...
2025-08-25 16:57:10,857 - INFO - Converting dataset 1/15: Trends/ART_Dias
2025-08-25 16:57:11,258 - INFO -   Successfully saved to: PatientData_1755638164371998322_Trends_ART_Dias.xpt
2025-08-25 16:57:11,300 - INFO - Converting dataset 2/15: Trends/ART_Mean
...
2025-08-25 16:57:15,123 - INFO - Completed conversion of 15 dataset(s)
2025-08-25 16:57:15,123 - INFO - All datasets converted successfully
```

To convert only a specific dataset, use the `-d` option:
```bash
python3 Converter.py PatientData_1755638164371998322.h5 -d "Trends/ART_Dias"
```

### Inspect H5 File Structure

Before converting, inspect the structure to see available datasets:
```bash
python3 Converter.py PatientData_1755638164371998322.h5 --inspect
```

This will display all groups and datasets in the file, including their shapes and data types.

### Convert Specific Dataset

If your H5 file contains multiple datasets (as shown by inspect), convert a specific one:
```bash
python3 Converter.py PatientData_1755638164371998322.h5 -d "Trends/SpO2_na"
```

### Custom Output Path

Specify a custom output filename:
```bash
python3 Converter.py PatientData_1755638164371998322.h5 -o my_output.xpt
```

### Batch Conversion

Convert all H5 files in the current directory:
```bash
python3 Converter.py . --batch
```

Convert with custom output directory:
```bash
python3 Converter.py . --batch -o ./output_folder
```

## Command Line Options

| Option | Long Form | Description |
|--------|-----------|-------------|
| `-o` | `--output` | Specify output file or directory |
| `-d` | `--dataset` | Specify dataset name to convert (for files with multiple datasets) |
| `-i` | `--inspect` | Inspect H5 file structure only (no conversion) |
| `-l` | `--list` | List all datasets in H5 file |
| `-b` | `--batch` | Batch convert all H5 files in a directory |
| | `--pattern` | File pattern for batch conversion (default: *.h5) |

### Default Behavior (No Dataset Specified)

**NEW:** When no dataset is specified with `-d`, the converter will:
1. Automatically identify all datasets in the H5 file
2. Convert each dataset to a separate output file
3. Name output files with the dataset name appended (e.g., `output_Trends_HR_na.xpt`)

This means you can now convert all datasets at once without specifying each one individually!

## Examples

### Example 1: Simple Conversion
```bash
# Convert the patient data file
python3 Converter.py PatientData_1755638164371998322.h5

# Check the output
ls -la PatientData_1755638164371998322.*
```

### Example 2: Inspect and Convert Specific Dataset
```bash
# First, inspect to see available datasets
python3 Converter.py PatientData_1755638164371998322.h5 --inspect

# List all datasets (simpler output)
python3 Converter.py PatientData_1755638164371998322.h5 --list

# Convert a specific dataset (e.g., arterial pressure)
python3 Converter.py PatientData_1755638164371998322.h5 -d "Trends/ART_Mean" -o arterial_mean.xpt

# Convert ALL datasets automatically (NEW!)
python3 Converter.py PatientData_1755638164371998322.h5
# This will create multiple output files, one for each dataset
```

### Example 3: Complete Workflow
```bash
# 1. Setup environment (first time only)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Verify installation
python3 -c "import h5py, pandas, numpy, pyreadstat; print('✓ Ready to convert')"

# 3. Inspect the H5 file structure
python3 Converter.py PatientData_1755638164371998322.h5 --inspect

# 4. Convert to SAS XPORT format
python3 Converter.py PatientData_1755638164371998322.h5

# 5. Verify output was created
ls -la *.xpt *.csv *.sas
```

### Example 4: Batch Processing
```bash
# Convert all H5 files in current directory
python3 Converter.py . --batch

# Convert specific pattern
python3 Converter.py . --batch --pattern "Patient*.h5"
```

## Output Formats

The converter attempts multiple output formats in order of preference:

### Primary: SAS XPORT (.xpt)
- **Extension:** `.xpt`
- **Format:** SAS Transport (XPORT) format
- **Compatibility:** Can be read by SAS, R, Python, and other statistical software
- **When used:** When pyreadstat is installed (recommended)

### Fallback: CSV with SAS Import Script
- **Extensions:** `.csv` + `.sas`
- **Format:** Comma-separated values with accompanying SAS import code
- **When used:** If XPORT conversion fails or pyreadstat is not available
- **Files created:**
  - `filename.csv` - Data in CSV format with SAS-compatible column names
  - `filename.sas` - SAS script to import the CSV into SAS

**Note:** The tool does not directly create `.sas7bdat` files, but the XPORT format (`.xpt`) is fully compatible with SAS and can be imported directly.

## Data Type Handling

The converter automatically handles various data types:

| H5 Data Type | Converted To | Notes |
|--------------|--------------|-------|
| int8, int16, int32, int64 | int64 | Standardized integer format |
| uint8, uint16, uint32, uint64 | int64 | Converted to signed integers |
| float32, float64 | float64 | Preserved as floating point |
| bool | int64 | Converted to 0/1 |
| object/string | string | Max 32 characters for SAS compatibility |

## Troubleshooting

### Installation Issues

**Problem:** `ModuleNotFoundError: No module named 'h5py'`
```bash
# Solution: Ensure virtual environment is activated
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Problem:** `error: externally-managed-environment`
```bash
# Solution: Use virtual environment (already included in setup steps)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Conversion Issues

**Problem:** Output is CSV instead of XPT
```bash
# Solution: Install pyreadstat for XPORT support
pip install pyreadstat
```

**Problem:** "No datasets found in H5 file"
```bash
# Solution: Inspect file structure first
python3 Converter.py PatientData_1755638164371998322.h5 --inspect
```

**Problem:** Large file taking too long
```bash
# Solution: Convert specific dataset instead of entire file
python3 Converter.py PatientData_1755638164371998322.h5 -d "Trends/ART_Dias"
```

### Common Issues and Solutions

1. **Virtual environment not activated:**
   - Symptom: Import errors or wrong Python version
   - Fix: Always run `source .venv/bin/activate` before using the converter

2. **Column names modified:**
   - Symptom: Column names differ from original
   - Reason: SAS requires alphanumeric names (max 32 chars)
   - This is normal and ensures SAS compatibility

3. **Multi-dimensional arrays flattened:**
   - Symptom: 3D+ arrays become 2D in output
   - Reason: SAS datasets are 2-dimensional
   - Column names indicate original dimensions

## Performance Considerations

- **Large files (>1GB):** Consider converting specific datasets rather than the entire file
- **Memory usage:** The converter loads datasets into memory; ensure sufficient RAM
- **Processing time:** XPORT conversion is faster than CSV generation

## Project Structure

```
hd5-7bdat/
├── Converter.py                          # Main converter script
├── requirements.txt                       # Python dependencies
├── README.md                             # This documentation
├── test.h5                               # Test H5 file (2 rows per dataset)
└── .venv/                                # Virtual environment (after setup)
```

## Dependencies

- **h5py** (>=3.7.0): For reading HDF5 files
- **pandas** (>=1.5.0): For data manipulation
- **numpy** (>=1.21.0): For numerical operations
- **pyreadstat** (>=1.2.0): For writing SAS XPORT format

## License

This project is provided as-is for data conversion purposes.

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Inspect your H5 file structure using `--inspect`
3. Verify all dependencies are installed correctly
4. Ensure you're using Python 3.7 or higher