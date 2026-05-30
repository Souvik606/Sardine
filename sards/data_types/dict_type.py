from .number_type import Number
from .string_type import String
from sards.core.error import RunTimeError, IllegalOperationError, DictKeyError
import threading
_repr_state = threading.local()

class DictNode:
    def __init__(self, keyval_nodes, pos_start, pos_end):
        self.keyval_nodes = keyval_nodes
        self.pos_start = pos_start
        self.pos_end = pos_end


    def __repr__(self):
        return f'{{{", ".join([f"{str(k)}: {str(v)}" for k, v in self.keyval_nodes])}}}'
    
class Dict:
    def __init__(self, elements):
        self.pos_end = None
        self.context = None
        self.pos_start = None
        self.elements = {}
        for key, value in elements:
            if hasattr(key, 'value'):
                self.elements[key.value] = value
            else:
                self.elements[key] = value
            
        self.set_pos()
        self.set_context()


    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self
    
    def copy(self):
        elements = [(k, v)
                   for k, v in self.elements.items()]
        copy = Dict(elements)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy
    
    def __repr__(self):
        if not hasattr(_repr_state, 'visited'):
            _repr_state.visited = set()
        if id(self) in _repr_state.visited:
            return "{...}"
        _repr_state.visited.add(id(self))
        try:
            def format_key(k):
                return f"'{k}'" if isinstance(k, str) else str(k)
            res = f'{{{", ".join([f"{format_key(k)}: {repr(v)}" for k, v in self.elements.items()])}}}'
        finally:
            _repr_state.visited.remove(id(self))
        return res
    
    def is_true(self):
        return Number(len(self.elements)).set_context(self.context), None    

    def getByIndex(self, indexes):
        from .list_type import List #Avoiding Circular Import
        temp = self.copy()
        try:
            for idx in indexes:
                if isinstance(temp, Dict):
                    if isinstance(idx, (Number, String)):
                        temp = temp.elements.get(idx.value)
                        if temp is None:
                            return None, DictKeyError(
                                idx.pos_start, idx.pos_end,
                                "Key does not exist",
                                self.context
                            )
                    else:
                        return None, DictKeyError(
                            idx.pos_start, idx.pos_end,
                            "Dictionary keys must be numbers or strings",
                            self.context
                        )
                elif isinstance(idx, Number) and not isinstance(idx.value, float):
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
        from .list_type import List #Avoiding Circular Import
        new_dict = self.copy()
        temp = new_dict
        try:
            for idx in indexes[:-1]:
                if isinstance(temp, Dict):
                    if isinstance(idx, (Number, String)):
                        temp = temp.elements.get(idx.value)
                        if temp is None:
                            return None, DictKeyError(
                                idx.pos_start, idx.pos_end,
                                "Key does not exist",
                                self.context
                            )
                    else:
                        return None, DictKeyError(
                            idx.pos_start, idx.pos_end,
                            "Dictionary keys must be numbers or strings",
                            self.context
                        )
                elif isinstance(idx, Number) and not isinstance(idx.value, float):
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

            #Case 3: assigning inside a Dict
            if isinstance(temp, Dict):
                if isinstance(last_idx, (Number, String)):
                    temp.elements[last_idx.value] = val
                    return new_dict, None
                else:
                    return None, DictKeyError(
                        last_idx.pos_start, last_idx.pos_end,
                        "Dictionary keys must be numbers or strings",
                        self.context
                    )
                
            if not isinstance(last_idx, Number) or isinstance(last_idx.value, float):
                return None, RunTimeError(
                    last_idx.pos_start, last_idx.pos_end,
                    "Invalid Index Type",
                    self.context
                )

            # Case 1: assigning inside a List
            if isinstance(temp, List):
                temp.elements[last_idx.value] = val
                return new_dict, None

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

                    # Instead of indexing into String, go back to the parent List or Dict
                    parent = new_dict
                    for idx in indexes[:-2]:
                        parent = parent.elements[idx.value]

                    parent.elements[indexes[-2].value] = replaced
                    return new_dict, None

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

    def add(self, operand):
        """Merges second dict into this one, overwriting duplicate keys"""
        if not isinstance(operand, Dict):
            return None, IllegalOperationError(
                operand.pos_start, 
                operand.pos_end,
                'Can only add dictionary to another dictionary',
                self.context
            )

        new_dict = self.copy()
        
        for k, v in operand.elements.items():
            new_dict.elements[k] = v
            
        return new_dict, None

    def subtract(self, operand):
        """Removes key-value pair with given key if it exists"""
        if not isinstance(operand, (Number, String)):
            return None, DictKeyError(
                operand.pos_start,
                operand.pos_end,
                'Dictionary key must be a number or string',
                self.context
            )
        
        new_dict = self.copy()
        
        if operand.value in new_dict.elements:
            del new_dict.elements[operand.value]
            
        return new_dict, None

    def get_comparison_eq(self, operand):
        """Returns 1 if dicts have same key-value pairs, 0 otherwise"""
        if not isinstance(operand, Dict):
            return None, IllegalOperationError(
                operand.pos_start, 
                operand.pos_end,
                'Expected a Dictionary',
                self.context
            )
            
        if not hasattr(_repr_state, 'comparing'):
            _repr_state.comparing = set()
        pair = (id(self), id(operand))
        if pair in _repr_state.comparing:
            return Number(1).set_context(self.context), None
        _repr_state.comparing.add(pair)
        try:
            if len(self.elements) != len(operand.elements):
                return Number(0).set_context(self.context), None
                
            try:
                for k, v in self.elements.items():
                    if k not in operand.elements:
                        return Number(0).set_context(self.context), None
                    if str(v) != str(operand.elements[k]):
                        return Number(0).set_context(self.context), None
                        
                return Number(1).set_context(self.context), None
            except:
                return Number(0).set_context(self.context), None
        finally:
            _repr_state.comparing.remove(pair)

    def get_comparison_neq(self, operand):
        """Returns opposite of eq comparison"""
        if not isinstance(operand, Dict):
            return None, IllegalOperationError(
                operand.pos_start, 
                operand.pos_end,
                'Expected a Dictionary',
                self.context
            )
        result, error = self.get_comparison_eq(operand)
        if error:
            return None, error
        return Number(1 if result.value == 0 else 0).set_context(self.context), None

    def multiply(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'*\' to a Dictionary',
            self.context
        )

    def divide(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'/\' to a Dictionary',
            self.context
        )

    def modulus(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'%\' to a Dictionary',
            self.context
        )
    
    def bitwise_and(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'&\' to a Dictionary',
            self.context
        )
    
    def bitwise_xor(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'^\' to a Dictionary',
            self.context
        )
    
    def bitwise_or(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'|\' to a Dictionary',
            self.context
        )
    
    def bitwise_not(self):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'~\' to a Dictionary',
            self.context
        )
    
    def lshift(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'<<\' to a Dictionary',
            self.context
        )
    
    def rshift(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'>>\' to a Dictionary',
            self.context
        )

    def floor_divide(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'//\' to a Dictionary',
            self.context
        )

    def exponent(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'^\' to a Dictionary',
            self.context
        )

    def get_comparison_lt(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'<\' to a Dictionary',
            self.context
        )

    def get_comparison_gt(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'>\' to a Dictionary',
            self.context
        )

    def get_comparison_lte(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'<=\' to a Dictionary',
            self.context
        )

    def get_comparison_gte(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'>=\' to a Dictionary',
            self.context
        )

    def and_by(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'and\' to a Dictionary',
            self.context
        )

    def or_by(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'or\' to a Dictionary',
            self.context
        )

    def not_by(self):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'not\' to a Dictionary',
            self.context
        )

    def get_attr(self, name, calling_context):
        from sards.user_functions import BoundMethod
        from sards.core.error import AttributeError, ArgumentError, IllegalOperationError, DictKeyError
        from sards.core import RunTimeResult
        from sards.data_types import Number, String, List, Dict

        def method_keys(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if pos_args or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "keys() takes no arguments", exec_context))
            
            list_keys = []
            for k in instance.elements.keys():
                if isinstance(k, (int, float)):
                    node = Number(k)
                else:
                    node = String(str(k))
                list_keys.append(node.set_context(calling_context))
            return res.success(List(list_keys).set_context(calling_context))

        def method_values(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if pos_args or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "values() takes no arguments", exec_context))
            
            list_vals = [v.copy() for v in instance.elements.values()]
            return res.success(List(list_vals).set_context(calling_context))

        def method_entries(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if pos_args or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "entries() takes no arguments", exec_context))
            
            pairs = []
            for k, v in instance.elements.items():
                if isinstance(k, (int, float)):
                    k_node = Number(k)
                else:
                    k_node = String(str(k))
                k_node.set_context(calling_context)
                
                pair_list = List([k_node, v.copy()]).set_context(calling_context)
                pairs.append(pair_list)
            return res.success(List(pairs).set_context(calling_context))

        def method_items(instance, pos_args, kw_args, exec_context):
            return method_entries(instance, pos_args, kw_args, exec_context)

        def method_get(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if len(pos_args) < 1 or len(pos_args) > 2 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "get() takes 1 or 2 arguments: (key, [default])", exec_context))
            
            key = pos_args[0]
            if not isinstance(key, (Number, String)):
                return res.failure(IllegalOperationError(key.pos_start, key.pos_end, "Key must be a Number or String", exec_context))
            
            default_val = pos_args[1] if len(pos_args) == 2 else Number(0)
            
            val = instance.elements.get(key.value)
            if val is None:
                return res.success(default_val)
            return res.success(val.copy())

        def method_has_key(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if len(pos_args) != 1 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "has_key() takes exactly 1 argument", exec_context))
            
            key = pos_args[0]
            if not isinstance(key, (Number, String)):
                return res.failure(IllegalOperationError(key.pos_start, key.pos_end, "Key must be a Number or String", exec_context))
            
            ans = 1 if key.value in instance.elements else 0
            return res.success(Number(ans))

        def method_contains(instance, pos_args, kw_args, exec_context):
            return method_has_key(instance, pos_args, kw_args, exec_context)

        def method_pop(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if len(pos_args) < 1 or len(pos_args) > 2 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "pop() takes 1 or 2 arguments: (key, [default])", exec_context))
            
            key = pos_args[0]
            if not isinstance(key, (Number, String)):
                return res.failure(IllegalOperationError(key.pos_start, key.pos_end, "Key must be a Number or String", exec_context))
            
            if key.value not in instance.elements:
                if len(pos_args) == 2:
                    return res.success(pos_args[1])
                return res.failure(DictKeyError(key.pos_start, key.pos_end, f"Key '{key.value}' not found in dictionary", exec_context))
            
            popped = instance.elements.pop(key.value)
            return res.success(popped)

        def method_pop_item(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if pos_args or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "pop_item() takes no arguments", exec_context))
            
            if not instance.elements:
                return res.failure(IllegalOperationError(instance.pos_start, instance.pos_end, "pop_item() called on empty dictionary", exec_context))
            
            k, v = instance.elements.popitem()
            if isinstance(k, (int, float)):
                k_node = Number(k)
            else:
                k_node = String(str(k))
            k_node.set_context(calling_context)
            
            pair_list = List([k_node, v]).set_context(calling_context)
            return res.success(pair_list)

        def method_update(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if len(pos_args) != 1 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "update() takes exactly 1 argument: (other_dict)", exec_context))
            
            other = pos_args[0]
            if not isinstance(other, Dict):
                return res.failure(IllegalOperationError(other.pos_start, other.pos_end, "Argument to update() must be a Dictionary", exec_context))
            
            for k, v in other.elements.items():
                instance.elements[k] = v.copy()
            return res.success(instance)

        def method_clear(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if pos_args or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "clear() takes no arguments", exec_context))
            instance.elements.clear()
            return res.success(instance)

        def method_copy(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if pos_args or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "copy() takes no arguments", exec_context))
            return res.success(instance.copy())

        methods = {
            "keys": method_keys,
            "values": method_values,
            "entries": method_entries,
            "items": method_items,
            "get": method_get,
            "has_key": method_has_key,
            "contains": method_contains,
            "pop": method_pop,
            "pop_item": method_pop_item,
            "update": method_update,
            "clear": method_clear,
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