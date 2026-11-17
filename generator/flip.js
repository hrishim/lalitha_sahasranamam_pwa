(function(){
var $=function(i){return document.getElementById(i)};
var stage=document.querySelector('.stage'),book=$('book'),flow=$('flow'),vp=book.querySelector('.viewport');
var zoom=100,cur=0,total=1,step=1,single=false,G=60,anchors={},segs=[];
function layout(){
  dropEnv();
  var sw=window.innerWidth,sh=stage.clientHeight;
  single=sw<900;
  var bw=single?Math.min(sw-20,560):Math.min(sw-110,1100),bh=Math.min(sh-16,single?sh-16:820);
  book.style.width=bw+'px';book.style.height=bh+'px';book.classList.toggle('single',single);
  document.documentElement.style.setProperty('--fs',(single?16:17)*zoom/100+'px');
  var W=vp.clientWidth,H=vp.clientHeight;
  flow.style.width=W+'px';flow.style.height=H+'px';
  flow.style.columnCount=single?1:2;flow.style.columnGap=G+'px';
  $('blank').style.display=single?'none':'block';
  void flow.offsetWidth;
  var colw=single?W:(W-G)/2;step=colw+G;
  var base=flow.getBoundingClientRect().left;
  var firstTransform=flow.style.transform;flow.style.transition='none';flow.style.transform='none';
  base=flow.getBoundingClientRect().left;
  total=Math.max(1,Math.round((flow.scrollWidth+G)/step));
  var ids=document.querySelectorAll('#flow [id]');anchors={};
  ids.forEach(function(e){if(e.id==='blank')return;
    anchors[e.id]=Math.max(0,Math.round((e.getBoundingClientRect().left-base)/step));});
  segs=[];var kids=flow.children;
  for(var i=0;i<kids.length;i++){var k=kids[i];
    if(i===0||k.classList.contains('chap-head')||k.classList.contains('front-head'))
      segs.push({nodes:[k],start:Math.max(0,Math.round((k.getBoundingClientRect().left-base)/step))});
    else segs[segs.length-1].nodes.push(k);}
  flow.style.transform=firstTransform;
  void flow.offsetWidth;flow.style.transition='';
}
function segIdx(p){var j=0;for(var i=0;i<segs.length;i++){if(segs[i].start<=p)j=i;else break}return j}
function pageLabel(p){return single?p+1:p}
function show(noAnim){
  var spreadStart=single?cur:cur-(cur%2);
  cur=Math.max(0,Math.min(spreadStart,total-1));
  flow.style.transform='translateX('+(-cur*step)+'px)';
  var a=single?cur:cur,b=Math.min(total-1,cur+1);
  var shownA=single?cur+1:Math.max(cur,1),shownB=single?null:b;
  var nPages=single?total:total-1; // exclude blank left page in spread mode
  var txt=single?('Page '+(cur+1)+' / '+total):(cur===0?'Cover':('Pages '+cur+(b<total&&b!==cur?'–'+b:'')))+' / '+(total-1);
  $('pg').textContent=txt;
  if(!noAnim){vp.classList.remove('turn');void vp.offsetWidth;vp.classList.add('turn');}
  try{history.replaceState(null,'','#p='+cur)}catch(e){}
  try{localStorage.setItem('pos-'+document.title,cur)}catch(e){}
}
var env=null,animating=false,pending=null,TURN_MS=1500;
function norm(p){var s=single?p:p-(p%2);return Math.max(0,Math.min(s,total-1))}
function mkVP(){
  var d=document.createElement('div');d.className='lf-vp';
  d.style.cssText='top:'+vp.offsetTop+'px;width:'+vp.clientWidth+'px;height:'+vp.clientHeight+'px';
  var f=flow.cloneNode(false);f.removeAttribute('id');f.className='lf-flow';
  f.style.transition='none';f.style.columnFill='auto';f.style.willChange='transform';
  d.appendChild(f);return {box:d,flow:f};
}
function fillVP(c,spread){
  var s1=segIdx(spread),s2=segIdx(Math.min(total-1,spread+1));
  c.flow.textContent='';
  for(var i=s1;i<=s2;i++)segs[i].nodes.forEach(function(n){
    var cl=n.cloneNode(true);cl.removeAttribute('id');
    cl.querySelectorAll('[id]').forEach(function(e){e.removeAttribute('id')});
    c.flow.appendChild(cl)});
  c.flow.style.transform='translateX('+(-(spread-segs[s1].start)*step)+'px)';
}
function buildEnv(){
  if(single||env)return;
  var bw=book.offsetWidth,L=vp.offsetLeft;
  var layer=document.createElement('div');layer.className='lf-layer';layer.style.display='none';
  var A=mkVP(),B=mkVP(),D=mkVP();
  var under=document.createElement('div');under.className='lf-half';under.appendChild(D.box);
  var leaf=document.createElement('div');leaf.className='lf-leaf';
  var front=document.createElement('div');front.className='lf-face';front.appendChild(A.box);
  var fs=document.createElement('div');fs.className='lf-shade';front.appendChild(fs);
  var back=document.createElement('div');back.className='lf-face';back.appendChild(B.box);
  var bs=document.createElement('div');bs.className='lf-shade';back.appendChild(bs);
  leaf.appendChild(front);leaf.appendChild(back);layer.appendChild(under);layer.appendChild(leaf);
  book.appendChild(layer);
  env={layer:layer,under:under,leaf:leaf,front:front,back:back,fs:fs,bs:bs,A:A,B:B,D:D,bw:bw,L:L};
}
function dropEnv(){if(env){env.layer.remove();env=null}}
function setSpread(c,s){c.flow.style.transform='translateX('+(-s*step)+'px)'}
function paper(el,off){
  var cs=getComputedStyle(book),w=book.offsetWidth+'px',h=book.offsetHeight+'px';
  el.style.backgroundColor=cs.backgroundColor;el.style.backgroundImage=cs.backgroundImage;
  el.style.backgroundSize='260px 260px,'+w+' '+h+','+w+' '+h+','+w+' '+h;
  var o=(-off)+'px 0';el.style.backgroundPosition=o+','+o+','+o+','+o;
}
function flip(np){
  var fwd=np>cur,e=env,h=e.bw/2,L=e.L,old=cur;
  animating=true;
  e.layer.style.display='block';
  var rightOff=L-h;
  e.leaf.style.left=fwd?'50%':'0';e.under.style.left=fwd?'50%':'0';
  e.leaf.style.transformOrigin=fwd?'left center':'right center';
  e.front.className='lf-face';e.back.className='lf-face';
  e.under.className='lf-half';
  e.back.style.transform='rotateY(180deg)';
  paper(e.front,fwd?e.bw/2:0);paper(e.back,fwd?0:e.bw/2);paper(e.under,fwd?e.bw/2:0);
  e.A.box.style.left=(fwd?rightOff:L)+'px';
  e.B.box.style.left=(fwd?L:rightOff)+'px';
  e.D.box.style.left=(fwd?rightOff:L)+'px';
  fillVP(e.A,old);fillVP(e.B,np);fillVP(e.D,np);
  var rot=fwd?-180:180,ease='cubic-bezier(.4,.02,.2,1)';
  var a1=e.leaf.animate([{transform:'rotateY(0deg)'},{transform:'rotateY('+rot+'deg)'}],{duration:TURN_MS,easing:ease,fill:'forwards'});
  e.fs.animate([{opacity:0},{opacity:.55}],{duration:TURN_MS/2,easing:'ease-in',fill:'forwards'});
  e.bs.animate([{opacity:.5},{opacity:0}],{duration:TURN_MS,easing:'ease-out',fill:'forwards'});
  a1.onfinish=function(){
    flow.style.transition='none';cur=np;show(true);void flow.offsetWidth;flow.style.transition='';
    e.layer.style.display='none';
    [e.A,e.B,e.D].forEach(function(c){c.flow.textContent=''});
    [e.leaf,e.fs,e.bs].forEach(function(x){x.getAnimations().forEach(function(a){a.cancel()})});
    animating=false;
    if(pending!=null){var p=pending;pending=null;go(p)}
  };
}
function go(p){
  var np=norm(p);
  if(animating){pending=p;return}
  if(np===cur){show(true);return}
  if(!single&&env&&matchMedia('(prefers-reduced-motion: no-preference)').matches)flip(np);
  else{cur=np;show()}
}
function next(){go(cur+(single?1:2))}
function prev(){go(cur-(single?1:2))}
function fit(){
  var open=$('toc').classList.contains('open')&&!single;
  stage.style.left=open?'340px':'0';
  var bw=book.offsetWidth,k=open?Math.min(1,(window.innerWidth-340-30)/bw):1;
  book.style.transform=k<1?'scale('+k+')':'';
}
function toc(){
  document.querySelectorAll('#flow a.ix').forEach(function(a){
    var id=a.getAttribute('data-go'),p=anchors[id];
    var s=a.querySelector('[data-pg]');if(s&&p!=null)s.textContent=single?p+1:p;
    a.onclick=function(e){e.preventDefault();if(anchors[id]!=null)go(anchors[id])};
  });
  document.querySelectorAll('#toc [data-go]').forEach(function(a){
    var id=a.getAttribute('data-go'),p=anchors[id];
    a.querySelector('[data-pg]').textContent=p==null?'':(single?p+1:p);
    a.onclick=function(){go(anchors[id]);if(single){$('toc').classList.remove('open');fit()}};
  });
}
$('next').onclick=$('next2').onclick=next;$('prev').onclick=$('prev2').onclick=prev;
$('first').onclick=function(){go(0)};
$('menu').onclick=$('contents').onclick=function(){$('toc').classList.toggle('open');fit()};
$('go').onclick=function(){var n=parseInt($('gopage').value,10);if(n>0)go(single?n-1:n)};
$('gopage').onkeydown=function(e){if(e.key==='Enter')$('go').click()};
(function(){var d=document.documentElement,rq=d.requestFullscreen||d.webkitRequestFullscreen,ex=document.exitFullscreen||document.webkitExitFullscreen,b=$('fs');
if(!rq||!(document.fullscreenEnabled||document.webkitFullscreenEnabled))return;b.style.display='';
b.onclick=function(){try{if(document.fullscreenElement||document.webkitFullscreenElement)ex.call(document);else rq.call(d)}catch(e){}};
function lab(){b.textContent=(document.fullscreenElement||document.webkitFullscreenElement)?'Exit full screen':'⛶ Full screen'}
document.addEventListener('fullscreenchange',lab);document.addEventListener('webkitfullscreenchange',lab)})();
$('larger').onclick=function(){zoom=Math.min(160,zoom+10);relayout()};
$('smaller').onclick=function(){zoom=Math.max(70,zoom-10);relayout()};
document.addEventListener('keydown',function(e){if(e.target.tagName==='INPUT')return;
  if(e.key==='ArrowRight')next();else if(e.key==='ArrowLeft')prev();});
function relayout(){
  var frac=total>1?cur/total:0;
  layout();cur=Math.round(frac*total);toc();fit();show(true);$('zoom').textContent=zoom+'%';idle();
}
function idle(){}
var rt,lw=window.innerWidth,lh=window.innerHeight;window.addEventListener('resize',function(){clearTimeout(rt);rt=setTimeout(function(){if(!started||(window.innerWidth===lw&&window.innerHeight===lh))return;lw=window.innerWidth;lh=window.innerHeight;relayout()},200)});
function start(){
  layout();toc();
  var m=/#p=(\d+)/.exec(location.hash),h=location.hash.slice(1);
  if(m)cur=+m[1];else if(h&&anchors[h]!=null)cur=anchors[h];
  flow.style.transition='none';show();void flow.offsetWidth;flow.style.transition='';
}
var started=false;
try{layout();flow.style.transition='none';flow.style.transform='translateX(0px)';$('pg').textContent='Cover'}catch(e){}
function begin(){
  if(started)return;started=true;
  document.body.classList.add('go');start();document.body.classList.add('ready');idle();
}
var fonts=document.fonts&&document.fonts.load?Promise.all([
  document.fonts.load('17px "Noto Serif"'),document.fonts.load('italic 17px "Noto Serif"'),
  document.fonts.load('17px "Noto Serif"','\u0101\u1e47'),document.fonts.load('17px "Noto Serif Devanagari"','\u0936\u094d\u0930\u0940')
]):Promise.resolve();
Promise.race([fonts,new Promise(function(r){setTimeout(r,4000)})]).catch(function(){}).then(function(){
  requestAnimationFrame(function(){setTimeout(begin,0)});
});
})();
