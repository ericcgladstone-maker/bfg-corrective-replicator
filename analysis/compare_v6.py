import re, csv, sys
from collections import defaultdict

def get_h_gridlines(panel):
    path_file = f'C:/Users/ericc/projects/Paper BFG/figures/Figure 1, Panel {panel}.svg'
    with open(path_file) as f:
        content = f.read()
    lines_el = re.findall(r'<line([^>]+)/>', content)
    h_lines = set()
    for l in lines_el:
        x1 = re.search(r'x1="([^"]+)"', l)
        y1 = re.search(r'y1="([^"]+)"', l)
        y2 = re.search(r'y2="([^"]+)"', l)
        if x1 and abs(float(y1.group(1)) - float(y2.group(1))) < 0.5 and abs(float(x1.group(1)) - 390.8) < 2:
            h_lines.add(round(float(y1.group(1)), 1))
    return sorted(h_lines)

def get_path_points(panel):
    path_file = f'C:/Users/ericc/projects/Paper BFG/figures/Figure 1, Panel {panel}.svg'
    with open(path_file) as f:
        content = f.read()
    full_paths = re.findall(r'<path([^>]+)/?>', content)
    result = []
    for p in full_paths:
        d_match = re.search(r'd="([^"]+)"', p)
        stroke_match = re.search(r'stroke[=:]#?([0-9a-fA-F]{6})', p)
        if d_match and stroke_match:
            coords = re.findall(r'[ML]\s*([\d.]+)\s+([\d.]+)', d_match.group(1))
            result.append({'color': stroke_match.group(1).upper(), 'pts': [(float(x), float(y)) for x, y in coords]})
    return result

x_min = 454.04; x_max = 3795.66

def make_ymap(grid, y_vals):
    svg_lo = max(grid[:len(y_vals)])
    svg_hi = min(grid[:len(y_vals)])
    val_lo = y_vals[0]
    val_hi = y_vals[-1]
    def convert(svg_y):
        return val_lo + (svg_lo - svg_y) / (svg_lo - svg_hi) * (val_hi - val_lo)
    return convert

grid_A = get_h_gridlines('A')[:5]
yA = make_ymap(grid_A, [0.4, 0.6, 0.8, 1.0, 1.2])
def xAB(svg_x): return (svg_x - x_min)/(x_max - x_min)*200

grid_B = get_h_gridlines('B')[:5]
yB = make_ymap(grid_B, [-200, 0, 200, 400, 600])

