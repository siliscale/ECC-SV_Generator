# ECC-SV Generator

A Python-based tool for automatically generating SEC-DED (Single Error Correction, Double Error Detection) encoder and decoder modules in SystemVerilog.

## Overview

This tool generates Error Correction Code (ECC) modules that can:
- **Detect** up to 2 bit errors
- **Correct** single bit errors
- Support both **Even Parity (EP)** and **Odd Parity (OP)** configurations

The generated modules are written in SystemVerilog and follow standard ECC encoding/decoding principles using Hamming codes with an additional parity bit.

## Features

- **Automatic Generation**: Creates both encoder and decoder modules based on input parameters
- **Configurable Data Width**: Supports any input data size (specified in bits)
- **Parity Options**: Supports both Even Parity (EP) and Odd Parity (OP) configurations
- **Code Formatting**: Automatically formats generated SystemVerilog code using `verible-verilog-format` if installed

## Requirements

### System Requirements
- Python 3.x
- `verible-verilog-format` (optional, for code formatting), part of the [Verible Suite](https://github.com/chipsalliance/verible)


## Usage

### Basic Usage

```bash
python main.py --input-size <data_width> --code-type <parity_type>
```

### Parameters

- `--input-size`: The width of the input data in bits (required)
- `--code-type`: The parity type (required)
  - `SEC_DED_EP`: Single Error Correction, Double Error Detection with Even Parity
  - `SEC_DED_OP`: Single Error Correction, Double Error Detection with Odd Parity

### Examples

Generate a 32-bit ECC module with Even Parity:
```bash
python main.py --input-size 32 --code-type SEC_DED_EP
```

Generate a 64-bit ECC module with Odd Parity:
```bash
python main.py --input-size 64 --code-type SEC_DED_OP
```

Generate an 8-bit ECC module with Even Parity:
```bash
python main.py --input-size 8 --code-type SEC_DED_EP
```

## Output

The tool generates two SystemVerilog files in the `out/` directory:

1. **Encoder Module** (`ECC_<size>b_<type>_encoder.sv`)
   - Takes data input and produces ECC bits
   - Input: `data[<size>-1:0]`
   - Output: `ecc[<ecc_bits>-1:0]`

2. **Decoder Module** (`ECC_<size>b_<type>_decoder.sv`)
   - Takes data and ECC bits, produces corrected data and error flags
   - Inputs: `data[<size>-1:0]`, `ecc[<ecc_bits>-1:0]`
   - Outputs: `data_out[<size>-1:0]`, `sec`, `ded`

### ECC Bit Calculation

The number of ECC bits is calculated as:
```
ECC bits = log2(data_width) + 2
```

For example:
- 8-bit data → 5 ECC bits
- 32-bit data → 7 ECC bits
- 64-bit data → 8 ECC bits

## Generated Module Interface

### Encoder Module
```systemverilog
module ECC_<size>b_SEC_DED_<parity>_encoder(
    input logic [<size>-1:0] data,
    output logic [<ecc_bits>-1:0] ecc
);
```

### Decoder Module
```systemverilog
module ECC_<size>b_SEC_DED_<parity>_decoder(
    input logic [<size>-1:0] data,
    input logic [<ecc_bits>-1:0] ecc,
    output logic [<size>-1:0] data_out,
    output logic sec,    // Single error corrected
    output logic ded     // Double error detected
);
```

## Error Detection and Correction

- **`sec` (Single Error Correction)**: High when a single bit error is detected and corrected
- **`ded` (Double Error Detection)**: High when two bit errors are detected (cannot be corrected)

### Error Scenarios

1. **No Errors**: `sec = 0`, `ded = 0`, `data_out = data`
2. **Single Bit Error**: `sec = 1`, `ded = 0`, `data_out = corrected_data`
3. **Double Bit Error**: `sec = 0`, `ded = 1`, `data_out = undefined`

## Technical Details

### Hamming Code Implementation

The tool implements a Hamming code with an additional parity bit:
- Uses powers of 2 positions for parity bits
- Calculates syndrome for error detection and correction
- Supports both even and odd parity configurations

### Code Generation Process

1. **Encoder Generation**:
   - Calculates required ECC bits
   - Generates parity equations for each ECC bit
   - Adds overall parity bit

2. **Decoder Generation**:
   - Reconstructs the original codeword vector
   - Calculates syndrome by comparing received and computed ECC
   - Implements error correction logic
   - Generates error detection flags

## File Structure

```
ECC-SV_Generator/
├── main.py              # Main generation script
├── README.md           # This file
├── .gitignore          # Git ignore file
└── out/                # Generated output directory (created automatically)
    ├── ECC_<size>b_<type>_encoder.sv
    └── ECC_<size>b_<type>_decoder.sv
```

## Limitations

- Maximum practical input size is limited by SystemVerilog synthesis tools
- Generated code uses combinational logic (no sequential elements)
- Error correction is limited to single bit errors
- Double bit errors are detected but not corrected
