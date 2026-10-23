"""Sending dropped text to the Recycle Bin (internal/shared/recycle_bin.py). The tests can't touch
the real bin, so the ones that reach Windows leave out the bin's flags, which deletes for good:
that still runs every COM call and the progress sink, and shows a delete for good is reported as
not in the bin. Sending a file to the real bin is checked by hand."""

import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from helpers import Sandbox, sandbox_for, shared_module

windows_only = pytest.mark.skipif(sys.platform != "win32", reason="IFileOperation is Windows'")


@pytest.fixture(scope="module")
def box(request: pytest.FixtureRequest) -> Iterator[Sandbox]:
    yield from sandbox_for(request, "recycle-bin")


@pytest.fixture
def code(box: Sandbox) -> ModuleType:
    return shared_module(box, "recycle_bin")


@windows_only
def test_a_file_deleted_for_good_is_reported_as_not_in_the_bin(
    code: ModuleType, tmp_path: Path
) -> None:
    path = tmp_path / "dropped.md"
    path.write_text("# Dropped\n", encoding="utf-8")
    sent = code.send_file(path, code.FOF_NO_UI)
    assert not path.exists()
    assert sent == code.Sent(
        False,
        "Windows deleted it for good rather than keep it in the Recycle Bin: its drive may have "
        "no bin, or the bin may be set to remove files at once, or be too small.",
    )


@windows_only
def test_a_file_that_isnt_there_is_reported_not_raised(code: ModuleType, tmp_path: Path) -> None:
    sent = code.send_file(tmp_path / "missing.md", code.FOF_NO_UI)
    assert not sent.in_bin
    assert sent.why_not.startswith(f"Finding {tmp_path / 'missing.md'} failed (HRESULT 0x"), sent


def test_text_goes_to_the_bin_in_a_file_of_its_name_that_leaves_nothing_behind(
    code: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent: list[tuple[Path, bytes]] = []

    def to_the_bin(path: Path) -> object:
        sent.append((path, path.read_bytes()))
        path.unlink()
        return code.Sent(True)

    monkeypatch.setattr(code, "send_file", to_the_bin)
    text = "# Rules\r\n\nCafé rule.\n"
    assert code.send_text(text, "codex lines dropped.md") == code.Sent(True)
    [(path, data)] = sent
    assert path.name == "codex lines dropped.md"
    # As written, with its line endings, in UTF-8.
    assert data == text.encode("utf-8")
    assert not path.parent.exists()


def test_text_the_bin_didnt_take_leaves_nothing_behind_either(
    code: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent: list[Path] = []

    def refused(path: Path) -> object:
        sent.append(path)
        return code.Sent(False, "No bin.")

    monkeypatch.setattr(code, "send_file", refused)
    assert code.send_text("# Rules\n", "dropped.md") == code.Sent(False, "No bin.")
    [path] = sent
    assert not path.exists()
    assert not path.parent.exists()


@pytest.mark.parametrize(
    "name",
    ["", ".", "..", "rules/dropped.md", "../dropped.md", "rules:x.md", "dropped?.md", "a\tb.md"],
)
def test_text_needs_a_plain_file_name(code: ModuleType, name: str) -> None:
    # A colon would write to a stream of a file named rules, on NTFS.
    with pytest.raises(ValueError, match="isn't a plain file name"):
        code.send_text("# Rules\n", name)


def test_text_elsewhere_than_windows_isnt_sent_yet(
    code: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(code, "sys", SimpleNamespace(platform="linux"))
    sent = code.send_text("# Rules\n", "dropped.md")
    assert sent == code.Sent(False, "Setup can use the trash only on Windows so far.")


@pytest.mark.parametrize(
    ("text", "name"),
    [
        # A name longer than a file system takes.
        ("# Rules\n", "a" * 300 + ".md"),
        # Text with half of a character, which UTF-8 can't hold.
        ("# Rules \ud800\n", "dropped.md"),
    ],
)
def test_text_that_cant_be_written_is_reported_not_raised(
    code: ModuleType, monkeypatch: pytest.MonkeyPatch, text: str, name: str
) -> None:
    folders: list[Path] = []
    making = code.tempfile.mkdtemp

    def made(**options: str) -> str:
        folders.append(Path(making(**options)))
        return str(folders[-1])

    monkeypatch.setattr(code.tempfile, "mkdtemp", made)
    sent = code.send_text(text, name)
    assert not sent.in_bin
    assert sent.why_not.startswith("Setup couldn't write the text to a file: "), sent
    # Text UTF-8 can't hold fails before any folder is made.
    assert not any(folder.exists() for folder in folders)


def test_data_goes_to_the_bin_byte_for_byte(
    code: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Such as a file saved in another encoding, which isn't UTF-8.
    sent: list[bytes] = []

    def to_the_bin(path: Path) -> object:
        sent.append(path.read_bytes())
        path.unlink()
        return code.Sent(True)

    monkeypatch.setattr(code, "send_file", to_the_bin)
    data = b"\xff\xfe# Rules\r\n\x00caf\xe9\n"
    assert code.send_data(data, "dropped.md") == code.Sent(True)
    assert sent == [data]


def test_a_temporary_folder_that_cant_be_made_is_reported_not_raised(
    code: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    def no_folder(**_options: str) -> str:
        raise PermissionError("no temporary folder on purpose")

    monkeypatch.setattr(code.tempfile, "mkdtemp", no_folder)
    sent = code.send_data(b"# Rules\n", "dropped.md")
    assert sent == code.Sent(
        False,
        "Setup couldn't make a folder in the temporary folder: no temporary folder on purpose",
    )


@windows_only
def test_an_error_while_sending_is_reported_not_raised(
    code: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def broken(_path: Path, _flags: int) -> object:
        raise ValueError("broken on purpose")

    monkeypatch.setattr(code, "delete_in_apartment", broken)
    sent = code.send_file(tmp_path / "dropped.md")
    assert sent == code.Sent(False, "Windows couldn't delete it: broken on purpose")
