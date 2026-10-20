# netcalc

A small command-line subnet calculator for IPv4 and IPv6, written in pure Python with **zero third-party dependencies**.

## Description

`netcalc` answers the questions a network engineer asks every day: what is the broadcast address of this block, how many usable hosts does it hold, where do I cut it into smaller subnets, and does this address belong to that network?

It is built entirely on Python's standard-library `ipaddress` module, so there is nothing to install beyond Python itself. The logic lives in a small, pure-function core (`netcalc.core`) that you can import into your own scripts, with a thin `argparse` CLI on top (`netcalc.cli`).

**Features**

- `info` — full breakdown of a network: network address, netmask, wildcard, broadcast, host range, usable host count, private/public.
- `split` — cut a network into subnets of a given prefix length, generated lazily so a `/8` into `/30`s does not exhaust memory.
- `check` — test whether an address falls inside a network, with a shell-friendly exit code.
- `--json` on every command, for piping into other tools.
- Correct edge cases: `/31` point-to-point links (RFC 3021), `/32` host routes, and IPv6 (no broadcast address).

## Installation

**Requirements:** Python 3.8 or newer. No other dependencies.

```bash
# 1. Clone the repository
git clone https://github.com/Abd-alrhmaan/netcalc.git
cd netcalc

# 2. Install it (editable mode, so your edits take effect immediately)
pip install -e .
```

This puts a `netcalc` command on your `PATH`. If you would rather not install anything, you can run the package straight from the project folder:

```bash
python -m netcalc info 192.168.10.0/24
```

Using a virtual environment is recommended:

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e .
```

## Usage

### `info` — inspect a network

Host bits are masked off automatically, so you can paste an interface address as-is:

```console
$ netcalc info 192.168.10.77/26
network          192.168.10.64
prefix length    26
cidr             192.168.10.64/26
netmask          255.255.255.192
version          4
first host       192.168.10.65
last host        192.168.10.126
total addresses  64
usable hosts     62
is private       True
wildcard         0.0.0.63
broadcast        192.168.10.127
```

### `split` — divide a network into subnets

```console
$ netcalc split 192.168.10.0/24 26
192.168.10.0/26
192.168.10.64/26
192.168.10.128/26
192.168.10.192/26
```

Output is capped at 64 subnets by default. Use `--limit N` to raise the cap, or `--limit 0` to remove it.

### `check` — does this address belong to this network?

```console
$ netcalc check 192.168.10.0/24 192.168.10.50
192.168.10.50 is inside 192.168.10.0/24
$ echo $?
0
```

The exit code is `0` when the address is inside and `1` when it is not, so the command drops straight into a shell script:

```bash
if netcalc check 10.0.0.0/8 "$CLIENT_IP" > /dev/null; then
    echo "client is on the internal network"
fi
```

### JSON output

`--json` is a global flag, so it goes **before** the subcommand:

```console
$ netcalc --json info 10.10.0.0/22
{
  "network": "10.10.0.0",
  "prefix_length": 22,
  "cidr": "10.10.0.0/22",
  "netmask": "255.255.252.0",
  "version": 4,
  "first_host": "10.10.0.1",
  "last_host": "10.10.3.254",
  "total_addresses": 1024,
  "usable_hosts": 1022,
  "is_private": true,
  "wildcard": "0.0.3.255",
  "broadcast": "10.10.3.255"
}
```

Pipe it into `jq` to pull out a single field:

```bash
netcalc --json info 10.10.0.0/22 | jq -r '.usable_hosts'
```

### Using it as a library

```python
from netcalc import parse_network, summarize, split

net = parse_network("172.16.0.0/16")
print(summarize(net)["usable_hosts"])        # 65534

for subnet in split(net, 20):
    print(subnet)                            # 172.16.0.0/20, 172.16.16.0/20, ...
```

## Running the tests

```bash
python -m unittest discover -s tests -v
```

The suite covers parsing, host counting, `/31` and `/32` edge cases, IPv6, lazy splitting, and error handling.

## Project layout

```
netcalc/
├── netcalc/
│   ├── __init__.py     # public API re-exports
│   ├── __main__.py     # enables `python -m netcalc`
│   ├── core.py         # pure calculation functions
│   └── cli.py          # argparse command-line interface
├── tests/
│   └── test_core.py
├── pyproject.toml
├── LICENSE
└── README.md
```

## Contributing

Pull requests are welcome. Please keep the core dependency-free, and add a unit test alongside any new behaviour.

1. Fork the repository and create a branch: `git checkout -b feature/my-change`
2. Make your change and run `python -m unittest discover -s tests`
3. Commit, push, and open a pull request describing what changed and why.

## Contributors

| Contributor | Role |
| --- | --- |
| **Abdalrhman Ahmed Mohammedelhasen Khalifa** ([@Abd-alrhmaan](https://github.com/Abd-alrhmaan)) | Author — core logic, CLI, tests, documentation |

Built as a documentation and tooling exercise for a Computer Engineering course at Al-Neelain University. Thanks to the Python core developers for the `ipaddress` module, which does the arithmetic this tool is wrapped around.

## License

Released under the MIT License — see [LICENSE](LICENSE).
