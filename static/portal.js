// portal.js — shared tab navigation

function showTab(name, navEl){
  document.querySelectorAll('.tab-pane').forEach(p=>{
    p.classList.remove('active');
    p.classList.add('hidden');
  });
  const target=document.getElementById('tab-'+name);
  if(target){
    target.classList.remove('hidden');
    target.classList.add('active');
  }
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
  if(navEl) navEl.classList.add('active');
  else {
    document.querySelectorAll('.nav-item').forEach(n=>{
      if(n.getAttribute('onclick')&&n.getAttribute('onclick').includes("'"+name+"'"))
        n.classList.add('active');
    });
  }
}