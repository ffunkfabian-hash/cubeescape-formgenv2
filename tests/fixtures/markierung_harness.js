// Lauf von formgen/web/markierung.js ohne Browser: Three.js und DOM als Attrappen, ausgeführt von tests/test_markierung.py.
var W=arguments[0];
function V(x,y,z){this.x=x||0;this.y=y||0;this.z=z||0}
V.prototype={set(x,y,z){this.x=x;this.y=y;this.z=z;return this},clone(){return new V(this.x,this.y,this.z)},
 fromArray(a){this.x=a[0];this.y=a[1];this.z=a[2];return this},toArray(a,o){if(a){a[o]=this.x;a[o+1]=this.y;a[o+2]=this.z;return a}return [this.x,this.y,this.z]},
 fromBufferAttribute(at,i){return this.fromArray(at.a.slice(3*i,3*i+3))},addScaledVector(v,s){this.x+=v.x*s;this.y+=v.y*s;this.z+=v.z*s;return this},
 distanceToSquared(v){return (this.x-v.x)**2+(this.y-v.y)**2+(this.z-v.z)**2},distanceTo(v){return Math.sqrt(this.distanceToSquared(v))}};
var hit=null;
var T={Vector3:V,Vector2:function(){this.set=()=>{}},Raycaster:function(){this.setFromCamera=()=>{};this.intersectObjects=l=>hit&&l.includes(hit.object)?[hit]:[]},
 Triangle:{getNormal:(a,b,c,t)=>t.set(0,0,1),getBarycoord:(p,a,b,c,t)=>t.set(1/3,1/3,1/3)},MathUtils:{degToRad:d=>d*Math.PI/180},
 DataTexture:function(){this.dispose=()=>{}},RGBAFormat:0,FloatType:0};
function el(extra){return Object.assign({hidden:false,disabled:false,value:'',textContent:'',style:{},selectedIndex:-1,selectedOptions:[{}],dataset:{},
 setAttribute(){},replaceChildren(){},addEventListener(){},click(){},remove(){},querySelector(){return el()}},extra||{})}
var els={};
var pointBtn=el({dataset:{tool:'point'}});
var form={querySelector(s){return els[s]||(els[s]=el())},querySelectorAll(){return [pointBtn]}};
var saved=[];
var window=this;var self=this;
this.document={querySelector:()=>form,createElement:()=>el(),body:{append(){}},addEventListener(){}};
this.Option=function(){};this.requestAnimationFrame=()=>1;this.setTimeout=()=>0;this.crypto={randomUUID:()=>'u'+Math.random()};
this.Blob=function(p){this.p=p};this.URL={createObjectURL(b){saved.push(JSON.parse(b.p[0]));return 'x'},revokeObjectURL(){}};
load(W+'/formgen/web/change-request.js');load(arguments[1]||W+'/formgen/web/markierung.js');
var pos=[0,0,0, 1,0,0, 0,1,0];
function mesh(){var obj={geometry:{index:null,attributes:{position:{a:pos,count:3}},boundingSphere:{center:new V(.3,.3,0)}},material:{clone(){return {}}},worldToLocal:p=>p};
 return {obj,node:7,mesh:7,primitive:0,part:'pauldron_l',group:'hands',family:'arms'}}
