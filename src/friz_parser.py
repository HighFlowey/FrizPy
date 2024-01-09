from global_functions import functions_map

identifiers_map = {
    "function": "~~&&TYpeFunction&&@@~~"
}

def remove_whitespace(string: str) -> str:
    ns=""
    for i in string:
        if(not i.isspace()):
            ns+=i
    return ns

def parse_value(variable_value: str) -> dict:
    type = ""
    if variable_value.startswith("\"") and variable_value.endswith("\""):
        variable_value = variable_value[1:-1]
        type = "string"
    elif variable_value.isdigit():
        variable_value = int(variable_value)
        type = "integer"
    elif variable_value.find(">") > 0:
        def variable_value():
            return identifiers_map["function"]
        type = "function"
    elif eval(variable_value):
        variable_value = eval(variable_value, {})
        type = "integer|float"
    return {
        "value": variable_value,
        "type": type,
    }

in_block = False
def parse_token(memory: list[dict], token: str) -> dict|None:
    comment = token.startswith("~~")
    set = token.startswith("set")
    equal = token.find("=")
    put_in = token.find("<")

    if comment > 0:
        pass
    elif put_in > 0:
        function_name = remove_whitespace(token[:put_in])
        function_args = remove_whitespace(token[put_in+2:]).split(",")
        i = 0

        for token in function_args:    
            tokenized = False

            i += 1

            for var in memory:
                if var["key"] == token:
                    tokenized = True
                    token = var["value"]
                    break
                
            if tokenized == False:
                tokenized = True
                token = parse_value(token)
            
            function_args[i-1] = token

        function = functions_map.get(function_name)
        if function:
            function(function_args)
    elif set > 0 and equal > 0:
        variable_key = remove_whitespace(token[set+2:equal])
        variable_value = parse_value(token[equal+2:].rstrip())

        if variable_value["type"] == "function":
            in_block = True

        var = {
            "key": variable_key,
            "value": variable_value,
        }
        
        return var
    
    return None