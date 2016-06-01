# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import argparse
import forseti.parser
from forseti.formula import Formula, Symbol, Predicate, Not, And, Or, If, Iff
from six import string_types


TRUTH_COUNT = 1


def is_atomic(formula):
    """
    Is the given formula "Atomic" (contains no connectives), so Symbol or Predicate
    :param formula:
    :return:
    """
    return isinstance(formula, Symbol) or isinstance(formula, Predicate)


def is_binary_operator(formula):
    """
    Is the given formula a binary logical connective (and, or, if, iff)?
    :param formula:
    :return:
    """
    return isinstance(formula, And) or isinstance(formula, Or) \
        or isinstance(formula, If) or isinstance(formula, Iff)


def is_operator(formula):
    """
    Is the given formula a logical operator (binary connectives or not)
    :param formula:
    :return:
    """
    return is_binary_operator(formula) or isinstance(formula, Not)


def runner(formulas, goal):
    if isinstance(formulas, string_types):
        formulas = [formulas]

    if not isinstance(goal, string_types):
        raise TypeError("Expected str for goal, got " + str(type(goal)))

    parsed_formulas = []
    for formula in formulas:
        formula = formula.strip()
        if len(formula) == 0:
            continue
        parsed_formulas.append(forseti.parser.parse(formula))

    goal = forseti.parser.parse(goal)
    return ShortTruthTable(parsed_formulas, goal)


def is_connective(char):
    """
    Is the given character a logical connective (one of the pretty printed ones)
    :param char:
    :return:
    """
    return char in [u"¬", u"∧", u"∨", u"→", u"↔"]


def pretty_print(formula):
    """

    :param formula:
    :return:
    """
    if isinstance(formula, Symbol) or isinstance(formula, Predicate):
        text = str(formula)
    elif isinstance(formula, Not):
        text = "¬" + pretty_print(formula.args[0])
    else:
        temp = []
        for arg in formula.args:
            temp.append(pretty_print(arg))
        if isinstance(formula, And):
            text = " ∧ ".join(temp)
        elif isinstance(formula, Or):
            text = " ∨ ".join(temp)
        elif isinstance(formula, If):
            text = " → ".join(temp)
        elif isinstance(formula, Iff):
            text = " ↔ ".join(temp)
        else:
            raise TypeError("Invalid Formula Type: " + str(type(formula)))
        text = "(" + text + ")"
    return text.strip()


class FormulaException(Exception):
    def __init__(self, formula):
        super(FormulaException, self).__init__("Already set truth value")
        self.formula = formula
        self.number = formula.number


class ShortTruthTableFormula(object):
    def __init__(self, formula, parent=None):
        """

        :param formula:
        :type formula: Formula
        :param parent:
        :type parent: ShortTruthTableFormula
        :param number:
        :type number: int
        """
        self.formula = formula
        self.parent = parent
        self.children = []
        """:type children: list[ShortTruthTableFormula]"""
        self.truth_value = None
        self.number = None

    def get_connective_values(self):
        """
        Returns a list of the truth values of all formulas in the Formula by traversing the tree to the left
        when possible and then up and right as necessary
        :return:
        """
        values = [[self.truth_value, self.number]]
        if len(self.children) == 1:
            values.extend(self.children[0].get_connective_values())
        elif len(self.children) == 2:
            child = self.children[0].get_connective_values()
            child.extend(values)
            child.extend(self.children[1].get_connective_values())
            values = child
        return values

    def set_truth_value(self, boolean, count):
        if self.truth_value is None:
            self.truth_value = boolean
            self.number = count
        else:
            raise FormulaException(self)


class ShortTruthTableSymbol(object):
    def __init__(self, symbol):
        """

        :param symbol:
        """
        assert(is_atomic(symbol))
        self.symbol = symbol
        self.formula = None
        self.truth_value = None
        self.number = None

    def set_truth_value(self, formula, count):
        if self.truth_value is None:
            self.formula = formula
            self.truth_value = formula.truth_value
            self.number = count
        else:
            raise FormulaException(formula)


