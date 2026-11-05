// Änderungsdatei im Editor: dieselbe Migration wie formgen/change_request.py (Test vergleicht beide an den Fixtures).
(function(root){
 'use strict';
 const FORMAT='formgen/change-request',VERSION=1,LEGACY_FORMAT='formgen/robot-change-request';
 const LEGACY_VERSIONS=[1,2],LEGACY_TARGET_ID='legacy-target';
 const LEGACY_MODELS={'RoboterBasic-01':['RA01','robot']};
 const LOCATION_KEYS=['gltf_node','gltf_mesh','gltf_primitive','gltf_triangle','triangle_vertex_indices','barycentric',
   'local_gltf_xyz_m','local_normal_gltf_xyz','local_formgen_fux_mm'];
 function sample(target){
   const location={},source={};
   for(const [key,value] of Object.entries(target)){
     if(LOCATION_KEYS.includes(key))location[key]=value;
     else if(key!=='formgen_part_id'&&key!=='assembly')source[key]=value;
   }
   const result={part:target.formgen_part_id,assembly:target.assembly,location};
   if(Object.keys(source).length)result.source=source;
   return result;
 }
 function migrate(doc){
   if(doc===null||typeof doc!=='object')throw Error('Unbekanntes Dateiformat.');
   if(doc.format===FORMAT){
     if(doc.version!==VERSION)throw Error('Unbekannte Dateiversion.');
     return doc;
   }
   if(doc.format!==LEGACY_FORMAT||!LEGACY_VERSIONS.includes(doc.version))throw Error('Unbekanntes Dateiformat.');
   const known=LEGACY_MODELS[doc.model];
   if(!known)throw Error('Unbekanntes Modell in der Altdatei.');
   const markings=doc.version===1
     ?[{id:LEGACY_TARGET_ID,tool:'point',comment:'',diameter_mm:null,samples:[sample(doc.target)]}]
     :doc.markings.map(m=>({id:m.id,tool:m.tool,comment:m.comment,diameter_mm:m.diameter_mm,samples:m.samples.map(sample)}));
   return {format:FORMAT,version:VERSION,created_at:doc.created_at,
     model:{id:known[0],kind:known[1],name:doc.model,asset:doc.asset,asset_sha256:doc.asset_sha256},
     requested_change:doc.requested_change,markings,migrated_from:{format:LEGACY_FORMAT,version:doc.version}};
 }
 root.FormgenChangeRequest={FORMAT,VERSION,LEGACY_FORMAT,LEGACY_VERSIONS,LEGACY_TARGET_ID,LEGACY_MODELS,LOCATION_KEYS,migrate};
})(typeof window==='undefined'?this:window);
