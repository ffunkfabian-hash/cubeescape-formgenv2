// Filter der Waffenseite: Suchtext und Variante; Abschnitte ohne Treffer verschwinden.
(function(){
 const q=document.querySelector('input[type=search]'),s=document.querySelector('.tools select');
 if(!q)return;
 function filter(){
   const text=q.value.toLowerCase();
   for(const c of document.querySelectorAll('.card'))c.hidden=!(c.textContent.toLowerCase().includes(text)&&(!s.value||c.dataset.variant===s.value));
   for(const g of document.querySelectorAll('main section'))g.hidden=![...g.querySelectorAll('.card')].some(c=>!c.hidden);
 }
 q.addEventListener('input',filter);s.addEventListener('change',filter);
})();
