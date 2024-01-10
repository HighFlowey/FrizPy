from enum import Enum
from timeit import default_timer as timer
import argparse, regex

class Variable(Enum):
    String = 1
    Number = 2
    Function = 3

class Operation(Enum):
    EditVariable = 1
    CallFunction = 2

class BookItem():
    def __init__(self, type: Variable):
        self.type = type
    def __setitem__(self, key, value):
        setattr(self, key, value)
    def __getitem__(self, key):
        return getattr(self, key)

class ThreadItem():
    def __init__(self, type: Operation):
        self.type = type
    def __setitem__(self, key, value):
        setattr(self, key, value)
    def __getitem__(self, key):
        return getattr(self, key)

class Scope():
    __slots__ = ["start_character_index", "end_character_index", "nest", "tiedToVariable", "bookItems", "threadItems"]
    def __init__(self, start_character_index, nest=0):
        self.start_character_index = start_character_index
        self.bookItems: list[BookItem] = []
        self.threadItems: list[ThreadItem] = []
        self.tiedToVariable = False
        self.nest = nest

class Lexer():
    def __init__(self, content: str):
        self.content = content.replace("\n", "")
        self.character_index = -1
        self.character = ""
        self.word = ""

        self.scopes: list[Scope] = [
            Scope(0, 0)
            #      ^^^ main scope ^^^
        ]
        self.current_scope_nest = 0
        self.current_scope: Scope = self.scopes[0]
        self.scope_history = [self.current_scope]
        self.accepting_scope = None
    
    def next_character(self):
        self.character_index += 1
        self.character = self.content[self.character_index] if self.character_index < len(self.content) else None

    def accept_character(self):
        self.word = self.word + self.character if self.character else None

    def reset_word(self):
        self.word = ""

    def one_character_back(self):
        self.character_index -= 2
        self.next_character()

    def get_next_character(self):
        return self.content[self.character_index+1] if self.character_index+1 < len(self.content) else None

    def run_scope(self, scope: Scope):
        for threadItem in scope.threadItems:
            if threadItem.type == Operation.EditVariable:
                threadItem.bookItem.type = threadItem.newBookItem.type
                threadItem.bookItem.value = threadItem.newBookItem.value
            elif threadItem.type == Operation.CallFunction:
                self.run_scope(threadItem.scope)

    def find_variable(self, key):
        for scope in self.scopes:
            if scope.nest > self.current_scope.nest:
                continue
            elif scope.nest == self.current_scope.nest and scope != self.current_scope:
                continue
            for bookItem in scope.bookItems:
                if bookItem.type == None:
                    continue
                if bookItem.type not in Variable:
                    continue
                if bookItem.key == key:
                    return bookItem
    
    def parse_value(self, variable: Variable):
        value = ""
        type = None

        if variable != None:
            while self.character != "=":
                self.next_character()
            self.reset_word()

        while True:
            self.next_character()
            if self.character == "{":
                self.one_character_back()
                break
            elif self.character == ";":
                break
            self.accept_character()

        value = self.word.strip()
        self.reset_word()

        if value.startswith("\"") and value.endswith("\""):
            type = Variable.String
        elif value.startswith("("):
            type = Variable.Function
            match = regex.search(r"\((.*)\)\s*=>", value)
            args = regex.findall(r"(\w+)", match.group())
            for i, v in enumerate(args):
                # print(i, v)
                pass
            value = { "scope": "waiting" }
            self.accepting_scope = value
        elif value.isdigit():
            type = Variable.Number

        return value, type

    def book_variable(self, variable: Variable):
        key = ""
        value = ""
        type = None

        if variable == None:
            self.reset_word()
            self.next_character()

            assert self.character.isspace(), "! shouldve put an space after the keyword 'set'"

            while self.character != "=":
                self.next_character()
                if self.character != "=":
                    self.accept_character()
        
        key = self.word.strip()
        self.reset_word()
        value, type = self.parse_value(variable)

        if variable == None:
            bookItem = BookItem(type)
            bookItem.key = key
            bookItem.value = value

            for refScope in self.scopes:
                if refScope.nest > self.current_scope.nest:
                    continue
                elif refScope.nest == self.current_scope.nest and refScope != self.current_scope:
                    continue
                for refBookItem in refScope.bookItems:
                    if refBookItem.type == None:
                        continue
                    if refBookItem.type not in Variable:
                        continue
                    assert refBookItem.key != bookItem.key, "! shouldnt use the keyword 'set' on a variable that already exists"

            self.current_scope.bookItems.insert(len(self.current_scope.bookItems), bookItem)
        else:
            for refScope in self.scopes:
                if refScope.nest > self.current_scope.nest:
                    continue
                elif refScope.nest == self.current_scope.nest and refScope != self.current_scope:
                    continue
                for refBookItem in refScope.bookItems:
                    if refBookItem.type == None:
                        continue
                    if refBookItem.type not in Variable:
                        continue
                    if refBookItem.key == key:
                        threadItem = ThreadItem(Operation.EditVariable)
                        threadItem.bookItem = refBookItem
                        threadItem.newBookItem = BookItem(type)
                        threadItem.newBookItem.value = value
                        self.current_scope.threadItems.insert(-1, threadItem)
                        break

    def init_book(self):
        while self.character != None:
            variable = self.find_variable(self.word)

            if self.word == "~~":
                while self.character != ";":
                    self.next_character()
                    self.accept_character()
                self.reset_word()
            elif (self.get_next_character() == "(") and (variable.type is Variable.Function):
                threadItem = ThreadItem(Operation.CallFunction)
                threadItem.scope = variable.value["scope"]
                self.current_scope.threadItems.insert(-1, threadItem)
                while True:
                    self.next_character()
                    if self.character == ";":
                        self.reset_word()
                        break
            elif self.word == "set" or (variable != None and variable.key != "" and variable.type != Variable.Function):
                self.book_variable(variable)
            elif self.word == "{":
                self.current_scope_nest += 1
                self.scope_history.insert(len(self.scope_history), self.current_scope)
                self.current_scope = Scope(self.character_index, self.current_scope_nest)
                self.scopes.insert(len(self.scopes), self.current_scope)

                if self.accepting_scope is not None:
                    self.current_scope.tiedToVariable = True
                    self.accepting_scope["scope"] = self.current_scope
                    self.accepting_scope = None

                # print("+", self.current_scope.nest)

                self.reset_word()
                self.next_character()
                self.accept_character()
            elif self.word == "}":
                if self.current_scope.tiedToVariable is False:
                    self.run_scope(self.current_scope)

                self.current_scope_nest -= 1
                self.current_scope = self.scope_history[-1]
                self.scope_history.pop()

                # print("-", self.current_scope.nest)
                
                self.reset_word()
                self.next_character()
                self.accept_character()
            elif self.character.isspace():
                self.reset_word()
                self.next_character()
                self.accept_character()
            else:
                self.next_character()
                self.accept_character()

start_script = timer()
cli = argparse.ArgumentParser(
    prog="Friz",
    description="Friz is a toy language that's made with Python",
)

cli.add_argument("filepath", help="path to a file with the .friz extension")
args = cli.parse_args()

code = ""
with open(args.filepath, 'rt') as f:
    code = f.read()

parser = Lexer(code)
parser.init_book()
parser.run_scope(parser.scopes[0])
end_script = timer()

def print_scope(book: list[Scope]=parser.scopes):
    for scope in book:
        for bookItem in scope.bookItems:
            print("-------", bookItem.type, bookItem.key, bookItem.value)
        for threadItem in scope.threadItems:
            print("|______", threadItem.type)

print_scope()
print("time it took to compile and run code:", end_script - start_script)
