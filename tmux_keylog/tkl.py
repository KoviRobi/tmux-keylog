#!/usr/bin/env python3

# A key-logger that works with TMUX without SUDO
#
# Inspired by https://xoc3.io/blog/2021-11-22 github
# https://github.com/alanxoc3/dotfiles/blob/main/bin/tkl
# But this doesn't require root, and uses a style I prefer

import shlex
import typing as t
from argparse import ArgumentParser
from signal import SIGINT, signal
from subprocess import run

from pynput import keyboard

Events = keyboard.Events
KeyCode = keyboard.KeyCode
Key = keyboard.Key

mappings = {
    "default": {
        "f1": "F1",
        "f2": "F2",
        "f3": "F3",
        "f4": "F4",
        "f5": "F5",
        "f6": "F6",
        "f7": "F7",
        "f8": "F8",
        "f9": "F9",
        "f10": "F10",
        "f11": "F11",
        "f12": "F12",
        "backspace": "⌫",
        "delete": "⌦",
        "tab": "⇥",
        "space": "␣",
        "enter": "⏎",
        "esc": "⎋",
        "left": "←",
        "right": "→",
        "up": "↑",
        "down": "↓",
        "page_up": "↥",
        "page_down": "↧",
        "home": "↤",
        "end": "↦",
        "control": "C",
        "alt": "A",
        "gui": "M",
        "shift": "S",
        "mod_sep": "",
    },
    # See https://jdebp.uk/FGA/iso-9995-7-symbols.html
    "ISO-9995-7": {
        "f1": "F1",
        "f2": "F2",
        "f3": "F3",
        "f4": "F4",
        "f5": "F5",
        "f6": "F6",
        "f7": "F7",
        "f8": "F8",
        "f9": "F9",
        "f10": "F10",
        "f11": "F11",
        "f12": "F12",
        "backspace": "⌫",
        "delete": "⌦",
        "tab": "⇥",
        "space": "␣",
        "enter": "⏎",
        "esc": "⎋",
        "left": "←",
        "right": "→",
        "up": "↑",
        "down": "↓",
        "page_up": "⎗",
        "page_down": "⎘",
        "home": "⇱",
        "end": "⇲",
        "control": "⎈",
        "alt": "⌥",
        "gui": "⌘",
        "shift": "⇧",
        "mod_sep": "",
    },
    "name": {
        "f1": "F1",
        "f2": "F2",
        "f3": "F3",
        "f4": "F4",
        "f5": "F5",
        "f6": "F6",
        "f7": "F7",
        "f8": "F8",
        "f9": "F9",
        "f10": "F10",
        "f11": "F11",
        "f12": "F12",
        "backspace": "bs",
        "delete": "del",
        "tab": "tab",
        "space": "space",
        "enter": "ret",
        "esc": "esc",
        "left": "left",
        "right": "right",
        "up": "up",
        "down": "down",
        "page_up": "pgup",
        "page_down": "pgdn",
        "home": "home",
        "end": "end",
        "control": "ctrl",
        "alt": "alt",
        "gui": "gui",
        "shift": "shift",
        "mod_sep": "-",
    },
}
mappings["iso"] = mappings["ISO-9995-7"]


def normalise_mods(key: "Key | KeyCode | None") -> "Key | KeyCode | None":
    if key in [Key.ctrl_l, Key.ctrl_r]:
        return Key.ctrl
    if key in [Key.alt_l, Key.alt_r, Key.alt_gr]:
        return Key.alt
    if key in [Key.shift_l, Key.shift_r]:
        return Key.shift
    if key in [Key.cmd_l, Key.cmd_r]:
        return Key.cmd
    return key


def is_mod(key: "Key | KeyCode | None"):
    return key in [Key.ctrl, Key.alt, Key.shift, Key.cmd]


