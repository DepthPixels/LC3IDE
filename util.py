def parse_lines(file_lines):
  """
  Reads lines from a file and returns them as a list,
  stripping whitespace, and returning separated opcode and operands
  """
  
  parsed_data = []
  extra = []
  
  for line in file_lines:
    if line != "\n" and line != "\r\n" and not line.strip().startswith(';'):
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