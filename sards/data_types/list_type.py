from .number_type import Number
from .string_type import String
from sards.core.error import RunTimeError, IllegalOperationError

class ListNode:
    def __init__(self, element_nodes, pos_start, pos_end):
        self.element_nodes = element_nodes
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f'[{", ".join([str(x) for x in self.element_nodes])}]'


class List:
    def __init__(self, elements):
        self.elements = elements
        self.set_pos()
        self.set_context()

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def add(self, operand):
        if isinstance(operand, Number) or isinstance(operand, String):
            new_list = self.copy()
            new_list.elements.append(operand)
            return new_list, None

        elif isinstance(operand, List):
            new_list = self.copy()
            for i in operand.elements:
                new_list.elements.append(i)
            return new_list, None

    def subtract(self, operand):
        if isinstance(operand, Number):
            new_list = self.copy()
            try:
                new_list.elements.pop(operand.value)
                return new_list, None
            except:
                return None, RunTimeError(operand.pos_start, operand.pos_end,
                                          'Index out of bounds', self.context)
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Index must be of Number type')

    def multiply(self, operand):
        if isinstance(operand, Number):
            if operand.value < 0:
                return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'List repetition cannot be negative')
            temp_list=list(self.elements)

            for i in range(operand.value-1):
                for ele in temp_list:
                    self.elements.append(ele)
            return self, None
        else:
            return None, IllegalOperationError(
                operand.pos_start, operand.pos_end, 'Expected a Number type')

    def divide(self, operand):
        new_list = self.copy()
        for i, el in enumerate(new_list.elements):
            if isinstance(operand,List) and isinstance(el,List):
                if el.get_comparison_eq(operand):
                    del new_list.elements[i]
                    break
            elif not isinstance(el,List) and not isinstance(operand,List) and el.value == operand.value:
                del new_list.elements[i]
                break
        return new_list, None

    def modulus(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'%\' to a List')

    def floor_divide(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'//\' to a List')

    def exponent(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'**\' to a List')

    def get_comparison_eq(self, operand):
        if isinstance(operand, List):
            new_list = self.copy()
            if len(new_list.elements)==len(operand.elements):
                return Number(int(all(a.value==b.value for a, b in zip(new_list.elements, operand.elements)))).set_context(self.context), None
            else:
                return Number(0).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a List')

    def get_comparison_neq(self, operand):
        if isinstance(operand, List):
            new_list = self.copy()
            return Number(int(not(new_list.get_comparison_eq(operand)[0].value))).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a List')

    def get_comparison_lte(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'<=\' to a List')

    def get_comparison_lt(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'<\' to a List')

    def get_comparison_gte(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'>=\' to a List')

    def get_comparison_gt(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'>\' to a List')

    def and_by(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'and\' to a List')

    def or_by(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'or\' to a List')

    def not_by(self):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'not\' to a List')
        
    def getByIndex(self, indexes):
        temp = self.copy()
        try:
            for idx in indexes:
                if isinstance(idx, Number):
                    if isinstance(temp, List):
                        temp = temp.elements[idx.value]
                    elif isinstance(temp, String):
                        temp = String(temp.value[idx.value]).set_context(self.context)
                    else:
                        return None, RunTimeError(
                            idx.pos_start, idx.pos_end,
                            "Can't index a data type which is not iterable",
                            self.context
                        )
                else:
                    return None, RunTimeError(
                        idx.pos_start, idx.pos_end,
                        "Invalid Index Type",
                        self.context
                    )

            return temp, None

        except IndexError:
            bad_idx = indexes[-1]
            return None, RunTimeError(
                bad_idx.pos_start, bad_idx.pos_end,
                "Index out of bounds",
                self.context
            )

    def assignIndex(self, indexes, val):
        new_list = self.copy()
        temp = new_list
        try:
            for idx in indexes[:-1]:
                if isinstance(idx, Number):
                    if isinstance(temp, List):
                        temp = temp.elements[idx.value]
                    elif isinstance(temp, String):
                        return None, RunTimeError(
                            idx.pos_start, idx.pos_end,
                            "Can't assign inside string beyond one level",
                            self.context
                        )
                    else:
                        return None, RunTimeError(
                            idx.pos_start, idx.pos_end,
                            "Can't index a data type which is not iterable",
                            self.context
                        )
                else:
                    return None, RunTimeError(
                        idx.pos_start, idx.pos_end,
                        "Invalid Index Type",
                        self.context
                    )

            last_idx = indexes[-1]
            if not isinstance(last_idx, Number):
                return None, RunTimeError(
                    last_idx.pos_start, last_idx.pos_end,
                    "Invalid Index Type",
                    self.context
                )

            # Case 1: assigning inside a List
            if isinstance(temp, List):
                temp.elements[last_idx.value] = val
                return new_list, None

            # Case 2: assigning inside a String
            elif isinstance(temp, String):
                if not isinstance(val, String) or len(val.value) != 1:
                    return None, RunTimeError(
                        getattr(val, "pos_start", None),
                        getattr(val, "pos_end", None),
                        "Assigned value must be a single character string",
                        self.context
                    )
                s = list(temp.value)
                try:
                    s[last_idx.value] = val.value
                    replaced = String("".join(s)).set_context(self.context)

                    # Instead of indexing into String, go back to the parent List
                    parent = new_list
                    for idx in indexes[:-2]:
                        parent = parent.elements[idx.value]

                    parent.elements[indexes[-2].value] = replaced
                    return new_list, None

                except IndexError:
                    return None, RunTimeError(
                        last_idx.pos_start, last_idx.pos_end,
                        "Index out of bounds",
                        self.context
                    )

            else:
                return None, RunTimeError(
                    last_idx.pos_start, last_idx.pos_end,
                    "Can't index a data type which is not iterable",
                    self.context
                )

        except IndexError:
            bad_idx = indexes[-1]
            return None, RunTimeError(
                bad_idx.pos_start, bad_idx.pos_end,
                "Index out of bounds",
                self.context
            )

    def is_true(self):
        return Number(len(self.elements)).set_context(self.context), None

    def __repr__(self):
        return f'[{", ".join([str(x) for x in self.elements])}]'

    def copy(self):
        copy = List(self.elements)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy