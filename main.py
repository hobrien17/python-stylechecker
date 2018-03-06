import ast
import functools
import fnmatch
import optparse

file = None

def is_name_valid(name, loop=False):
    types = ["str", "string", "int", "float", "lst", "list", "dict", "tuple"]
    if len(name) == 1 and not loop:
        return False
    if name.split("_")[0] in types:
        return False
    if name.split("_")[-1] in types:
        return False
    for char in name:
        if char.isupper() and not name.isupper():
            return False
        if not char.isalpha() and not char.isdigit():
            return False
    return True


class Visitor(ast.NodeVisitor):

    def visit_arg(self, node):
        if not is_name_valid(node.arg):
            print("Bad function argument: {}".format(node.arg))
        self.generic_visit(node)

    def visit_Assign(self, node):
        line = file[node.lineno - 1]
        if line.split(" = ") == [line]:
            print("No spacing around '=' on line {}".format(node.lineno))
        elif line.split(" = ")[0].endswith(" ") or line.split(" = ")[1].startswith(" "):
            print("Too much spacing around '=' on line {}".format(node.lineno))
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    self._to_visit_assignment_name(item)
            else:
                self._to_visit_assignment_name(value)

    def _to_visit_assignment_name(self, item):
        if isinstance(item, ast.Name):
            self.visit_assignment_name(item)
        elif isinstance(item, ast.AST):
            self.visit(item)

    def visit_assignment_name(self, node):
        if not is_name_valid(node.id):
            print("Invalid variable name: " + node.id)
        self.visit(node)



class PrintVisitor(ast.NodeVisitor):

    def __init__(self):
        super().__init__()
        self._indent = -1
        self._for = False
        self._checked = []

    def print(self, string):
        print(self._indent * "    " + string)

    def visit(self, node):
        self._indent += 1
        if isinstance(node, ast.Name):
            print(self._indent * "    " + type(node).__name__ + " (" + node.id + ")")
        elif isinstance(node, ast.Num):
            print(self._indent * "    " + type(node).__name__ + " (" + str(node.n) + ")")
        elif isinstance(node, ast.Str):
            print(self._indent * "    " + type(node).__name__ + " ('" + node.s + "')")
        elif isinstance(node, ast.arg):
            self.print("{} ({})".format(type(node).__name__, node.arg))
        else:
            print(self._indent * "    " + type(node).__name__)

        super().visit(node)
        self._indent -= 1


def main():
    with open("test.py", "r") as f:
        content = f.read().replace("\t", "    ")
        global file
        file = content.split("\n")
        tree = ast.parse(content)
        visitor = Visitor()
        visitor.visit(tree)

if __name__ == "__main__":
    main()