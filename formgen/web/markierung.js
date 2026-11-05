(function(){
'use strict';
// Die Markierung färbt ausschließlich Fragmente der getroffenen Originaloberfläche.
function surfacePaint(T) {
 const layers=new Map();
 function layer(obj){
   if(layers.has(obj))return layers.get(obj);
   const material=obj.material.clone();
   const state={original:obj.material,material,texture:{value:null},count:{value:0}};
   material.onBeforeCompile=shader=>{
     shader.uniforms.fgStamps=state.texture;shader.uniforms.fgCount=state.count;
     shader.vertexShader='varying vec3 fgPosition,fgNormal;\n'+shader.vertexShader.replace('#include <begin_vertex>',
       '#include <begin_vertex>\nfgPosition=position;fgNormal=normal;');
     shader.fragmentShader='uniform highp sampler2D fgStamps;uniform int fgCount;varying vec3 fgPosition,fgNormal;\n'+shader.fragmentShader.replace('#include <opaque_fragment>', `
       for(int i=0;i<fgCount;i++){
         ivec2 uv=ivec2((i%128)*2,i/128);
         vec4 stamp=texelFetch(fgStamps,uv,0);
         vec3 delta=fgPosition-stamp.xyz;
         vec4 brush=texelFetch(fgStamps,uv+ivec2(1,0),0);vec3 n=brush.xyz;
         if(dot(delta,delta)<=stamp.w*stamp.w && abs(dot(delta,n))<stamp.w*.5 && dot(fgNormal,n)>0.0){
           outgoingLight=mix(outgoingLight,mix(vec3(1.6,.18,.015),vec3(.02,1.2,1.4),brush.w),.95);break;
         }
       }
       #include <opaque_fragment>`);
   };
   material.customProgramCacheKey=()=>'formgen-surface-brush-v2';
   layers.set(obj,state);return state;
 }
 return (strokes,active)=>{
   const byMesh=new Map();
   for(const stroke of strokes)for(const sample of stroke.samples){
     if(!byMesh.has(sample.obj))byMesh.set(sample.obj,[]);
     byMesh.get(sample.obj).push([sample,stroke===active]);
   }
   for(const obj of new Set([...layers.keys(),...byMesh.keys()])){
     const s=layer(obj),points=byMesh.get(obj)||[];
     if(s.texture.value)s.texture.value.dispose();
     s.texture.value=null;s.count.value=points.length;
     if(!points.length){obj.material=s.original;s.material.dispose();layers.delete(obj);continue;}
     const height=Math.ceil(points.length/128),pixels=new Float32Array(256*height*4);
     points.forEach(([{pos,normal,radius},selected],i)=>{
       pos.toArray(pixels,8*i);pixels[8*i+3]=radius;normal.toArray(pixels,8*i+4);pixels[8*i+7]=Number(selected);
     });
     const tex=new T.DataTexture(pixels,256,height,T.RGBAFormat,T.FloatType);
     tex.needsUpdate=true;s.texture.value=tex;obj.material=s.material;
   }
 };
}

window.formgenEnableAnnotation=function({T,stage,canvas,meshes,group,camera,controls,radius,render,model}){
 const changeRequest=window.FormgenChangeRequest;
 const uid=()=>crypto.randomUUID?crypto.randomUUID():Date.now().toString(36)+'-'+Math.random().toString(36).slice(2);
 const form=document.querySelector('[data-annotation]'), find=s=>form.querySelector(s);
 const comment=find('[data-global]'),save=find('[data-export]'),status=find('[role=status]');
 const width=find('[data-width]'),panel=find('[data-editor]');
 const buttons=[...form.querySelectorAll('[data-tool]')];
 const available=meshes.filter(item=>group==='all'||item.group===group);
 const objects=available.map(item=>item.obj),owners=new Map(available.map(item=>[item.obj,item]));
 const ray=new T.Raycaster(),ndc=new T.Vector2(),paint=surfacePaint(T);
 let done=[],active=null;
 const previous=[],undone=[];
 const list=find('[data-list]'),note=find('[data-note]');
 const labels={point:'Punkt',line:'Strich',brush:'Pinsel'};
 let origin=null,migrated=null;   // Herkunft einer geöffneten Datei, gehört wie die Markierungen zum Undo-Stand
 const snapshot=()=>({items:done.slice(),active,comment:comment.value,origin,migrated});
 function checkpoint(){previous.push(snapshot());undone.length=0;}
 function rowText(s,i){
   const part=s.samples[0].data.part,name=model.labels.parts[part]||part;
   return (i+1)+'. '+labels[s.tool]+' · '+name+(s.note?' — '+s.note.slice(0,65):'');
 }
 function showList(){
   list.replaceChildren(...done.map((s,i)=>new Option(rowText(s,i),String(i))));
   list.selectedIndex=done.indexOf(active);note.value=active?.note||'';
   note.disabled=!active;find('[data-remove]').disabled=!active;
 }
 list.onchange=()=>{active=done[list.selectedIndex];showList();requestDraw()};
 note.oninput=()=>{
   if(!active)return;
   active.note=note.value;list.selectedOptions[0].textContent=rowText(active,list.selectedIndex);update();
 };
 find('[data-remove]').onclick=()=>{
   if(!active||gesture)return;
   checkpoint();const i=done.indexOf(active);done.splice(i,1);active=done[Math.min(i,done.length-1)]||null;
   showList();requestDraw();update();
 };
 let tool='orbit',gesture=null,frame=0;
 function refresh(){
   paint(gesture?[...done,gesture]:done,gesture||active);render();
 }
 function requestDraw(){
   if(!frame)frame=requestAnimationFrame(()=>{frame=0;refresh()});
 }
 function update(){
   find('[data-undo]').disabled=!previous.length||!!gesture;
   find('[data-redo]').disabled=!undone.length||!!gesture;
   save.disabled=!done.length||!!gesture;
   panel.hidden=!done.length&&!undone.length;
   find('[data-count]').textContent=done.length===1?'1 Markierung':done.length+' Markierungen';
 }
 function cancel(){
   if(!gesture)return;
   const id=gesture.pointer;gesture=null;
   if(canvas.hasPointerCapture(id))canvas.releasePointerCapture(id);
   guide.hidden=true;requestDraw();update();
 }
 function mode(value){
   cancel();tool=value;canvas.style.cursor=tool==='orbit'?'grab':'crosshair';
   for(const b of buttons)b.setAttribute('aria-pressed',String(b.dataset.tool===value));
   find('[data-size]').hidden=value!=='brush';
   status.textContent={orbit:'Ziehen zum Drehen · Scrollen zum Zoomen',point:'Auf eine Stelle klicken.',
     line:'Vom Anfang bis zum Ende der Linie ziehen.',brush:'Über die gewünschte Fläche streichen.'}[tool];
 }
 for(const b of buttons){b.disabled=false;b.onclick=()=>mode(b.dataset.tool)}
 width.value=String(Math.max(2,Math.min(60,Math.round(radius*75))));
 const showSize=()=>{find('output').textContent=width.value+' mm'};width.oninput=showSize;showSize();
 const guide=stage.querySelector('[data-guide]'),line=guide.querySelector('line');
 function target(x,y){
   const r=canvas.getBoundingClientRect();
   if(x<r.left||x>r.right||y<r.top||y>r.bottom)return null;
   ndc.set((x-r.left)/r.width*2-1,1-(y-r.top)/r.height*2);
   ray.setFromCamera(ndc,camera);return ray.intersectObjects(objects,false)[0]||null;
 }
 function sample(x,y,stroke){
   const hit=target(x,y);if(!hit)return;
   const obj=hit.object,pos=obj.worldToLocal(hit.point.clone());
   const a=obj.geometry.attributes.position,ids=[hit.face.a,hit.face.b,hit.face.c];
   const tri=ids.map(i=>new T.Vector3().fromBufferAttribute(a,i));
   const bary=T.Triangle.getBarycoord(pos,...tri,new T.Vector3());if(!bary)return;
   const last=stroke.samples.at(-1);
   if(last?.obj===obj && last.pos.distanceToSquared(pos)<1e-16)return;
   const owner=owners.get(obj),normal=hit.face.normal.clone();
   const place={gltf_node:owner.node,gltf_mesh:owner.mesh,gltf_primitive:owner.primitive,gltf_triangle:hit.faceIndex,
     triangle_vertex_indices:ids,barycentric:bary.toArray(),local_gltf_xyz_m:pos.toArray(),local_normal_gltf_xyz:normal.toArray(),
     model_gltf_xyz_m:hit.point.toArray()};
   // Autorenrahmen: f vorn, u oben, x links; glTF x, y, z = x, u, f (formgen/change_request.py › fux_from_gltf). Migrierte Altwerte behalten ihren Rahmen.
   if(model.kind==='robot')place.local_formgen_fux_mm=[1000*pos.z,1000*pos.y,1000*pos.x];
   stroke.samples.push({obj,pos,normal,radius:stroke.radius,data:{part:owner.part,assembly:owner.group,location:place}});
 }
 function trace(stroke,from,to){
   const distance=Math.hypot(to.x-from.x,to.y-from.y);
   const steps=Math.ceil(distance/stroke.spacing);
   for(let i=1;i<=steps;i++)sample(from.x+(to.x-from.x)*i/steps,from.y+(to.y-from.y)*i/steps,stroke);
 }
 const coords=e=>({x:e.clientX,y:e.clientY});
 canvas.addEventListener('pointerdown',e=>{
   if(tool==='orbit'||e.button!==0)return;
   // Nur der primäre Mal-Kontakt gehört dem Werkzeug; die mittlere Taste bedient OrbitControls.
   e.stopImmediatePropagation();
   if(gesture||!e.isPrimary)return;
   const start=coords(e),height=canvas.clientHeight;
   const mPerPixel=2*camera.position.distanceTo(controls.target)*Math.tan(T.MathUtils.degToRad(camera.fov/2))/height;
   const r=tool==='brush'?Number(width.value)/2000:mPerPixel*(tool==='point'?6:2.4);
   gesture={pointer:e.pointerId,tool,radius:r,spacing:Math.max(.8,Math.min(12,r/mPerPixel*.75)),start,last:start,samples:[]};
   canvas.setPointerCapture(e.pointerId);
   sample(start.x,start.y,gesture);
   if(tool==='line'){
     const rect=canvas.getBoundingClientRect();
     line.setAttribute('x1',start.x-rect.left);line.setAttribute('y1',start.y-rect.top);
     line.setAttribute('x2',start.x-rect.left);line.setAttribute('y2',start.y-rect.top);guide.hidden=false;
   }
   requestDraw();update();
 },{capture:true});
 canvas.addEventListener('pointermove',e=>{
   if(!gesture||gesture.pointer!==e.pointerId)return;
   if(tool==='brush'){
     const to=coords(e);trace(gesture,gesture.last,to);gesture.last=to;requestDraw();
   }else if(tool==='line'){
     const rect=canvas.getBoundingClientRect();
     line.setAttribute('x2',e.clientX-rect.left);line.setAttribute('y2',e.clientY-rect.top);
   }
 });
 canvas.addEventListener('pointerup',e=>{
   if(!gesture||gesture.pointer!==e.pointerId)return;
   if(tool!=='point')trace(gesture,tool==='line'?gesture.start:gesture.last,coords(e));
   const stroke=gesture;gesture=null;guide.hidden=true;
   if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);
   if(stroke.samples.length){checkpoint();stroke.id=uid();stroke.note='';done.push(stroke);active=stroke;showList();status.textContent='Markierung hinzugefügt.';}
   else status.textContent='Keine Modelloberfläche getroffen.';
   requestDraw();update();
 });
 canvas.addEventListener('lostpointercapture',e=>{if(gesture?.pointer===e.pointerId)cancel()});
 canvas.addEventListener('pointercancel',cancel);
 function history(redo){
   if(gesture)return;
   const [from,to]=redo?[undone,previous]:[previous,undone];
   if(!from.length)return;
   to.push(snapshot());const old=from.pop();done=old.items;active=old.active;comment.value=old.comment;origin=old.origin;migrated=old.migrated;showList();status.textContent=redo?'Markierung wiederhergestellt.':'Markierung zurückgenommen.';
   requestDraw();update();
 }
 find('[data-undo]').onclick=()=>history(false);find('[data-redo]').onclick=()=>history(true);
 document.addEventListener('keydown',e=>{
   if(e.target.matches('textarea,input,[contenteditable=true]'))return;
   if(e.key==='Escape'){mode('orbit');return;}
   if(!e.ctrlKey&&!e.metaKey||e.altKey)return;
   const key=e.key.toLowerCase();
   if(key==='z'||key==='y'){e.preventDefault();history(key==='y'||e.shiftKey)}
 });
 comment.addEventListener('input',update);
 save.onclick=()=>{
   if(save.disabled)return;
   const created=new Date();
   const payload={format:changeRequest.FORMAT,version:changeRequest.VERSION,created_at:created.toISOString(),
     // Solange Proben eines anderen Modellstands geladen sind, nennt die Datei weiter dessen Asset: nur so erkennt das nächste Öffnen sie wieder.
     model:{id:model.id,kind:model.kind,name:model.name,asset:origin?.asset??model.asset,asset_sha256:origin?.asset_sha256??model.asset_sha256},
     ...(migrated?{migrated_from:migrated}:{}),
     requested_change:comment.value.trim(),
     markings:done.map(stroke=>({id:stroke.id,tool:stroke.tool,comment:stroke.note,
       diameter_mm:stroke.diameter===undefined?stroke.radius*2000:stroke.diameter,samples:stroke.samples.map(p=>p.data)}))};
   const url=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)+'\n'],{type:'application/json'}));
   const link=document.createElement('a');link.href=url;
   link.download=model.id+'_'+group+'_'+created.toISOString().replace(/[:.]/g,'-')+'.json';
   document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);
   status.textContent='Download gestartet. Die JSON-Datei kannst du an den Chat anhängen.';
 };
 const fileInput=find('[data-file]');
 find('[data-open]').onclick=()=>fileInput.click();
 const slot=(node,primitive)=>node+':'+primitive;
 function readRecords(records,same=true,stats={approx:0,lost:0}){
   const bySlot=new Map(available.map(item=>[slot(item.node,item.primitive),item.obj]));
   return records.map(record=>{
     const known=record.diameter_mm!==null&&record.diameter_mm!==undefined;
     // Altdateien v1 kennen keinen Durchmesser: nur die Anzeige bekommt einen Wert, die Datei behält null.
     const r=known?record.diameter_mm/2000:radius*.023;
     if(!Object.hasOwn(labels,record.tool)||!Number.isFinite(r)||r<=0||!Array.isArray(record.samples)||!record.samples.length)
       throw Error('Ungültige Markierung.');
     const samples=record.samples.map(data=>{
       try{return exact(data,r)}
       catch(error){if(same)throw error;return onPart(data,r,stats)}
     });
     return {id:record.id||uid(),tool:record.tool,radius:r,diameter:known?undefined:null,note:String(record.comment||''),samples};
   });
   function exact(data,r){
       const place=data.location,obj=bySlot.get(slot(place.gltf_node,place.gltf_primitive??0));
       if(!obj)throw Error('Diese Markierung liegt außerhalb der Baugruppe. Bitte im Gesamtmodell öffnen.');
       const valid=v=>Array.isArray(v)&&v.length===3&&v.every(Number.isFinite);
       const geom=obj.geometry,idx=geom.index,n=place.gltf_triangle;
       if(!Number.isInteger(n)||n<0||3*n+2>=(idx?.count??geom.attributes.position.count))throw Error('Ungültige Fläche.');
       const tri=[0,1,2].map(offset=>new T.Vector3().fromBufferAttribute(geom.attributes.position,idx?idx.getX(3*n+offset):3*n+offset));
       const w=place.barycentric;
       if(!valid(w)||w.some(k=>k<-.0001||k>1.0001)||Math.abs(w[0]+w[1]+w[2]-1)>.0001||!valid(place.local_gltf_xyz_m))throw Error('Ungültiger Oberflächenpunkt.');
       const pos=new T.Vector3().fromArray(place.local_gltf_xyz_m);
       const resolved=new T.Vector3();tri.forEach((v,i)=>resolved.addScaledVector(v,w[i]));
       if(resolved.distanceTo(pos)>1e-5)throw Error('Oberflächenpunkt stimmt nicht mit der Datei überein.');
       return {obj,pos,normal:T.Triangle.getNormal(...tri,new T.Vector3()),radius:r,data};
   }
 }
 // Anderer Modellstand: Lage ist verloren, das Teil nicht. Punkt auf den Netzpunkt nahe der Teilmitte, die Dateidaten bleiben unverändert.
 // Altnamen: Zähler am Ende (pauldron_l_338), Helmteile ohne Präfix (Crown_62 → helmet_crown). Ohne Teil steht die Probe am ersten sichtbaren Teil.
 function onPart(data,radius,stats){
   const name=String(data.part).replace(/_\d+$/,''),snake='helmet_'+name.replace(/([a-z])([A-Z])/g,'$1_$2').toLowerCase();
   const wanted=[String(data.part),name,snake];
   const found=available.find(m=>wanted.includes(m.part));
   if(found)stats.approx++;else stats.lost++;
   const obj=(found||available[0]).obj,geom=obj.geometry,at=geom.attributes.position,v=new T.Vector3(),pos=new T.Vector3();
   if(!geom.boundingSphere)geom.computeBoundingSphere();
   let best=Infinity,index=0;
   for(let i=0;i<at.count;i++){const d=v.fromBufferAttribute(at,i).distanceToSquared(geom.boundingSphere.center);if(d<best){best=d;index=i}}
   pos.fromBufferAttribute(at,index);
   const normal=geom.attributes.normal?new T.Vector3().fromBufferAttribute(geom.attributes.normal,index):new T.Vector3(0,1,0);
   return {obj,pos,normal,radius,data};
 }
 fileInput.onchange=async()=>{
   const file=fileInput.files[0];if(!file)return;
   try{
     const data=changeRequest.migrate(JSON.parse(await file.text()));
     if(data.model.id!==model.id)throw Error('Die Datei gehört zu '+data.model.id+', nicht zu '+model.id+'.');
     if(!Array.isArray(data.markings)||!data.markings.length)throw Error('Keine Markierungen gefunden.');
     // Anderer Modellstand: je Probe genau, sonst ungefähr auf ihrem Teil; die Datei bleibt lesbar.
     const same=data.model.asset_sha256===model.asset_sha256,stats={approx:0,lost:0};
     const loaded=readRecords(data.markings,same,stats);
     cancel();checkpoint();done=loaded;active=done[0];comment.value=String(data.requested_change||'');
     origin=same?null:{asset:data.model.asset,asset_sha256:data.model.asset_sha256};
     migrated=data.migrated_from??null;
     mode('orbit');showList();requestDraw();update();
     const moved=stats.approx+stats.lost;
     status.textContent=same?'Datei geöffnet.':!moved?'Datei geöffnet. Sie stammt von einem anderen Modellstand, die Punkte passen aber.':
       'Datei geöffnet. Anderer Modellstand: '+stats.approx+' Proben stehen nur ungefähr auf ihrem Teil'+(stats.lost?', '+stats.lost+' ohne bekanntes Teil.':'.');
   }catch(error){status.textContent='Öffnen fehlgeschlagen. '+error.message}
   finally{fileInput.value=''}
 };
 mode('orbit');update();
};
})();
