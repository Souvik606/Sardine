from .number_type import *
from sards.core.error import RunTimeError, IllegalOperationError, IndexOutOfBoundsError


class StringNode:
    def __init__(self, token):
        self.token = token
        self.pos_start = self.token.pos_start
        self.pos_end = self.token.pos_end

    def __repr__(self):
        return f'{self.token}'


class String:
    def __init__(self, value):
        self.value = value
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
        if isinstance(operand, String):
            return String(self.value + operand.value).set_context(self.context), None
        else:
            _hint = None
            if isinstance(operand, Number):
                _hint = f"Cannot concatenate String and Number. Try converting with 'String({operand.value})' or wrap in an f-string."
            return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a String type', self.context,
                    hint=_hint)

    def subtract(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'-\' to a String type', self.context)

    def multiply(self, operand):
        if isinstance(operand, Number) and not isinstance(operand.value, float):
            if operand.value < 0:
                return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'String repetition cannot be negative', self.context)
            
            if len(self.value) * operand.value > 100000:
                from sards.core.error import ValueError as SardineValueError
                return None, SardineValueError(
                    operand.pos_start, operand.pos_end,
                    f"String repetition limit exceeded (size {len(self.value) * operand.value} > 100,000 characters limit)",
                    self.context
                )
            
            try:
                return String(self.value * operand.value).set_context(self.context), None
            except (OverflowError, MemoryError):
                from sards.core.error import ValueError as SardineValueError
                return None, SardineValueError(
                    operand.pos_start, operand.pos_end, 'Memory error or overflow during string repetition', self.context)
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected an integer Number type', self.context)

    def divide(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'/\' to a String type', self.context)

    def modulus(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'%\' to a String type', self.context)
    
    def bitwise_and(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'&\' to a String type', self.context)
    
    def bitwise_xor(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'^\' to a String type', self.context)
    
    def bitwise_or(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'|\' to a String type', self.context)
    
    def bitwise_not(self):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'~\' to a String type', self.context)
    
    def lshift(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'<<\' to a String type', self.context)
    
    def rshift(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'>>\' to a String type', self.context)

    def floor_divide(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'//\' to a String type', self.context)

    def exponent(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'**\' to a String type', self.context)

    def get_comparison_eq(self, operand):
        if isinstance(operand, String):
            return Number(int(self.value == operand.value)).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a String type', self.context)

    def get_comparison_neq(self, operand):
        if isinstance(operand, String):
            return Number(int(self.value != operand.value)).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a String type', self.context)

    def get_comparison_lte(self, operand):
        if isinstance(operand, String):
            return Number(int(self.value <= operand.value)).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a String type', self.context)

    def get_comparison_lt(self, operand):
        if isinstance(operand, String):
            return Number(int(self.value < operand.value)).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a String type', self.context)

    def get_comparison_gte(self, operand):
        if isinstance(operand, String):
            return Number(int(self.value >= operand.value)).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a String type', self.context)

    def get_comparison_gt(self, operand):
        if isinstance(operand, String):
            return Number(int(self.value > operand.value)).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a String type', self.context)

    def and_by(self, operand):
        if isinstance(operand, String):
            return (Number(int(bool(self.value) and bool(operand.value))).set_context(self.context),
                    None)
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a String type', self.context)

    def or_by(self, operand):
        if isinstance(operand, String):
            return (Number(int(bool(self.value) or bool(operand.value))).set_context(self.context),
                    None)
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a String type', self.context)

    def not_by(self):
        return Number(int(not self.value)).set_context(self.context), None

    def is_true(self):
        return Number(len(self.value)).set_context(self.context), None
    
    def getByIndex(self, indexes):
        temp = self.value
        try:
            for idx in indexes:
                if isinstance(idx, Number) and not isinstance(idx.value, float):
                    if not isinstance(temp, str):
                        return None, IllegalOperationError(
                            idx.pos_start, idx.pos_end,
                            "Can't index a non-string value",
                            self.context
                        )
                    temp = temp[idx.value]
                else:
                    return None, IllegalOperationError(
                        idx.pos_start, idx.pos_end,
                        "Invalid Index Type",
                        self.context
                    )
            return String(temp).set_context(self.context), None
        except IndexError:
            bad_idx = indexes[-1]
            return None, IndexOutOfBoundsError(
                bad_idx.pos_start, bad_idx.pos_end,
                "Index out of bounds",
                self.context
            )
        except OverflowError:
            bad_idx = indexes[-1]
            return None, IndexOutOfBoundsError(
                bad_idx.pos_start, bad_idx.pos_end,
                "Index too large (overflow)",
                self.context
            )

    def assignIndex(self, indexes, val):
        if not isinstance(val, String) or len(val.value) != 1:
            return None, IllegalOperationError(
                getattr(val, "pos_start", None),
                getattr(val, "pos_end", None),
                "Assigned value must be a single character string",
                self.context
            )

        try:
            s = list(self.value)
            for idx in indexes[:-1]:
                if not isinstance(idx, Number) or isinstance(idx.value, float):
                    return None, IllegalOperationError(
                        idx.pos_start, idx.pos_end,
                        "Invalid Index Type",
                        self.context
                    )
                
                return None, IllegalOperationError(
                    idx.pos_start, idx.pos_end,
                    "Can't index beyond one dimension in string",
                    self.context
                )

            last_idx = indexes[-1]
            if not isinstance(last_idx, Number) or isinstance(last_idx.value, float):
                return None, RunTimeError(
                    last_idx.pos_start, last_idx.pos_end,
                    "Invalid Index Type",
                    self.context
                )

            try:
                s[last_idx.value] = val.value
                return String("".join(s)).set_context(self.context), None
            except IndexError:
                return None, IndexOutOfBoundsError(
                    last_idx.pos_start, last_idx.pos_end,
                    "Index out of bounds",
                    self.context
                )
            except OverflowError:
                return None, IndexOutOfBoundsError(
                    last_idx.pos_start, last_idx.pos_end,
                    "Index too large (overflow)",
                    self.context
                )

        except Exception as e:
            if isinstance(e, OverflowError):
                bad_idx = indexes[-1]
                return None, IndexOutOfBoundsError(
                    bad_idx.pos_start, bad_idx.pos_end,
                    "Index too large (overflow)",
                    self.context
                )
            bad_idx = indexes[-1]
            return None, RunTimeError(
                bad_idx.pos_start, bad_idx.pos_end,
                "Unexpected error in assignIndex",
                self.context
            )

    def copy(self):
        copy = String(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def get_attr(self, name, calling_context):
        from sards.user_functions import BoundMethod
        from sards.core.error import AttributeError, ArgumentError, IllegalOperationError
        from sards.core import RunTimeResult
        from sards.data_types import Number, List

        def method_split(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if len(pos_args) != 1 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "split() takes exactly 1 argument: (delimiter)", exec_context))
            
            delim = pos_args[0]
            if not isinstance(delim, String):
                return res.failure(IllegalOperationError(delim.pos_start, delim.pos_end, "Delimiter must be a String", exec_context))
            
            if not delim.value:
                from sards.core.error import ValueError as SardineValueError
                return res.failure(SardineValueError(delim.pos_start, delim.pos_end, "split delimiter cannot be empty", exec_context))

            try:
                parts = instance.value.split(delim.value)
                list_parts = [String(p).set_context(calling_context) for p in parts]
                return res.success(List(list_parts).set_context(calling_context))
            except (MemoryError, OverflowError):
                from sards.core.error import ValueError as SardineValueError
                return res.failure(SardineValueError(delim.pos_start, delim.pos_end, "Memory error or overflow during string split", exec_context))

        def method_upper(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if pos_args or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "upper() takes no arguments", exec_context))
            return res.success(String(instance.value.upper()).set_context(calling_context))

        def method_lower(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if pos_args or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "lower() takes no arguments", exec_context))
            return res.success(String(instance.value.lower()).set_context(calling_context))

        def method_trim(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if pos_args or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "trim() takes no arguments", exec_context))
            return res.success(String(instance.value.strip()).set_context(calling_context))


        def method_starts_with(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if len(pos_args) != 1 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "starts_with() takes exactly 1 argument: (prefix)", exec_context))
            
            prefix = pos_args[0]
            if not isinstance(prefix, String):
                return res.failure(IllegalOperationError(prefix.pos_start, prefix.pos_end, "Prefix must be a String", exec_context))
            
            ans = 1 if instance.value.startswith(prefix.value) else 0
            return res.success(Number(ans))

        def method_ends_with(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if len(pos_args) != 1 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "ends_with() takes exactly 1 argument: (suffix)", exec_context))
            
            suffix = pos_args[0]
            if not isinstance(suffix, String):
                return res.failure(IllegalOperationError(suffix.pos_start, suffix.pos_end, "Suffix must be a String", exec_context))
            
            ans = 1 if instance.value.endswith(suffix.value) else 0
            return res.success(Number(ans))
        def method_replace(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if len(pos_args) != 2 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "replace() takes exactly 2 arguments: (old, new)", exec_context))
            
            old = pos_args[0]
            new = pos_args[1]
            if not isinstance(old, String) or not isinstance(new, String):
                return res.failure(IllegalOperationError(instance.pos_start, instance.pos_end, "Both old and new arguments must be Strings", exec_context))
            
            try:
                replaced = instance.value.replace(old.value, new.value)
                return res.success(String(replaced).set_context(calling_context))
            except (MemoryError, OverflowError):
                from sards.core.error import ValueError as SardineValueError
                return res.failure(SardineValueError(instance.pos_start, instance.pos_end, "Memory error or overflow during string replace", exec_context))
        def method_find(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if len(pos_args) != 1 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "find() takes exactly 1 argument", exec_context))
            
            sub = pos_args[0]
            if not isinstance(sub, String):
                return res.failure(IllegalOperationError(sub.pos_start, sub.pos_end, "Search term must be a String", exec_context))
            
            idx = instance.value.find(sub.value)
            return res.success(Number(idx))

        def method_contains(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if len(pos_args) != 1 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "contains() takes exactly 1 argument", exec_context))
            
            sub = pos_args[0]
            if not isinstance(sub, String):
                return res.failure(IllegalOperationError(sub.pos_start, sub.pos_end, "Search term must be a String", exec_context))
            
            ans = 1 if sub.value in instance.value else 0
            return res.success(Number(ans))

        def method_is_digit(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if pos_args or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "is_digit() takes no arguments", exec_context))
            ans = 1 if instance.value.isdigit() else 0
            return res.success(Number(ans))

        def method_is_alpha(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if pos_args or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "is_alpha() takes no arguments", exec_context))
            ans = 1 if instance.value.isalpha() else 0
            return res.success(Number(ans))

        methods = {
            "split": method_split,
            "upper": method_upper,
            "lower": method_lower,
            "trim": method_trim,
            "starts_with": method_starts_with,
            "ends_with": method_ends_with,
            "replace": method_replace,
            "find": method_find,
            "contains": method_contains,
            "is_digit": method_is_digit,
            "is_alpha": method_is_alpha
        }

        if name in methods:
            bound = BoundMethod(name, self, methods[name])
            return bound.set_context(calling_context).set_pos(self.pos_start, self.pos_end), None

        return None, AttributeError(
            self.pos_start, self.pos_end,
            f"'{type(self).__name__}' has no attribute '{name}'",
            calling_context
        )

    def __str__(self):
        return f'{self.value}'

    def __repr__(self):
        return f'"{self.value}"'