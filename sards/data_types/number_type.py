"""
number_type.py

Defines the Sardine numeric type hierarchy:

    Number (abstract base)
    ├── Integer   – wraps Python int, used for integer literals and bitwise ops
    ├── Float     – wraps Python decimal.Decimal for exact float arithmetic
    │                 0.1 + 0.2 → 0.3 exactly (no IEEE-754 drift)
    └── Boolean   – wraps Python bool, displays as True/False
                    Inherits from Integer so it participates in arithmetic.

Type-promotion rules for binary operations:
  Integer  op Integer  → Integer  (except  /  →  Float)
  Integer  op Float    → Float
  Float    op Integer  → Float
  Float    op Float    → Float
  Boolean  op *        → promotes as Integer (True=1, False=0) then applies above
  comparisons          → Boolean
  logical and/or/not   → Boolean
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, getcontext

# Set decimal precision high enough for practical use
getcontext().prec = 28
getcontext().rounding = ROUND_HALF_EVEN

from sards.core.error import IllegalOperationError, DivisionByZeroError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_decimal(value):
    """Convert a numeric Python value to Decimal."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        return Decimal(int(value))
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    return Decimal(str(value))


def _make_number(raw_value):
    """
    Given a raw Python value (int, float, bool, Decimal), return the
    appropriate Sardine Number subclass instance.
    """
    if isinstance(raw_value, bool):
        return Boolean(raw_value)
    if isinstance(raw_value, int):
        return Integer(raw_value)
    if isinstance(raw_value, Decimal):
        # If it happens to be a whole number, keep it as Float (not Integer)
        return Float(raw_value)
    if isinstance(raw_value, float):
        return Float(_to_decimal(raw_value))
    # fallback
    return Integer(int(raw_value))


