async function register(){
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;
  const res = await fetch('/api/register', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body:JSON.stringify({username,password})
  });
  alert(await res.text());
}

async function login(){
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;
  const res = await fetch('/api/login', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body:JSON.stringify({username,password})
  });
  const j = await res.json();
  if(j.status === 'ok'){
    document.getElementById('crud').style.display = 'block';
    loadNotes();
  } else alert('Invalid credentials');
}

async function logout(){
  await fetch('/api/logout', {method:'POST'});
  document.getElementById('crud').style.display='none';
}

async function createNote(){
  const topic = document.getElementById('topic').value;
  const message = document.getElementById('message').value;
  await fetch('/api/notes', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body:JSON.stringify({topic,message})
  });
  loadNotes();
}

async function loadNotes(){
  const res = await fetch('/api/notes');
  const j = await res.json();
  const ul = document.getElementById('notesList');
  ul.innerHTML = '';
  if(j.status === 'ok'){
    for(const n of j.notes){
      const li = document.createElement('li');
      li.textContent = `[${n.note_id}] ${n.topic} - ${n.message}`;
      ul.appendChild(li);
    }
  }
}

async function sendLLM(){
  const prompt = document.getElementById('nlcmd').value;
  const res = await fetch('/api/llm', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body:JSON.stringify({prompt})
  });
  const data = await res.json();
  document.getElementById('llmResult').innerText =
    JSON.stringify(data, null, 2);
  loadNotes();
}
