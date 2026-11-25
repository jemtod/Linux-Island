"""Hint EWMH untuk X11/XWayland, tanpa dependensi program wmctrl."""

import ctypes as C
from ctypes.util import find_library


class _Data(C.Union):
    _fields_ = [("l", C.c_long * 5), ("b", C.c_char * 20)]


class _ClientMessage(C.Structure):
    _fields_ = [
        ("type", C.c_int), ("serial", C.c_ulong), ("send_event", C.c_int),
        ("display", C.c_void_p), ("window", C.c_ulong),
        ("message_type", C.c_ulong), ("format", C.c_int), ("data", _Data),
    ]


class _Event(C.Union):
    _fields_ = [("client", _ClientMessage), ("pad", C.c_long * 24)]


def place_above(xid: int, x: int, y: int) -> None:
    """Minta compositor menaruh window di atas tanpa merebut fokus lagi."""
    library = find_library("X11")
    if not library:
        raise RuntimeError("libX11 tidak ditemukan")
    lib = C.CDLL(library)
    lib.XOpenDisplay.argtypes = [C.c_char_p]
    lib.XOpenDisplay.restype = C.c_void_p
    lib.XDefaultRootWindow.argtypes = [C.c_void_p]
    lib.XDefaultRootWindow.restype = C.c_ulong
    lib.XInternAtom.argtypes = [C.c_void_p, C.c_char_p, C.c_int]
    lib.XInternAtom.restype = C.c_ulong
    lib.XSendEvent.argtypes = [C.c_void_p, C.c_ulong, C.c_int, C.c_long, C.POINTER(_Event)]
    lib.XFlush.argtypes = [C.c_void_p]
    lib.XCloseDisplay.argtypes = [C.c_void_p]
    display = lib.XOpenDisplay(None)
    if not display:
        raise RuntimeError("Tidak dapat membuka display X11")
    try:
        root = lib.XDefaultRootWindow(display)

        def atom(name):
            return lib.XInternAtom(display, name.encode("ascii"), 0)

        def send(name, values):
            event = _Event()
            event.client.type = 33  # ClientMessage
            event.client.display = display
            event.client.window = xid
            event.client.message_type = atom(name)
            event.client.format = 32
            event.client.data.l[:] = values
            if not lib.XSendEvent(display, root, 0, (1 << 20) | (1 << 19), C.byref(event)):
                raise RuntimeError(f"Hint {name} ditolak X11")

        send("_NET_WM_STATE", [1, atom("_NET_WM_STATE_ABOVE"), atom("_NET_WM_STATE_SKIP_TASKBAR"), 1, 0])
        # NorthWestGravity, posisi x/y, sumber aplikasi; ukuran tetap dari GTK.
        send("_NET_MOVERESIZE_WINDOW", [1 | (1 << 8) | (1 << 9) | (1 << 12), x, y, 0, 0])
        lib.XFlush(display)
    finally:
        lib.XCloseDisplay(display)
