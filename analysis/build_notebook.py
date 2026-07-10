import re, base64, gzip, json, os

HTML = r'C:\Users\ericc\projects\Paper BFG\simulation\bfg_v6_50-50_ecm80.html'
OUT  = r'C:\Users\ericc\projects\Paper BFG\analysis\BFG_Simulation_v6.ipynb'

with open(HTML, encoding='utf-8') as f:
    content = f.read()

dict_match  = re.search(r'(?:const|let|var)\s+DICT_B64\s*=\s*"(.*?)"\s*;', content, re.DOTALL)
seeds_match = re.search(r'(?:const|let|var)\s+SEEDS\s*=\s*(\[.*?\])\s*;', content, re.DOTALL)
tgts_match  = re.search(r'(?:const|let|var)\s+TARGETS_RAW\s*=\s*(\[.*?\])\s*;', content, re.DOTALL)

seeds    = json.loads(seeds_match.group(1))
targets  = json.loads(tgts_match.group(1))
dict_b64 = dict_match.group(1)

print(f"Seeds: {len(seeds)}, Targets: {len(targets)}, Dict B64: {len(dict_b64)} chars")

seeds_repr   = json.dumps(seeds, indent=4)
targets_repr = json.dumps(targets, indent=4)

# ── Cell sources ──────────────────────────────────────────────────────────────

cell1 = [
    "# Cell 1 -- Install dependencies and environment check\n",
    "!pip install rapidfuzz -q\n",
    "import sys, os, multiprocessing\n",
    "print(f'Python {sys.version}')\n",
    "print(f'CPU cores available: {os.cpu_count()}')\n",
    "print(f'multiprocessing start method: {multiprocessing.get_start_method()}')\n"
]

