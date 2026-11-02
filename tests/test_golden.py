"""v1-Golden-Mechanik: SHA256 und Prozess-Determinismus, Bildstufe explizit."""
import hashlib,json,os,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];GOLDEN=ROOT/'tests/golden.json'

def collect(images=False):
    files=list((ROOT/'out/specs').glob('*.json'))+list((ROOT/'out/prompts').glob('*.json'))
    if images:files+=list((ROOT/'out/views').glob('*/*.png'))+list((ROOT/'out/sheets').glob('*.html'))
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}

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
        # Prüfumfang ausdrücklich: FORMGEN_GOLDEN_MODELS=BA01,BB01,… (sonst ALLE Golden-Modelle). Für jedes Modell im Umfang
        # müssen alle Golden-Dateien (Specs, Prompts, Ansichten, Blätter) vorhanden und gleich sein, und es darf nichts
        # Ungolden-Gebautes geben. Die Gesamtabnahme läuft ohne Umfang.
        expected=json.loads(GOLDEN.read_text());actual=collect(images=True)
        model=lambda k:k.split('/')[2].split('.')[0]
        scope=set(filter(None,os.environ.get('FORMGEN_GOLDEN_MODELS','').split(','))) or {model(k) for k in expected}
        unknown=scope-{model(k) for k in expected}
        self.assertFalse(unknown,f'Umfang enthält Modelle ohne Golden: {sorted(unknown)}')
        pick=lambda d:{k:v for k,v in d.items() if model(k) in scope}
        self.assertEqual(pick(expected),pick(actual))

if __name__=='__main__':
    if '--update' in sys.argv:
        images='--images' in sys.argv;data=collect(images=images)
        # Einträge behalten, deren Datei hier nicht gebaut wurde (z. B. Bildstufe anderer Modelle); Gebautes neu setzen
        old=json.loads(GOLDEN.read_text())
        keep={k:v for k,v in old.items() if not (ROOT/k).exists() or (not images and '/specs/' not in k and '/prompts/' not in k)}
        data={**keep,**data}
        GOLDEN.write_text(json.dumps(dict(sorted(data.items())),indent=2)+'\n');print(len(data),'Golden-Hashes geschrieben')
    else:unittest.main()
