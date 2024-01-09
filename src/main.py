import sys
import friz_parser

# turn every line of the code into a seperate string
tokens = [] # type: list[str]
with open(sys.argv[1], 'rt') as f:
    code = ""
    code = f.read()
    tokens.extend(code.strip().split("\n"))

# read tokens and run them
memory = []
for token in tokens:
    var = friz_parser.parse_token(memory, token)
    if var:
        memory.insert(len(memory), var)
