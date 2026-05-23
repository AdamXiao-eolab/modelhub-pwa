var UD=localStorage.getItem("mh_ud")||"",EM=localStorage.getItem("mh_em")||"",AK=localStorage.getItem("mh_ak")||"";

// Onboarding step tracking
var ONBOARDING_STEP = parseInt(localStorage.getItem("mh_onboarding") || "0");

function setOnboardingStep(step) {
  ONBOARDING_STEP = Math.max(ONBOARDING_STEP, step);
  localStorage.setItem("mh_onboarding", String(ONBOARDING_STEP));
  renderOnboardingBar();
}

function dismissOnboarding() {
  ONBOARDING_STEP = 4;
  localStorage.setItem("mh_onboarding", "4");
  renderOnboardingBar();
}

function renderOnboardingBar() {
  var el = document.getElementById("ob-bar");
  if (!el) return;
  if (ONBOARDING_STEP >= 4) { el.style.display = "none"; return; }
  el.style.display = "block";
  
  var steps = [
    { num: 1, title: "复制你的 API Key", desc: "复制下方 Key 到剪贴板", done: ONBOARDING_STEP >= 1, action: "copyQuickstart(); setOnboardingStep(1);" },
    { num: 2, title: "一键测试请求", desc: "点击发送，验证连接", done: ONBOARDING_STEP >= 2, action: "runTestFromDashboard(); setOnboardingStep(2);" },
    { num: 3, title: "接入你的项目", desc: "查看文档，开始集成", done: ONBOARDING_STEP >= 3, action: "window.location.href='docs.html';" }
  ];
  
  var html = '<div class="obc"><div class="obh"><span class="obl">&#127881; 快速上手教程</span><button class="obd" onclick="dismissOnboarding()">&#10005;</button></div><div class="obs">';
  steps.forEach(function(s) {
    html += '<div class="osi' + (s.done ? ' od' : '') + '" onclick="' + (s.done ? '' : s.action) + '">';
    html += '<div class="oc' + (s.done ? ' ocd' : '') + '">' + (s.done ? '&#10003;' : s.num) + '</div>';
    html += '<div class="oi"><div class="ot">' + s.title + '</div><div class="odc">' + s.desc + '</div></div>';
    html += '</div>';
  });
  html += '</div></div>';
  el.innerHTML = html;
}

function sd(){
  document.getElementById("ac").style.display="none";
  document.getElementById("dc").style.display="block";
  ld();
  renderOnboardingBar();
}

if(UD&&AK)sd();

function signup(){
  var e=document.getElementById("se").value.trim();
  if(!e||!e.includes("@")) return st("Enter valid email","er");
  fetch("/v1/auth/signup",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({email:e})
  }).then(function(r){
    if(!r.ok) throw new Error("HTTP "+r.status);
    return r.json();
  }).then(function(d){
    if(d.error) throw new Error(d.error.message||"Failed");
    document.getElementById("sf").style.display="none";
    document.getElementById("lf").style.display="none";
    document.getElementById("ss").style.display="block";
    document.getElementById("nk").textContent=d.api_key;
    UD=d.user_id; EM=d.email; AK=d.api_key;
    localStorage.setItem("mh_ud",UD);
    localStorage.setItem("mh_em",EM);
    localStorage.setItem("mh_ak",AK);
  }).catch(function(e){
    st("Error: "+e.message,"er");
  });
}

function login(){
  var e=document.getElementById("le").value.trim(),k=document.getElementById("lk").value.trim();
  if(!e||!k) return st("Fill both fields","er");
  fetch("/v1/auth/login",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({email:e,api_key:k})
  }).then(function(r){
    if(!r.ok) throw new Error("HTTP "+r.status);
    return r.json();
  }).then(function(d){
    if(d.error) throw new Error("Invalid email or key");
    UD=d.user_id; EM=e; AK=k;
    localStorage.setItem("mh_ud",UD);
    localStorage.setItem("mh_em",EM);
    localStorage.setItem("mh_ak",AK);
    sd();
  }).catch(function(e){
    st("Error: "+e.message,"er");
  });
}

