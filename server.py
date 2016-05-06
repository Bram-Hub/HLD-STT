# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from flask import Flask, Markup, render_template, request
import shorttruthtables

TRUE_STRING = "<span class='truth' style='color: green;' id='#'>T</span>"
FALSE_STRING = "<span class='truth' style='color: red;' id='#'>F</span>"
FLASK_APP = Flask(__name__)


@FLASK_APP.route("/")
def index_page():
    return render_template('index.html')


@FLASK_APP.route("/submit", methods=['POST'])
def generate_table():
    formulas = request.form.getlist('formula[]')
    goal = request.form['goal']
    i = 0
    while i < len(formulas):
        formulas[i] = str(formulas[i]).strip()
        if len(formulas[i]) == 0:
            del formulas[i]
            i -= 1
        i += 1
    form = Markup(render_template('form.html', formulas=formulas, goal=goal))

    try:
        table = shorttruthtables.runner(formulas, goal)
    except (SyntaxError, TypeError) as exception:
        return render_template('error.html', error=str(exception), form=form)

    pretty = []
    truthy = []
    for formula in table.formulas:
        pretty_formula = shorttruthtables.pretty_print(formula.formula)
        truth_values = formula.get_connective_values()
        truth_formula = u""
        idx = 0
        seen_string = False
        for i in range(len(pretty_formula)):
            if shorttruthtables.is_connective(pretty_formula[i]):
                if truth_values[idx][0] is True:
                    truth_formula += TRUE_STRING.replace("#", str(truth_values[idx][1]))
                elif truth_values[idx][0] is False:
                    truth_formula += FALSE_STRING.replace("#", str(truth_values[idx][1]))
                else:
                    truth_formula += "&nbsp;"
                seen_string = False
                idx += 1
            elif pretty_formula[i].isalnum() and not seen_string:
                if truth_values[idx][0] is True:
                    truth_formula += TRUE_STRING.replace("#", str(truth_values[idx][1]))
                elif truth_values[idx][0] is False:
                    truth_formula += FALSE_STRING.replace("#", str(truth_values[idx][1]))
                else:
                    truth_formula += "&nbsp;"
                seen_string = True
                idx += 1
            else:
                if pretty_formula[i] == " ":
                    seen_string = False
                truth_formula += "&nbsp;"
        pretty.append(pretty_formula)
        truthy.append(Markup(truth_formula))

    if table.contradiction:
        parent_formula = shorttruthtables.pretty_print(table.contradiction_parent.formula)
        contradiction_formula = shorttruthtables.pretty_print(table.contradiction_formula.formula)
        if not table.contradiction_formula.truth_value:
            formula_truth = "<span style='color: green;'>True</span>"
            actual_truth = "<span style='color: red;'>False</span>"
        else:
            formula_truth = "<span style='color: red;'>False</span>"
            actual_truth = "<span style='color: green;'>True</span>"
        formula_truth = Markup(formula_truth)
        actual_truth = Markup(actual_truth)
    else:
        parent_formula = None
        contradiction_formula = None
        formula_truth = ""
        actual_truth = ""

    symbols = []
    for symbol in table.unfulled_symbols:
        symbols.append(shorttruthtables.pretty_print(symbol.symbol))

    return render_template('table.html', form=form, contradiction=table.contradiction, step=table.count,
                           parent_formula=parent_formula, formula=contradiction_formula,
                           formula_truth=formula_truth, actual_truth=actual_truth, formulas=pretty, truths=truthy,
                           symbols=symbols)

if __name__ == '__main__':
    FLASK_APP.debug = True
    FLASK_APP.run()
