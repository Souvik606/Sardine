from sards.data_types.number_type import Number
from sards.data_types.string_type import String

class File:
    def __init__(self, filepath, mode, file_obj):
        self.filepath = filepath
        self.mode = mode
        self.file_obj = file_obj
        self.pos_start = None
        self.pos_end = None
        self.context = None

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def copy(self):
        copy = File(self.filepath, self.mode, self.file_obj)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def is_true(self):
        closed = self.file_obj.closed
        return Number(0 if closed else 1).set_context(self.context), None

    def __repr__(self):
        closed = self.file_obj.closed
        state = "closed" if closed else "open"
        return f"<file '{self.filepath}' mode='{self.mode}' state={state}>"

    def get_attr(self, name, calling_context):
        from sards.user_functions import BoundMethod
        from sards.core.error import FileIOError, ArgumentError, TypeError, AttributeError
        from sards.core import RunTimeResult

        def method_read(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if pos_args or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "read() takes no arguments", exec_context))
            if instance.file_obj.closed:
                return res.failure(FileIOError(instance.pos_start, instance.pos_end, "I/O operation on closed file.", exec_context))
            if instance.mode not in ("r", "r+"):
                return res.failure(FileIOError(instance.pos_start, instance.pos_end, "File not open for reading", exec_context))
            try:
                content = instance.file_obj.read()
                return res.success(String(content).set_context(calling_context))
            except Exception as e:
                return res.failure(FileIOError(instance.pos_start, instance.pos_end, f"Failed to read file: {str(e)}", exec_context))

        def method_lread(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if pos_args or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "lread() takes no arguments", exec_context))
            if instance.file_obj.closed:
                return res.failure(FileIOError(instance.pos_start, instance.pos_end, "I/O operation on closed file.", exec_context))
            if instance.mode not in ("r", "r+"):
                return res.failure(FileIOError(instance.pos_start, instance.pos_end, "File not open for reading", exec_context))
            try:
                content = instance.file_obj.readline()
                return res.success(String(content).set_context(calling_context))
            except Exception as e:
                return res.failure(FileIOError(instance.pos_start, instance.pos_end, f"Failed to read line: {str(e)}", exec_context))

        def method_write(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if len(pos_args) != 1 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "write() takes exactly 1 argument: (text)", exec_context))
            if instance.file_obj.closed:
                return res.failure(FileIOError(instance.pos_start, instance.pos_end, "I/O operation on closed file.", exec_context))
            if instance.mode not in ("w", "a", "r+", "w+", "a+"):
                return res.failure(FileIOError(instance.pos_start, instance.pos_end, "File not open for writing", exec_context))
            text_arg = pos_args[0]
            if not isinstance(text_arg, String):
                return res.failure(TypeError(text_arg.pos_start, text_arg.pos_end, "write() argument must be a String", exec_context))
            try:
                instance.file_obj.write(text_arg.value)
                return res.success(Number(0))
            except Exception as e:
                return res.failure(FileIOError(instance.pos_start, instance.pos_end, f"Failed to write to file: {str(e)}", exec_context))

        def method_lwrite(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if len(pos_args) != 1 or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "lwrite() takes exactly 1 argument: (text)", exec_context))
            if instance.file_obj.closed:
                return res.failure(FileIOError(instance.pos_start, instance.pos_end, "I/O operation on closed file.", exec_context))
            if instance.mode not in ("w", "a", "r+", "w+", "a+"):
                return res.failure(FileIOError(instance.pos_start, instance.pos_end, "File not open for writing", exec_context))
            text_arg = pos_args[0]
            if not isinstance(text_arg, String):
                return res.failure(TypeError(text_arg.pos_start, text_arg.pos_end, "lwrite() argument must be a String", exec_context))
            try:
                instance.file_obj.write(text_arg.value + "\n")
                return res.success(Number(0))
            except Exception as e:
                return res.failure(FileIOError(instance.pos_start, instance.pos_end, f"Failed to write line to file: {str(e)}", exec_context))

        def method_close(instance, pos_args, kw_args, exec_context):
            res = RunTimeResult()
            if pos_args or kw_args:
                return res.failure(ArgumentError(instance.pos_start, instance.pos_end, "close() takes no arguments", exec_context))
            if not instance.file_obj.closed:
                try:
                    instance.file_obj.close()
                except Exception as e:
                    return res.failure(FileIOError(instance.pos_start, instance.pos_end, f"Failed to close file: {str(e)}", exec_context))
            return res.success(Number(0))

        methods = {
            "read": method_read,
            "lread": method_lread,
            "write": method_write,
            "lwrite": method_lwrite,
            "close": method_close
        }

        if name in methods:
            bound = BoundMethod(name, self, methods[name])
            return bound.set_context(calling_context).set_pos(self.pos_start, self.pos_end), None

        return None, AttributeError(
            self.pos_start, self.pos_end,
            f"'{type(self).__name__}' has no attribute '{name}'",
            calling_context
        )