function logout(){
  localStorage.removeItem("mh_ud");
  localStorage.removeItem("mh_em");
  localStorage.removeItem("mh_ak");
  UD="";EM="";AK="";
  document.getElementById("dc").style.display="none";
  document.getElementById("ac").style.display="block";
  document.getElementById("sf").style.display="block";
  document.getElementById("lf").style.display="none";
  document.getElementById("ss").style.display="none";
}

function showLogin(){
  document.getElementById("sf").style.display="none";
  document.getElementById("lf").style.display="block";
}

function showSignup(){
  document.getElementById("lf").style.display="none";
  document.getElementById("sf").style.display="block";
}

function goToDashboard(){sd();}

function copyKey(){
  navigator.clipboard.writeText(document.getElementById("nk").textContent).then(function(){
    st("Copied!","ok");
    document.getElementById("ckb").textContent="Copied!";
    setTimeout(function(){document.getElementById("ckb").textContent="Copy";},2000);
  });
}

function copyNewKey(){
  navigator.clipboard.writeText(document.getElementById("krv").textContent).then(function(){
    st("Copied!","ok");
    document.getElementById("cnkb").textContent="Copied!";
    setTimeout(function(){document.getElementById("cnkb").textContent="Copy";},2000);
  });
}

function copyText(t){
  navigator.clipboard.writeText(t).then(function(){st("Copied!","ok");});
}

function copyQuickstart(){
  navigator.clipboard.writeText(document.getElementById("qak").textContent).then(function(){
    st("Copied!","ok");
    setOnboardingStep(1);
  });
}

function copyCurlCommand(){
  var cmd='curl https://modelhub-api.com/v1/chat/completions -H "Content-Type: application/json" -H "Authorization: Bearer '+AK+'" -d \'{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"Hello!"}]}\'';
  navigator.clipboard.writeText(cmd).then(function(){st("cURL copied!","ok");});
}

function st(m,t){
  var e=document.getElementById("tt");
  e.textContent=m;
  e.className="tt s "+(t||"");
  clearTimeout(e._t);
  e._t=setTimeout(function(){e.className="tt";},4000);
}

function ld(){
  document.getElementById("ue").textContent=EM;
  fetch("/v1/account",{headers:{"Authorization":"Bearer "+AK}}).then(function(r){return r.json();}).then(function(d){
    if(d.error) return logout();
    document.getElementById("sb").textContent="$"+d.balance.toFixed(2);
    document.getElementById("st").textContent=d.monthly_tokens_used||0;
    document.getElementById("sr").textContent=d.total_requests||0;
    var p=document.getElementById("up");
    p.textContent=d.plan_name||d.plan||"free";
    p.className="pt "+(d.plan||"free");
  }).catch(function(){});
  document.getElementById("qak").textContent=AK;
  fetch("/v1/account/keys",{headers:{"Authorization":"Bearer "+AK}}).then(function(r){return r.json();}).then(function(d){
    var l=document.getElementById("kl");
    if(!d.keys||!d.keys.length){
      l.innerHTML='<div class="em"><div class="ei">🔑</div><h3>No API Keys</h3><p>Create your first API key to start.</p></div>';
      return;
    }
    l.innerHTML=d.keys.map(function(k){
      var s=k.revoked?"r":"a",sl=k.revoked?"Revoked":"Active";
      return '<div class="kr"><div class="ki"><div class="kn">'+esc(k.name||"Untitled")+' <span class="ks '+s+'">'+sl+'</span></div><div class="kv">'+esc(k.key)+'</div></div><div class="ka">'+(k.revoked?"":'<button class="d" onclick="confirmRevoke(\''+k.id+'\',\''+esc(k.name||"this key")+'\')">Revoke</button>')+'</div></div>';
    }).join("");
  }).catch(function(){});
}

