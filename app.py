#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import gradio as gr
import numpy as np
import math
import datetime
import ast
import operator

# ---------- CSS ----------
css = """
#top-bar {
    background-color:#2A9D8F;
    padding:10px;
    text-align:center;
    color:white;
    font-size:24px;
    font-weight:bold;
}
#expression {
    border:1px solid #CCCCCC !important;
    width:100% !important;
}
button {
    margin:2px;
    font-size:16px;
    width:100%;
    height:50px;
}
.btn-number {
    background-color:#E0E0E0;
}
.btn-operator {
    background-color:#E76F51;
    color:white;
}
.btn-func {
    background-color:#264653;
    color:white;
}
.btn-equal {
    background-color:#2A9D8F;
    color:white;
}
.btn-copy {
    background-color:#E9C46A;
}
#history {
    background-color:#F4F4F4;
    padding:10px;
    overflow-y:auto;
    height:400px;
}
"""

# ---------- Safe evaluation ----------
_allowed_names = {
    k: getattr(math, k) for k in [
        "sin", "cos", "tan", "log", "sqrt", "pi", "e"
    ]
}
_allowed_names.update({
    "np": np,
    "abs": abs,
    "pow": pow
})

_allowed_nodes = {
    ast.Expression, ast.Call, ast.Name, ast.Load,
    ast.BinOp, ast.UnaryOp, ast.Num, ast.Constant,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow,
    ast.Mod, ast.USub, ast.UAdd, ast.FloorDiv,
    ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd,
    ast.And, ast.Or, ast.Not, ast.Compare,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.Tuple, ast.List
}

def _eval_node(node):
    if isinstance(node, ast.Num):  # pragma: no cover
        return node.n
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Unsupported constant")
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        op_type = type(node.op)
        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.Mod: operator.mod,
            ast.FloorDiv: operator.floordiv,
        }
        if op_type not in ops:
            raise ValueError("Unsupported binary operator")
        return ops[op_type](left, right)
    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        op_type = type(node.op)
        ops = {
            ast.UAdd: operator.pos,
            ast.USub: operator.neg,
        }
        if op_type not in ops:
            raise ValueError("Unsupported unary operator")
        return ops[op_type](operand)
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name):
            func_name = func.id
            if func_name not in _allowed_names:
                raise ValueError(f"Function '{func_name}' not allowed")
            fn = _allowed_names[func_name]
            args = [_eval_node(arg) for arg in node.args]
            return fn(*args)
        else:
            raise ValueError("Only direct function calls allowed")
    if isinstance(node, ast.Name):
        if node.id in _allowed_names:
            return _allowed_names[node.id]
        raise ValueError(f"Name '{node.id}' is not allowed")
    raise ValueError("Unsupported expression")

def safe_eval(expr: str):
    # Replace '^' with '**' for exponentiation
    expr = expr.replace("^", "**")
    tree = ast.parse(expr, mode='eval')
    for node in ast.walk(tree):
        if not isinstance(node, tuple(_allowed_nodes)):
            raise ValueError("Invalid expression")
    return _eval_node(tree.body)

# ---------- UI logic ----------
def append_char(char, expression):
    """Add a character or function token to the expression."""
    if char in ["sin", "cos", "tan", "log", "sqrt"]:
        return expression + char + "("
    else:
        return expression + char

def evaluate(expression, history):
    """Evaluate the expression, update result and history."""
    if not expression.strip():
        return "", history, ""
    try:
        result = safe_eval(expression)
        result_str = str(result)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {"expression": expression, "result": result_str, "timestamp": timestamp}
        # keep only last 10
        new_history = (history + [entry])[-10:]
        # build html for history panel
        html = "<ul>"
        for item in reversed(new_history):
            html += f"<li><b>{item['expression']}</b> = {item['result']} <br><i>{item['timestamp']}</i></li>"
        html += "</ul>"
        return result_str, new_history, html
    except ZeroDivisionError:
        return "Error: division by zero", history, ""
    except Exception as e:
        return f"Error: {str(e)}", history, ""

def clear_expression():
    return ""