def _promote(left, right):
    """
    Return the numeric value pair as Decimals if either operand is Float,
    otherwise as plain ints.
    Returns (lv, rv, is_float).
    """
    l_is_float = isinstance(left, Float) and not isinstance(left, Boolean)
    r_is_float = isinstance(right, Float) and not isinstance(right, Boolean)
    if l_is_float or r_is_float:
        return _to_decimal(left.value), _to_decimal(right.value), True
    return int(left.value), int(right.value), False


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class Number:
    """
    Abstract base class for all Sardine numeric types.

    Subclasses: Integer, Float, Boolean
    """

    def __init__(self, value):
        self.context = None
        self.pos_end = None
        self.pos_start = None
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

    # ------------------------------------------------------------------
    # Arithmetic helpers shared by all subclasses
    # ------------------------------------------------------------------

    def _err_illegal(self, operand, msg):
        pos_s = getattr(operand, 'pos_start', None)
        pos_e = getattr(operand, 'pos_end', None)
        return None, IllegalOperationError(pos_s, pos_e, msg, self.context)

    def _err_divzero(self, operand, msg):
        pos_s = getattr(operand, 'pos_start', None)
        pos_e = getattr(operand, 'pos_end', None)
        return None, DivisionByZeroError(pos_s, pos_e, msg, self.context)

    def _check_number(self, operand):
        """Return True if operand is a Number; otherwise return error tuple."""
        if isinstance(operand, Number):
            return True
        return self._err_illegal(operand, 'Expected a Number type')

    # ------------------------------------------------------------------
    # Arithmetic operations — implemented once on the base class
    # ------------------------------------------------------------------

    def add(self, operand):
        if not isinstance(operand, Number):
            return self._err_illegal(operand, 'Expected a Number type')
        lv, rv, is_float = _promote(self, operand)
        result = lv + rv
        node = Float(result).set_context(self.context) if is_float else Integer(result).set_context(self.context)
        return node, None

    def subtract(self, operand):
        if not isinstance(operand, Number):
            return self._err_illegal(operand, 'Expected a Number type')
        lv, rv, is_float = _promote(self, operand)
        result = lv - rv
        node = Float(result).set_context(self.context) if is_float else Integer(result).set_context(self.context)
        return node, None

    def multiply(self, operand):
        if not isinstance(operand, Number):
            return self._err_illegal(operand, 'Expected a Number type')
        lv, rv, is_float = _promote(self, operand)
        result = lv * rv
        node = Float(result).set_context(self.context) if is_float else Integer(result).set_context(self.context)
        return node, None

    def divide(self, operand):
        if not isinstance(operand, Number):
            return self._err_illegal(operand, 'Expected a Number type')
        if getattr(operand, 'value', None) == 0:
            return self._err_divzero(operand, 'Division by zero')
        try:
            lv = _to_decimal(self.value)
            rv = _to_decimal(operand.value)
            result = lv / rv
            return Float(result).set_context(self.context), None
        except ZeroDivisionError:
            return self._err_divzero(operand, 'Division by zero')
        except (InvalidOperation, OverflowError):
            return self._err_illegal(operand, 'Float division overflow or invalid operation')

    def modulus(self, operand):
        if not isinstance(operand, Number):
            return self._err_illegal(operand, 'Expected a Number type')
        if getattr(operand, 'value', None) == 0:
            return self._err_divzero(operand, 'Division by zero')
        try:
            lv, rv, is_float = _promote(self, operand)
            result = lv % rv
            node = Float(result).set_context(self.context) if is_float else Integer(result).set_context(self.context)
            return node, None
        except ZeroDivisionError:
            return self._err_divzero(operand, 'Division by zero')
        except (OverflowError, InvalidOperation):
            return self._err_illegal(operand, 'Modulus overflow')

    def floor_divide(self, operand):
        if not isinstance(operand, Number):
            return self._err_illegal(operand, 'Expected a Number type')
        if getattr(operand, 'value', None) == 0:
            return self._err_divzero(operand, 'Division by zero')
        try:
            lv, rv, is_float = _promote(self, operand)
            result = lv // rv
            # Keep as Float if either operand is Float (not Boolean)
            if is_float:
                return Float(Decimal(int(result))).set_context(self.context), None
            return Integer(int(result)).set_context(self.context), None
        except ZeroDivisionError:
            return self._err_divzero(operand, 'Division by zero')
        except (OverflowError, InvalidOperation):
            return self._err_illegal(operand, 'Floor division overflow')

    def exponent(self, operand):
        if not isinstance(operand, Number):
            return self._err_illegal(operand, 'Expected a Number type')
        try:
            lv, rv, is_float = _promote(self, operand)
            result = lv ** rv
            # If either operand is Float, or the result is fractional (e.g. 2**-3 = 0.125)
            # we need to return a Float.
            if is_float:
                return Float(result if isinstance(result, Decimal) else Decimal(str(result))).set_context(self.context), None
            # Integer ** negative Integer produces a fractional result in Python → Float
            if isinstance(result, float):
                return Float(Decimal(str(result))).set_context(self.context), None
            return Integer(result).set_context(self.context), None
        except ZeroDivisionError:
            return self._err_divzero(operand, 'Division by zero: 0.0 cannot be raised to a negative power')
        except (OverflowError, MemoryError, ValueError, InvalidOperation):
            return self._err_illegal(operand, 'Result too large or invalid exponentiation')

    # ------------------------------------------------------------------
    # Bitwise — integers only
    # ------------------------------------------------------------------

    def _require_int(self, operand=None):
        """Ensure self (and optionally operand) are Integer-like, not Float."""
        if isinstance(self, Float) and not isinstance(self, Boolean):
            pos_s = self.pos_start
            pos_e = self.pos_end
            return None, IllegalOperationError(pos_s, pos_e, 'Bitwise operations require Integer values', self.context)
        if operand is not None:
            if isinstance(operand, Float) and not isinstance(operand, Boolean):
                pos_s = getattr(operand, 'pos_start', None)
                pos_e = getattr(operand, 'pos_end', None)
                return None, IllegalOperationError(pos_s, pos_e, 'Bitwise operations require Integer values', self.context)
        return True, None

    def bitwise_and(self, operand):
        if not isinstance(operand, Number):
            return self._err_illegal(operand, 'Expected a Number type')
        ok, err = self._require_int(operand)
        if err: return None, err
        return Integer(int(self.value) & int(operand.value)).set_context(self.context), None

    def bitwise_xor(self, operand):
        if not isinstance(operand, Number):
            return self._err_illegal(operand, 'Expected a Number type')
        ok, err = self._require_int(operand)
        if err: return None, err
        return Integer(int(self.value) ^ int(operand.value)).set_context(self.context), None

    def bitwise_or(self, operand):
        if not isinstance(operand, Number):
            return self._err_illegal(operand, 'Expected a Number type')
        ok, err = self._require_int(operand)
        if err: return None, err
        return Integer(int(self.value) | int(operand.value)).set_context(self.context), None

    def bitwise_not(self):
        ok, err = self._require_int()
        if err: return None, err
        return Integer(~int(self.value)).set_context(self.context), None

    def lshift(self, operand):
        if not isinstance(operand, Number):
            return self._err_illegal(operand, 'Expected a Number type')
        ok, err = self._require_int(operand)
        if err: return None, err
        if operand.value < 0:
            return self._err_illegal(operand, 'Negative shift count')
        try:
            return Integer(int(self.value) << int(operand.value)).set_context(self.context), None
        except (ValueError, OverflowError, MemoryError):
            return self._err_illegal(operand, 'Shift count too large or result overflow')

    def rshift(self, operand):
        if not isinstance(operand, Number):
            return self._err_illegal(operand, 'Expected a Number type')
        ok, err = self._require_int(operand)
        if err: return None, err
        if operand.value < 0:
            return self._err_illegal(operand, 'Negative shift count')
        try:
            return Integer(int(self.value) >> int(operand.value)).set_context(self.context), None
        except (ValueError, OverflowError, MemoryError):
            return self._err_illegal(operand, 'Shift count too large or result overflow')

    # ------------------------------------------------------------------
    # Comparisons — return Boolean
    # ------------------------------------------------------------------

    def get_comparison_eq(self, operand):
        if not isinstance(operand, Number):
            return self._err_illegal(operand, 'Expected a Number type')
        lv, rv, _ = _promote(self, operand)
        return Boolean(lv == rv).set_context(self.context), None

    def get_comparison_neq(self, operand):
        if not isinstance(operand, Number):
            return self._err_illegal(operand, 'Expected a Number type')
        lv, rv, _ = _promote(self, operand)
        return Boolean(lv != rv).set_context(self.context), None

    def get_comparison_lt(self, operand):
        if not isinstance(operand, Number):
            return self._err_illegal(operand, 'Expected a Number type')
        lv, rv, _ = _promote(self, operand)
        return Boolean(lv < rv).set_context(self.context), None

    def get_comparison_lte(self, operand):
        if not isinstance(operand, Number):
            return self._err_illegal(operand, 'Expected a Number type')
        lv, rv, _ = _promote(self, operand)
        return Boolean(lv <= rv).set_context(self.context), None

    def get_comparison_gt(self, operand):
        if not isinstance(operand, Number):
            return self._err_illegal(operand, 'Expected a Number type')
        lv, rv, _ = _promote(self, operand)
        return Boolean(lv > rv).set_context(self.context), None

    def get_comparison_gte(self, operand):
        if not isinstance(operand, Number):
            return self._err_illegal(operand, 'Expected a Number type')
        lv, rv, _ = _promote(self, operand)
        return Boolean(lv >= rv).set_context(self.context), None

    # ------------------------------------------------------------------
    # Logical — return Boolean
    # ------------------------------------------------------------------

    def and_by(self, operand):
        if not isinstance(operand, Number):
            return self._err_illegal(operand, 'Expected a Number type')
        return Boolean(bool(self.value) and bool(operand.value)).set_context(self.context), None

    def or_by(self, operand):
        if not isinstance(operand, Number):
            return self._err_illegal(operand, 'Expected a Number type')
        return Boolean(bool(self.value) or bool(operand.value)).set_context(self.context), None

    def not_by(self):
        return Boolean(not bool(self.value)).set_context(self.context), None

    def is_true(self):
        return self, None

    def copy(self):
        """Fallback copy — creates the most appropriate subclass copy."""
        if type(self) is Number:
            # Shouldn't normally be instantiated, but handle gracefully
            if isinstance(self.value, bool):
                c = Boolean(self.value)
            elif isinstance(self.value, Decimal):
                c = Float(self.value)
            else:
                c = Integer(int(self.value))
            c.set_pos(self.pos_start, self.pos_end)
            c.set_context(self.context)
            return c
        raise NotImplementedError("Subclasses must implement copy()")

    def __repr__(self):
        return str(self.value)