function esc(s){var d=document.createElement("div");d.textContent=s;return d.innerHTML;}

function runTest(ak,oe,be){
  if(!ak) return st("No API key","er");
  oe.className="to show"; oe.textContent="Sending..."; be.disabled=true; be.textContent="Testing...";
  fetch("https://modelhub-api.com/v1/chat/completions",{
    method:"POST",
    headers:{"Content-Type":"application/json","Authorization":"Bearer "+ak},
    body:JSON.stringify({model:"deepseek-v4-flash",messages:[{role:"user",content:"Just say 'Hello from DeepSeek!' and nothing else."}]})
  }).then(function(r){
    if(!r.ok) throw new Error("HTTP "+r.status);
    return r.json();
  }).then(function(d){
    oe.style.color="#34d399";
    oe.textContent="Success! AI replied: "+d.choices[0].message.content;
  }).catch(function(e){
    oe.style.color="#ef4444";
    oe.textContent="Error: "+e.message;
  }).finally(function(){
    be.disabled=false; be.textContent="Test Request";
  });
}

function runTestFromRegister(){
  runTest(AK,document.getElementById("rto"),document.getElementById("rtb"));
}

function runTestFromDashboard(){
  runTest(AK,document.getElementById("dto"),document.getElementById("dtb"));
  setOnboardingStep(2);
}

function loadDash(){
  document.getElementById("ue").textContent=EM;
  fetch("/v1/account",{headers:{"Authorization":"Bearer "+AK}}).then(function(r){return r.json();}).then(function(d){
    if(d.error) return logout();
    document.getElementById("sb").textContent="$"+d.balance.toFixed(2);
    document.getElementById("st").textContent=d.monthly_tokens_used||0;
    document.getElementById("sr").textContent=d.total_requests||0;
    var p=document.getElementById("up");
    p.textContent=d.plan_name||d.plan||"free";
    p.className="pt "+(d.plan||"free");
  }).catch(function(){});
  document.getElementById("qak").textContent=AK;
  fetch("/v1/account/keys",{headers:{"Authorization":"Bearer "+AK}}).then(function(r){return r.json();}).then(function(d){
    var l=document.getElementById("kl");
    if(!d.keys||!d.keys.length){
      l.innerHTML='<div class="em"><div class="ei">🔑</div><h3>No API Keys</h3><p>Create your first API key to start.</p></div>';
      return;
    }
    l.innerHTML=d.keys.map(function(k){
      var s=k.revoked?"r":"a",sl=k.revoked?"Revoked":"Active";
      return '<div class="kr"><div class="ki"><div class="kn">'+esc(k.name||"Untitled")+' <span class="ks '+s+'">'+sl+'</span></div><div class="kv">'+esc(k.key)+'</div></div><div class="ka">'+(k.revoked?"":'<button class="d" onclick="confirmRevoke(\''+k.id+'\',\''+esc(k.name||"this key")+'\')">Revoke</button>')+'</div></div>';
    }).join("");
  }).catch(function(){});
}

function showCreateKeyModal(){
  document.getElementById("nkn").value="";
  document.getElementById("ckm").className="mo o";
}

function closeCreateKeyModal(){
  document.getElementById("ckm").className="mo";
}

function createKey(){
  var n=document.getElementById("nkn").value.trim()||"My Key";
  closeCreateKeyModal();
  fetch("/v1/account/keys",{
    method:"POST",
    headers:{"Authorization":"Bearer "+AK,"Content-Type":"application/json"},
    body:JSON.stringify({name:n})
  }).then(function(r){
    if(!r.ok) throw new Error("HTTP "+r.status);
    return r.json();
  }).then(function(d){
    if(d.error) throw new Error(d.error.message||"Failed");
    document.getElementById("krv").textContent=d.key;
    document.getElementById("krm").style.display="flex";
    ld();
  }).catch(function(e){st("Error: "+e.message,"er");});
}

function closeKeyResultModal(){document.getElementById("krm").className="mo";}