grid_C = get_h_gridlines('C')[:6]
yC = make_ymap(grid_C, [0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
def xCD(svg_x): return (svg_x - x_min)/(x_max - x_min)*2.0

grid_D = get_h_gridlines('D')[:6]
yD = make_ymap(grid_D, [-400, -200, 0, 200, 400, 600])

def extract_panel(panel, x_fn, y_fn):
    paths = get_path_points(panel)
    blue = [p for p in paths if p['color'] == '1A476F'][0]
    red  = [p for p in paths if p['color'] == '90353B'][0]
    result = []
    for (bx, by), (rx, ry) in zip(blue['pts'], red['pts']):
        result.append({'x': x_fn(bx), 'noecm': y_fn(by), 'ecm': y_fn(ry)})
    return result

pA = extract_panel('A', xAB, yA)
pB = extract_panel('B', xAB, yB)
pC = extract_panel('C', xCD, yC)
pD = extract_panel('D', xCD, yD)

fname = 'C:/Users/ericc/projects/Paper BFG/data/v6/BFG_Replication_v6_50-50_ecm80_full_1.csv'
all_rows = list(csv.DictReader(open(fname)))

runs_final = {}
for row in all_rows:
    runs_final[row['run_id']] = row

gen_pool = defaultdict(lambda: {'ecm_mf': [], 'noecm_mf': [], 'ecm_nff': [], 'noecm_nff': []})
for row in all_rows:
    g = int(row['generation'])
    if row['use_ecm'] == '1':
        gen_pool[g]['ecm_mf'].append(float(row['mean_fitness']))
        gen_pool[g]['ecm_nff'].append(int(row['n_full_fit']))
    else:
        gen_pool[g]['noecm_mf'].append(float(row['mean_fitness']))
        gen_pool[g]['noecm_nff'].append(int(row['n_full_fit']))

def avg(lst): return sum(lst)/len(lst) if lst else None

# Panel A
print("="*80)
print("PANEL A: Mean Fitness vs Generation (pooled across all scalars)")
print("="*80)
print(f"{'gen':>5} | {'paper_noECM':>12} | {'paper_ECM':>11} | {'v6_noECM':>10} | {'v6_ECM':>8} | {'n_runs':>7}")
print("-"*72)
highlight_gens = {0,10,20,30,40,50,60,80,100,120,150,200}
for r in pA:
    g = int(round(r['x']))
    if g not in highlight_gens: continue
    pool = gen_pool[g]
    v6n = avg(pool['noecm_mf'])
    v6e = avg(pool['ecm_mf'])
    n = len(pool['noecm_mf'])
    print(f"{g:>5} | {r['noecm']:>12.4f} | {r['ecm']:>11.4f} | {(v6n or 0):>10.4f} | {(v6e or 0):>8.4f} | {n:>7}")

print()
print("="*80)
print("PANEL B: Fitted Count of Fully-Fit Replicators vs Generation (pooled)")
print("="*80)
print(f"{'gen':>5} | {'paper_noECM':>12} | {'paper_ECM':>11} | {'v6_noECM':>10} | {'v6_ECM':>8}")
print("-"*65)
for r in pB:
    g = int(round(r['x']))
    if g not in highlight_gens: continue
    pool = gen_pool[g]
    v6n = avg(pool['noecm_nff'])
    v6e = avg(pool['ecm_nff'])
    print(f"{g:>5} | {r['noecm']:>12.1f} | {r['ecm']:>11.1f} | {(v6n or 0):>10.1f} | {(v6e or 0):>8.1f}")

# Build scalar-level final data
scalar_finals_mf  = defaultdict(lambda: {'ecm': [], 'noecm': []})
scalar_finals_nff = defaultdict(lambda: {'ecm': [], 'noecm': []})
for rid, row in runs_final.items():
    s = float(row['mutation_scalar'])
    if row['use_ecm'] == '1':
        scalar_finals_mf[s]['ecm'].append(float(row['mean_fitness']))
        scalar_finals_nff[s]['ecm'].append(int(row['n_full_fit']))
    else:
        scalar_finals_mf[s]['noecm'].append(float(row['mean_fitness']))
        scalar_finals_nff[s]['noecm'].append(int(row['n_full_fit']))

print()
print("="*80)
print("PANEL C: Final Mean Fitness by Scalar Mutation Rate")
print("="*80)
print(f"{'scalar':>8} | {'paper_noECM':>12} | {'paper_ECM':>11} | {'v6_noECM':>10} | {'v6_ECM':>8} | direction match?")
print("-"*80)
target_scalars = [0.25, 0.5, 1.0, 1.5]
for r in pC:
    s = round(r['x'], 2)
    if s not in target_scalars: continue
    v6n = avg(scalar_finals_mf[s]['noecm'])
    v6e = avg(scalar_finals_mf[s]['ecm'])
    p_dir = 'ECM>' if r['ecm'] > r['noecm'] else 'noECM>'
    v6_dir = 'ECM>' if (v6e and v6n and v6e > v6n) else 'noECM>'
    match = 'YES' if p_dir == v6_dir else 'NO **'
    print(f"{s:>8.2f} | {r['noecm']:>12.4f} | {r['ecm']:>11.4f} | {v6n:>10.4f} | {v6e:>8.4f} | {p_dir:8} {match} ({v6_dir})")

print()
print("="*80)
print("PANEL D: Final Fully-Fit Replicator Count by Scalar")
print("="*80)
print(f"{'scalar':>8} | {'paper_noECM':>12} | {'paper_ECM':>11} | {'v6_noECM':>10} | {'v6_ECM':>8} | direction match?")
print("-"*80)
for r in pD:
    s = round(r['x'], 2)
    if s not in target_scalars: continue
    v6n = avg(scalar_finals_nff[s]['noecm'])
    v6e = avg(scalar_finals_nff[s]['ecm'])
    p_dir = 'ECM>' if r['ecm'] > r['noecm'] else 'noECM>'
    v6_dir = 'ECM>' if (v6e is not None and v6n is not None and v6e > v6n) else 'noECM>'
    match = 'YES' if p_dir == v6_dir else 'NO **'
    print(f"{s:>8.2f} | {r['noecm']:>12.1f} | {r['ecm']:>11.1f} | {v6n:>10.1f} | {v6e:>8.1f} | {p_dir:8} {match} ({v6_dir})")

print()
print("="*80)
print("EARLY ADVANTAGE CHECK: Is no-ECM ahead of ECM in early generations?")
print("(Paper: no-ECM leads ECM prior to ~gen 30, then ECM takes over)")
print("="*80)
early_gens = sorted([g for g in gen_pool.keys() if g <= 60])
print(f"{'gen':>5} | {'v6_noECM':>10} | {'v6_ECM':>8} | {'leader':>10} | {'ECM_lead':>10}")
print("-"*55)
crossover = None
for g in early_gens:
    pool = gen_pool[g]
    v6n = avg(pool['noecm_mf'])
    v6e = avg(pool['ecm_mf'])
    if v6n is None or v6e is None: continue
    leader = 'ECM' if v6e > v6n else 'noECM'
    diff = (v6e - v6n) if v6e and v6n else 0
    if crossover is None and v6e > v6n and g > 0:
        crossover = g
    print(f"{g:>5} | {v6n:>10.4f} | {v6e:>8.4f} | {leader:>10} | {diff:>+10.4f}")
if crossover:
    print(f"\nECM takes lead at generation: {crossover} (paper: ~gen 30)")

print()
print("="*80)
print("CONVERGENCE SUMMARY by condition")
print("="*80)
cond_data = defaultdict(list)
for rid, row in runs_final.items():
    s = float(row['mutation_scalar'])
    ecm = int(row['use_ecm'])
    gen = int(row['generation'])
    nff = int(row['n_full_fit'])
    cond_data[(s, ecm)].append({'gen': gen, 'nff': nff})

print(f"{'scalar':>8} | {'ecm':>5} | {'avg_gen':>8} | {'avg_mf  ':>10} | {'avg_nff':>8} | {'full_conv':>10}")
print("-"*65)
for (s, ecm) in sorted(cond_data.keys()):
    rows_c = cond_data[(s, ecm)]
    mf_vals = scalar_finals_mf[s]['ecm' if ecm else 'noecm']
    avg_gen = avg([r['gen'] for r in rows_c])
    avg_nff = avg([r['nff'] for r in rows_c])
    avg_mf  = avg(mf_vals)
    n_full  = sum(1 for r in rows_c if r['nff'] == 1000)
    n = len(rows_c)
    print(f"{s:>8.2f} | {ecm:>5} | {avg_gen:>8.1f} | {avg_mf:>10.4f} | {avg_nff:>8.1f} | {n_full}/{n}")
