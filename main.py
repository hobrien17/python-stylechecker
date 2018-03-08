import ast
from enum import Enum, auto

file = None      # TODO: This shouldn't be global


class NamingError(Enum):
    BAD = auto(),
    BAD_CLASS_NAME = auto(),
    BAD_TYPE_NAME = auto(),
    BAD_EX_NAME = auto(),
    BAD_FUNC_NAME = auto(),
    BAD_LOOP_VAR_NAME = auto(),
    BAD_LAMBDA_VAR_NAME = auto(),
    BAD_VAR_NAME = auto(),
    BAD_METHOD_NAME = auto(),
    BAD_INST_VAR_NAME = auto(),


def check_name(name):
    if name == 'l' or name == 'O' or name == 'I' or name == "_":
        return NamingError.BAD
    if not all(c.isalpha() or c.isdigit() or c == "_" for c in name):
        return NamingError.BAD


def check_name_len(name):
    if len(name) <= 1:
        return NamingError.BAD


def check_class_name(name):
    if name[0].islower() or not all(c != "_" for c in name) or check_name(name) or check_name_len(name):
        return NamingError.BAD_CLASS_NAME


def check_typevar_name(name):
    if name[0].islower() or (not name.endswith("_co") and not name.endswith("_contra") and
                                 not all(c != "_" for c in name)) or check_name(name) or check_name_len(name):
        return NamingError.BAD_TYPE_NAME


def check_ex_name(name):
    if not name.endswith("Error") or not name.endswith("Exception") or check_name(name) or check_name_len(name):
        return NamingError.BAD_EX_NAME


def check_loop_var_name(name):
    if name.isupper() or check_name(name) or not name[0].isalpha():
        return NamingError.BAD_LOOP_VAR_NAME


def check_lambda_var_name(name):
    if check_loop_var_name(name):
        return NamingError.BAD_LAMBDA_VAR_NAME


def check_var_name(name):
    if check_loop_var_name(name) or check_name_len(name):
        return NamingError.BAD_VAR_NAME


def check_func_name(name):
    if check_var_name(name):
        return NamingError.BAD_FUNC_NAME


def check_inst_var_name(name):
    if name.isupper() or check_name(name) or check_name_len(name) or (name.startswith("_") and len(name) <= 2):
        return NamingError.BAD_INST_VAR_NAME


def check_method_name(name):
    if check_inst_var_name(name):
        return NamingError.BAD_METHOD_NAME


class GenericVisitor(ast.NodeVisitor):

    def __init__(self):
        super().__init__()
        self._vars = []

    def visit_Assign(self, node):
        # TARGETS = VALUE
        line = file[node.lineno - 1]
        if line.split(" = ") == [line]:
            print("No spacing around '=' on line {}".format(node.lineno))
        elif line.split(" = ")[0].endswith(" ") or line.split(" = ")[1].startswith(" "):
            print("Too much spacing around '=' on line {}".format(node.lineno))
        for var in node.targets:
            if isinstance(var, ast.Name) and var.id not in self._vars:
                print(check_var_name(var.id))
                self._vars.append(var.id)
            elif isinstance(var, ast.Attribute) and var.attr not in self._vars:
                print(check_inst_var_name(var.attr))
                self._vars.append(var.attr)
        self.generic_visit(node)

    def _descend(self, node, vars, body="body"):
        temp = list(self._vars)
        self._vars = vars
        if isinstance(getattr(node, body), list):
            for item in getattr(node, body):
                if isinstance(item, ast.AST):
                    self.visit(item)
        elif isinstance(getattr(node, body), ast.AST):
            self.visit(getattr(node, body))
        self._vars = temp

    def check_tuple_args(self, node):
        for item in node.target.elts:
            print(check_loop_var_name(item.id))
            self._vars.extend(node.target.elts)
            self._descend(node, list(self._vars))
            self._vars = [x for x in self._vars if x not in node.target.elts]

    def visit_For(self, node):
        # for TARGET in ITER: BODY
        if isinstance(node.target, ast.Tuple):
            for item in node.target.elts:
                print(check_loop_var_name(item.id))
                self._vars.extend(node.target.elts)
                self._descend(node, list(self._vars))
                self._vars = [x for x in self._vars if x not in node.target.elts]   
        else:
            print(check_loop_var_name(node.target.id))
            self._vars.append(node.target.id)
            self._descend(node, list(self._vars))
            self._vars.pop(-1)

    def visit_Lambda(self, node):
        for arg in node.args.args:
            if arg.arg not in self._vars:
                print(check_lambda_var_name(arg.arg))

        self._descend(node, list(self._vars) + [i.arg for i in node.args.args])
        
    def visit_FunctionDef(self, node):
        # TODO: varargs & kwargs
        print(check_func_name(node.name))
        for arg in node.args.args:
            if arg.arg not in self._vars:
                print(check_loop_var_name(arg.arg))

        self._descend(node, [i.arg for i in node.args.args])

    def visit_comprehension(self, node):
        if isinstance(node.target, ast.Tuple):
            for item in node.target.elts:
                print(check_loop_var_name(item.id))
        else:
            print(check_loop_var_name(node.target.id))

    def visit_ClassDef(self, node):
        ClassVisitor().visit(node)


class ClassVisitor(GenericVisitor):

    def visit_ClassDef(self, node):
        # TODO: Exceptions and Types
        print(check_class_name(node.name))
        self._descend(node, [])

    def visit_FunctionDef(self, node):
        print(check_method_name(node.name))
        # TODO: check for self/cls
        for arg in node.args.args:
            if arg.arg not in self._vars:
                print(check_var_name(arg.arg))

        self._descend(node, [i.arg for i in node.args.args])


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
        visitor = GenericVisitor()
        visitor.visit(tree)

if __name__ == "__main__":
    main()