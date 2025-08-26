#!/usr/bin/env python3
"""
H5 to 7BDAT Converter

This script converts HDF5 (.h5) files to SAS 7BDAT format.
The conversion preserves data structure and types as much as possible.
"""

import h5py
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
import argparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class H5To7BDATConverter:
    """Converter class for H5 to 7BDAT file conversion."""
    
    def __init__(self):
        self.supported_dtypes = {
            'int8', 'int16', 'int32', 'int64',
            'uint8', 'uint16', 'uint32', 'uint64',
            'float32', 'float64',
            'bool', 'object'
        }
    
    def inspect_h5_file(self, h5_path):
        """Inspect the structure of an H5 file."""
        logger.info(f"Inspecting H5 file: {h5_path}")
        
        try:
            with h5py.File(h5_path, 'r') as f:
                print(f"\nH5 File Structure for: {h5_path}")
                print("=" * 50)
                
                def print_structure(name, obj):
                    if isinstance(obj, h5py.Dataset):
                        print(f"Dataset: {name}")
                        print(f"  Shape: {obj.shape}")
                        print(f"  Dtype: {obj.dtype}")
                        print(f"  Size: {obj.size}")
                        if obj.attrs:
                            print(f"  Attributes: {dict(obj.attrs)}")
                        print()
                    elif isinstance(obj, h5py.Group):
                        print(f"Group: {name}")
                        if obj.attrs:
                            print(f"  Attributes: {dict(obj.attrs)}")
                        print()
                
                f.visititems(print_structure)
                
        except Exception as e:
            logger.error(f"Error inspecting H5 file: {e}")
            return False
        
        return True
    
    def convert_h5_dataset_to_dataframe(self, dataset, dataset_name):
        """Convert an H5 dataset to a pandas DataFrame."""
        try:
            data = dataset[:]
            
            # Handle different data shapes
            if len(data.shape) == 1:
                # 1D array - create single column DataFrame
                df = pd.DataFrame({dataset_name: data})
            elif len(data.shape) == 2:
                # 2D array - use as is or create column names
                if data.shape[1] == 1:
                    df = pd.DataFrame({dataset_name: data.flatten()})
                else:
                    # Create column names for multi-column data
                    columns = [f"{dataset_name}_col_{i}" for i in range(data.shape[1])]
                    df = pd.DataFrame(data, columns=columns)
            else:
                # Higher dimensional data - flatten to 2D
                logger.warning(f"Dataset {dataset_name} has {len(data.shape)} dimensions. Flattening to 2D.")
                reshaped_data = data.reshape(data.shape[0], -1)
                columns = [f"{dataset_name}_dim_{i}" for i in range(reshaped_data.shape[1])]
                df = pd.DataFrame(reshaped_data, columns=columns)
            
            # Handle data type conversion
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Try to convert object columns to string
                    try:
                        df[col] = df[col].astype(str)
                    except:
                        logger.warning(f"Could not convert column {col} to string")
                elif np.issubdtype(df[col].dtype, np.integer):
                    # Ensure integer types are compatible
                    if df[col].dtype not in ['int32', 'int64']:
                        df[col] = df[col].astype('int64')
                elif np.issubdtype(df[col].dtype, np.floating):
                    # Ensure float types are compatible
                    if df[col].dtype not in ['float32', 'float64']:
                        df[col] = df[col].astype('float64')
            
            return df
            
        except Exception as e:
            logger.error(f"Error converting dataset {dataset_name}: {e}")
            return None
    
    def generate_sas_import_script(self, file_path, df, file_type='csv'):
        """Generate a SAS script to import the file (CSV or XPORT)."""
        file_name = Path(file_path).stem
        file_path_str = str(file_path).replace('\\', '/')  # Ensure forward slashes for SAS
        
        # Clean filename for SAS dataset name
        sas_dataset_name = ''.join(c for c in file_name if c.isalnum() or c == '_')
        if sas_dataset_name and sas_dataset_name[0].isdigit():
            sas_dataset_name = '_' + sas_dataset_name
        sas_dataset_name = sas_dataset_name[:32]  # SAS dataset name limit
        
        if file_type == 'xport' or file_path.suffix.lower() == '.xpt':
            # Generate XPORT import script with better SAS 9.4 compatibility
            sas_code = f"""/* SAS Import Script for XPORT file: {file_path} */
/* Generated by H5 to 7BDAT Converter */
/* Compatible with SAS 9.4 */

/* Clear any existing libraries with same name */
libname myxpt clear;
libname outlib clear;

/* Define library for output dataset */
libname outlib ".";

/* Method 1: Using PROC COPY (Recommended for SAS 9.4) */
/* Define XPORT library for input file */
libname myxpt xport "{file_path_str}";

/* Check what's in the XPORT file */
proc contents data=myxpt._all_;
    title "Contents of XPORT file";
run;

/* Copy all datasets from XPORT file to work library */
proc copy in=myxpt out=work;
run;

/* Alternative Method: If PROC COPY fails, try direct data step */
/*
data work.{sas_dataset_name};
    set myxpt._first_;
run;
*/

/* Display first 10 observations */
proc print data=work._first_ (obs=10);
    title "First 10 observations from imported XPORT file";
run;

/* Save as permanent SAS dataset */
data outlib.{sas_dataset_name};
    set work._first_;
run;

/* Clear the XPORT library */
libname myxpt clear;

/* Confirmation message */
%put NOTE: Dataset import attempted from XPORT file;
%put NOTE: If import failed, use the CSV file instead (recommended for SAS 9.4);
"""
        else:
            # Generate CSV import script (RECOMMENDED for SAS 9.4)
            # Determine data types for SAS
            sas_types = []
            for col, dtype in df.dtypes.items():
                if np.issubdtype(dtype, np.integer):
                    sas_types.append(f"{col} 8")
                elif np.issubdtype(dtype, np.floating):
                    sas_types.append(f"{col} 8")
                else:
                    # Determine appropriate string length
                    max_len = 32
                    if col in df.columns:
                        try:
                            max_len = min(200, max(32, df[col].astype(str).str.len().max()))
                        except:
                            max_len = 32
                    sas_types.append(f"{col} ${max_len}")
            
            sas_code = f"""/* SAS Import Script for CSV file: {file_path} */
/* Generated by H5 to 7BDAT Converter */
/* RECOMMENDED METHOD for SAS 9.4 */

/* Clear any existing library */
libname outlib clear;
libname outlib ".";

/* Method 1: PROC IMPORT (Simple and reliable) */
proc import datafile="{file_path_str}"
    out=work.{sas_dataset_name}
    dbms=csv
    replace;
    getnames=yes;
    guessingrows=MAX;  /* Use all rows to determine data types */
run;

/* Check the imported data */
proc contents data=work.{sas_dataset_name};
    title "Structure of imported CSV data";
run;

/* Display first 10 observations */
proc print data=work.{sas_dataset_name} (obs=10);
    title "First 10 observations from CSV file";
run;

/* Method 2: DATA step with INFILE (More control over data types) */
/* Uncomment and modify if PROC IMPORT has issues */
/*
data work.{sas_dataset_name}_v2;
    length {' '.join(sas_types)};
    infile "{file_path_str}" 
        delimiter=',' 
        missover 
        dsd 
        firstobs=2;
    input {' '.join(col + ' $' if '$' in str(dtype) else col for col, dtype in zip(df.columns, sas_types))};
run;
*/

/* Save as permanent SAS dataset */
data outlib.{sas_dataset_name};
    set work.{sas_dataset_name};
run;

/* Summary statistics */
proc means data=outlib.{sas_dataset_name} n nmiss min max mean;
    title "Summary Statistics";
run;

/* Success message */
%put NOTE: Dataset successfully imported from CSV file;
%put NOTE: Saved as outlib.{sas_dataset_name} in current directory;
%put NOTE: This is the recommended import method for SAS 9.4;
"""
        return sas_code
    
    def list_datasets(self, h5_path):
        """List all datasets in an H5 file."""
        datasets = []
        try:
            with h5py.File(h5_path, 'r') as f:
                def collect_datasets(name, obj):
                    if isinstance(obj, h5py.Dataset):
                        datasets.append(name)
                f.visititems(collect_datasets)
        except Exception as e:
            logger.error(f"Error listing datasets: {e}")
        return datasets
    
    def convert_h5_to_7bdat(self, h5_path, output_path=None, dataset_name=None, convert_all=False):
        """
        Convert H5 file to 7BDAT format.
        
        Args:
            h5_path (str): Path to input H5 file
            output_path (str): Path for output 7BDAT file (optional)
            dataset_name (str): Specific dataset to convert (optional)
            convert_all (bool): Convert all datasets if no specific dataset is given
        """
        h5_path = Path(h5_path)
        
        if not h5_path.exists():
            logger.error(f"Input file does not exist: {h5_path}")
            return False
        
        # Generate output path if not provided
        if output_path is None:
            output_path = h5_path.with_suffix('.sas7bdat')
        else:
            output_path = Path(output_path)
        
        logger.info(f"Converting {h5_path} to {output_path}")
        
        try:
            with h5py.File(h5_path, 'r') as f:
                # Get all datasets
                datasets = []
                
                def collect_datasets(name, obj):
                    if isinstance(obj, h5py.Dataset):
                        datasets.append((name, obj))
                
                f.visititems(collect_datasets)
                
                if not datasets:
                    logger.error("No datasets found in H5 file")
                    return False
                
                # Select dataset(s) to convert
                if dataset_name:
                    # Convert specific dataset
                    selected_dataset = None
                    for name, dataset in datasets:
                        if name == dataset_name or name.endswith(f"/{dataset_name}"):
                            selected_dataset = (name, dataset)
                            break
                    
                    if selected_dataset is None:
                        logger.error(f"Dataset '{dataset_name}' not found")
                        logger.info(f"Available datasets: {[name for name, _ in datasets]}")
                        return False
                    
                    datasets_to_convert = [selected_dataset]
                else:
                    # No dataset specified - identify all datasets and convert each
                    logger.info(f"No dataset specified. Found {len(datasets)} dataset(s) in H5 file:")
                    for name, _ in datasets:
                        logger.info(f"  - {name}")
                    
                    # Convert all datasets
                    datasets_to_convert = datasets
                    logger.info(f"Converting all {len(datasets_to_convert)} dataset(s)...")
                
                # Convert each selected dataset
                all_successful = True
                for idx, (name, dataset) in enumerate(datasets_to_convert):
                    logger.info(f"\nConverting dataset {idx+1}/{len(datasets_to_convert)}: {name}")
                    
                    # Generate unique output path for each dataset
                    if len(datasets_to_convert) > 1:
                        # Clean dataset name for filename
                        clean_name = name.replace('/', '_').strip('_')
                        if output_path.suffix:
                            dataset_output_path = output_path.parent / f"{output_path.stem}_{clean_name}{output_path.suffix}"
                        else:
                            dataset_output_path = output_path.parent / f"{output_path.name}_{clean_name}.sas7bdat"
                    else:
                        dataset_output_path = output_path
                    
                    df = self.convert_h5_dataset_to_dataframe(dataset, name.split('/')[-1])
                
                    if df is None:
                        logger.error(f"Failed to convert dataset: {name}")
                        all_successful = False
                        continue
                    
                    logger.info(f"  Dataset shape: {df.shape}")
                    logger.info(f"  Columns: {list(df.columns)}")
                    logger.info(f"  Data types: {df.dtypes.to_dict()}")
                    
                    # Save data - prioritize CSV for better SAS 9.4 compatibility
                    saved_successfully = False
                    
                    # Method 1: Save as CSV with SAS-compatible format (MOST RELIABLE for SAS 9.4)
                    logger.info("  Saving as CSV with SAS-compatible formatting (recommended for SAS 9.4)...")
                    csv_path = dataset_output_path.with_suffix('.csv')
                    
                    # Ensure column names are SAS-compatible (max 32 chars, no special chars)
                    df_sas_compatible = df.copy()
                    new_columns = {}
                    for col in df_sas_compatible.columns:
                        # Make column names SAS-compatible
                        new_col = str(col).replace(' ', '_').replace('-', '_')
                        new_col = ''.join(c for c in new_col if c.isalnum() or c == '_')
                        # Ensure column name starts with letter or underscore
                        if new_col and new_col[0].isdigit():
                            new_col = '_' + new_col
                        new_col = new_col[:32]  # SAS max column name length
                        new_columns[col] = new_col
                    
                    df_sas_compatible.rename(columns=new_columns, inplace=True)
                    df_sas_compatible.to_csv(csv_path, index=False)
                    logger.info(f"  ✓ Saved as SAS-compatible CSV: {csv_path}")
                    
                    # Create a SAS import script for CSV
                    sas_script_path = dataset_output_path.with_suffix('.sas')
                    sas_import_code = self.generate_sas_import_script(csv_path, df_sas_compatible, file_type='csv')
                    with open(sas_script_path, 'w') as f:
                        f.write(sas_import_code)
                    logger.info(f"  ✓ Created SAS import script: {sas_script_path}")
                    saved_successfully = True
                    
                    # Method 2: Also try XPORT format if pyreadstat is available
                    try:
                        import pyreadstat
                        xport_path = dataset_output_path.with_suffix('.xpt')
                        
                        # Ensure dataset name is max 8 characters for XPORT
                        table_name = clean_name[:8] if len(clean_name) > 8 else clean_name
                        # Remove any non-alphanumeric characters from table name
                        table_name = ''.join(c for c in table_name if c.isalnum())
                        if not table_name:
                            table_name = 'DATA'
                        
                        # Truncate column names to 8 characters for XPORT format
                        df_xport = df_sas_compatible.copy()
                        xport_columns = {}
                        for col in df_xport.columns:
                            xport_col = col[:8]
                            # Ensure uniqueness
                            counter = 1
                            while xport_col in xport_columns.values():
                                xport_col = col[:7] + str(counter)
                                counter += 1
                            xport_columns[col] = xport_col
                        
                        df_xport.rename(columns=xport_columns, inplace=True)
                        
                        # Write XPORT file with SAS 9.4 compatible settings
                        pyreadstat.write_xport(
                            df_xport, 
                            str(xport_path), 
                            table_name=table_name.upper(),
                            file_label='H5 to SAS Conversion'
                        )
                        logger.info(f"  ✓ Also saved as XPORT format: {xport_path}")
                        
                        # Create XPORT-specific import script
                        xport_sas_script = xport_path.with_suffix('.sas')
                        xport_import_code = self.generate_sas_import_script(xport_path, df_xport, file_type='xport')
                        with open(xport_sas_script, 'w') as f:
                            f.write(xport_import_code)
                        
                    except ImportError:
                        if idx == 0:  # Only warn once
                            logger.info("  Note: pyreadstat not available for XPORT format. CSV format will work fine with SAS.")
                    except Exception as e:
                        logger.warning(f"  Could not create XPORT file: {e}")
                        logger.info("  CSV format is still available and recommended for SAS 9.4")
                    
                    if not saved_successfully:
                        all_successful = False
                        logger.error(f"  Failed to save dataset: {name}")
                
                if len(datasets_to_convert) > 1:
                    logger.info(f"\nCompleted conversion of {len(datasets_to_convert)} dataset(s)")
                    if all_successful:
                        logger.info("All datasets converted successfully")
                    else:
                        logger.warning("Some datasets failed to convert")
                
                return all_successful
                
        except Exception as e:
            logger.error(f"Error processing H5 file: {e}")
            return False
    
    def batch_convert(self, input_dir, output_dir=None, pattern="*.h5"):
        """Convert multiple H5 files in a directory."""
        input_dir = Path(input_dir)
        
        if output_dir is None:
            output_dir = input_dir
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        h5_files = list(input_dir.glob(pattern))
        
        if not h5_files:
            logger.warning(f"No H5 files found in {input_dir} with pattern {pattern}")
            return
        
        logger.info(f"Found {len(h5_files)} H5 files to convert")
        
        success_count = 0
        for h5_file in h5_files:
            output_file = output_dir / h5_file.with_suffix('.sas7bdat').name
            if self.convert_h5_to_7bdat(h5_file, output_file):
                success_count += 1
        
        logger.info(f"Successfully converted {success_count}/{len(h5_files)} files")


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description='Convert H5 files to SAS 7BDAT format')
    parser.add_argument('input', help='Input H5 file or directory')
    parser.add_argument('-o', '--output', help='Output file or directory')
    parser.add_argument('-d', '--dataset', help='Specific dataset name to convert')
    parser.add_argument('-i', '--inspect', action='store_true', help='Inspect H5 file structure only')
    parser.add_argument('-b', '--batch', action='store_true', help='Batch convert all H5 files in directory')
    parser.add_argument('-l', '--list', action='store_true', help='List all datasets in H5 file')
    parser.add_argument('--pattern', default='*.h5', help='File pattern for batch conversion (default: *.h5)')
    
    args = parser.parse_args()
    
    converter = H5To7BDATConverter()
    
    if args.inspect:
        converter.inspect_h5_file(args.input)
    elif args.list:
        datasets = converter.list_datasets(args.input)
        if datasets:
            print(f"\nDatasets found in {args.input}:")
            for dataset in datasets:
                print(f"  - {dataset}")
        else:
            print(f"No datasets found in {args.input}")
    elif args.batch:
        converter.batch_convert(args.input, args.output, args.pattern)
    else:
        # Convert with automatic dataset detection if none specified
        converter.convert_h5_to_7bdat(args.input, args.output, args.dataset, convert_all=True)


if __name__ == "__main__":
    # If run directly, try to convert the sample file in the current directory
    if len(sys.argv) == 1:
        # Look for H5 files in current directory
        h5_files = list(Path('.').glob('*.h5'))
        if h5_files:
            converter = H5To7BDATConverter()
            print("Found H5 files in current directory:")
            for i, h5_file in enumerate(h5_files):
                print(f"{i+1}. {h5_file}")
            
            # Convert the first one as an example
            print(f"\nInspecting: {h5_files[0]}")
            converter.inspect_h5_file(h5_files[0])
            
            # List datasets
            datasets = converter.list_datasets(h5_files[0])
            if datasets:
                print(f"\nFound {len(datasets)} dataset(s). Converting all...")
                converter.convert_h5_to_7bdat(h5_files[0], convert_all=True)
            else:
                print("No datasets found to convert.")
        else:
            print("No H5 files found in current directory.")
            print("Usage: python Converter.py <input.h5> [-o output.sas7bdat] [-d dataset_name]")
            print("       python Converter.py <input.h5> -l  # List all datasets")
            print("       python Converter.py <input.h5>     # Convert all datasets automatically")
    else:
        main()