# ---------- Gradio Interface ----------
with gr.Blocks(css=css) as demo:
    # Top bar
    gr.HTML("<div id='top-bar'>Simple Calculator</div>", elem_id="top-bar")
    with gr.Row():
        with gr.Column(scale=7):
            # Expression input
            expr = gr.Textbox(
                label="Expresión",
                placeholder="Escribe la expresión…",
                lines=1,
                elem_id="expression"
            )
            # Result display
            result = gr.Textbox(
                label="Resultado",
                interactive=False,
                elem_id="result"
            )
            # Error / message placeholder (empty string)
            message = gr.Markdown("", elem_id="message")
            # Buttons grid
            with gr.Row():
                # First row: 7 8 9 /
                btn_7 = gr.Button("7", elem_classes=["btn-number"])
                btn_8 = gr.Button("8", elem_classes=["btn-number"])
                btn_9 = gr.Button("9", elem_classes=["btn-number"])
                btn_div = gr.Button("/", elem_classes=["btn-operator"])
            with gr.Row():
                btn_4 = gr.Button("4", elem_classes=["btn-number"])
                btn_5 = gr.Button("5", elem_classes=["btn-number"])
                btn_6 = gr.Button("6", elem_classes=["btn-number"])
                btn_mul = gr.Button("*", elem_classes=["btn-operator"])
            with gr.Row():
                btn_1 = gr.Button("1", elem_classes=["btn-number"])
                btn_2 = gr.Button("2", elem_classes=["btn-number"])
                btn_3 = gr.Button("3", elem_classes=["btn-number"])
                btn_sub = gr.Button("-", elem_classes=["btn-operator"])
            with gr.Row():
                btn_0 = gr.Button("0", elem_classes=["btn-number"])
                btn_dot = gr.Button(".", elem_classes=["btn-number"])
                btn_pow = gr.Button("^", elem_classes=["btn-operator"])
                btn_add = gr.Button("+", elem_classes=["btn-operator"])
            with gr.Row():
                btn_sin = gr.Button("sin", elem_classes=["btn-func"])
                btn_cos = gr.Button("cos", elem_classes=["btn-func"])
                btn_tan = gr.Button("tan", elem_classes=["btn-func"])
                btn_log = gr.Button("log", elem_classes=["btn-func"])
            with gr.Row():
                btn_sqrt = gr.Button("sqrt", elem_classes=["btn-func"])
                btn_eq = gr.Button("=", elem_classes=["btn-equal"])
                btn_copy = gr.Button("Copiar", elem_classes=["btn-copy"])
                btn_clear = gr.Button("C", elem_classes=["btn-operator"])

            # History panel
        with gr.Column(scale=3):
            gr.HTML("<div id='history'><b>Historial</b></div>", elem_id="history")
            history_display = gr.HTML("", elem_id="history-content")

    # ---------- State ----------
    history_state = gr.State([])

    # ---------- Button callbacks ----------
    # Numbers and operators
    for btn in [
        btn_0, btn_1, btn_2, btn_3, btn_4, btn_5, btn_6, btn_7, btn_8, btn_9,
        btn_dot, btn_add, btn_sub, btn_mul, btn_div, btn_pow
    ]:
        btn.click(fn=append_char,
                  inputs=[btn, expr],
                  outputs=expr)

    # Functions
    for btn in [btn_sin, btn_cos, btn_tan, btn_log, btn_sqrt]:
        btn.click(fn=append_char,
                  inputs=[btn, expr],
                  outputs=expr)

    # Clear button
    btn_clear.click(fn=clear_expression, inputs=None, outputs=expr)

    # Evaluate button
    btn_eq.click(fn=evaluate,
                 inputs=[expr, history_state],
                 outputs=[result, history_state, history_display])

    # Copy button (JS only)
    btn_copy.click(
        fn=None,
        inputs=None,
        outputs=None,
        _js="""
function(){
    const res = document.getElementById('result');
    if(res){
        navigator.clipboard.writeText(res.value);
    }
}
"""
    )

demo.launch(css=css)