cell2 = [
    "# Cell 2 -- Simulation core\n",
    "import random\n",
    "from collections import defaultdict\n",
    "from rapidfuzz.distance import Levenshtein as _lev\n",
    "\n",
    "VALID_CHARS = list(\"abcdefghijklmnopqrstuvwxyz-'\")\n",
    "BASE_RATES  = {'sub': 0.02, 'del': 0.004, 'ins': 0.004, 'sd': 0.02, 'si': 0.004}\n",
    "SIMILARITY_THRESHOLD = 0.80  # ECM dictionary match threshold\n",
    "\n",
    "def levenshtein(a, b):\n",
    "    return _lev.distance(a, b)\n",
    "\n",
    "def get_trigrams(w):\n",
    "    n = 2 if len(w) < 3 else 3\n",
    "    p = ' ' + w + ' '\n",
    "    return [p[i:i+n] for i in range(len(p) - n + 1)]\n",
    "\n",
    "def mutate(s, scalar):\n",
    "    ps  = BASE_RATES['sub'] * scalar\n",
    "    pd  = BASE_RATES['del'] * scalar\n",
    "    pi  = BASE_RATES['ins'] * scalar\n",
    "    psd = BASE_RATES['sd']  * scalar\n",
    "    psi = BASE_RATES['si']  * scalar\n",
    "    out = []\n",
    "    for c in s:\n",
    "        is_alpha = c.islower() or c in ('-', \"'\")\n",
    "        if is_alpha:\n",
    "            if random.random() >= pd:\n",
    "                out.append(random.choice(VALID_CHARS) if random.random() < ps else c)\n",
    "        elif c == ' ':\n",
    "            if random.random() >= psd:\n",
    "                out.append(c)\n",
    "        else:\n",
    "            out.append(c)\n",
    "        if random.random() < pi:\n",
    "            out.append(random.choice(VALID_CHARS))\n",
    "        if random.random() < psi:\n",
    "            out.append(' ')\n",
    "    return ''.join(out)\n",
    "\n",
    "_correction_cache = {}\n",
    "\n",
    "def correct_word(w, word_set, tg_idx):\n",
    "    if not w or len(w) < 2: return w\n",
    "    if w in word_set: return w\n",
    "    if w in _correction_cache:\n",
    "        cands = _correction_cache[w]\n",
    "        return random.choice(cands) if cands else w\n",
    "    wtgs = set(get_trigrams(w))\n",
    "    cand_count = defaultdict(int)\n",
    "    for tg in wtgs:\n",
    "        if tg in tg_idx:\n",
    "            for cw in tg_idx[tg]:\n",
    "                cand_count[cw] += 1\n",
    "    n = len(w)\n",
    "    results = []\n",
    "    for cw in cand_count:\n",
    "        lmax = max(n, len(cw))\n",
    "        if (lmax - abs(n - len(cw))) / lmax < SIMILARITY_THRESHOLD: continue\n",
    "        d = levenshtein(w, cw)\n",
    "        sim = (lmax - d) / lmax\n",
    "        if sim >= SIMILARITY_THRESHOLD:\n",
    "            results.append((sim, cw))\n",
    "    results.sort(reverse=True)\n",
    "    cands = [cw for _, cw in results[:10]]\n",
    "    if len(_correction_cache) > 60000: _correction_cache.clear()\n",
    "    _correction_cache[w] = cands if cands else None\n",
    "    return random.choice(cands) if cands else w\n",
    "\n",
    "def correct(s, word_set, tg_idx):\n",
    "    return ' '.join(correct_word(w, word_set, tg_idx) if w else w for w in s.split(' '))\n",
    "\n",
    "def fitness(s, targets):\n",
    "    sw = set(s.split())\n",
    "    best = 0.0\n",
    "    for ts, tset in targets:\n",
    "        lmax = max(len(s), len(ts))\n",
    "        lsc  = (lmax - levenshtein(s, ts)) / lmax if lmax else 1.0\n",
    "        sh   = sum(1 for w in sw if w in tset)\n",
    "        wmax = max(len(sw), len(tset))\n",
    "        wsc  = sh / wmax if wmax else 1.0\n",
    "        v    = (wsc + lsc) / 2\n",
    "        if v > best: best = v\n",
    "    return best\n",
    "\n",
    "def run_one(run_id, scalar, use_ecm, targets, seeds, word_set, tg_idx,\n",
    "            pop_size=1000, n_children=10, max_gens=500,\n",
    "            exit_fit=0.99, exit_count=1000):\n",
    "    pop = list(seeds)\n",
    "    cache = {}\n",
    "    rows = []\n",
    "    def gf(s):\n",
    "        if s not in cache: cache[s] = fitness(s, targets)\n",
    "        return cache[s]\n",
    "    for g in range(max_gens):\n",
    "        offspring = []\n",
    "        for parent in pop:\n",
    "            for _ in range(n_children):\n",
    "                child = mutate(parent, scalar)\n",
    "                if use_ecm:\n",
    "                    child = correct(child, word_set, tg_idx)\n",
    "                offspring.append(child)\n",
    "        offspring.sort(key=gf, reverse=True)\n",
    "        pop = offspring[:pop_size]\n",
    "        fits = [gf(s) for s in pop]\n",
    "        mean_fit = sum(fits) / len(fits)\n",
    "        n_full   = sum(1 for f in fits if f >= exit_fit)\n",
    "        rows.append({\n",
    "            'run_id': run_id, 'generation': g,\n",
    "            'mutation_scalar': scalar, 'use_ecm': 1 if use_ecm else 0,\n",
    "            'mean_fitness': round(mean_fit, 5), 'max_fitness': round(fits[0], 5),\n",
    "            'n_full_fit': n_full\n",
    "        })\n",
    "        if n_full >= exit_count: break\n",
    "        if g >= 3 and len(set(pop)) == 1: break\n",
    "    cache.clear()\n",
    "    return rows\n",
    "\n",
    "print('Simulation core loaded.')\n"
]

cell3 = (
    ["# Cell 3 -- Load data (seeds, targets, dictionary + trigram index)\n",
     "import base64, gzip\n",
     "from collections import defaultdict\n",
     "\n",
     "SEEDS = " + seeds_repr + "\n",
     "\n",
     "TARGETS_RAW = " + targets_repr + "\n",
     "\n",
     "targets_proc = [(t, set(t.split())) for t in TARGETS_RAW]\n",
     "\n"] +
    ['_DICT_B64 = "' + dict_b64 + '"\n'] +
    ["\n",
     '_raw  = base64.b64decode(_DICT_B64)\n',
     '_text = gzip.decompress(_raw).decode("utf-8")\n',
     'WORD_SET = set(w for w in _text.split("\\n") if w)\n',
     "\n",
     "def _get_tg(w):\n",
     "    n = 2 if len(w) < 3 else 3\n",
     "    p = ' ' + w + ' '\n",
     "    return [p[i:i+n] for i in range(len(p) - n + 1)]\n",
     "\n",
     "TG_IDX = defaultdict(list)\n",
     "for _w in WORD_SET:\n",
     "    for _tg in _get_tg(_w):\n",
     "        TG_IDX[_tg].append(_w)\n",
     "TG_IDX = dict(TG_IDX)\n",
     "\n",
     'print(f"Seeds:    {len(SEEDS)} sentences")\n',
     'print(f"Targets:  {len(targets_proc)} sentences")\n',
     'print(f"Dict:     {len(WORD_SET):,} words")\n',
     'print(f"Trigrams: {len(TG_IDX):,} entries")\n',
     'print("Ready.")\n']
)

