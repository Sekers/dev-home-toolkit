"""This PC's name, for what dev-home-toolkit names after a PC (decision 0083)."""

import socket


def computer_name() -> str:
    """This PC's name: its host name, the name its owner gave it, up to the first dot, in
    capitals. Headings and commit labels show it as it is; rules.pc_folder makes a folder's name
    from it. facts.py has a copy, which a test checks gives the same name."""
    return socket.gethostname().split(".")[0].upper()
