"""Gezielter, gecachter Meilenstein W01; nach unabhängiger Cache-Abnahme."""
import io,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from formgen.cache import Artifact,canonical,file_hash,run_artifacts
from formgen import versions

def render_artifact(artifact):
 from formgen import model,geom,raster
 doc=geom.evaluate(model.load(ROOT/'formgen/models/weapons/w01_auto_rifle.py'))
 img=raster.render(doc,view='side_left',width=960,height=640)
 buf=io.BytesIO();img.save(buf,format='PNG');return buf.getvalue()

def main():
 from formgen import model,geom
 source=ROOT/'formgen/models/weapons/w01_auto_rifle.py'
 target=Path.home()/'Library/Caches/CubeEscapeFormgen/evidence/first-ortho'
 art=Artifact('W01','views',file_hash(source),{'view':'side_left','width':960,'height':640,'skin_sha':file_hash(ROOT/'skins.toml')},{'GEOM':versions.GEOM,'RASTER':versions.RASTER},'W01-side-left.png','tools.first_ortho:render_artifact',{})
 results=run_artifacts([art],target,Path.home()/'Library/Caches/CubeEscapeFormgen/artifacts')
 doc=geom.evaluate(model.load(source))
 (target/'geometry-summary.json').write_bytes(canonical({'counts':doc['counts'],'bounds_m':doc['bounds_m'],'warnings':doc['warnings']})+b'\n')
 print('W01 erste Ortho',results[0].reason,doc['counts'],str(target/'W01-side-left.png'))
if __name__=='__main__':main()
