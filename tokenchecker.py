import tokenize
from io import BytesIO


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


def check_lines_2(iterator):
    indent = 0

    all_toks = []
    for tok in iterator:
        all_toks.append(tok)

    lines = split_list(all_toks, tokenize.NEWLINE)

    for lno, line in enumerate(lines):
        if len(line) == 0 or all([i.type in (tokenize.NL, tokenize.ENDMARKER) for i in line]):
            continue  # blank line

        if line[0].type in (tokenize.INDENT, tokenize.DEDENT):
            indent = line[1].start[1]

        if lno + 1 < len(lines) and len(lines[lno + 1]) > 0 and \
                lines[lno + 1][0].type in (tokenize.INDENT, tokenize.DEDENT):
            next_indent = lines[lno + 1][1].start[1]
        else:
            next_indent = indent

        subline = split_list(line, tokenize.NL)
        opens = []
        hanging = False

        for sno, tokens in enumerate(subline):
            for tno, token in enumerate(tokens):
                if token.type == tokenize.OP and token.string in ("(", "["):
                    opens.append(token.end[1])
                    if tno == len(tokens) - 1:
                        hanging = True
                elif token.type == tokenize.OP and token.string in (")", "]"):
                    if len(tokens) == 1:
                        if hanging and token.start[1] != indent and token.start[1] != next_indent + 4:
                            print("Bad indentation 3: Closing bracket misaligned")
                        elif token.start[1] != opens[-1]:
                            print("Bad indentation 4: Closing bracket misaligned")
                        opens.pop(-1)
                        break
                    opens.pop(-1)

                if sno != 0 and tno == 0:
                    if hanging:
                        if token.start[1] != next_indent + 4:
                            print("Bad indentation 1: Misalign for hanging indent")
                    else:
                        if len(opens) > 0 and token.start[1] != opens[-1]:
                            print("Bad indentation 2: Misalign with bracket")


def main():
    with open("test.py", "r") as f:
        content = f.read()
        tokens = tokenize.tokenize(BytesIO(content.encode('utf-8')).readline)
        next(tokens) # remove encoding token
        check_lines_2(tokens)

if __name__ == "__main__":
    main()