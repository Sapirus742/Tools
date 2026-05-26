#!/usr/bin/env python3
"""Find all valid words from the letters of a given word (multi-language)."""

import sys
import argparse
import itertools
import urllib.request
import json
import csv
import io
import pickle
from collections import defaultdict
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent / "data"
RU_RANK_LIMIT = 50000

DICT_URLS = {
    "en": "https://raw.githubusercontent.com/dwyl/english-words/master/words_dictionary.json",
}

RU_CSV_FILES = [
    "https://raw.githubusercontent.com/jenh/russian-dictionary/master/nouns.csv",
    "https://raw.githubusercontent.com/jenh/russian-dictionary/master/verbs.csv",
    "https://raw.githubusercontent.com/jenh/russian-dictionary/master/adjectives.csv",
    "https://raw.githubusercontent.com/jenh/russian-dictionary/master/others.csv",
]

ELEMENTS = [
    "h", "he", "li", "be", "b", "c", "n", "o", "f", "ne",
    "na", "mg", "al", "si", "p", "s", "cl", "ar", "k", "ca",
    "sc", "ti", "v", "cr", "mn", "fe", "co", "ni", "cu", "zn",
    "ga", "ge", "as", "se", "br", "kr", "rb", "sr", "y", "zr",
    "nb", "mo", "tc", "ru", "rh", "pd", "ag", "cd", "in", "sn",
    "sb", "te", "i", "xe", "cs", "ba", "la", "ce", "pr", "nd",
    "pm", "sm", "eu", "gd", "tb", "dy", "ho", "er", "tm", "yb",
    "lu", "hf", "ta", "w", "re", "os", "ir", "pt", "au", "hg",
    "tl", "pb", "bi", "po", "at", "rn", "fr", "ra", "ac", "th",
    "pa", "u", "np", "pu", "am", "cm", "bk", "cf", "es", "fm",
    "md", "no", "lr", "rf", "db", "sg", "bh", "hs", "mt", "ds",
    "rg", "cn", "nh", "fl", "mc", "lv", "ts", "og",
]

RU_VOWELS = set("аеёиоуыэюя")
EN_VOWELS = set("aeiouy")
RU_MAX_CONS = 3
EN_MAX_CONS = 4

PICKLE_CACHE_VERSION = 1


def is_real_word(word: str, lang: str) -> bool:
    if not word or len(word) < 2:
        return False
    if any(ch.isdigit() or ch in "-_" for ch in word):
        return False
    vowels = RU_VOWELS if lang == "ru" else EN_VOWELS
    if not any(ch in vowels for ch in word):
        return False
    max_cons = RU_MAX_CONS if lang == "ru" else EN_MAX_CONS
    streak = 0
    for ch in word:
        if ch not in vowels:
            streak += 1
            if streak > max_cons:
                return False
        else:
            streak = 0
    return True


def download_dict(url: str, path: Path, lang: str) -> dict[str, int]:
    print("Downloading dictionary...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=60)
        text = resp.read().decode("utf-8")
        data = json.loads(text.lower())
        data = {w: 1 for w in data if is_real_word(w, lang)}
        for sym in ELEMENTS:
            data[sym] = 1
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")
        _clear_cache(lang)
        return data
    except Exception as e:
        raise RuntimeError(f"Error downloading dictionary: {e}")


def download_ru_dict(path: Path) -> dict[str, int]:
    words = {}
    local_txt = DATA_DIR / "russian.txt"
    fallback_to_local = False

    try:
        print("Downloading OpenRussian + frequency top dictionary...")
        for url in RU_CSV_FILES:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            resp = urllib.request.urlopen(req, timeout=60)
            reader = csv.DictReader(io.StringIO(resp.read().decode("utf-8")), delimiter="\t")
            for row in reader:
                bare = row.get("bare", "").strip().lower()
                if bare and "/" not in bare and "*" not in bare and is_real_word(bare, "ru"):
                    words[bare] = 0

        hingston_url = "https://raw.githubusercontent.com/hingston/russian/master/100000-russian-words.txt"
        try:
            req = urllib.request.Request(hingston_url, headers={"User-Agent": "Mozilla/5.0"})
            resp = urllib.request.urlopen(req, timeout=60)
            for i, lb in enumerate(resp):
                if i >= RU_RANK_LIMIT:
                    break
                w = lb.decode("utf-8").strip().lower()
                if is_real_word(w, "ru"):
                    if w in words:
                        words[w] = 2
                    else:
                        words[w] = 1
        except Exception:
            pass

        if len(words) < 1000 and local_txt.exists():
            fallback_to_local = True
    except Exception:
        if local_txt.exists():
            fallback_to_local = True
        else:
            raise RuntimeError("Error downloading Russian dictionary")

    if fallback_to_local:
        print("Download failed. Falling back to local russian.txt...")
        raw = local_txt.read_bytes()
        text = decode_fallback(raw)
        words = {}
        for line in text.splitlines():
            w = line.strip().lower()
            if not w:
                continue
            if not is_real_word(w, "ru"):
                continue
            if w in words:
                continue
            if len(w) > 4 or sum(1 for c in w if c in RU_VOWELS) >= 2:
                words[w] = 0

    for sym in ELEMENTS:
        words[sym] = 0

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(words), encoding="utf-8")
    _clear_cache("ru")
    return words


