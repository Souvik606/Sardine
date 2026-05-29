from .number_type import Number
from .string_type import String
from sards.core.error import RunTimeError, IllegalOperationError, DictKeyError, IndexOutOfBoundsError

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
        from .dict_type import Dict #Avoiding Circular Import
        if isinstance(operand, Number) or isinstance(operand, String) or isinstance(operand, Dict):
            new_list = self.copy()
            new_list.elements.append(operand)
            return new_list, None

        elif isinstance(operand, List):
            new_list = self.copy()
            for i in operand.elements:
                new_list.elements.append(i)
            return new_list, None
        else:
            return None, IllegalOperationError(
                operand.pos_start, operand.pos_end,
                f"Cannot add '{type(operand).__name__}' to a List",
                self.context
            )

    def subtract(self, operand):
        if isinstance(operand, Number) and not isinstance(operand.value, float):
            new_list = self.copy()
            try:
                new_list.elements.pop(operand.value)
                return new_list, None
            except:
                return None, IndexOutOfBoundsError(operand.pos_start, operand.pos_end,
                                          'Index out of bounds', self.context)
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Index must be of an integer Number type', self.context)

    def multiply(self, operand):
        if isinstance(operand, Number) and not isinstance(operand.value, float):
            if operand.value < 0:
                return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'List repetition cannot be negative', self.context)
            new_list = self.copy()
            if operand.value == 0:
                new_list.elements = []
                return new_list, None
            temp_list = list(new_list.elements)

            for i in range(operand.value - 1):
                for ele in temp_list:
                    new_list.elements.append(ele)
            return new_list, None
        else:
            return None, IllegalOperationError(
                operand.pos_start, operand.pos_end, 'Expected an integer Number type', self.context)

    def divide(self, operand):
        new_list = self.copy()
        for i, el in enumerate(new_list.elements):
            if isinstance(operand,List) and isinstance(el,List):
                if el.get_comparison_eq(operand):
                    del new_list.elements[i]
                    break
            elif not isinstance(el,List) and not isinstance(operand,List) and hasattr(el, 'value') and hasattr(operand, 'value') and el.value == operand.value:
                del new_list.elements[i]
                break
        return new_list, None

    def modulus(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'%\' to a List', self.context)

    def floor_divide(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'//\' to a List', self.context)

    def exponent(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'**\' to a List', self.context)

    def get_comparison_eq(self, operand):
        if isinstance(operand, List):
            new_list = self.copy()
            if len(new_list.elements) == len(operand.elements):
                try:
                    all_eq = True
                    for a, b in zip(new_list.elements, operand.elements):
                        if hasattr(a, 'get_comparison_eq') and hasattr(b, 'get_comparison_eq'):
                            eq_node, err = a.get_comparison_eq(b)
                            if err or eq_node.value == 0:
                                all_eq = False
                                break
                        elif hasattr(a, 'value') and hasattr(b, 'value'):
                            if a.value != b.value:
                                all_eq = False
                                break
                        elif not hasattr(a, 'value') and not hasattr(b, 'value'):
                            if a != b:
                                all_eq = False
                                break
                        else:
                            all_eq = False
                            break
                    return Number(1 if all_eq else 0).set_context(self.context), None
                except Exception:
                    return Number(0).set_context(self.context), None
            else:
                return Number(0).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a List', self.context)

    def get_comparison_neq(self, operand):
        if isinstance(operand, List):
            new_list = self.copy()
            return Number(int(not new_list.get_comparison_eq(operand)[0].value)).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a List', self.context)

    def get_comparison_lte(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'<=\' to a List', self.context)

    def get_comparison_lt(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'<\' to a List', self.context)

    def get_comparison_gte(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'>=\' to a List', self.context)

    def get_comparison_gt(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'>\' to a List', self.context)

    def and_by(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'and\' to a List', self.context)

    def or_by(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'or\' to a List', self.context)

    def not_by(self):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'not\' to a List', self.context)
        
    def getByIndex(self, indexes):
        from .dict_type import Dict #Avoiding Circular Import
        temp = self.copy()
        try:
            for idx in indexes:
                if isinstance(temp, Dict):
                    if isinstance(idx, (Number, String)):
                        temp = temp.elements.get(idx.value)
                        if temp is None:
                            return None, DictKeyError(
                                idx.pos_start, idx.pos_end,
                                "Key does not exist"
                            )
                    else:
                        return None, DictKeyError(
                            idx.pos_start, idx.pos_end,
                            "Dictionary keys must be numbers or strings"
                        )
                elif isinstance(idx, Number) and not isinstance(idx.value, float):
                    if isinstance(temp, List):
                        temp = temp.elements[idx.value]
                    elif isinstance(temp, String):
                        temp = String(temp.value[idx.value]).set_context(self.context)
                    else:
                        return None, IllegalOperationError(
                            idx.pos_start, idx.pos_end,
                            "Can't index a data type which is not iterable",
                            self.context
                        )
                else:
                    return None, IllegalOperationError(
                        idx.pos_start, idx.pos_end,
                        "Invalid Index Type",
                        self.context
                    )

            return temp, None

        except IndexError:
            bad_idx = indexes[-1]
            return None, IndexOutOfBoundsError(
                bad_idx.pos_start, bad_idx.pos_end,
                "Index out of bounds",
                self.context
            )

    def assignIndex(self, indexes, val):
        from .dict_type import Dict #Avoiding Circular Import
        new_list = self.copy()
        temp = new_list
        try:
            for idx in indexes[:-1]:
                if isinstance(temp, Dict):
                    if isinstance(idx, (Number, String)):
                        temp = temp.elements.get(idx.value)
                        if temp is None:
                            return None, DictKeyError(
                                idx.pos_start, idx.pos_end,
                                "Key does not exist"
                            )
                    else:
                        return None, DictKeyError(
                            idx.pos_start, idx.pos_end,
                            "Dictionary keys must be numbers or strings"
                        )
                elif isinstance(idx, Number) and not isinstance(idx.value, float):
                    if isinstance(temp, List):
                        temp = temp.elements[idx.value]
                    elif isinstance(temp, String):
                        return None, IllegalOperationError(
                            idx.pos_start, idx.pos_end,
                            "Can't assign inside string beyond one level",
                            self.context
                        )
                    else:
                        return None, IllegalOperationError(
                            idx.pos_start, idx.pos_end,
                            "Can't index a data type which is not iterable",
                            self.context
                        )
                else:
                    return None, IllegalOperationError(
                        idx.pos_start, idx.pos_end,
                        "Invalid Index Type",
                        self.context
                    )

            last_idx = indexes[-1]

            #Case 3: assigning inside a Dict
            if isinstance(temp, Dict):
                if isinstance(last_idx, (Number, String)):
                    temp.elements[last_idx.value] = val
                    return new_list, None
                else:
                    return None, DictKeyError(
                        last_idx.pos_start, last_idx.pos_end,
                        "Dictionary keys must be numbers or strings",
                    )

            if not isinstance(last_idx, Number) or isinstance(last_idx.value, float):
                return None, IllegalOperationError(
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
                    return None, IllegalOperationError(
                        getattr(val, "pos_start", None),
                        getattr(val, "pos_end", None),
                        "Assigned value must be a single character string",
                        self.context
                    )
                s = list(temp.value)
                try:
                    s[last_idx.value] = val.value
                    replaced = String("".join(s)).set_context(self.context)

                    # Instead of indexing into String, go back to the parent List or Dict
                    parent = new_list
                    for idx in indexes[:-2]:
                        parent = parent.elements[idx.value]

                    parent.elements[indexes[-2].value] = replaced
                    return new_list, None

                except IndexError:
                    return None, IndexOutOfBoundsError(
                        last_idx.pos_start, last_idx.pos_end,
                        "Index out of bounds",
                        self.context
                    )

            else:
                return None, IllegalOperationError(
                    last_idx.pos_start, last_idx.pos_end,
                    "Can't index a data type which is not iterable",
                    self.context
                )

        except IndexError:
            bad_idx = indexes[-1]
            return None, IndexOutOfBoundsError(
                bad_idx.pos_start, bad_idx.pos_end,
                "Index out of bounds",
                self.context
            )

    def is_true(self):
        return Number(len(self.elements)).set_context(self.context), None

    def __repr__(self):
        return f'[{", ".join([str(x) for x in self.elements])}]'

    def copy(self):
        copy_elements = []
        for element in self.elements:
            if hasattr(element, 'copy'):
                copy_elements.append(element.copy())
            else:
                copy_elements.append(element)
        copy = List(copy_elements)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def get_attr(self, name, calling_context):
        from sards.user_functions import BoundMethod
        from sards.core.error import AttributeError, ArgumentError, IllegalOperationError, IndexOutOfBoundsError
        from sards.core import RunTimeResult
        from sards.data_types import Number, String

        def method_append(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if len(pos_args) != 1 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "append() takes exactly 1 argument", exec_context))
            instance.elements.append(pos_args[0])
            return res.success(instance)

        def method_prepend(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if len(pos_args) != 1 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "prepend() takes exactly 1 argument", exec_context))
            instance.elements.insert(0, pos_args[0])
            return res.success(instance)

        def method_insert(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if len(pos_args) != 2 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "insert() takes exactly 2 arguments: (index, item)", exec_context))
            idx = pos_args[0]
            if not isinstance(idx, Number) or isinstance(idx.value, float):
                return res.failure(IllegalOperationError(idx.pos_start, idx.pos_end, "Index must be an integer Number", exec_context))
            
            instance.elements.insert(idx.value, pos_args[1])
            return res.success(instance)

        def method_pop(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if len(pos_args) > 1 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "pop() takes at most 1 argument: [index]", exec_context))
            
            if len(pos_args) == 1:
                idx = pos_args[0]
                if not isinstance(idx, Number) or isinstance(idx.value, float):
                    return res.failure(IllegalOperationError(idx.pos_start, idx.pos_end, "Index must be an integer Number", exec_context))
                index_val = idx.value
            else:
                index_val = -1

            try:
                popped = instance.elements.pop(index_val)
                return res.success(popped)
            except IndexError:
                return res.failure(IndexOutOfBoundsError(instance.pos_start, instance.pos_end, "Index out of bounds", exec_context))

        def method_remove(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if len(pos_args) != 1 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "remove() takes exactly 1 argument", exec_context))
            
            target = pos_args[0]
            found_idx = -1
            for i, el in enumerate(instance.elements):
                eq_node, err = el.get_comparison_eq(target) if hasattr(el, 'get_comparison_eq') else (None, None)
                if eq_node and eq_node.value == 1:
                    found_idx = i
                    break
                elif not hasattr(el, 'get_comparison_eq') and hasattr(el, 'value') and hasattr(target, 'value') and el.value == target.value:
                    found_idx = i
                    break
            
            if found_idx == -1:
                return res.failure(IllegalOperationError(target.pos_start, target.pos_end, "Element not found in list", exec_context))
            
            instance.elements.pop(found_idx)
            return res.success(instance)

        def method_clear(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if pos_args or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "clear() takes no arguments", exec_context))
            instance.elements.clear()
            return res.success(instance)

        def method_sort(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            descending = False
            if len(pos_args) > 1 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "sort() takes at most 1 argument: [descending]", exec_context))
            if len(pos_args) == 1:
                desc = pos_args[0]
                if not isinstance(desc, Number) or isinstance(desc.value, float):
                    return res.failure(IllegalOperationError(desc.pos_start, desc.pos_end, "descending argument must be a Boolean Number (0 or 1)", exec_context))
                descending = bool(desc.value)

            import builtins
            try:
                sorted_elements = sorted(instance.elements, key=lambda x: x.value, reverse=descending)
                new_list = List([el.copy() if hasattr(el, 'copy') else el for el in sorted_elements]).set_context(calling_context)
                return res.success(new_list)
            except (builtins.TypeError, builtins.AttributeError):
                return res.failure(IllegalOperationError(instance.pos_start, instance.pos_end, "List elements are not comparable for sorting", exec_context))

        def method_reverse(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if pos_args or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "reverse() takes no arguments", exec_context))
            reversed_elements = [el.copy() if hasattr(el, 'copy') else el for el in reversed(instance.elements)]
            new_list = List(reversed_elements).set_context(calling_context)
            return res.success(new_list)

        def method_slice(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if len(pos_args) != 2 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "slice() takes exactly 2 arguments: (start, end)", exec_context))
            
            start_arg = pos_args[0]
            end_arg = pos_args[1]
            if not isinstance(start_arg, Number) or isinstance(start_arg.value, float) or not isinstance(end_arg, Number) or isinstance(end_arg.value, float):
                return res.failure(IllegalOperationError(instance.pos_start, instance.pos_end, "Slice bounds must be integer Numbers", exec_context))
            
            sliced_elements = [el.copy() if hasattr(el, 'copy') else el for el in instance.elements[start_arg.value:end_arg.value]]
            return res.success(List(sliced_elements).set_context(calling_context))

        def method_join(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if len(pos_args) != 1 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "join() takes exactly 1 argument: (separator)", exec_context))
            
            sep = pos_args[0]
            if not isinstance(sep, String):
                return res.failure(IllegalOperationError(sep.pos_start, sep.pos_end, "Separator must be a String", exec_context))
            
            joined_str = sep.value.join(str(el.value if hasattr(el, 'value') else el) for el in instance.elements)
            return res.success(String(joined_str).set_context(calling_context))

        def method_index_of(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if len(pos_args) != 1 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "index_of() takes exactly 1 argument", exec_context))
            
            target = pos_args[0]
            found_idx = -1
            for i, el in enumerate(instance.elements):
                eq_node, err = el.get_comparison_eq(target) if hasattr(el, 'get_comparison_eq') else (None, None)
                if eq_node and eq_node.value == 1:
                    found_idx = i
                    break
                elif not hasattr(el, 'get_comparison_eq') and hasattr(el, 'value') and hasattr(target, 'value') and el.value == target.value:
                    found_idx = i
                    break
            
            return res.success(Number(found_idx))

        def method_contains(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if len(pos_args) != 1 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "contains() takes exactly 1 argument", exec_context))
            
            target = pos_args[0]
            found = 0
            for el in instance.elements:
                eq_node, err = el.get_comparison_eq(target) if hasattr(el, 'get_comparison_eq') else (None, None)
                if eq_node and eq_node.value == 1:
                    found = 1
                    break
                elif not hasattr(el, 'get_comparison_eq') and hasattr(el, 'value') and hasattr(target, 'value') and el.value == target.value:
                    found = 1
                    break
            
            return res.success(Number(found))

        def method_extend(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if len(pos_args) != 1 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "extend() takes exactly 1 argument", exec_context))
            
            other = pos_args[0]
            if not isinstance(other, List):
                return res.failure(IllegalOperationError(other.pos_start, other.pos_end, "Argument to extend() must be a List", exec_context))
            
            instance.elements.extend([el.copy() for el in other.elements])
            return res.success(instance)

        def method_copy(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if pos_args or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "copy() takes no arguments", exec_context))
            return res.success(instance.copy())

        methods = {
            "append": method_append,
            "prepend": method_prepend,
            "insert": method_insert,
            "pop": method_pop,
            "remove": method_remove,
            "clear": method_clear,
            "sort": method_sort,
            "reverse": method_reverse,
            "slice": method_slice,
            "join": method_join,
            "index_of": method_index_of,
            "contains": method_contains,
            "extend": method_extend,
            "copy": method_copy
        }

        if name in methods:
            bound = BoundMethod(name, self, methods[name])
            return bound.set_context(calling_context).set_pos(self.pos_start, self.pos_end), None

        return None, AttributeError(
            self.pos_start, self.pos_end,
            f"'{type(self).__name__}' has no attribute '{name}'",
            calling_context
        )