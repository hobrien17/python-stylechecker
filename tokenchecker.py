import tokenize
from io import BytesIO
import re

def split_list(lst, delimiter):
    result = []
    to_add = []
    for elem in lst:
        if elem.type == delimiter:
            result.append(list(to_add))
            to_add = []
        else:
            to_add.append(elem)
    result.append(list(to_add))
    return result


class LineChecker:

    def __init__(self, tokens):
        self._indent = 0
        self._next_indent = 0
        self._top = (True, True, True)
        self._iterator = tokens

    def run(self):
        all_toks = []
        for tok in self._iterator:
            all_toks.append(tok)

        lines = split_list(all_toks, tokenize.NEWLINE)

        for lno, line in enumerate(lines):
            if len(line) == 0 or all([i.type in (tokenize.NL, tokenize.ENDMARKER) for i in line]):
                continue  # blank line

            if line[0].type in (tokenize.INDENT, tokenize.DEDENT):
                self._indent = line[1].start[1]

            if lno + 1 < len(lines) and len(lines[lno + 1]) > 0 and \
                            lines[lno + 1][0].type in (tokenize.INDENT, tokenize.DEDENT):
                self._next_indent = lines[lno + 1][1].start[1]
            else:
                self._next_indent = self._indent

            subline = split_list(line, tokenize.NL)
            self.check_line(subline)

    def check_import(self, tokens):
        if re.match(r'import (.+), (.+)', tokens[0].line):
            print("Imports should be on separate lines")
        elif re.match(r'from __future__ import (.+)', tokens[0].line):
            if not all(self._top):
                print("Future import should be at very top of file")
        elif re.match(r'(__all__)|(__author__)|(__version__)(.+)', tokens[0].line):
            if not all(self._top[1:]):
                print("Module level dunders should be at top of file, before non-future imports")
            self._top = (False, True, True)
        elif re.match(r'import (.+)', tokens[0].line) or re.match(r'from (.+) import (.+)', tokens[0].line):
            if not self._top[2]:
                print("Imports should be at the top of the file, after future imports and module level dunders")
            self._top = (False, False, True)
        else:
            self._top = (False, False, False)

    def check_line(self, subline):
        opens = []
        hanging = False

        for sno, tokens in enumerate(subline):
            if len(tokens) == 0 or all([i.type in (tokenize.INDENT, tokenize.DEDENT, tokenize.STRING,
                                                   tokenize.COMMENT) for i in tokens]):
                continue  # blank line or comment
            self.check_import(tokens)

            for tno, token in enumerate(tokens):
                if token.type == tokenize.OP and token.string in ("(", "["):
                    opens.append(token.end[1])
                    if tno == len(tokens) - 1:
                        hanging = True
                elif token.type == tokenize.OP and token.string in (")", "]"):
                    if len(tokens) == 1:
                        if hanging and token.start[1] != self._indent and token.start[1] != self._next_indent + 4:
                            print("Bad indentation 3: Closing bracket misaligned")
                        elif token.start[1] != opens[-1]:
                            print("Bad indentation 4: Closing bracket misaligned")
                        opens.pop(-1)
                        break
                    opens.pop(-1)

                if sno != 0 and tno == 0:
                    if hanging:
                        if token.start[1] != self._next_indent + 4:
                            print("Bad indentation 1: Misalign for hanging indent")
                    else:
                        if len(opens) > 0 and token.start[1] != opens[-1]:
                            print("Bad indentation 2: Misalign with bracket")


def main():
    with open("test.py", "r") as f:
        content = f.read()
        tokens = tokenize.tokenize(BytesIO(content.encode('utf-8')).readline)
        next(tokens) # remove encoding token
        checker = LineChecker(tokens)
        checker.run()

if __name__ == "__main__":
    main()