class ShortTruthTable(object):
    def __init__(self, formulas, goal):
        """

        :param formulas:
        :type formulas: List[Formula]
        :param goal:
        :type goal: Formula
        """
        self.basic_formulas = formulas
        self.goal = goal
        self.count = 1
        self.formulas = []
        """:type : List[ShortTruthTableFormula]"""

        for formula in formulas:
            self.formulas.append(ShortTruthTableFormula(formula))
        self.formulas.append(ShortTruthTableFormula(Not(self.goal)))

        self.symbols = []
        """:type : List[ShortTruthTableSymbol]"""
        self.break_apart_formulas()

        self.contradiction = False
        self.contradiction_formula = None
        self.contradiction_parent = None

        try:
            for formula in self.formulas:
                self.set_truth_value(formula, True)

            self.evaluate_table()
        except FormulaException as e:
            self.contradiction = True
            self.contradiction_formula = e.formula
            formula = e.formula
            while formula.parent is not None:
                formula = formula.parent
            self.contradiction_parent = formula

        self.unfulled_symbols = []
        if not self.contradiction:
            for symbol in self.symbols:
                if symbol.truth_value is None:
                    self.unfulled_symbols.append(symbol)

    def break_apart_formulas(self):
        """

        :return:
        """
        for formula in self.formulas:
            broken_formula = [formula]
            while len(broken_formula) > 0:
                use_formula = broken_formula.pop(0)
                assert(isinstance(use_formula, ShortTruthTableFormula))
                if is_atomic(use_formula.formula):
                    not_in = True
                    for symbol in self.symbols:
                        if use_formula.formula == symbol.symbol:
                            not_in = False
                            break
                    if not_in:
                        self.symbols.append(ShortTruthTableSymbol(use_formula.formula))
                else:
                    for arg in use_formula.formula.args:
                        new_child = ShortTruthTableFormula(arg, use_formula)
                        use_formula.children.append(new_child)
                        broken_formula.append(new_child)

    def set_truth_value(self, formula, boolean):
        """

        :param formula:
        :type formula: ShortTruthTableFormula
        :param boolean:
        :type boolean: bool
        :return:
        """
        if formula.truth_value is boolean:
            # we've already dealt with this formula and we don't have a contradiction
            return False
        formula.set_truth_value(boolean, self.count)
        update_symbol = None
        if is_atomic(formula.formula):
            for symbol in self.symbols:
                if formula.formula == symbol.symbol:
                    # prevent running update_symbols in a recursive mess
                    if formula.truth_value == symbol.truth_value:
                        break
                    symbol.set_truth_value(formula, self.count)
                    update_symbol = symbol
                    break
        self.count += 1
        if update_symbol is not None:
            for formula in self.formulas:
                self.update_symbol(formula, update_symbol)

        if formula.parent is not None:
            self.update_parent(formula.parent, formula)

        return True

    def update_parent(self, formula, child):
        child_idx = -1
        for i in range(len(formula.children)):
            if formula.children[i] == child:
                child_idx = i
                break

        other_idx = 0 if child_idx == 1 else 1
        
        if isinstance(formula.formula, Not):
            self.set_truth_value(formula, not child.truth_value)
        elif isinstance(formula.formula, And):
            if child.truth_value is False:
                self.set_truth_value(formula, False)
            elif child.truth_value is True:
                if formula.children[other_idx].truth_value is True:
                    self.set_truth_value(formula, True)
                elif formula.children[other_idx].truth_value is False:
                    self.set_truth_value(formula, False)
        elif isinstance(formula.formula, Or):
            if child.truth_value is True:
                self.set_truth_value(formula, True)
            elif child.truth_value is False:
                if formula.children[other_idx].truth_value is True:
                    self.set_truth_value(formula, True)
                elif formula.children[other_idx].truth_value is False:
                    self.set_truth_value(formula, False)
        elif isinstance(formula.formula, If):
            if child_idx == 1:
                if child.truth_value is True:
                    self.set_truth_value(formula, True)
                elif child.truth_value is False and formula.children[0].truth_value is True:
                    self.set_truth_value(formula, False)
                elif child.truth_value is False and formula.children[0].truth_value is False:
                    self.set_truth_value(formula, True)
            else:
                if child.truth_value is False:
                    self.set_truth_value(formula, True)
                elif child.truth_value is True and formula.children[1].truth_value is False:
                    self.set_truth_value(formula, False)
                elif child.truth_value is True and formula.children[1].truth_value is True:
                    self.set_truth_value(formula, True)
        elif isinstance(formula.formula, Iff):
            if child.truth_value is not None and child.truth_value == formula.children[other_idx].truth_value:
                self.set_truth_value(formula, True)
            elif child.truth_value is not None and formula.children[other_idx] is not None \
                    and child.truth_value != formula.children[other_idx].truth_value:
                self.set_truth_value(formula, False)

    def update_symbol(self, formula, symbol):
        """

        :param formula:
        :type formula: ShortTruthTableFormula
        :param symbol:
        :type symbol: ShortTruthTableSymbol
        :return:
        """
        if formula.formula == symbol.symbol:
            self.set_truth_value(formula, symbol.truth_value)
        else:
            for child in formula.children:
                self.update_symbol(child, symbol)

    def evaluate_table(self):
        can_evaluate = True
        while can_evaluate:
            can_evaluate = False
            for formula in self.formulas:
                evaluate = self.evaluate_formula(formula)
                can_evaluate = evaluate or can_evaluate

    def evaluate_formula(self, formula):
        """

        :param formula:
        :type formula: ShortTruthTableFormula
        :return:
        """
        change = False

        if is_atomic(formula.formula):
            if formula.truth_value is None:
                for symbol in self.symbols:
                    if symbol == formula.formula:
                        if symbol.truth_value is not None:
                            self.set_truth_value(formula, symbol.truth_value)
                            change = True
                        break
            return change

        if formula.truth_value is None:
            if isinstance(formula.formula, Not):
                if formula.children[0].truth_value is not None:
                    self.set_truth_value(formula, not formula.children[0].truth_value)
                    change = True
            elif isinstance(formula.formula, And):
                if formula.children[0].truth_value is False or formula.children[1].truth_value is False:
                    self.set_truth_value(formula, False)
                    change = True
                elif formula.children[0].truth_value is True and formula.children[1].truth_value is True:
                    self.set_truth_value(formula, True)
                    change = True
            elif isinstance(formula.formula, Or):
                if formula.children[0].truth_value is True or formula.children[1].truth_value is True:
                    self.set_truth_value(formula, True)
                    change = True
                elif formula.children[0].truth_value is False and formula.children[1].truth_value is False:
                    self.set_truth_value(formula, False)
                    change = True
            elif isinstance(formula.formula, If):
                if formula.children[0].truth_value is True and formula.children[1].truth_value is False:
                    self.set_truth_value(formula, False)
                    change = True
                elif formula.children[0].truth_value is False or formula.children[1].truth_value is True:
                    self.set_truth_value(formula, True)
                    change = True
            elif isinstance(formula.formula, Iff):
                if (formula.children[0].truth_value is True and formula.children[1].truth_value is True) or \
                        (formula.children[0].truth_value is False and formula.children[1].truth_value is False):
                    self.set_truth_value(formula, True)
                    change = True
                elif formula.children[0].truth_value is not None and formula.children[1].truth_value is not None and \
                        formula.children[0].truth_value is not formula.children[1].truth_value:
                    self.set_truth_value(formula, False)
                    change = True

        not_done = True
        for child in formula.children:
            if child.truth_value is None:
                not_done = False
                break

        if not not_done and formula.truth_value is not None:
            if isinstance(formula.formula, Not):
                self.set_truth_value(formula.children[0], not formula.truth_value)
                change = True
            elif isinstance(formula.formula, And):
                if formula.truth_value is True:
                    self.set_truth_value(formula.children[0], True)
                    self.set_truth_value(formula.children[1], True)
                    change = True
                else:
                    if formula.children[0].truth_value is True:
                        self.set_truth_value(formula.children[1], False)
                        change = True
                    elif formula.children[1].truth_value is True:
                        self.set_truth_value(formula.children[0], False)
                        change = True
            elif isinstance(formula.formula, Or):
                if formula.truth_value is False:
                    self.set_truth_value(formula.children[0], False)
                    self.set_truth_value(formula.children[1], False)
                    change = True
                else:
                    if formula.children[0] is False:
                        self.set_truth_value(formula.children[1], True)
                        change = True
                    elif formula.children[1] is False:
                        self.set_truth_value(formula.children[0], True)
                        change = True
            elif isinstance(formula.formula, If):
                if formula.truth_value is False:
                    self.set_truth_value(formula.children[0], True)
                    self.set_truth_value(formula.children[1], False)
                    change = True
                else:
                    if formula.children[0].truth_value is True:
                        self.set_truth_value(formula.children[1], True)
                    elif formula.children[1].truth_value is False:
                        self.set_truth_value(formula.children[0], False)
            elif isinstance(formula.formula, Iff):
                if formula.truth_value is True:
                    if formula.children[0].truth_value is not None:
                        self.set_truth_value(formula.children[1], formula.children[0].truth_value)
                        change = True
                    elif formula.children[1].truth_value is not None:
                        self.set_truth_value(formula.children[0], formula.children[1].truth_value)
                        change = True
                elif formula.truth_value is False:
                    if formula.children[0].truth_value is not None:
                        self.set_truth_value(formula.children[1], not formula.children[0].truth_value)
                        change = True
                    elif formula.children[1].truth_value is not None:
                        self.set_truth_value(formula.children[0], not formula.children[1].truth_value)
                        change = True

        for child in formula.children:
            change_child = self.evaluate_formula(child)
            change = change_child or change

        return change


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description="Generate Truth Table for a logical formula")
    PARSER.add_argument('formulas', metavar='formula', type=str, nargs="*", help='Logical formula')
    PARSER.add_argument('goal', metavar='goal', type=str, help='Goal Formula')
    PARSER_ARGS = PARSER.parse_args()
    SHORT_TRUTH_TABLE = runner(PARSER_ARGS.formulas, PARSER_ARGS.goal)
    if SHORT_TRUTH_TABLE.contradiction:
        print("Contradiction trying to set " + str(SHORT_TRUTH_TABLE.contradiction_formula) + " as " +
              str(not SHORT_TRUTH_TABLE.contradiction_formula.truth_value) + " on step " +
              str(SHORT_TRUTH_TABLE.count))
    else:
        print("No contradiction found. Invalid argument.")