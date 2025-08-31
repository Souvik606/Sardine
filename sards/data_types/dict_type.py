from .number_type import Number
from .string_type import String
from sards.core.error import RunTimeError, IllegalOperationError, DictKeyError

class DictNode:
    def __init__(self, keyval_nodes, pos_start, pos_end):
        self.keyval_nodes = keyval_nodes
        self.pos_start = pos_start
        self.pos_end = pos_end


    def __repr__(self):
        return f'{{{", ".join([f"{str(k)}: {str(v)}" for k, v in self.keyval_nodes])}}}'
    
class Dict:
    def __init__(self, elements):
        self.elements = {}
        for key, value in elements:
            if not isinstance(key, (Number, String)):
                raise IllegalOperationError(
                    key.pos_start, 
                    key.pos_end,
                    'Dictionary keys must be numbers or strings'
                )
            self.elements[key.value] = value
            
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
        elements = [(Number(k) if isinstance(k, (int, float)) else String(k), v) 
                   for k, v in self.elements.items()]
        copy = Dict(elements)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy
    
    def __repr__(self):
        return f'{{{", ".join([f"{k}: {str(v)}" for k, v in self.elements.items()])}}}'
    
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
                'Dictionary key must be a number or string'
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
                'Expected a Dictionary'
            )
            
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

    def get_comparison_neq(self, operand):
        """Returns opposite of eq comparison"""
        if not isinstance(operand, Dict):
            return None, IllegalOperationError(
                operand.pos_start, 
                operand.pos_end,
                'Expected a Dictionary'
            )
        result, error = self.get_comparison_eq(operand)
        if error:
            return None, error
        return Number(1 if result.value == 0 else 0).set_context(self.context), None

    def multiply(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'*\' to a Dictionary',
        )

    def divide(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'/\' to a Dictionary',
        )

    def modulus(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'%\' to a Dictionary',
        )

    def floor_divide(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'//\' to a Dictionary',
        )

    def exponent(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'^\' to a Dictionary',
        )

    def get_comparison_lt(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'<\' to a Dictionary',
        )

    def get_comparison_gt(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'>\' to a Dictionary',
        )

    def get_comparison_lte(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'<=\' to a Dictionary',
        )

    def get_comparison_gte(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'>=\' to a Dictionary',
        )

    def and_by(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'and\' to a Dictionary',
        )

    def or_by(self, operand):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'or\' to a Dictionary',
        )

    def not_by(self):
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            'Cannot apply \'not\' to a Dictionary',
        )



