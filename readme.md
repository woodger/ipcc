# IPCC — Aggregated Country CIDR Generator

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](#)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](#)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](#)

**IPCC** is a program for generating aggregated CIDR blocks by country based on official data from Regional Internet Registries (RIRs).

It supports **IPv4 and IPv6** and can automatically merge adjacent networks.


## Overview

* Generates CIDR blocks by country (ISO 3166-1 alpha-2)
* Supports IPv4 and IPv6
* Automatically collapses adjacent networks (`collapse`)
* Uses RIR data:

  * RIPE NCC
  * ARIN
  * APNIC
  * LACNIC
  * AFRINIC

## Architecture

```
.
├── app
│   ├── __init__.py
│   ├── args.py      # CLI arguments
│   └── ipcc.py      # programm
├── tests
│   ├── test_ipcc.py
│   └── test_args.py
├── pyproject.toml
└── README.md
```

## Usage

Generate USA IPv4:

```bash
./ipcc --country US --output ~/us.zone
```

The program will download RIR data, select networks of the specified country, merge adjacent CIDRs, and save the result to a file.

If any RIR download fails, the command exits without writing the output so that a partial list is never presented as complete.


## Testing

To run tests, use **pytest**:

```bash
pytest
```

Все тесты проходят, что гарантирует корректность парсинга и объединения сетей.


## CLI Reference

| Option      | Description      | Default          |
| ----------- | ---------------- | ---------------- |
| `--country` | ISO country code | RU               |
| `--ipv6`    | Use IPv6         | false            |
| `--output`  | Output file name | `<country>.zone` |

## Output Format

Plain text CIDR list:

```
5.8.0.0/13
5.16.0.0/12
31.128.0.0/10
```

---

## License

MIT License
