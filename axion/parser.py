class parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    
    def current(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else ('None', 'None')
    
    def match(self, expected):
        token, token_type = self.current()
        if token == expected or token_type == expected:
            self.pos += 1
            return token
        raise SyntaxError(f"Expected {expected}, got {token}")
    
    def parse_expression(self):
        return self.parse_assignment()

    def parse_assignment(self):
        expr = self.parse_logical()
        if self.current()[0] in ["=", "+=", "-=", "*=", "/=", "%="]:
            op = self.match(self.current()[0])
            value = self.parse_expression()
            return {
                "type": "Assignment",
                "target": expr,
                "op": op,
                "value": value
            }
        return expr

    def parse_logical(self):
        expr = self.parse_equality()
        while self.current()[0] in ["both", "any"]:
            op = self.match(self.current()[0])
            right = self.parse_equality()
            expr = {"type": "BinaryOp", "op": op, "left": expr, "right": right}
        return expr

    def parse_equality(self):
        expr = self.parse_comparison()
        while self.current()[0] in ["==", "!="]:
            op = self.match(self.current()[0])
            right = self.parse_comparison()
            expr = {"type": "BinaryOp", "op": op, "left": expr, "right": right}
        return expr

    def parse_comparison(self):
        expr = self.parse_bitwise()
        while self.current()[0] in ["<", "<=", ">", ">="]:
            op = self.match(self.current()[0])
            right = self.parse_additive()
            expr = {"type": "BinaryOp", "op": op, "left": expr, "right": right}
        return expr
    def parse_shift(self):
        expr = self.parse_multiplicative()
        while self.current()[0] in ["<<", ">>"]:
            op = self.match(self.current()[0])
            right = self.parse_multiplicative()
            expr = {"type": "BinaryOp", "op": op, "left": expr, "right": right}
        return expr

    def parse_bitwise(self):
        expr = self.parse_additive()
        while self.current()[0] in ["&", "|", "^","<<",">>"]:
            op = self.match(self.current()[0])
            right = self.parse_additive()
            expr = {"type": "BinaryOp", "op": op, "left": expr, "right": right}
        return expr


    def parse_additive(self):
        expr = self.parse_shift()
        while self.current()[0] in ["+", "-"]:
            op = self.match(self.current()[0])
            right = self.parse_multiplicative()
            expr = {"type": "BinaryOp", "op": op, "left": expr, "right": right}
        return expr

    def parse_multiplicative(self):
        expr = self.parse_unary()
        while self.current()[0] in ["*", "/", "%"]:
            op = self.match(self.current()[0])
            right = self.parse_unary()
            expr = {"type": "BinaryOp", "op": op, "left": expr, "right": right}
        return expr

    def parse_unary(self):
        if self.current()[0] in ["invert", "~","-"]:
            op = self.match(self.current()[0])
            right = self.parse_unary()
            return {"type": "UnaryOp", "op": op, "expr": right}
        return self.parse_primary()

    def parse_primary(self):
        token, token_type = self.current()

        if token_type == "NUMBER":
            self.match("NUMBER")
            return {"type": "NUMBER", "value": token}

        elif token_type == "STRING":
            self.match("STRING")
            return {"type": "STRING", "value": token.strip('"').strip("'")}

        elif token_type == "IDENTIFIER":
            node = {"type": "IDENTIFIER", "value": self.match("IDENTIFIER")}

            while self.current()[0] in ["[", ".", "("]:
                if self.current()[0] == "[":
                    self.match("[")
                    index_expr = self.parse_expression()
                    self.match("]")
                    node = {"type": "Index", "target": node, "index": index_expr}

                elif self.current()[0] == ".":
                    self.match(".")
                    prop = self.match("IDENTIFIER")
                    node = {"type": "MemberAccess", "object": node, "property": prop}

                elif self.current()[0] == "(":
                    self.match("(")
                    args = self.parse_elements() if self.current()[0] != ")" else []
                    self.match(")")
                    node = {"type": "Call", "callee": node, "args": args}

            return node


        elif token == "(":
            self.match("(")
            expr = self.parse_expression()
            self.match(")")
            return expr

        elif token == "[":
            return self.parse_array()

        else:
            raise SyntaxError(f"Unexpected token in expression: {self.current()}")

    def parse_array(self):
        self.match("[")
        elements = self.parse_elements() if self.current()[0] != "]" else []
        self.match("]")
        return {"type": "ArrayLiteral", "elements": elements}

    def parse_elements(self):
        elements = [self.parse_expression()]
        while self.current()[0] == ",":
            self.match(",")
            elements.append(self.parse_expression())
        return elements
    def parse_include(self):
        self.match("include")
        path_token = self.match("STRING")
        self.match(";")
        return {
            "type":"Include",
            "path": path_token.strip('"')
        }

    def parse_io(self):
        if self.current()[0] == "log":
            self.match("log")
            self.match("(")
            expr = self.parse_expression()
            self.match(")")
            self.match(";")
            return {
                "type": "IO",
                "action": "log",
                "expr": expr
            }
        elif    self.current()[0] == "logln":
                self.match("logln")
                self.match("(")
                expr = self.parse_expression()
                self.match(")")
                self.match(";")
                return {
                    "type": "IO",
                    "action": "logln",
                    "expr": expr
                }

        elif self.current()[0] == "input":
            self.match("input")
            self.match("(")
            target = self.parse_expression()
            message = ""
            if self.current()[0] == ",":
                self.match(",")
                tok = self.match("STRING")
                if (tok.startswith('"') and tok.endswith('"')) or (tok.startswith("'") and tok.endswith("'")):
                    msg_val = tok[1:-1]
                else:
                    msg_val = tok
                message = {"type": "STRING", "value": msg_val}
            self.match(")")
            self.match(";")
            return {
                "type": "IO",
                "action": "input",
                "target": target,
                "message": message
            }


        else:
            raise SyntaxError(f"Unexpected I/O statement at {self.current()}")


    def parse_return(self):
        self.match("return")
        expr = self.parse_expression()
        self.match(";")
        return {
            "type": "ReturnStatement",
            "expr": expr
        }
    def parse_break(self):
        self.match("break")
        self.match(";")
        return{
            "type": "BreakStatement",
        }
    def parse_skip(self):
        self.match("skip")
        self.match(";")
        return{
            "type": "SkipStatement",
        }

    def parse_match(self):
        self.match("match")
        self.match("(")
        expr = self.parse_expression()
        self.match(")")
        self.match("{")

        cases = []
        else_case = None

        while self.current()[0] not in ["}"]:
            if self.current()[0] == "else":
                else_case = self.parse_case(is_else=True)
            else:
                cases.append(self.parse_case())

        self.match("}")

        return {
            "type": "MatchStatement",
            "expr": expr,
            "cases": cases,
            "else": else_case
        }

    def parse_case(self, is_else=False):
        if is_else:
            self.match("else")
            self.match("->")
            stmt = self.parse_statement()
            return {"type": "ElseCase", "body": stmt}
        else:
            value = self.parse_expression()
            self.match("->")
            stmt = self.parse_statement()
            return {"type": "Case", "value": value, "body": stmt}

    def parse_loop(self):
        self.match("loop")
        self.match("(")
        varname = self.match("IDENTIFIER")
        self.match("from")
        start = self.parse_expression()
        self.match("to")
        end = self.parse_expression()
        self.match("step")
        step = self.parse_expression()
        self.match(")")
        body = self.parse_block()
        return {
            "type": "ForLoop",
            "var": varname,
            "start": start,
            "end": end,
            "step": step,
            "body": body
        }

    def parse_while(self):
        self.match("while")
        self.match("(")
        condition = self.parse_expression()
        self.match(")")
        body = self.parse_block()
        return {
            "type": "WhileLoop",
            "condition": condition,
            "body": body
        }

    def parse_do_while(self):
        self.match("repeat")
        body = self.parse_block()
        self.match("while")
        self.match("(")
        condition = self.parse_expression()
        self.match(")")
        self.match(";")
        return {
            "type": "DoWhileLoop",
            "condition": condition,
            "body": body
        }


    def parse_if(self):
        self.match("if")
        self.match("(")
        condition = self.parse_expression()
        self.match(")")
        self.match("then")

        if self.current()[0] == "{":
            body = self.parse_block()
        else:
            body = [self.parse_statement()]

        elseifs = []
        while self.current()[0] == "else" and self.tokens[self.pos+1][0] == "if":
            self.match("else")
            self.match("if")
            self.match("(")
            cond = self.parse_expression()
            self.match(")")
            self.match("then")
            blk = self.parse_block() if self.current()[0] == "{" else [self.parse_statement()]
            elseifs.append({"condition": cond, "body": blk})

        else_block = None
        if self.current()[0] == "else":
            self.match("else")
            else_block = self.parse_block() if self.current()[0] == "{" else [self.parse_statement()]

        return {
            "type": "IfStatement",
            "condition": condition,
            "body": body,
            "elseifs": elseifs,
            "else": else_block
        }

    
    def parse_func_decl(self):
        self.match("func")
        name = self.match("IDENTIFIER")
        self.match("(")
        params = self.parse_params()
        self.match(")")
        body = self.parse_block()
        return {
            "type": "FuncDecl",
            "name": name,
            "params": params,
            "body": body
        }

    def parse_params(self):
        params = []
        token, token_type = self.current()
        if token_type == "IDENTIFIER":
            params.append(self.match("IDENTIFIER"))
            while self.current()[0] == ",":
                self.match(",")
                params.append(self.match("IDENTIFIER"))
        return params

    def parse_block(self):
        self.match("{")
        statements = []
        while self.current()[0] != "}":
            statements.append(self.parse_statement())
        self.match("}")
        return statements


    def parse_var_decl(self):
        self.match("set")
        name = self.match("IDENTIFIER")
        value = None
        if self.current()[0] == "=": 
            self.match("=")
            value = self.parse_expression()
        self.match(";")
        return {
            "type": "VarDecl",
            "name": name,
            "value": value
        }

    def parse_const_decl(self):
        self.match("const")
        name = self.match("IDENTIFIER")
        value = None
        if self.current()[0] == "=": 
            self.match("=")
            value = self.parse_expression()
        self.match(";")
        return {
            "type": "ConstDecl",
            "name": name,
            "value": value
        }

    def parse_statement(self):
        token, token_type = self.current()
        if token == "set":
            return self.parse_var_decl()
        elif token == "const":
            return self.parse_const_decl()
        elif token == "func":
            return self.parse_func_decl()
        elif token == "if":
            return self.parse_if()
        elif token == "loop":
            return self.parse_loop()
        elif token == "while":
            return self.parse_while()
        elif token == "repeat":
            return self.parse_do_while()
        elif token == "match":
            return self.parse_match()
        elif token == "return":
            return self.parse_return()
        elif token in ("log", "input","logln"):
            return self.parse_io()
        elif token == "break":
            return self.parse_break()
        elif token == "skip":
            return self.parse_skip()
        elif token == "include":
            return self.parse_include()
        else:
            expr = self.parse_expression()
            self.match(";")
            return {"type": "ExpressionStatement", "expr": expr}
    
    def parse_program(self):
        statements = []
        while self.pos < len(self.tokens):
            statements.append(self.parse_statement())
        return {
            "type": "Program",
            "body": statements
        }
        