def format_key(key: str, mods: "set[Key]", mappings: "dict[str, str]"):
    mod = []
    if Key.ctrl in mods:
        mod.append(mappings["control"])
    if Key.alt in mods:
        mod.append(mappings["alt"])
    if Key.cmd in mods:
        mod.append(mappings["gui"])
    if Key.shift in mods:
        # We want S-F1, S-backspace, S-␣ but not S-A
        if len(key) == 1 and key.isascii() and not key.isspace():
            pass
        else:
            mod.append(mappings["shift"])

    if mod != []:
        return f"⟨{mappings['mod_sep'].join(mod)}-{key}⟩"
    elif len(key) > 1:
        return f"⟨{key}⟩"
    else:
        return key


def tmux_escape(status: str):
    # Escape #, %
    # Note: # needs escaping twice, once for the `set` and once for the
    # `status-format` printing.
    status = status.replace("#", "####")
    status = status.replace("%", "%%")
    return status


def make_tmux_set_status(set_commands: "list[str]"):
    def callback(status: str):
        status = tmux_escape(status)
        for command in set_commands:
            set_exec = [arg.format(status) for arg in shlex.split(command)]
            run(set_exec)

    return callback


def loop(status: str, status_cb: t.Callable[[str], None], mappings: "dict[str, str]", width: int, align: str):
    with keyboard.Events() as events:
        mods = set()
        for event in events:
            if isinstance(event, Events.Press):
                key = normalise_mods(event.key)
                if key is None:
                    continue
                elif is_mod(key):
                    mods.add(key)
                    continue
                elif isinstance(key, KeyCode):
                    if key.char is None:
                        continue
                    name = key.char
                else:
                    name = key.name
                    if name in mappings:
                        name = mappings[name]

                name = format_key(name, mods, mappings)

                status = (status + " " + name)[-width:]

                # Ensure no partial brackets
                opening = status.find("⟨")
                if opening < 0:
                    opening = len(status)
                closing = status.find("⟩")
                if closing < opening:
                    status = " " * closing + status[closing + 1 :]

                # Pad back to length
                status = f"{status:{align}{width}}"

                status_cb(status)
            elif isinstance(event, Events.Release):
                key = normalise_mods(event.key)
                if key in mods:
                    mods.remove(key)


def main():
    parser = ArgumentParser()
    exec_default = "tmux set -g status-format[1] #[align=centre]{};"
    parser.add_argument(
        "--exec",
        "-e",
        default=[exec_default],
        nargs="*",
        help="Program to execute with the status string. The {} will "
        + "be substituted with the escaped string. Default is "
        + f"`{exec_default}`. Can be specified multiple times, each "
        + "will be executed separately. Note: put a trailing "
        + "semicolon to stop tmux from stripping trailing semicolons.",
    )
    parser.add_argument(
        "--width",
        "-w",
        default=40,
        type=int,
        help="Width under which the status line should be kept. Default is 40.",
    )
    parser.add_argument(
        "--align",
        "-a",
        default=">",
        help="Alignment of the status line (one of <, ^, >, see "
        + "`help('FORMATTING')`). Default is `>`",
    )
    parser.add_argument(
        "--no-init",
        "-n",
        dest="init",
        action="store_false",
        help="Don't execute initial commands "
        + "`tmux set -g status 2` and "
        + "`set -g status-format[1] <padded blank>` on startup",
    )
    parser.add_argument(
        "--mappings",
        "-m",
        default=mappings["default"],
        type=mappings.get,
        help=f"Mappings/descriptions for keys, one of {', '.join(mappings)}",
    )
    args = parser.parse_args()

    init_status = f"{'':{args.align}{args.width}}"
    cb = make_tmux_set_status(args.exec)
    if args.init:
        # Ensure status[1] is visible
        run(["tmux", "set", "-g", "status", "2"])
        cb(init_status)
    loop(
        status=init_status,
        status_cb=make_tmux_set_status(args.exec),
        mappings=args.mappings,
        width=args.width,
        align=args.align,
    )


if __name__ == "__main__":
    signal(signalnum=SIGINT, handler=lambda *_: exit(0))
    main()
