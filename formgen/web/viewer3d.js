// 3D-Seite: ein Blatt je Aufruf (3d.html?id=BA01, optional &baugruppe=…). Das GLB kommt als Skript, weil fetch unter file:// scheitert.
(function(){
 'use strict';
 const {THREE:T,GLTFLoader,OrbitControls,RoomEnvironment}=window.FormgenThree;
 const items=window.formgenCatalog.items;
 const query=new URLSearchParams(location.search);
 const id=query.get('id')||location.hash.slice(1);
 const wanted=query.get('baugruppe')||'all';
 const pick=s=>document.querySelector(s);
 function fail(text){const e=pick('#error');e.textContent=text;e.hidden=false;pick('[data-workspace]').hidden=true}
 function bytes(base64){
   const text=atob(base64),result=new Uint8Array(text.length);
   for(let i=0;i<text.length;i++)result[i]=text.charCodeAt(i);
   return result;
 }
 function nodeOf(parser,obj){
   for(let o=obj;o;o=o.parent){
     const a=parser.associations.get(o);
     if(a&&a.nodes!==undefined)return a.nodes;
   }
   return null;
 }
 function extra(obj,key){
   for(let o=obj;o;o=o.parent){
     const value=o.userData&&o.userData[key];
     if(value!==undefined&&value!==null&&value!=='')return value;
   }
   return null;
 }
 // Teil und Baugruppe aus den Node-Extras; ohne Extras der Node-Name, ohne Namen der Mesh-Index.
 function describe(parser,obj){
   const node=nodeOf(parser,obj),info=parser.json.nodes[node]||{};
   const primitive=parser.associations.get(obj)?.primitives??0;
   const parent=obj.parent&&parser.json.nodes[nodeOf(parser,obj.parent)]?.name;
   return {obj,node,mesh:info.mesh,primitive,part:extra(obj,'basic_part')||info.name||'mesh_'+info.mesh,
     group:extra(obj,'basic_assembly')||extra(obj,'source_segment')||parent||null,family:extra(obj,'basic_group')||null};
 }
 function header(entry){
   pick('[data-id]').textContent=entry.id;pick('[data-name]').textContent=entry.name;
   document.title=entry.id+' · '+entry.name+' · Formgen 2';
   const sheet=pick('[data-sheet]');sheet.href='sheets/'+entry.id+'.dc.html';sheet.hidden=false;
   const same=items.filter(i=>i.kind===entry.kind&&i.has_3d),at=same.findIndex(i=>i.id===entry.id);
   for(const [selector,other] of [['[data-prev]',same[at-1]],['[data-next]',same[at+1]]]){
     if(other){const a=pick(selector),skin=query.get('skin');a.href='3d.html?id='+encodeURIComponent(other.id)+(skin?'&skin='+encodeURIComponent(skin):'');a.hidden=false}   // Skin bleibt beim Blättern
   }
 }
 function chooser(meshes,model,group){
   const ids=[...new Set(meshes.map(m=>m.group).filter(Boolean))];
   if(ids.length<2)return;
   const names=model.labels.assemblies,select=pick('[data-assembly]');
   const order=model.labels.order||[],rank=g=>order.includes(g)?order.indexOf(g):order.length;   // Roboter: Reihenfolge am Körper
   const rows=ids.map(g=>[g,names[g]||g]).sort((a,b)=>rank(a[0])-rank(b[0])||a[1].localeCompare(b[1],'de'));
   const families=model.labels.families||[],level=(label,items)=>{const box=document.createElement('optgroup');box.label=label;
     box.append(...items.map(([g,text])=>new Option(text,g)));return box};
   select.replaceChildren(new Option('Gesamtmodell','all'),...(families.length?[level('Baugruppen',families.map(f=>[f.id,f.de])),level('Einzelteile',rows)]:rows.map(([g,label])=>new Option(label,g))));
   select.value=group;pick('[data-view]').hidden=false;
   select.onchange=()=>{
     const next=new URLSearchParams(location.search);next.set('id',model.id);        // bleibt: gewählter Skin
     if(select.value!=='all')next.set('baugruppe',select.value);else next.delete('baugruppe');
     location.search=next.toString();
   };
 }
 // Farbskin wechseln: Materialien heißen wie ihre Rolle (Roboter `shell`, Waffen `MT_shell_color`); nur reine Farbskins, Textur-Skins fehlen im Katalog.
 function skinSwitch(root,entry,render){
   const list=(window.formgenCatalog.skins||{})[entry.kind]||[];
   if(!list.length)return;
   const label=pick('[data-skin]'),select=pick('[data-skin-select]');
   const role=m=>m.name.replace(/^MT_/,'').replace(/_color$/,'');
   const baseOf=m=>({color:m.color.clone(),emissive:m.emissive?m.emissive.clone():null});
   const seen=new Map(),byRole=new Map();      // Originale beim Start; Klone des Pinsels (markierung.js) kommen beim nächsten Wechsel dazu und erben die Ursprungsfarbe ihrer Rolle
   const collect=initial=>root.traverse(o=>{if(o.isMesh)for(const m of [].concat(o.material))if(!seen.has(m.uuid)){
     const entry={m,base:initial?baseOf(m):null};seen.set(m.uuid,entry);
     if(initial&&!byRole.has(role(m)))byRole.set(role(m),entry.base)}});
   collect(true);
   const own=list.find(s=>s.id===entry.skin_id);
   select.replaceChildren(new Option('Original'+(own?' ('+own.de+')':''),''),...list.map(s=>new Option(s.de,s.id)));
   function apply(id){
     const skin=list.find(s=>s.id===id);
     collect(false);
     for(const {m,base} of seen.values()){
       const hex=skin&&skin.roles[role(m)],origin=base||byRole.get(role(m));
       if(hex){
         m.color.set(hex);
         if(origin.emissive&&origin.emissive.getHex()!==0){      // Leuchtstärke des Originals behalten, nur der Farbton wechselt
           const peak=Math.max(origin.emissive.r,origin.emissive.g,origin.emissive.b)/Math.max(origin.color.r,origin.color.g,origin.color.b,1e-6);
           m.emissive.copy(m.color).multiplyScalar(peak);
         }
       }else{m.color.copy(origin.color);if(origin.emissive)m.emissive.copy(origin.emissive)}
     }
     render();
   }
   select.onchange=()=>{
     const next=new URLSearchParams(location.search);
     if(select.value)next.set('skin',select.value);else next.delete('skin');
     history.replaceState(null,'','?'+next.toString());
     apply(select.value);
   };
   const first=query.get('skin');
   if(first&&list.some(s=>s.id===first)){select.value=first;apply(first)}
   label.hidden=false;
 }
 async function show(entry,model){
   const {scene:root,parser}=await new GLTFLoader().parseAsync(bytes(model.glb).buffer,'');
   model.glb=null;
   root.updateMatrixWorld(true);
   const meshes=[];
   root.traverse(obj=>{if(obj.isMesh)meshes.push(describe(parser,obj))});
   const group=meshes.some(m=>m.group===wanted||m.family===wanted)?wanted:'all';
   const renderer=new T.WebGLRenderer({antialias:true});
   renderer.toneMapping=T.ACESFilmicToneMapping;
   const scene=new T.Scene();scene.background=new T.Color(0x808080);
   scene.environment=new T.PMREMGenerator(renderer).fromScene(new RoomEnvironment(),.04).texture;
   const key=new T.DirectionalLight(0xffffff,2.3);key.position.set(-2,4,3);
   scene.add(root,key,new T.HemisphereLight(0xffffff,0xa1a7af,1));
   const box=new T.Box3();
   for(const m of meshes){
     m.obj.visible=group==='all'||m.group===group||m.family===group;
     if(m.obj.visible)box.expandByObject(m.obj,true);
   }
   if(box.isEmpty())throw Error('Leeres Modell');
   const stage=pick('[data-orbit]'),canvas=renderer.domElement;
   pick('[data-workspace]').hidden=false;
   const center=box.getCenter(new T.Vector3()),radius=box.getSize(new T.Vector3()).length()/2;
   const camera=new T.PerspectiveCamera(32,1,radius*.01,radius*60);
   canvas.setAttribute('aria-label',entry.name+' in 3D');
   stage.append(canvas);
   const controls=new OrbitControls(camera,canvas);
   controls.target.copy(center);controls.enablePan=true;controls.mouseButtons.MIDDLE=T.MOUSE.ROTATE;
   // Verhindert den mittleren Autoscroll-Klick im Browser innerhalb der 3D-Fläche.
   for(const event of ['mousedown','auxclick'])canvas.addEventListener(event,e=>{if(e.button===1)e.preventDefault()});
   controls.minDistance=radius*1.12;controls.maxDistance=radius*14;
   const render=()=>renderer.render(scene,camera);
   const reset=()=>{
     const half=T.MathUtils.degToRad(camera.fov/2),limit=Math.min(half,Math.atan(Math.tan(half)*camera.aspect));
     controls.target.copy(center);
     camera.position.set(.78,.38,1).normalize().multiplyScalar(radius*1.07/Math.sin(limit)).add(center);
     controls.update();render();
   };
   const resize=()=>{
     const w=stage.clientWidth,h=stage.clientHeight;
     if(!w||!h)return;
     camera.aspect=w/h;camera.updateProjectionMatrix();
     renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
     renderer.setSize(w,h,false);render();
   };
   controls.addEventListener('change',render);
   resize();reset();new ResizeObserver(resize).observe(stage);
   const button=pick('[data-reset]');button.disabled=false;button.onclick=reset;
   chooser(meshes,model,group);
   skinSwitch(root,entry,render);
   window.formgenEnableAnnotation({T,stage,canvas,meshes,group,camera,controls,radius,render,
     model:{...model,kind:entry.kind,name:entry.name}});
 }
 const entry=items.find(i=>i.id===id);
 if(!entry){fail(id?'Unbekanntes Blatt: '+id:'Kein Blatt gewählt. Bitte über Waffen oder Roboter öffnen.');return}
 header(entry);
 const script=document.createElement('script');
 script.src='models3d/'+encodeURIComponent(entry.id)+'.js';
 script.onerror=()=>fail('3D-Daten fehlen: models3d/'+entry.id+'.js. Im Release liegen sie als eigenes 3D-Zip bei; bitte in denselben Ordner auspacken.');
 script.onload=()=>{
   const model=window.formgenModel;
   if(!model||model.id!==entry.id){fail('3D-Daten passen nicht zum Blatt '+entry.id+'.');return}
   show(entry,model).catch(error=>{
     console.error(error);
     fail('Das Modell lässt sich nicht anzeigen. Bitte WebGL im Browser aktivieren.');
   });
 };
 document.head.append(script);
})();