var CUR='a'.repeat(64),OLD='b'.repeat(64);
function editor(view){
 els={};saved=[];var ls={};
 var canvas={style:{},addEventListener(n,f){ls[n]=f},hasPointerCapture:()=>false,setPointerCapture(){},releasePointerCapture(){},clientHeight:100,getBoundingClientRect:()=>({left:0,right:100,top:0,bottom:100,width:100,height:100})};
 var m=mesh();
 window.formgenEnableAnnotation({T,stage:{querySelector:()=>el()},canvas,meshes:[m],group:view||'all',camera:{position:new V(0,0,1),fov:50},controls:{target:new V()},radius:1,render(){},
  model:{id:'RA01',kind:'robot',name:'RoboterBasic-01',asset:'RA01.glb',asset_sha256:CUR,labels:{parts:{}}}});
 return {m,mark(){pointBtn.onclick();hit={object:m.obj,point:new V(1/3,1/3,0),face:{a:0,b:1,c:2,normal:new V(0,0,1)},faceIndex:0};
   var e={button:0,isPrimary:true,pointerId:1,clientX:5,clientY:5,stopImmediatePropagation(){}};ls.pointerdown(e);ls.pointerup(e);els['[data-global]'];},
  async open(doc){var f=els['[data-file]'];f.files=[{text:async()=>JSON.stringify(doc)}];await f.onchange();return els['[role=status]'].textContent},
  undo(){els['[data-undo]'].onclick()},save(){els['[data-export]'].onclick();return saved[saved.length-1]}}}
var foreignSample={part:'pauldron_l_338',assembly:'SHOULDER_L',location:{gltf_node:396,gltf_mesh:338,gltf_primitive:0,gltf_triangle:1933,triangle_vertex_indices:[1,2,3],barycentric:[.2,.3,.5],local_gltf_xyz_m:[1,2,3]},source:{source_member:'x'}};
function F(h,extra){return Object.assign({format:'formgen/change-request',version:1,created_at:'t',model:{id:'RA01',kind:'robot',name:'RoboterBasic-01',asset:'old.glb',asset_sha256:h},requested_change:'r',markings:[{id:'m1',tool:'point',comment:'',diameter_mm:10,samples:[foreignSample]}]},extra||{})}
var exactSample={part:'pauldron_l',assembly:'all',location:{gltf_node:7,gltf_mesh:7,gltf_primitive:0,gltf_triangle:0,triangle_vertex_indices:[0,1,2],barycentric:[1/3,1/3,1/3],local_gltf_xyz_m:[1/3,1/3,0]}};
function G(){return {format:'formgen/change-request',version:1,created_at:'t',model:{id:'RA01',kind:'robot',name:'RoboterBasic-01',asset:'RA01.glb',asset_sha256:CUR},requested_change:'g',markings:[{id:'g1',tool:'point',comment:'',diameter_mm:10,samples:[exactSample]}]}}
(async()=>{
 var R={},migrated={migrated_from:{format:'formgen/robot-change-request',version:1}};
 var e=editor();await e.open(F(OLD));e.mark();var s=e.save();
 var e2=editor();R.reopen=await e2.open(s);var s2=e2.save();
 R.mixed={sha:s.model.asset_sha256,markings:s.markings.length,same:JSON.stringify(s2.markings)===JSON.stringify(s.markings)};
 var e3=editor();await e3.open(F(OLD));await e3.open(G());e3.undo();var t=e3.save();
 R.undoForeign={sha:t.model.asset_sha256,reopen:await editor().open(t)};
 var e5=editor();e5.mark();await e5.open(F(OLD,migrated));e5.undo();var u=e5.save();
 R.undoOwn={sha:u.model.asset_sha256,migrated:u.migrated_from||null};
 var e6=editor();await e6.open(F(OLD,migrated));var w=e6.save();
 R.kept={sha:w.model.asset_sha256,asset:w.model.asset,migrated:w.migrated_from||null};
 var e7=editor();e7.mark();var v=e7.save();
 R.fresh={sha:v.model.asset_sha256,fux:v.markings[0].samples[0].location.local_formgen_fux_mm};
 var e8=editor('arms');e8.mark();R.family=e8.save().markings[0].samples[0].assembly;
 var e9=editor('hands');e9.mark();R.single=e9.save().markings[0].samples[0].assembly;
 var e10=editor('legs');e10.mark();R.otherFamily=els['[data-count]'].textContent;
 R.cur=CUR;R.old=OLD;print(JSON.stringify(R));
})().catch(x=>print('ERR',x,x.stack));
drainMicrotasks();
