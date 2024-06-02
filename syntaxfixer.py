import ast
import autopep8
import subprocess
import sys
import tempfile
import os

class SyntaxFixer:
    def __init__(self):
        self.fixes = {
            'EOL while scanning string literal': self.fix_eol_string_literal,
            'invalid syntax': self.fix_invalid_syntax,
            'unmatched brackets': self.fix_unmatched_brackets,
        }

    def fix_eol_string_literal(self, code):
        return code.replace('"\n', '"\n').replace("'\n", "'\n")

    def fix_invalid_syntax(self, code):
        return autopep8.fix_code(code)

    def fix_unmatched_brackets(self, code):
        stack = []
        fixed_code = ""

        for char in code:
            if char in "({[":
                stack.append(char)
            elif char in ")}]":
                if stack and ((char == ")" and stack[-1] == "(") or
                              (char == "}" and stack[-1] == "{") or
                              (char == "]" and stack[-1] == "[")):
                    stack.pop()
                else:
                    continue
            fixed_code += char

        for char in reversed(stack):
            if char == "(":
                fixed_code += ")"
            elif char == "{":
                fixed_code += "}"
            elif char == "[":
                fixed_code += "]"

        return fixed_code

    def fix_code(self, code):
        try:
            ast.parse(code)
            return code, False
        except SyntaxError as e:
            error_message = e.msg
            for error, fix in self.fixes.items():
                if error in error_message:
                    return fix(code), True
        return code, False

    def lint_code(self, code):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.py') as temp_file:
            temp_file.write(code.encode())
            temp_filename = temp_file.name

        pylint_result = subprocess.run(['pylint', temp_filename], capture_output=True, text=True)
        os.remove(temp_filename)

        pylint_output = pylint_result.stdout
        issues = self.parse_pylint_output(pylint_output)
        return issues

    def parse_pylint_output(self, output):
        issues = []
        for line in output.split('\n'):
            if 'E:' in line or 'F:' in line:  # E for Errors, F for Fatal
                issues.append(line)
        return issues

def correct_syntax_errors(file_path):
    try:
        with open(file_path, 'r') as file:
            code = file.read()
    except IOError as e:
        print(f"Error reading file {file_path}: {e}")
        return

    syntax_fixer = SyntaxFixer()

    # Initial syntax fix
    fixed_code, fixed = syntax_fixer.fix_code(code)

    if fixed:
        try:
            with open(file_path, 'w') as file:
                file.write(fixed_code)
        except IOError as e:
            print(f"Error writing file {file_path}: {e}")
            return

    # Apply autopep8
    fixed_code = autopep8.fix_code(fixed_code)

    # Apply black
    try:
        with open(file_path, 'w') as file:
            file.write(fixed_code)
    except IOError as e:
        print(f"Error writing file {file_path}: {e}")
        return

    subprocess.run(['black', file_path])

    # Lint with pylint and display issues
    issues = syntax_fixer.lint_code(fixed_code)
    if issues:
        print("Pylint issues found:")
        for issue in issues:
            print(issue)
    else:
        print("No pylint issues found.")

    # Save final corrected code
    try:
        with open(file_path, 'w') as file:
            file.write(fixed_code)
    except IOError as e:
        print(f"Error writing file {file_path}: {e}")
    else:
        print(f"Syntax errors fixed and saved to {file_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python syntax_fixer.py <file_path>")
    else:
        correct_syntax_errors(sys.argv[1])