def decode_fallback(raw: bytes) -> str:
    for enc in ("utf-8", "windows-1251", "koi8-r", "cp866"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


def _clear_cache(lang: str):
    for pkl in [DATA_DIR / f"{lang}.lookup.pkl", DATA_DIR / f"{lang}.index.pkl"]:
        try:
            pkl.unlink(missing_ok=True)
        except Exception:
            pass


def load_index(lang: str) -> tuple[dict[str, list[str]], dict[frozenset, list[str]]]:
    json_path = DATA_DIR / f"{lang}.json"
    lookup_pkl = DATA_DIR / f"{lang}.lookup.pkl"
    index_pkl = DATA_DIR / f"{lang}.index.pkl"

    if lookup_pkl.exists() and index_pkl.exists():
        json_mtime = json_path.stat().st_mtime if json_path.exists() else 0
        pkl_mtime = min(lookup_pkl.stat().st_mtime, index_pkl.stat().st_mtime)
        if pkl_mtime >= json_mtime:
            try:
                with open(lookup_pkl, "rb") as f:
                    ver_l, lookup = pickle.load(f)
                with open(index_pkl, "rb") as f:
                    ver_i, index = pickle.load(f)
                if ver_l == PICKLE_CACHE_VERSION and ver_i == PICKLE_CACHE_VERSION:
                    return lookup, index
            except Exception:
                pass

    dictionary = load_dict(lang)
    lookup = build_lookup(dictionary)
    index = build_set_index(lookup)

    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(lookup_pkl, "wb") as f:
            pickle.dump((PICKLE_CACHE_VERSION, lookup), f, protocol=pickle.HIGHEST_PROTOCOL)
        with open(index_pkl, "wb") as f:
            pickle.dump((PICKLE_CACHE_VERSION, index), f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception:
        pass

    return lookup, index


def load_dict(lang: str) -> dict[str, int]:
    path = DATA_DIR / f"{lang}.json"

    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
        vals = list(raw.values())
        if vals and isinstance(vals[0], int):
            if lang == "ru" and any(v not in (0, 1, 2) for v in vals):
                return {w: 0 for w in raw}
            if all(v == 1 for v in vals):
                return {w: 0 for w in raw}
            return raw
        return {w: 0 for w in raw}

    if lang == "ru":
        return download_ru_dict(path)

    url = DICT_URLS.get(lang)
    if url:
        return download_dict(url, path, lang)

    raise ValueError(f"No dictionary available for language: {lang}")


def detect_lang(word: str) -> str:
    for ch in word:
        cp = ord(ch)
        if 0x0430 <= cp <= 0x044F or 0x0410 <= cp <= 0x042F or cp in (0x0451, 0x0401):
            return "ru"
    return "en"


def get_letter_key(word: str) -> str:
    return "".join(sorted(word.lower()))


def build_lookup(words: dict[str, int]) -> dict[str, list[str]]:
    lookup: dict[str, list[str]] = {}
    for word in words:
        key = get_letter_key(word)
        lookup.setdefault(key, []).append(word)
    return lookup


def build_set_index(lookup: dict[str, list[str]]) -> dict[frozenset, list[str]]:
    index: dict[frozenset, list[str]] = {}
    for key in lookup:
        fs = frozenset(key)
        if fs in index:
            index[fs].append(key)
        else:
            index[fs] = [key]
    return index


def is_subset(a_key: str, b_key: str) -> bool:
    ia = ib = 0
    while ia < len(a_key) and ib < len(b_key):
        if a_key[ia] == b_key[ib]:
            ia += 1
        ib += 1
    return ia == len(a_key)


def is_junk_word(word: str) -> bool:
    return len(word) >= 3 and len(set(word)) == 1


def find_words(letters: str, lookup: dict[str, list[str]], set_index: dict[frozenset, list[str]], elem_lookup: dict[str, list[str]], min_len: int = 3, max_len: int = 0, show_elems: bool = True, subset_mode: bool = False, exact_mode: bool = False) -> dict[int, set[str]]:
    letters = letters.lower()
    results = defaultdict(set)
    n = len(letters)
    if not max_len:
        max_len = 999 if subset_mode else n
    input_set = set(letters)
    input_key = "".join(sorted(letters))

    if show_elems:
        for r in range(1, min(3, max_len + 1)):
            for combo in set(itertools.combinations(letters, r)):
                key = "".join(sorted(combo))
                if key in elem_lookup:
                    for w in elem_lookup[key]:
                        results[len(w)].add(w)

    if subset_mode:
        for fs, keys in set_index.items():
            if not input_set.issubset(fs):
                continue
            for key in keys:
                if len(key) < n or len(key) > max_len:
                    continue
                if not is_subset(input_key, key):
                    continue
                for w in lookup[key]:
                    if is_junk_word(w):
                        continue
                    results[len(w)].add(w)
    elif exact_mode:
        for r in range(min_len, min(max_len, n) + 1):
            for combo in set(itertools.combinations(letters, r)):
                key = "".join(sorted(combo))
                if key in lookup:
                    for w in lookup[key]:
                        if is_junk_word(w):
                            continue
                        results[len(w)].add(w)
    else:
        for fs, keys in set_index.items():
            if not fs.issubset(input_set):
                continue
            for key in keys:
                if len(key) < min_len or len(key) > max_len:
                    continue
                for w in lookup[key]:
                    if is_junk_word(w):
                        continue
                    results[len(w)].add(w)

    return dict(results)


def check_cache_status():
    ok = all(
        (DATA_DIR / f"{lang}.lookup.pkl").exists()
        and (DATA_DIR / f"{lang}.index.pkl").exists()
        for lang in ("en", "ru")
    )
    print("[offline]" if ok else "[online]")

def main():
    check_cache_status()
    parser = argparse.ArgumentParser(
        prog="anagram",
        description="Find all valid words from the letters of a given word",
        epilog="Examples:\n  anagram guitar\n  anagram --exact cat\n  anagram --lang ru privet\n  anagram кол --sub --min 2 --max 8",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("word", help="Source word to find anagrams from")
    parser.add_argument("--min", "-m", type=int, default=None, help="Minimum word length (default: 3)")
    parser.add_argument("--max", "-M", type=int, default=0, help="Maximum word length (default: same as input)")
    parser.add_argument("--lang", "-l", choices=["en", "ru"], help="Language (auto-detected by default)")
    parser.add_argument("--all", "-a", action="store_true", help="Show input word in results")
    parser.add_argument("--sub", "-s", action="store_true", help="Find words that CONTAIN all input letters (superset mode)")
    parser.add_argument("--exact", "-e", action="store_true", help="Exact anagrams only (no repetitions)")
    args = parser.parse_args()

    lang = args.lang or detect_lang(args.word)

    try:
        lookup, set_index = load_index(lang)
    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    elem_lookup = {}
    for sym in ELEMENTS:
        key = get_letter_key(sym)
        elem_lookup.setdefault(key, []).append(sym)

    min_len = args.min if args.min is not None else 3
    show_elems = (args.min is None) or (args.min <= 2)
    results = find_words(args.word, lookup, set_index, elem_lookup, min_len, args.max, show_elems, args.sub, args.exact)

    if not results:
        print(f"No words found from '{args.word}'")
        return

    total = sum(len(v) for v in results.values())
    print(f"Found {total} words from '{args.word}':\n")

    for length in sorted(results.keys(), reverse=True):
        words = sorted(results[length])
        if not args.all:
            if length == len(args.word):
                words = [w for w in words if w != args.word.lower()]
                if not words:
                    continue
        print(f"  [{length}] {'  '.join(words)}")


if __name__ == "__main__":
    main()
