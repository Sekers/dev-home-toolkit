"""Sending text an end user dropped to the Recycle Bin, so a wrong answer at a prompt never loses
it (decision 0069, "Dropped text"). Setup writes the text to a file of its own, sends that file to
the bin, and only once the bin has it removes or overwrites anything. Windows only for now: macOS's
Trash and Linux's trash folder come with those systems.

On Windows the file goes through the shell's IFileOperation, called with ctypes, so nothing new
is installed: Microsoft's documentation says IFileOperation replaced SHFileOperation. Windows
deletes a file for good, rather than sending it to the bin, when its drive has no Recycle Bin or
the bin is set to remove files at once, and says nothing. So setup gives IFileOperation a progress
sink, which hears about each item it deletes: when the file went to the bin, the sink is given the
item it became there, and when it was deleted for good, no item. Either way the file was setup's
own copy of the text, so nothing is lost: the caller still has the text, and asks what to do.

IFileOperation works only in a single-threaded apartment, so each call runs in a thread of its
own that sets COM up and takes it down again, and the rest of the process is left as it was.
ctypes is imported only there, so loading this module costs a setup run nothing."""

import contextlib
import sys
import tempfile
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# IFileOperation's flags: no window, question, or error box (FOF_NO_UI), and the Recycle Bin
# rather than deleting for good (FOF_ALLOWUNDO, and Windows 8's FOFX_RECYCLEONDELETE).
FOF_NO_UI = 0x0614
FOF_ALLOWUNDO = 0x0040
FOFX_RECYCLEONDELETE = 0x00080000
TO_THE_BIN = FOF_NO_UI | FOF_ALLOWUNDO | FOFX_RECYCLEONDELETE

CLSID_FILE_OPERATION = "3AD05575-8857-4850-9277-11B85BDB8E09"
IID_FILE_OPERATION = "947AAB5F-0A5C-4C13-B4D6-4BF7836FC9F8"
IID_PROGRESS_SINK = "04B0F1A7-9490-44BC-96E1-4296A31252E2"
IID_SHELL_ITEM = "43826D1E-E718-42EE-BC55-A1E261C37BFE"
IID_UNKNOWN = "00000000-0000-0000-C000-000000000046"

# Where each method used here sits in its interface's table of methods, IUnknown's first.
RELEASE = 2
SET_OPERATION_FLAGS = 5
DELETE_ITEM = 18
PERFORM_OPERATIONS = 21

COINIT_APARTMENTTHREADED = 0x2
COINIT_DISABLE_OLE1DDE = 0x4
CLSCTX_ALL = 0x17
S_OK = 0
E_NOINTERFACE = -0x7FFFBFFE  # 0x80004002, as a signed HRESULT

# Each IFileOperationProgressSink method after IUnknown's three, in the interface's order, with
# its arguments after the object itself: P a pointer, D a DWORD, S a string, H an HRESULT, U a
# UINT. Only PostDeleteItem does anything here.
SINK_METHODS = (
    ("StartOperations", ""),
    ("FinishOperations", "H"),
    ("PreRenameItem", "DPS"),
    ("PostRenameItem", "DPSHP"),
    ("PreMoveItem", "DPPS"),
    ("PostMoveItem", "DPPSHP"),
    ("PreCopyItem", "DPPS"),
    ("PostCopyItem", "DPPSHP"),
    ("PreDeleteItem", "DP"),
    ("PostDeleteItem", "DPHP"),
    ("PreNewItem", "DPS"),
    ("PostNewItem", "DPSSDHP"),
    ("UpdateProgress", "UU"),
    ("ResetTimer", ""),
    ("PauseTimer", ""),
    ("ResumeTimer", ""),
)


@dataclass(frozen=True)
class Sent:
    """Whether the Recycle Bin has the file, and when it doesn't, why, as a sentence."""

    in_bin: bool
    why_not: str = ""


def send_text(text: str, name: str) -> Sent:
    """Sends text, as UTF-8, to the Recycle Bin as a file called name (see send_data)."""
    check_name(name)
    try:
        data = text.encode("utf-8")
    except UnicodeError as error:
        return Sent(False, f"Setup couldn't write the text to a file: {error}")
    return send_data(data, name)


