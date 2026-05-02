"""Read and write self-improve setup state."""

import argparse
import json
import os
import subprocess


STATE_PATH = os.path.expanduser("~/.si-state.json")
IMPORT_MARKER = "<!-- SI:IMPORT:START -->"


def resolve_claude_root():
    for cmd in (["readlink", "-f", os.path.expanduser("~/.claude")], ["realpath", os.path.expanduser("~/.claude")]):
        try:
            result = subprocess.check_output(cmd, text=True).strip()
        except Exception:
            continue
        if result:
            return result
    return os.path.expanduser("~/.claude")


def build_state():
    claude_root = resolve_claude_root()
    claude_md = os.path.join(claude_root, "CLAUDE.md")
    claude_si_md = os.path.join(claude_root, "CLAUDE-si.md")
    skills_dir = os.path.join(claude_root, "skills")
    import_wired = False
    if os.path.exists(claude_md):
        with open(claude_md) as f:
            import_wired = IMPORT_MARKER in f.read()

    return {
        "setup_complete": os.path.exists(claude_si_md) and import_wired,
        "claude_root": claude_root,
        "claude_md": claude_md,
        "claude_si_md": claude_si_md,
        "skills_dir": skills_dir,
        "import_wired": import_wired,
    }


def write_state():
    state = build_state()
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")
    return state


def read_state():
    if not os.path.exists(STATE_PATH):
        return None
    with open(STATE_PATH) as f:
        return json.load(f)


def print_status():
    state = read_state()
    if not state or not state.get("setup_complete"):
        print("missing")
        return 1
    print("ok")
    print(json.dumps(state))
    return 0


def reset_state():
    if os.path.exists(STATE_PATH):
        os.remove(STATE_PATH)
        print(f"Removed: {STATE_PATH}")
    else:
        print(f"Not found (skipped): {STATE_PATH}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("status", "write", "reset"))
    args = parser.parse_args()

    if args.command == "status":
        raise SystemExit(print_status())
    if args.command == "write":
        print(json.dumps(write_state(), indent=2))
        return
    reset_state()


if __name__ == "__main__":
    main()
