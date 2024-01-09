def _print(args: list[dict]):
    string = ""
    for var in args:
        value = var["value"]
        string += str(value) + "; "
    print(string)

functions_map = {
    "print": _print
}