# m3u_validator

Utilities to fetch, normalize, deduplicate, and validate IPTV M3U playlists.

## Setup

```bash
python3 -m pip install -r requirements.txt
```

## Generate Playlists

```bash
./autorun.sh
```

Windows:

```bat
autorun.bat
```

## Run Tests

```bash
python3 -m unittest discover -s tests -q
```

Optional (if `pytest` is installed):

```bash
pytest
```
