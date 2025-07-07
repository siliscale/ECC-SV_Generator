import argparse
import os
import logging
from math import log2
import shutil
import subprocess

def format_verilog_file(filename):
    # Check if verible-verilog-format is in path
    if not shutil.which("verible-verilog-format"):
        logging.error("verible-verilog-format not found in path")
        return False
    else:
        logging.info(f"verible-verilog-format found in path - Formatting {filename}")
        # Format the file
        process = subprocess.run(["verible-verilog-format", "--inplace", filename])
        # Print any errors
        if process.returncode != 0:
            logging.error(f"Error formatting {filename}: {process.stderr.decode('utf-8')}")

def generate_sec_ded_encoder(input_size, base_filename, parity):
    encoder_fd = open(f"{base_filename}_encoder.sv", "w")
    outbits = int(log2(int(input_size)) + 1 + 1)
    logging.info(f"Generating encoder unit for {input_size}b SEC-DED-EP code")
    encoder_fd.write(f"""module ECC_{input_size}b_SEC_DED_EP_encoder(
    input logic [{int(input_size)-1}:0] data,
    output logic [{outbits-1}:0] ecc
);
""")
        # Generate an array with all powers of 2 up to outbits
    powers = [2**i for i in range(outbits)]

        #Generate the codewords
    for i in range(len(powers)-1):
        line = f"assign ecc[{i}] = "
        first_elem = True
        for j in range(2**i+1, int(input_size) + outbits):
            tmp = (j >> i) & 1
            if tmp:
                if not first_elem:
                    line += " ^ "
                else:
                    first_elem = False   
                # Get the index of the first elemnt of which j is greater or equal to
                index = 0
                while j >= powers[index]:
                    index += 1
                line += f"data[{(j-1)-index}]"
        line += f";\n"
        encoder_fd.write(line)
    # Generate the parity bit
    encoder_fd.write(f"assign ecc[{outbits-1}] = {'~' if parity == 'OP' else ''}(^data[{int(input_size)-1}:0]^(^ecc[{outbits-2}:0]));\n")
    encoder_fd.write("endmodule\n")
    encoder_fd.close()

    # Format the encoder unit
    format_verilog_file(f"{base_filename}_encoder.sv")

def generate_sec_ded_decoder(input_size, base_filename, parity):
    decoder_fd = open(f"{base_filename}_decoder.sv", "w")
    outbits = int(log2(int(input_size)) + 1 + 1)
    decoder_fd.write(f"""module ECC_{input_size}b_SEC_DED_EP_decoder(
    input logic [{int(input_size)-1}:0] data,
    input logic [{outbits-1}:0] ecc,
    output logic [{int(input_size)-1}:0] data_out,
    output logic \t\t\t\tsec,
    output logic \t\t\t\tded
);
""")
    powers = [2**i for i in range(outbits)]
        # Construct the new vector that will allow us to build the syndrome
    decoder_fd.write(f"logic [{int(input_size)+outbits-2}:0] vec;\n")
    decoder_fd.write(f"logic [{int(input_size)+outbits-2}:0] vec_corrected;\n")
    vec = "assign vec = {"
    ecc_i = outbits-1
    for i in range(int(input_size) + outbits - 1, 0, -1):
        if i in powers:
            vec += f"ecc[{ecc_i}]"
            ecc_i -= 1
        else:
            index = 0
            while i >= powers[index]:
                index += 1
            vec += f"data[{i-1-index}]"
        if i > 1:
            vec += f","
    
    vec += "};\n"
    decoder_fd.write(vec)

    # Generate the codewords
    decoder_fd.write(f"logic [{int(outbits-1)}:0] ecc_check;")
    decoder_fd.write(f"logic [{int(outbits-1)}:0] syndrome;")
    decoder_fd.write(f"logic [{int(outbits-2)}:0] sec_i;")
    decoder_fd.write(f"logic \t\t\t\t\t ded_i;")
    for i in range(len(powers)-1):
        line = f"assign ecc_check[{i}] = "
        first_elem = True
        for j in range(2**i+1, int(args.input_size) + outbits):
            tmp = (j >> i) & 1
            if tmp:
                if not first_elem:
                    line += " ^ "
                else:
                    first_elem = False   
                # Get the index of the first elemnt of which j is greater or equal to
                index = 0
                while j >= powers[index]:
                    index += 1
                line += f"data[{(j-1)-index}]"
        line += f";\n"
        decoder_fd.write(line)
    # Generate the parity bit
    decoder_fd.write(f"assign ecc_check[{outbits-1}] = {'~' if parity == 'OP' else ''}(^data[{int(input_size)-1}:0]^(^ecc[{outbits-2}:0]));\n")

    # Generate the syndrome
    decoder_fd.write(f"assign syndrome = ecc_check ^ ecc;\n")
    decoder_fd.write(f"assign sec_i = syndrome[{outbits-2}:0];\n")
    decoder_fd.write(f"assign ded_i = syndrome[{outbits-1}];\n")
    decoder_fd.write(f"assign sec = |sec_i;\n")
    decoder_fd.write(f"assign ded = ~ded_i & sec;\n")

    
    decoder_fd.write(f"logic [{int(args.input_size)+outbits-2}:0] error_mask;\n")
    decoder_fd.write(f"for (genvar i = 1; i < {int(args.input_size)+outbits}; i++) begin\n")
    decoder_fd.write(f"    assign error_mask[i-1] = (sec_i[{outbits-2}:0] == i);\n")
    decoder_fd.write(f"end\n")

    decoder_fd.write(f"assign vec_corrected = vec ^ error_mask;\n")

    # Generate the new data out based on vec_corrected
    decoder_fd.write("assign data_out = {")
    powers.pop()
    for i in powers[::-1]:
        if powers.index(i) == len(powers)-1:
            decoder_fd.write(f"vec_corrected[{int(args.input_size)+outbits-(len(powers)-powers.index(i))-1} : {i}],")
        elif powers.index(i) == 1:
            decoder_fd.write(f"vec_corrected[2]")
        elif powers.index(i) != 0:
            decoder_fd.write(f"vec_corrected[{pow(2,powers.index(i)+1)-2}: {i}],")

    decoder_fd.write("};\n")
    decoder_fd.write("endmodule\n")
    decoder_fd.close()
    format_verilog_file(f"{base_filename}_decoder.sv") 

logging.basicConfig(level=logging.INFO)

code_types = ["SEC_DED_EP", "SEC_DED_OP"]

parser = argparse.ArgumentParser()
parser.add_argument("--input-size", type=str, required=True)
parser.add_argument("--code-type", choices=code_types, required=True)
args = parser.parse_args()

# If doesn't exist, create output directory output
if not os.path.exists("out"):
    os.makedirs("out")

base_filename = f"out/ECC_{args.input_size}b_{args.code_type}"

# Generate the encoder unit

if args.code_type == "SEC_DED_OP":
    generate_sec_ded_encoder(args.input_size, base_filename, "OP")
    generate_sec_ded_decoder(args.input_size, base_filename, "OP")
elif args.code_type == "SEC_DED_EP":
    generate_sec_ded_encoder(args.input_size, base_filename, "EP")
    generate_sec_ded_decoder(args.input_size, base_filename, "EP")




        


