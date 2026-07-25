from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

import paramiko


def read_password(use_stdin: bool) -> str:
    if use_stdin:
        return sys.stdin.readline().rstrip("\r\n")
    return getpass.getpass("SSH password: ")


def connect(args: argparse.Namespace, password: str) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=args.host,
        port=args.port,
        username=args.user,
        password=password,
        timeout=args.timeout,
        banner_timeout=args.timeout,
        auth_timeout=args.timeout,
        look_for_keys=False,
        allow_agent=False,
    )
    return client


def run_remote(client: paramiko.SSHClient, command: str) -> int:
    stdin, stdout, stderr = client.exec_command(command)
    stdin.close()
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    if out:
        print(out, end="")
    if err:
        print(err, end="", file=sys.stderr)
    return code


def append_authorized_key(client: paramiko.SSHClient, public_key_file: str) -> None:
    public_key = Path(public_key_file).read_text(encoding="utf-8").strip()
    if not public_key:
        raise ValueError(f"empty public key file: {public_key_file}")

    code = run_remote(
        client,
        "mkdir -p ~/.ssh && chmod 700 ~/.ssh && touch ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys",
    )
    if code != 0:
        raise RuntimeError("failed to prepare ~/.ssh/authorized_keys")

    sftp = client.open_sftp()
    home = sftp.normalize(".")
    auth_path = f"{home}/.ssh/authorized_keys"
    try:
        with sftp.open(auth_path, "r") as handle:
            existing = handle.read().decode("utf-8", errors="replace")
    except OSError:
        existing = ""
    if public_key not in existing:
        with sftp.open(auth_path, "a") as handle:
            if existing and not existing.endswith("\n"):
                handle.write("\n")
            handle.write(public_key + "\n")
    sftp.close()
    print(f"authorized key installed: {Path(public_key_file).name}")


def put_file(client: paramiko.SSHClient, local: str, remote: str) -> None:
    sftp = client.open_sftp()
    remote_parent = str(Path(remote).parent).replace("\\", "/")
    if remote_parent and remote_parent != ".":
        run_remote(client, f"mkdir -p {remote_parent}")
    sftp.put(local, remote)
    sftp.close()
    print(f"uploaded: {local} -> {remote}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Password-based Paramiko helper for SnowCell remote bootstrap")
    parser.add_argument("--host", default="px1-jcy.matpool.com")
    parser.add_argument("--port", type=int, default=27683)
    parser.add_argument("--user", default="root")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--password-stdin", action="store_true")
    subparsers = parser.add_subparsers(dest="command", required=True)

    key_parser = subparsers.add_parser("append-key")
    key_parser.add_argument("--public-key-file", required=True)

    put_parser = subparsers.add_parser("put")
    put_parser.add_argument("--local", required=True)
    put_parser.add_argument("--remote", required=True)

    exec_parser = subparsers.add_parser("exec")
    exec_parser.add_argument("remote_command")

    args = parser.parse_args()
    password = read_password(args.password_stdin)
    client = connect(args, password)
    try:
        if args.command == "append-key":
            append_authorized_key(client, args.public_key_file)
        elif args.command == "put":
            put_file(client, args.local, args.remote)
        elif args.command == "exec":
            raise SystemExit(run_remote(client, args.remote_command))
    finally:
        client.close()


if __name__ == "__main__":
    main()
