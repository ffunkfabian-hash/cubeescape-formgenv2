"""v1-Baseline messen (nur lesen): Formgen v1 als git-archive-Kopie in einem Scratch-Ordner bauen und je Stufe stoppen.

  python3 tools/measure_v1.py --v1 ~/Claude/cubeescape-formgen --work <scratch> --python <venv-python> --out <json>

Die Kopie stammt aus `git archive <rev>` (v1-Checkout bleibt unberührt); Cache über CE_SHEET_CACHE im Scratch-Ordner.
Stufen: Blätter kalt (--nur-xl --force; Render, Rasterung und Layout laufen in v1 in einem Prozess je Blatt), Prompts,
Viewer, Vorschauen (Playwright), Profil eines Blatts (cProfile-Aufteilung Geometrie/Render/Rasterung/Layout), warmer
Lauf ohne Änderung, kleine Änderung (eine Zahl in einem Modell) mit Neubau von Blatt und Vorschau.
Die Karten-Altstufe C–H (gitignorierte Vorlagen) ist nicht Teil der Messung.
"""
import argparse, json, os, platform, re, subprocess, sys, time
from pathlib import Path


def run(cmd, cwd, env, log):
    t = time.time()
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    dt = time.time() - t
    log.write(f'$ {" ".join(map(str, cmd))}  [{dt:.1f} s, exit {r.returncode}]\n{r.stdout[-20000:]}\n{r.stderr[-4000:]}\n')
    log.flush()
    if r.returncode:
        raise SystemExit(f'Fehler in {cmd}: {r.stderr[-1000:]}')
    return dt, r.stdout


PROFILE = r'''
import cProfile, pstats, sys, re, io, time
sys.path.insert(0, '.')
import sheetmodels, xl
sid = sys.argv[1]
t = time.time(); d = sheetmodels.load(sid); t_model = time.time() - t
mm = re.search(r'VARIANTE\s+([A-Z])\s*·\s*„([^“]+)“', d['sub']); d['nick'] = mm.group(2).title()
pr = cProfile.Profile(); t = time.time(); pr.enable(); xl.sheet(d, mm.group(1)); pr.disable(); total = time.time() - t
st = pstats.Stats(pr); out = {}
for (f, line, name), (cc, nc, tt, ct, callers) in st.stats.items():
    mod = f.rsplit('/', 1)[-1]
    out[mod] = out.get(mod, 0) + tt
import json; print(json.dumps({'sheet': sid, 'model_load_s': t_model, 'sheet_s': total, 'self_time_by_file_s': out}))
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--v1', type=Path, required=True); ap.add_argument('--rev', default='origin/main')
    ap.add_argument('--work', type=Path, required=True); ap.add_argument('--python', required=True)
    ap.add_argument('--out', type=Path, required=True); ap.add_argument('--change', default='j01.py')
    a = ap.parse_args()
    rev = subprocess.check_output(['git', '-C', a.v1, 'rev-parse', a.rev], text=True).strip()
    src = a.work / 'v1'; cache = a.work / 'cache'
    if not src.exists():
        src.mkdir(parents=True)
        subprocess.run(f'git -C "{a.v1}" archive {rev} | tar -x -C "{src}"', shell=True, check=True)
    gen = src / 'claude/generator'
    env = dict(os.environ, CE_SHEET_CACHE=str(cache), PYTHONHASHSEED='0')
    log = open(a.work / 'measure.log', 'a')
    res = {'v1_rev': rev, 'machine': platform.platform(), 'cpus': os.cpu_count(), 'python': a.python,
           'load_before': os.getloadavg(), 'started': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'stages': {}}
    S = res['stages']
    py = a.python
    S['sheets_cold_s'], out = run([py, 'build_all.py', '--nur-xl', '--force'], gen, env, log)
    per = [float(x) for x in re.findall(r'OK  .*?  ([0-9.]+) s', out)]
    res['sheets'] = len(per); res['sheet_seconds_sum'] = sum(per); res['sheet_jobs'] = int(re.search(r'in (\d+) Prozessen', out).group(1))
    S['prompts_s'], _ = run([py, 'mkdoc.py'], gen, env, log)
    S['viewer_s'], _ = run([py, 'make_viewer.py'], gen, env, log)
    ids = sorted(p.stem for p in (gen / 'final').glob('*.html'))
    S['previews_s'], _ = run([py, 'preview.py', *ids], gen, env, log); res['previews'] = len(ids)
    _, out = run([py, '-c', PROFILE, 'KJ01'], gen, env, log)
    res['profile'] = json.loads(out.strip().splitlines()[-1])
    S['warm_s'], out = run([py, 'build_all.py', '--nur-xl'], gen, env, log)
    res['warm_hits'] = len(re.findall('Cache-Treffer', out))
    f = gen / a.change; text = f.read_text()
    # kleine Geometrieänderung: erster Punkt des ersten Bauteils 1 mm nach hinten (eine Variante, ein Blatt)
    new = re.sub(r'K\(\[\((\d+)', lambda m: 'K([(' + str(int(m.group(1)) + 1), text, count=1)
    f.write_text(new); res['change'] = {'file': a.change, 'diff_chars': sum(x != y for x, y in zip(text, new))}
    S['small_change_sheets_s'], out = run([py, 'build_all.py', '--nur-xl'], gen, env, log)
    res['small_change_built'] = len(re.findall(r'gebaut', out))
    S['small_change_preview_s'], _ = run([py, 'preview.py', 'K' + a.change[0].upper() + a.change[1:3]], gen, env, log)
    f.write_text(text)
    res['load_after'] = os.getloadavg(); res['finished'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')
    a.out.write_text(json.dumps(res, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps(S, indent=1))


if __name__ == '__main__':
    main()
