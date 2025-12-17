document.addEventListener('DOMContentLoaded',function(){
  const tutteCheckbox=document.getElementById('tutte');
  const classiCheckboxes=document.querySelectorAll('input[name="classi"]');
  const classiBox=document.querySelector('.classi-box');
  const form=document.querySelector('form');

  function toggleClassiIndividuali(disabled){
    classiCheckboxes.forEach(cb=>{
      cb.disabled=disabled;
      if(disabled) cb.checked=false;
    });
    if(classiBox){
      if(disabled) classiBox.classList.add('disabled');
      else classiBox.classList.remove('disabled');
    }
  }

  if(tutteCheckbox){
    if(tutteCheckbox.checked) toggleClassiIndividuali(true);
    tutteCheckbox.addEventListener('change',function(){
      if(this.checked) classiCheckboxes.forEach(cb=>cb.checked=false);
      toggleClassiIndividuali(this.checked);
    });
  }

  classiCheckboxes.forEach(cb=>{
    cb.addEventListener('change',function(){
      const almenoUnaSelezionata=Array.from(classiCheckboxes).some(x=>x.checked);
      if(tutteCheckbox){
        if(almenoUnaSelezionata){
          tutteCheckbox.disabled=true;
          tutteCheckbox.checked=false;
        }else{
          tutteCheckbox.disabled=false;
        }
      }
    });
  });

  if(form){
    form.addEventListener('submit',function(){
      const loading=document.getElementById('loading');
      const submitButton=form.querySelector('button[type="submit"]');
      if(loading){
        loading.classList.add('active');
        if(submitButton) submitButton.disabled=true;
      }
    });
  }

  function preventDefaults(e){
    e.preventDefault();
    e.stopPropagation();
  }

  ['dragenter','dragover','dragleave','drop'].forEach(ev=>{
    document.addEventListener(ev,preventDefaults,false);
  });

  function setFiles(input,files){
    const dt=new DataTransfer();
    Array.from(files).forEach(f=>dt.items.add(f));
    input.files=dt.files;
  }

  function bindDropZone(zone){
    const input=zone.querySelector('input[type="file"]');
    const strong=zone.querySelector('.upload-text strong');
    if(!input||!strong) return;

    if(!zone.dataset.originalText) zone.dataset.originalText=strong.textContent;

    let counter=0;

    function updateText(file){
      strong.textContent=`✓ ${file.name}`;
      strong.style.color='var(--success)';
    }

    ['dragenter','dragover'].forEach(ev=>{
      zone.addEventListener(ev,function(){
        counter++;
        zone.classList.add('drag-over');
      },false);
    });

    ['dragleave','drop'].forEach(ev=>{
      zone.addEventListener(ev,function(){
        counter--;
        if(counter<=0){
          counter=0;
          zone.classList.remove('drag-over');
        }
      },false);
    });

    zone.addEventListener('drop',function(e){
      counter=0;
      zone.classList.remove('drag-over');
      const files=e.dataTransfer.files;
      if(files&&files.length>0){
        setFiles(input,files);
        updateText(files[0]);
      }
    },false);

    input.addEventListener('change',function(){
      if(input.files&&input.files.length>0) updateText(input.files[0]);
      else{
        strong.textContent=zone.dataset.originalText;
        strong.style.color='';
      }
    });
  }

  document.querySelectorAll('.upload-area').forEach(bindDropZone);
});

