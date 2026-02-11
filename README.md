# d00r

<img src="https://img.shields.io/badge/-Python-black?style=for-the-badge&logo=python&logoColor=white"> <img src="https://img.shields.io/badge/-Terminal-black?style=for-the-badge&logo=GNU%20Bash&logoColor=white">

```text
      _  ___   ___
     | |/ _ \ / _ \\
   __| | | | | | | |_ __
  / _` | | | | | | | '__|
 | (_| | |_| | |_| | |
  \__,_|\___/ \___/|_|    v1.3.1 by CYB3RMX, extension by sultanjke
  
>> URL Brute-Force Tool
```

Fork of [`CYB3RMX/d00r`](https://github.com/CYB3RMX/d00r), extended for Ejudge.kz contest discovery workflows.

This version supports both:
- normal directory/path brute-force
- Ejudge query brute-force with `contest_id` URLs like:
  - `https://ejudge.kz/new-client?contest_id=<number>`

## Ejudge Logic

Ejudge can return HTTP `200` for both valid and invalid contest IDs.
This fork classifies by `<title>` and page content:

- `Error: Invalid contest`:
  - treated as non-existing/invalid contest
  - printed in red in terminal
- `User login page ...`:
  - recorded as login/lab/practice candidate
- `Permission denied`:
  - recorded as restricted quiz/exam candidate
  - attempts to extract contest name from HTML row:
    - `<td>Contest:</td><td>...</td>`

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Ejudge contest_id brute-force

```bash
python d00r.py --url "https://ejudge.kz/new-client?contest_id=" --wordlist wordlist.txt --status 200 --thread 100
```

### Directory brute-force

```bash
python d00r.py --url "https://example.com/" --wordlist wordlist.txt --status 200 301 403 --thread 50
```

### Optional install mode

```bash
python d00r.py --install
```

## Arguments

- `--url`: target base URL
- `--wordlist`: wordlist file (one entry per line)
- `--status`: status filter (example: `200 301 403`)
- `--thread`: thread count
- `--install`: install launcher script (`d00r.bat` on Windows)

## Report Output

Examples:
- `https://ejudge.kz/new-client?contest_id=1 | User login page [PP1 Lab 1]`
- `https://ejudge.kz/new-client?contest_id=213 | Contest: PP1 Credit-by-Exam | []: Permission denied`

## Credits

- Original project: [`CYB3RMX/d00r`](https://github.com/CYB3RMX/d00r)
- This fork: Ejudge.kz-oriented detection, extraction, and reporting improvements.
- Educational-case use.