function confirmRevoke(id,name){
  if(!confirm('Revoke "'+name+'"? This cannot be undone.')) return;
  fetch("/v1/account/keys/"+id,{method:"DELETE",headers:{"Authorization":"Bearer "+AK}}).then(function(r){return r.json();}).then(function(){st("Key revoked","ok");ld();}).catch(function(){st("Failed","er");});
}

// ===== AI Chat Assistant =====
function toggleAIChat(){
  var el=document.getElementById("aichat");
  el.style.display=el.style.display==="flex"?"none":"flex";
  if(el.style.display==="flex"){
    var input=document.getElementById("aimsg");
    input.focus();
    input.selectionStart=input.selectionEnd=input.value.length;
  }
}

function sendAIChat(){
  var input=document.getElementById("aimsg");
  var msg=input.value.trim();
  if(!msg) return;
  var box=document.getElementById("aibox");
  box.innerHTML+='<div class="aiu aiur"><div class="aic">'+esc(msg)+'</div></div>';
  input.value="";
  box.scrollTop=box.scrollHeight;
  
  var loading=document.createElement("div");
  loading.className="aiu aias";
  loading.innerHTML='<div class="aic"><div class="aith">...</div></div>';
  loading.id="aiload";
  box.appendChild(loading);
  box.scrollTop=box.scrollHeight;
  
  fetch("https://modelhub-api.com/v1/chat/completions",{
    method:"POST",
    headers:{"Content-Type":"application/json","Authorization":"Bearer "+AK},
    body:JSON.stringify({
      model:"deepseek-v4-flash",
      messages:[
        {role:"system",content:"你是 ModelHub 官方助手。你帮助用户使用 ModelHub 平台。ModelHub 是一个提供中国 AI 模型的 API 平台，支持 DeepSeek V4 Flash，兼容 OpenAI 协议。以下是常见问题的回答：\\n\\nQ: 如何获取 API Key？\\nA: 在 dashboard.modelhub-api.com 注册即可获得免费的 API Key。注册即送 $5 免费额度。\\n\\nQ: 价格是多少？\\nA: 我们有两个订阅方案：Backpack $15/月（含 100M tokens）和 Launch $65/月（含 500M tokens），也可以按量付费，DeepSeek V4 Flash 输入 $0.15/百万 token，输出 $0.30/百万 token。\\n\\nQ: 如何调用 API？\\nA: ModelHub 完全兼容 OpenAI 协议，只需将 base_url 改为 https://modelhub-api.com/v1，API Key 改为你的 ModelHub Key 即可。\\n\\nQ: 支持哪些模型？\\nA: 当前支持 DeepSeek V4 Flash，即将推出 DeepSeek Reasoner、Qwen 3、GLM-7 等。\\n\\nQ: 如何进行支付？\\nA: 支持 Paypal、信用卡、加密货币。点击 Dashboard 中的 Upgrade Plan 即可。\\n\\n请用中文回答，保持友好专业的语气。"},
        {role:"user",content:msg}
      ]
    })
  }).then(function(r){
    if(!r.ok) throw new Error("HTTP "+r.status);
    return r.json();
  }).then(function(d){
    var loader=document.getElementById("aiload");
    if(loader) loader.remove();
    var reply=d.choices[0].message.content;
    box.innerHTML+='<div class="aiu aib"><div class="aic aip">'+esc(reply).replace(/\n/g,"<br>")+'</div></div>';
    box.scrollTop=box.scrollHeight;
  }).catch(function(e){
    var loader=document.getElementById("aiload");
    if(loader) loader.remove();
    box.innerHTML+='<div class="aiu aib"><div class="aic aip" style="color:#ef4444;">抱歉，发生了错误：'+esc(e.message)+'</div></div>';
    box.scrollTop=box.scrollHeight;
  });
}

function handleAIKeyPress(e){
  if(e.key==="Enter" && !e.shiftKey){
    e.preventDefault();
    sendAIChat();
  }
}