def send_data(data: bytes, name: str) -> Sent:
    """Writes data, byte for byte, to a file called name in a new folder of the system's
    temporary folder, and sends that file to the Recycle Bin, where an end user finds it by that
    name. The folder is removed afterwards, and the file too when the bin didn't take it. name has
    to be a plain file name, with none of the characters Windows keeps out of one. Any other
    failure is a Sent that says why, never an error raised."""
    check_name(name)
    try:
        folder = Path(tempfile.mkdtemp(prefix="dev-home-toolkit-"))
    except OSError as error:
        return Sent(False, f"Setup couldn't make a folder in the temporary folder: {error}")
    path = folder / name
    try:
        try:
            path.write_bytes(data)
        except OSError as error:
            return Sent(False, f"Setup couldn't write the text to a file: {error}")
        return send_file(path)
    finally:
        # Something left in the temporary folder harms nothing, and the text is still the caller's.
        # Each step tries on its own: a name too long to write is too long to remove, too.
        with contextlib.suppress(OSError):
            path.unlink(missing_ok=True)
        with contextlib.suppress(OSError):
            folder.rmdir()


def check_name(name: str) -> None:
    """Raises ValueError for a name that isn't a plain file name (see plain_name): a caller's
    mistake, not something to report."""
    if not plain_name(name):
        raise ValueError(f"{name!r} isn't a plain file name.")


def plain_name(name: str) -> bool:
    """Whether name is a plain file name: no folder, not . or .., and none of the characters
    Windows keeps out of a file name, such as a colon, which would name a stream of another file
    on NTFS."""
    if name in ("", ".", "..") or Path(name).name != name:
        return False
    return not any(char in '<>:"/\\|?*' or ord(char) < 32 for char in name)


def send_file(path: Path, flags: int = TO_THE_BIN) -> Sent:
    """Sends a file to the Recycle Bin through IFileOperation, in a thread of its own (see the
    description above), and says whether the bin has it. When it doesn't, the file may still be
    there, as when Windows couldn't start the delete, or be deleted for good. flags are
    IFileOperation's: the tests leave out the bin's, and so delete for good, since they can't
    touch the real bin."""
    if sys.platform != "win32":
        return Sent(False, "Setup can use the trash only on Windows so far.")
    outcome: list[Sent] = []

    def work() -> None:
        try:
            outcome.append(delete_in_apartment(path, flags))
        except Exception as error:
            outcome.append(Sent(False, f"Windows couldn't delete it: {error}"))

    thread = threading.Thread(target=work, name="recycle-bin")
    thread.start()
    thread.join()
    return outcome[0] if outcome else Sent(False, "Sending it to the Recycle Bin stopped.")


def failed(hresult: int, what: str) -> Sent:
    return Sent(False, f"{what} failed (HRESULT {hresult & 0xFFFFFFFF:#010x}).")


def delete_in_apartment(path: Path, flags: int) -> Sent:
    """IFileOperation's delete of one file, in a single-threaded apartment for this thread."""
    import ctypes

    ole32 = ctypes.WinDLL("ole32")
    ole32.CoInitializeEx.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    ole32.CoInitializeEx.restype = ctypes.c_long
    started = ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED | COINIT_DISABLE_OLE1DDE)
    if started < 0:
        return failed(started, "Starting COM")
    try:
        return delete_with_sink(path, flags)
    finally:
        ole32.CoUninitialize()


def guid(text: str) -> Any:
    """A GUID as COM reads it: 16 bytes, with its first three fields little-endian."""
    import ctypes

    return (ctypes.c_ubyte * 16)(*uuid.UUID(text).bytes_le)


def method(interface: Any, index: int, *argtypes: Any) -> Callable[..., int]:
    """A COM interface's method, by its place in the interface's table of methods. A COM object is
    a pointer to that table, and an interface pointer is the object's address."""
    import ctypes

    table = ctypes.cast(interface, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))[0]
    prototype = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, *argtypes)
    function = prototype(table[index])
    return lambda *args: int(function(interface, *args))


