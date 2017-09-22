from mycroft import MycroftSkill


class MathSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.register_intent('math', self.handle_math)
        self.register_entity('{num}')
        self.register_entity('{equation}')

        import ast
        import operator as op

        # supported operators
        operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
                     ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
                     ast.USub: op.neg}

        def eval_expr(expr):
            """
            >>> eval_expr('2^6')
            4
            >>> eval_expr('2**6')
            64
            >>> eval_expr('1 + 2*3**(4^5) / (6 + -7)')
            -5.0
            """
            return eval_(ast.parse(expr, mode='eval').body)

        def eval_(node):
            if isinstance(node, ast.Num):  # <number>
                return node.n
            elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
                return operators[type(node.op)](eval_(node.left), eval_(node.right))
            elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
                return operators[type(node.op)](eval_(node.operand))
            else:
                raise TypeError(node)

    def handle_math(self, data):
        equation = data.matches.get('equation', data.query)
        answer, conf = self.parser.to_number(equation)
        self.add_result('equation', equation)
        self.add_result('answer', answer)
        return conf
