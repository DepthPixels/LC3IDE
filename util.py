def parse_lines(file_lines):
  """
  Reads lines from a file and returns them as a list,
  stripping whitespace, and returning separated opcode and operands
  """
  
  parsed_data = []
  extra = []
  
  for line in file_lines:
    if line == "\n" or line == "\r\n" or line.strip().startswith(';'):
      parsed_data.append((None, None))
    else:
      parts = line.split(',')
      parts = [part.strip() for part in parts]
      
      found_comment = False
      new_parts = []
      for part in parts:
        if ';' in part:
          sub_part = part.split(';')[0].strip()
          new_parts.append(sub_part)
          found_comment = True
        if found_comment == False:
          new_parts.append(part)
      
      parts = new_parts
      opcode = parts[0]
      operands = parts[1:] if len(parts) > 1 else []
      
      split_code = opcode.split()
      opcode = split_code[0]
      if len(split_code) > 1:
        operands = split_code[1:] + operands
        
      #if len(operands) == 0:
        
      
      if len(operands) > 1:
        if operands[0] == ".STRINGZ" or operands[0] == ".STRINGZP":
          operands_new = operands[1:]
          operands_new = " ".join(operands_new)
          if operands_new.startswith('"') and operands_new.endswith('"'):
            string_content = operands_new[1:-1]
            string_content = string_content.encode('utf-8').decode('unicode_escape')
            if operands[0] == ".STRINGZ":
              for i in range(len(string_content)):
                char = string_content[i]
                ascii_value = ord(char)
                binary_value = format(ascii_value, '016b')
                if i == 0:
                  parsed_data.append((opcode, [".STRINGZ", ".FILL", f"{binary_value}"]))
                  print(f"Parsed Line: Opcode: {parsed_data[-1][0]}, Operands: {parsed_data[-1][1]}")
                else:
                  parsed_data.append((".FILL", [f"{binary_value}"]))
                  print(f"Parsed Line: Opcode: {parsed_data[-1][0]}, Operands: {parsed_data[-1][1]}")
                
              parsed_data.append((".FILL", ['0x0000']))
            elif operands[0] == ".STRINGZP":
              for i in range(0, len(string_content), 2):
                char = string_content[i]
                if len(string_content)-1 >= i+1:
                  char2 = string_content[i+1]
                else:
                  char2 = "\0"
                ascii_value = ord(char)
                ascii_value2 = ord(char2)
                binary_value = format(ascii_value2, '08b') + format(ascii_value, '08b')
                if i == 0:
                  parsed_data.append((opcode, [".STRINGZP", ".FILL", f"{binary_value}"]))
                  print(f"Parsed Line: Opcode: {parsed_data[-1][0]}, Operands: {parsed_data[-1][1]}")
                else:
                  parsed_data.append((".FILL", [f"{binary_value}"]))
                  print(f"Parsed Line: Opcode: {parsed_data[-1][0]}, Operands: {parsed_data[-1][1]}")
              parsed_data.append((".FILL", ['0x0000']))
          continue
      
      if opcode == ".STRINGZ" or opcode == ".STRINGZP":
        operands = " ".join(operands)
        if operands[0].startswith('"') and operands.endswith('"'):
          string_content = operands[1:-1]
          string_content = string_content.encode('utf-8').decode('unicode_escape')
          if opcode == ".STRINGZ":
            for i in range(len(string_content)):
              char = string_content[i]
              ascii_value = ord(char)
              binary_value = format(ascii_value, '016b')
              if i == 0:
                parsed_data.append((".STRINGZ", [".FILL", f"{binary_value}"]))
                print(f"Parsed Line: Opcode: {parsed_data[-1][0]}, Operands: {parsed_data[-1][1]}")
              else:
                parsed_data.append((".FILL", [f"{binary_value}"]))
                print(f"Parsed Line: Opcode: {parsed_data[-1][0]}, Operands: {parsed_data[-1][1]}")
              
            parsed_data.append((".FILL", ['0x0000']))
          elif opcode == ".STRINGZP":
            for i in range(0, len(string_content), 2):
              char = string_content[i]
              if len(string_content)-1 >= (i+1):
                char2 = string_content[(i+1)]
              else:
                char2 = "\0"
              ascii_value = ord(char)
              ascii_value2 = ord(char2)
              binary_value = format(ascii_value2, '08b') + format(ascii_value, '08b')
              if i == 0:
                parsed_data.append((".STRINGZP", [".FILL", f"{binary_value}"]))
                print(f"Parsed Line: Opcode: {parsed_data[-1][0]}, Operands: {parsed_data[-1][1]}")
              else:
                parsed_data.append((".FILL", [f"{binary_value}"]))
                print(f"Parsed Line: Opcode: {parsed_data[-1][0]}, Operands: {parsed_data[-1][1]}")
            parsed_data.append((".FILL", ['0x0000']))
        continue        
            
      parsed_data.append((opcode, operands))
      
      print(f"Parsed Line: Opcode: {opcode}, Operands: {operands}")
      
      
  return parsed_data



# From LC3Assembler
opcode_dict = {
    "ADD": "0001",
    "AND": "0101",
    "BR": "0000",
    "JMP": "1100",
    "JSR": "0100",
    "JSRR": "0100",
    "LD": "0010",
    "LDI": "1010",
    "LDR": "0110",
    "LEA": "1110",
    "NOT": "1001",
    "RET": "1100",
    "RTI": "1000",
    "ST": "0011",
    "STI": "1011",
    "STR": "0111",
    "TRAP": "1111",
}

traps_shorthands = {
    "GETC": "1111000000100000",
    "OUT": "1111000000100001",
    "PUTS": "1111000000100010",
    "IN": "1111000000100011",
    "PUTSP": "1111000000100100",
    "HALT": "1111000000100101"
}

directives = [".ORIG", ".FILL", ".STRINGZ", ".STRINGZP"]

# Parse Labels for the Overlay
def initial_parse(content, label_dict):
    parsed_lines = parse_lines(content)
    label_parse([opcode for opcode, _ in parsed_lines], [operands for _, operands in parsed_lines], label_dict)


def label_parse(opcodes, operands, label_dict):
    if len(opcodes) > 1:
        for i in range(len(opcodes)):
            didnt_find_opcode = True
            opcode = opcodes[i]
            operand_index = 0
            if opcode == None:
              continue
            while didnt_find_opcode:
                if opcode not in opcode_dict and opcode[:2] != "BR" and opcode not in traps_shorthands and opcode not in directives and opcode != ".END":
                    label_dict[opcode] = i+1
                    if len(operands[i]) > operand_index+1:
                        opcode = operands[i][operand_index]
                        operand_index += 1
                    else:
                        break
                else:
                    didnt_find_opcode = False