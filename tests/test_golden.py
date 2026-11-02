"""v1-Golden-Mechanik: SHA256 und Prozess-Determinismus, Bildstufe explizit."""
import hashlib,json,os,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];GOLDEN=ROOT/'tests/golden.json'

def collect(images=False):
    files=list((ROOT/'out/specs').glob('*.json'))+list((ROOT/'out/prompts').glob('*.json'))
    if images:files+=list((ROOT/'out/views').glob('*/*.png'))+list((ROOT/'out/sheets').glob('*.html'))
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}

def model(path):
    return path.split('/')[2].split('.')[0]

def select(expected,actual,scope):
    """Volle Dicts ohne Umfang; sonst nur die Modelle im Umfang (müssen Golden besitzen)."""
    if not scope:return expected,actual
    unknown=scope-{model(k) for k in expected}
    assert not unknown,f'Umfang enthält Modelle ohne Golden: {sorted(unknown)}'
    pick=lambda d:{k:v for k,v in d.items() if model(k) in scope}
    return pick(expected),pick(actual)

class GoldenTests(unittest.TestCase):
    def test_data_hashes(self):
        expected=json.loads(GOLDEN.read_text())
        actual=collect()
        self.assertTrue(actual,'Keine Datenartefakte gebaut')
        self.assertEqual({k:v for k,v in expected.items() if '/specs/' in k or '/prompts/' in k},actual)
    def test_spec_determinism(self):
        code = 'from formgen import geo,spec;from formgen.cache import canonical;import hashlib;d=geo.load("tests/fixtures/KG02.geo.json");print(hashlib.sha256(canonical(spec.build(d))).hexdigest())'
        cmd=[sys.executable,'-c',code]
        values=[subprocess.check_output(cmd,cwd=ROOT,env={**os.environ,'PYTHONHASHSEED':seed}) for seed in ('1','42')]
        self.assertEqual(*values)
    @unittest.skipUnless(os.environ.get('FORMGEN_GOLDEN_IMAGES')=='1','explizite Bildstufe')
    def test_image_hashes(self):
        # Ohne FORMGEN_GOLDEN_MODELS: voller Vergleich (Gesamtabnahme, auch neue ungegoldete Dateien fallen auf).
        # Mit Umfang (BA01,BB01,…): genau diese Modelle vollständig.
        expected=json.loads(GOLDEN.read_text());actual=collect(images=True)
        scope=set(filter(None,os.environ.get('FORMGEN_GOLDEN_MODELS','').split(',')))
        self.assertEqual(*select(expected,actual,scope))
    def test_scope_selection(self):
        golden={'out/views/BA01/hero.png':'a','out/specs/BA01.spec.json':'b'}
        built={**golden,'out/views/BZ01/hero.png':'c'}   # neues, ungegoldetes Modell
        e,a=select(golden,built,set());self.assertNotEqual(e,a)
        e,a=select(golden,built,{'BA01'});self.assertEqual(e,a)
        e,a=select(golden,{'out/specs/BA01.spec.json':'b'},{'BA01'});self.assertNotEqual(e,a)   # fehlendes Bild
        with self.assertRaises(AssertionError):select(golden,built,{'BQ01'})

if __name__=='__main__':
    if '--update' in sys.argv:
        images='--images' in sys.argv;data=collect(images=images)
        # Einträge behalten, deren Datei hier nicht gebaut wurde (z. B. Bildstufe anderer Modelle); Gebautes neu setzen
        old=json.loads(GOLDEN.read_text())
        keep={k:v for k,v in old.items() if not (ROOT/k).exists() or (not images and '/specs/' not in k and '/prompts/' not in k)}
        data={**keep,**data}
        GOLDEN.write_text(json.dumps(dict(sorted(data.items())),indent=2)+'\n');print(len(data),'Golden-Hashes geschrieben')
    else:unittest.main()