cell4 = [
    "# Cell 4 -- Run simulation (multiprocessing, 2 workers)\n",
    "# Saves to Google Drive after every completed run. Resume-safe: skips already-completed runs.\n",
    "import multiprocessing, time, csv, os\n",
    "from google.colab import drive\n",
    "drive.mount('/content/drive')\n",
    "\n",
    "SCALARS    = [0.25, 0.5, 1.0, 1.5]\n",
    "N_RUNS     = 10\n",
    "POP_SIZE   = 1000\n",
    "N_CHILDREN = 10\n",
    "MAX_GENS   = 1000\n",
    "EXIT_FIT   = 0.99999\n",
    "EXIT_COUNT = 1000\n",
    'SAVE_PATH  = "/content/drive/MyDrive/BFG_Replication_v6_50-50_ecm80_full.csv"\n',
    "FIELDNAMES = ['run_id','generation','mutation_scalar','use_ecm',\n",
    "               'mean_fitness','max_fitness','n_full_fit']\n",
    "\n",
    "def _worker(args):\n",
    "    scalar, use_ecm, run_idx = args\n",
    "    run_id = f's{scalar}_ecm{int(use_ecm)}_{run_idx:02d}'\n",
    "    return run_one(\n",
    "        run_id, scalar, use_ecm,\n",
    "        targets_proc, SEEDS, WORD_SET, TG_IDX,\n",
    "        pop_size=POP_SIZE, n_children=N_CHILDREN, max_gens=MAX_GENS,\n",
    "        exit_fit=EXIT_FIT, exit_count=EXIT_COUNT\n",
    "    )\n",
    "\n",
    "jobs = [\n",
    "    (scalar, use_ecm, run_idx)\n",
    "    for scalar  in SCALARS\n",
    "    for use_ecm in [True, False]\n",
    "    for run_idx in range(N_RUNS)\n",
    "]\n",
    "\n",
    "# Resume: find already-completed run_ids on Drive\n",
    "completed = set()\n",
    "if os.path.exists(SAVE_PATH):\n",
    "    with open(SAVE_PATH, newline='') as f:\n",
    "        for row in csv.DictReader(f):\n",
    "            completed.add(row['run_id'])\n",
    '    print(f"Resuming -- {len(completed)} run_ids already on Drive")\n',
    "else:\n",
    "    with open(SAVE_PATH, 'w', newline='') as f:\n",
    "        csv.DictWriter(f, fieldnames=FIELDNAMES).writeheader()\n",
    '    print("Starting fresh -- header written to Drive")\n',
    "\n",
    "remaining = [(sc, ecm, idx) for sc, ecm, idx in jobs\n",
    "             if f's{sc}_ecm{int(ecm)}_{idx:02d}' not in completed]\n",
    'print(f"{len(remaining)} runs remaining (of {len(jobs)} total)")\n',
    "\n",
    "t0 = time.time()\n",
    "all_rows = []\n",
    "\n",
    "with multiprocessing.Pool(processes=2) as pool:\n",
    "    for i, result in enumerate(pool.imap_unordered(_worker, remaining), 1):\n",
    "        all_rows.extend(result)\n",
    "        with open(SAVE_PATH, 'a', newline='') as f:\n",
    "            csv.DictWriter(f, fieldnames=FIELDNAMES).writerows(result)\n",
    "        elapsed = time.time() - t0\n",
    '        print(f"  [{i}/{len(remaining)}] done -- {elapsed/60:.1f} min elapsed", flush=True)\n',
    "\n",
    'print(f"\\nComplete. {len(all_rows):,} new rows. {(time.time()-t0)/60:.1f} min.")\n',
    'print(f"Results saved to Drive: {SAVE_PATH}")\n',
]

cell5 = [
    "# Cell 5 -- Download completed CSV from Drive\n",
    "from google.colab import files\n",
    "files.download(SAVE_PATH)\n",
    'print(f"Download triggered for {SAVE_PATH}")\n',
]

def make_cell(src):
    return {"cell_type": "code", "execution_count": None,
            "metadata": {}, "outputs": [], "source": src}

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12.0"},
        "colab": {"name": "BFG_Simulation_v6.ipynb", "provenance": []}
    },
    "cells": [make_cell(cell1), make_cell(cell2), make_cell(cell3),
               make_cell(cell4), make_cell(cell5)]
}

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

size = os.path.getsize(OUT)
print(f"Written: {OUT}")
print(f"Size: {size/1024:.0f} KB")