# ---------------------------------------------------------------------------
# Integer
# ---------------------------------------------------------------------------

class Integer(Number):
    """Sardine Integer type — wraps a Python int."""

    def __init__(self, value):
        # Accept int, bool, Decimal, or float — always store as Python int
        if isinstance(value, bool):
            super().__init__(int(value))
        elif isinstance(value, Decimal):
            super().__init__(int(value))
        elif isinstance(value, float):
            super().__init__(int(value))
        else:
            super().__init__(int(value))

    def copy(self):
        c = Integer(self.value)
        c.set_pos(self.pos_start, self.pos_end)
        c.set_context(self.context)
        return c

    def __repr__(self):
        return str(self.value)


# ---------------------------------------------------------------------------
# Float  (exact arithmetic via decimal.Decimal)
# ---------------------------------------------------------------------------

class Float(Number):
    """
    Sardine Float type — uses Python decimal.Decimal for exact arithmetic.

    0.1 + 0.2 == 0.3 exactly (no IEEE-754 binary drift).
    """

    def __init__(self, value):
        if isinstance(value, Decimal):
            super().__init__(value)
        elif isinstance(value, bool):
            super().__init__(Decimal(int(value)))
        elif isinstance(value, int):
            super().__init__(Decimal(value))
        elif isinstance(value, float):
            # Use string conversion to get the decimal representation
            super().__init__(Decimal(str(value)))
        elif isinstance(value, str):
            try:
                super().__init__(Decimal(value))
            except InvalidOperation:
                super().__init__(Decimal('0'))
        else:
            super().__init__(Decimal(str(value)))

    def copy(self):
        c = Float(self.value)
        c.set_pos(self.pos_start, self.pos_end)
        c.set_context(self.context)
        return c

    def __repr__(self):
        """
        Display the float cleanly:
        - 3.0    → '3.0'
        - 0.3    → '0.3'
        - 1.5    → '1.5'
        - 10/3   → '3.3333333333333' (capped at 13 significant digits)
        Trailing zeros after the decimal point are stripped, but at least one
        digit remains so the value is always recognisable as a float.
        """
        d = self.value
        try:
            # Cap the display precision to 13 significant digits (like Python's float)
            # while still keeping exact values like 0.3 exact.
            rounded = d.quantize(Decimal('1E-13'), rounding=ROUND_HALF_EVEN) if abs(d) < Decimal('1E13') else d
            # Format as fixed-point
            s = format(rounded, 'f')
            # Strip trailing zeros but keep at least one decimal digit
            if '.' in s:
                s = s.rstrip('0')
                if s.endswith('.'):
                    s += '0'
            else:
                s += '.0'
            return s
        except Exception:
            return str(d)


# ---------------------------------------------------------------------------
# Boolean
# ---------------------------------------------------------------------------

class Boolean(Integer):
    """
    Sardine Boolean type — wraps Python bool, displays as True/False.

    Inherits from Integer so Boolean participates in arithmetic:
      True + 1  → Integer(2)
      False * 5 → Integer(0)

    Comparisons and logical ops always return Boolean.
    """

    def __init__(self, value):
        # Store the underlying bool truth value; parent Integer stores int(value)
        bool_val = bool(value)
        # Call Number.__init__ directly to store the bool-coerced int
        Number.__init__(self, int(bool_val))
        self._bool_value = bool_val

    def is_true(self):
        return self, None

    def copy(self):
        c = Boolean(self._bool_value)
        c.set_pos(self.pos_start, self.pos_end)
        c.set_context(self.context)
        return c

    def __repr__(self):
        return 'True' if self._bool_value else 'False'