def delete_with_sink(path: Path, flags: int) -> Sent:
    """Deletes path with IFileOperation, flags set, and a ProgressSink listening."""
    import ctypes

    create = ctypes.WinDLL("ole32").CoCreateInstance
    create.argtypes = [ctypes.c_void_p] * 2 + [ctypes.c_ulong] + [ctypes.c_void_p] * 2
    create.restype = ctypes.c_long
    parse = ctypes.WinDLL("shell32").SHCreateItemFromParsingName
    parse.argtypes = [ctypes.c_wchar_p] + [ctypes.c_void_p] * 3
    parse.restype = ctypes.c_long

    sink = ProgressSink()
    operation = ctypes.c_void_p()
    item = ctypes.c_void_p()
    clsid, iid = guid(CLSID_FILE_OPERATION), guid(IID_FILE_OPERATION)
    made = create(ctypes.byref(clsid), None, CLSCTX_ALL, ctypes.byref(iid), ctypes.byref(operation))
    if made < 0:
        return failed(made, "Starting IFileOperation")
    try:
        found = parse(str(path), None, ctypes.byref(guid(IID_SHELL_ITEM)), ctypes.byref(item))
        if found < 0:
            return failed(found, f"Finding {path}")
        steps: list[tuple[int, tuple[Any, ...], tuple[Any, ...], str]] = [
            (SET_OPERATION_FLAGS, (ctypes.c_ulong,), (flags,), "Setting IFileOperation's flags"),
            (DELETE_ITEM, (ctypes.c_void_p,) * 2, (item, sink.pointer), "Asking for the delete"),
            (PERFORM_OPERATIONS, (), (), "The delete"),
        ]
        for index, argtypes, args, what in steps:
            result = method(operation, index, *argtypes)(*args)
            if result < 0:
                return failed(result, what)
        if sink.deleted is None:
            return Sent(False, "Windows didn't report deleting it.")
        hresult, in_bin = sink.deleted
        if hresult < 0:
            return failed(hresult, "The delete")
        if not in_bin:
            return Sent(
                False,
                "Windows deleted it for good rather than keep it in the Recycle Bin: its drive may "
                "have no bin, or the bin may be set to remove files at once, or be too small.",
            )
        return Sent(True)
    finally:
        for interface in (item, operation):
            if interface.value:
                method(interface, RELEASE)()


class ProgressSink:
    """An IFileOperationProgressSink made with ctypes, which notes how the delete it hears about
    went: deleted is None until then, and then the delete's HRESULT and whether it left an item
    in the Recycle Bin. Every other method only says all is well. pointer is the interface
    pointer to give IFileOperation, and the sink has to stay alive until the operation ends."""

    def __init__(self) -> None:
        import ctypes

        kinds = {
            "P": ctypes.c_void_p,
            "D": ctypes.c_ulong,
            "S": ctypes.c_wchar_p,
            "H": ctypes.c_long,
            "U": ctypes.c_uint,
        }
        self.deleted: tuple[int, bool] | None = None
        known = (bytes(guid(IID_UNKNOWN)), bytes(guid(IID_PROGRESS_SINK)))

        def query_interface(this: int, riid: int, out: int) -> int:
            target = ctypes.cast(out, ctypes.POINTER(ctypes.c_void_p))
            if ctypes.string_at(riid, 16) in known:
                target[0] = this
                return S_OK
            target[0] = None
            return E_NOINTERFACE

        def counted(_this: int) -> int:
            # Python keeps the sink alive, so its count of references does nothing.
            return 1

        def post_delete(_this: int, _flags: int, _item: int, hresult: int, created: int) -> int:
            self.deleted = (hresult, bool(created))
            return S_OK

        def fine(*_args: object) -> int:
            return S_OK

        pointer = ctypes.c_void_p
        self.functions: list[Any] = [
            ctypes.WINFUNCTYPE(ctypes.c_long, pointer, pointer, pointer)(query_interface),
            ctypes.WINFUNCTYPE(ctypes.c_ulong, pointer)(counted),
            ctypes.WINFUNCTYPE(ctypes.c_ulong, pointer)(counted),
        ]
        for name, arguments in SINK_METHODS:
            prototype = ctypes.WINFUNCTYPE(ctypes.c_long, pointer, *(kinds[k] for k in arguments))
            self.functions.append(prototype(post_delete if name == "PostDeleteItem" else fine))
        self.table = (pointer * len(self.functions))(
            *(ctypes.cast(function, pointer) for function in self.functions)
        )
        self.object = pointer(ctypes.addressof(self.table))
        self.pointer = pointer(ctypes.addressof(self.object))
