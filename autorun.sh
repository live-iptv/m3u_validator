#!/bin/bash

script_dir="$(cd "$(dirname "$0")" && pwd)"

echo "$script_dir"

python3 -m pip install requests

cd "$script_dir/scripts/" || exit 1

update_m3u() {
    local script_name="$1"
    local output_name="$2"
    local tmp_file

    tmp_file="$(mktemp "${TMPDIR:-/tmp}/${output_name}.XXXXXX")" || return 1

    if python3 "$script_name" > "$tmp_file" && [ -s "$tmp_file" ]; then
        mv "$tmp_file" "../$output_name"
    else
        rm -f "$tmp_file"
    fi
}

# update_m3u "malayalam_m3u.py" "malayalam_m3u.m3u"
# update_m3u "tamil_m3u.py" "tamil_m3u.m3u"
# update_m3u "tamil_local_json.py" "tamil_local_json.m3u"
update_m3u "malayalam_local_json.py" "malayalam_local_json.m3u"
# update_m3u "xxx_m3u.py" "xxx_m3u.m3u"
# update_m3u "movies_m3u.py" "movies_m3u.m3u"
# update_m3u "test_m3u.py" "test_m3u.m3u"

echo m3u grabbed
