/**
 * Fingerprint v3.12.6 - Copyright (c) FingerprintJS, Inc, 2026 (https://fingerprint.com)
 */

function n(n,e) {
  return new Promise((r=>t$1(r,n,e)))
}
function t$1(n,t,...e) {
  const r=Date.now()+t;
  let o=0;
  const i=()=> {
    o=setTimeout((()=> {
      Date.now()<r?i():n(...e);
    }),r-Date.now());
  };
  return i(),()=>clearTimeout(o)
}
function e$1(n,e,...r) {
  const o=document,i="visibilitychange",u=()=>o.hidden?s():c(), {
    start:c,stop:s
  }
  =function(n,e,r,...o) {
    let i,u=false,c=n,s=0;
    const a=()=> {
      u||i||(s=Date.now(),i=t$1((()=> {
        u=true,r(...o);
      }),c));
    };
    return e&&a(), {
      start:a,stop:()=> {
        !u&&i&&(i(),i=undefined,c-=Date.now()-s);
      }

    }

  }
  (e,!o.hidden,(()=> {
    o.removeEventListener(i,u),n(...r);
  }));
  return o.addEventListener(i,u),()=> {
    o.removeEventListener(i,u),s();
  }

}
function r$1(n,t) {
  return new Promise((r=>e$1(r,n,t)))
}
async function o$1(n,t) {
  try {
    return await n()
  } catch(e) {
    return console.error(e),t
  }

}
function i$1(n,t) {
  return new Promise(((e,r)=> {
    let o=false;
    null==t||t.then((()=>o=true),(()=>o=true));
    ("function"==typeof n?i$1(Promise.resolve(),t).then(n):n).then((n=> {
      o||e(n);
    }),(n=> {
      o||r(n);
    }));
  }))
}
function u$1(n) {
  return n.then(undefined,(()=> {

  })),n
}
async function c$1(n,t) {
  let e,r,o;
  try {
    e=t().then((n=>r=[true,n]),(n=>r=[false,n]));
  } catch(u) {
    r=[false,u];
  }
  const i=n.then((n=>o=[true,n]),(n=>o=[false,n]));
  return await Promise.race([e,i]),()=> {
    if(r) {
      if(r[0])return r[1];
      throw r[1]
    }
    if(o) {
      if(o[0])return o[1];
      throw o[1]
    }
    throw new Error("96375")
  }

}
function s$1() {
  let n,t;
  const e=new Promise(((e,r)=> {
    n=e,t=r;
  }));
  return e.resolve=n,e.reject=t,e
}
function a$1(n) {
  return new Promise(((t,e)=> {
    n(t,e).then((()=>e(new Error("Action didn't call `resolve` or `reject`"))),e);
  }))
}
function l$1(n) {
  return n instanceof Error||null!==n&&"object"==typeof n&&"name"in n
}
function f$1(n,t) {
  let e=0;
  return ()=>Math.random()*Math.min(t,n*Math.pow(2,e++))
}
function d$1(n) {
  return n instanceof ArrayBuffer?new Uint8Array(n):new Uint8Array(n.buffer,n.byteOffset,n.byteLength)
}
function m$1(n,t) {
  return Object.prototype.hasOwnProperty.call(n,t)
}
function v$1(n,t,e,r) {
  return n.addEventListener(t,e,r),()=>n.removeEventListener(t,e,r)
}
const h$1="0123456789abcdef",p$1=65535;
function g$1(n,t) {
  if(0==t.length||t.length>n.length)return -1;
  for(let e=0;e<n.length;e++) {
    let r=0;
    for(let o=0;o<t.length;o++) {
      if(n[e+o]!==t[o]) {
        r=0;
        break
      }
      r++;
    }
    if(r==t.length)return e
  }
  return -1
}
function w$1(n) {
  const t=new Uint8Array(n.length);
  for(let e=0;e<n.length;e++) {
    const r=n.charCodeAt(e);
    if(r>127)return (new TextEncoder).encode(n);
    t[e]=r;
  }
  return t
}
function y$1(n) {
  if("function"==typeof TextDecoder) {
    const t=(new TextDecoder).decode(n);
    if(t)return t
  }
  const t=d$1(n);
  return decodeURIComponent(escape(String.fromCharCode.apply(null,t)))
}
function b$1(n) {
  return n.reduce(((n,t)=>n+(t?1:0)),0)
}
function E$1(n,t) {
  return (n-t+256)%256
}
function R$1(n) {
  const t=d$1(n),e=Math.ceil(t.length/p$1),r=[];
  for(let o=0;o<e;o++) {
    const n=o*p$1,e=t.slice(n,Math.min(n+p$1,t.length));
    r.push(String.fromCharCode.apply(null,e));
  }
  return btoa(r.join(""))
}
function S$1(n) {
  const t=atob(n),e=t.length,r=new Uint8Array(e);
  for(let o=0;o<e;o++)r[o]=t.charCodeAt(o);
  return r
}
function I$1(n) {
  return R$1(n).replace(/\+/g,"-").replace(/\//g,"_").replace(/=+$/,"")
}
let k$1;
function A(n) {
  return C(w$1(n))
}
function C(n) {
  const t=d$1(n);
  k$1=k$1||function() {
    let n;
    const t=new Uint32Array(256);
    for(let e=0;e<256;e++) {
      n=e;
      for(let t=0;t<8;t++)n=1&n?3988292384^n>>>1:n>>>1;
      t[e]=n;
    }
    return t
  }
  ();
  let e=-1;
  for(let r=0;r<t.length;r++)e=e>>>8^k$1[255&(e^t[r])];
  return (-1^e)>>>0
}
function L$1(n) {
  return undefined===n?undefined:`${n}`
}
function P$1(n,t) {
  if(undefined!==n) {
    if(!Array.isArray(n))throw new TypeError(`Expected ${t} to be an array, a ${function(n){return "object"==typeof n?n?Object.prototype.toString.call(n):"null":typeof n}(n)} is given`);
    return n.map(String)
  }

}
function x$1(n) {
  const t=new Uint8Array(n.length/2);
  for(let e=0;e<n.length;e+=2)t[e/2]=parseInt(n[e]+n[e+1],16);
  return t
}
function T$1(n) {
  if(n instanceof Array)return n.map(T$1);
  if(n&&"object"==typeof n) {
    const t= {

    };
    for(const e of Object.keys(n))t[e]=T$1(n[e]);
    return t
  }
  return n
}
function O$1(n,t) {
  const e=[],r=Object.getOwnPropertyNames(n);
  for(let o=0;o<r.length;o++) {
    const n=r[o],i=A(n);
    t.has(i)&&e.push( {
      i:o,n:n
    });
  }
  return  {
    l:r.length,p:e
  }

}
function _$1(n,t) {
  return new Promise((e=>setTimeout(e,n,t)))
}
function j$1(n) {
  return !!n&&"function"==typeof n.then
}
function V(n,t) {
  try {
    const e=n();
    j$1(e)?e.then((n=>t(true,n)),(n=>t(false,n))):t(true,e);
  } catch(e) {
    t(false,e);
  }

}
async function N(n,t,e=16) {
  const r=Array(n.length);
  let o=Date.now();
  for(let i=0;i<n.length;++i) {
    r[i]=t(n[i],i);
    const u=Date.now();
    u>=o+e&&(o=u,await new Promise((n=> {
      const t=new MessageChannel;
      t.port1.onmessage=()=>n(),t.port2.postMessage(null);
    })));
  }
  return r
}
function M$1(n) {
  return n.then(undefined,(()=> {

  })),n
}
function F(n) {
  return parseInt(n)
}
function D$1(n) {
  return parseFloat(n)
}
function W$1(n,t) {
  return "number"==typeof n&&isNaN(n)?t:n
}
function Z$1(n) {
  return n.reduce(((n,t)=>n+(t?1:0)),0)
}
function G$1(n,t) {
  const e=n[0]>>>16,r=65535&n[0],o=n[1]>>>16,i=65535&n[1],u=t[0]>>>16,c=65535&t[0],s=t[1]>>>16;
  let a=0,l=0,f=0,d=0;
  d+=i+(65535&t[1]),f+=d>>>16,d&=65535,f+=o+s,l+=f>>>16,f&=65535,l+=r+c,a+=l>>>16,l&=65535,a+=e+u,a&=65535,n[0]=a<<16|l,n[1]=f<<16|d;
}
function H$1(n,t) {
  const e=n[0]>>>16,r=65535&n[0],o=n[1]>>>16,i=65535&n[1],u=t[0]>>>16,c=65535&t[0],s=t[1]>>>16,a=65535&t[1];
  let l=0,f=0,d=0,m=0;
  m+=i*a,d+=m>>>16,m&=65535,d+=o*a,f+=d>>>16,d&=65535,d+=i*s,f+=d>>>16,d&=65535,f+=r*a,l+=f>>>16,f&=65535,f+=o*s,l+=f>>>16,f&=65535,f+=i*c,l+=f>>>16,f&=65535,l+=e*a+r*s+o*c+i*u,l&=65535,n[0]=l<<16|f,n[1]=d<<16|m;
}
function U$1(n,t) {
  const e=n[0];
  32===(t%=64)?(n[0]=n[1],n[1]=e):t<32?(n[0]=e<<t|n[1]>>>32-t,n[1]=n[1]<<t|e>>>32-t):(t-=32,n[0]=n[1]<<t|e>>>32-t,n[1]=e<<t|n[1]>>>32-t);
}
function B$2(n,t) {
  0!==(t%=64)&&(t<32?(n[0]=n[1]>>>32-t,n[1]=n[1]<<t):(n[0]=n[1]<<t-32,n[1]=0));
}
function $(n,t) {
  n[0]^=t[0],n[1]^=t[1];
}
const Y$1=[4283543511,3981806797],X=[3301882366,444984403];
function J$1(n) {
  const t=[0,n[0]>>>1];
  $(n,t),H$1(n,Y$1),t[1]=n[0]>>>1,$(n,t),H$1(n,X),t[1]=n[0]>>>1,$(n,t);
}
const q$1=[2277735313,289559509],z=[1291169091,658871167],K$1=[0,5],Q$1=[0,1390208809],nn=[0,944331445];
function tn(n) {
  return "function"!=typeof n
}
function en(n,t,e,r) {
  const o=Object.keys(n).filter((n=>!function(n,t) {
    for(let e=0,r=n.length;e<r;++e)if(n[e]===t)return true;
    return false
  }
  (e,n))),i=M$1(N(o,(e=>function(n,t) {
    const e=M$1(new Promise((e=> {
      const r=Date.now();
      V(n.bind(null,t),((...n)=> {
        const t=Date.now()-r;
        if(!n[0])return e((()=>( {
          error:n[1],duration:t
        })));
        const o=n[1];
        if(tn(o))return e((()=>( {
          value:o,duration:t
        })));
        e((()=>new Promise((n=> {
          const e=Date.now();
          V(o,((...r)=> {
            const o=t+Date.now()-e;
            if(!r[0])return n( {
              error:r[1],duration:o
            });
            n( {
              value:r[1],duration:o
            });
          }));
        }))));
      }));
    })));
    return function() {
      return e.then((n=>n()))
    }

  }
  (n[e],t)),r));
  return async function() {
    const n=await i,t=await N(n,(n=>M$1(n())),r),e=await Promise.all(t),u= {

    };
    for(let r=0;r<o.length;++r)u[o[r]]=e[r];
    return u
  }

}
function rn(n,t) {
  const e=n=>tn(n)?t(n):()=> {
    const e=n();
    return j$1(e)?e.then(t):t(e)
  };
  return t=> {
    const r=n(t);
    return j$1(r)?r.then(e):e(r)
  }

}
function on() {
  const n=window,t=navigator;
  return Z$1(["MSCSSMatrix"in n,"msSetImmediate"in n,"msIndexedDB"in n,"msMaxTouchPoints"in t,"msPointerEnabled"in t])>=4
}
function un() {
  const n=window,t=navigator;
  return Z$1(["msWriteProfilerMark"in n,"MSStream"in n,"msLaunchUri"in t,"msSaveBlob"in t])>=3&&!on()
}
function cn() {
  const n=window,t=navigator;
  return Z$1(["webkitPersistentStorage"in t,"webkitTemporaryStorage"in t,0===(t.vendor||"").indexOf("Google"),"webkitResolveLocalFileSystemURL"in n,"BatteryManager"in n,"webkitMediaStream"in n,"webkitSpeechGrammar"in n])>=5
}
function sn() {
  const n=window;
  return Z$1(["ApplePayError"in n,"CSSPrimitiveValue"in n,"Counter"in n,0===navigator.vendor.indexOf("Apple"),"RGBColor"in n,"WebKitMediaKeys"in n])>=4
}
function an() {
  const n=window, {
    HTMLElement:t,Document:e
  }
  =n;
  return Z$1(["safari"in n,!("ongestureend"in n),!("TouchEvent"in n),!("orientation"in n),t&&!("autocapitalize"in t.prototype),e&&"pointerLockElement"in e.prototype])>=4
}
function ln() {
  var n,t;
  const e=window;
  return Z$1(["buildID"in navigator,"MozAppearance"in(null!==(t=null===(n=document.documentElement)||undefined===n?undefined:n.style)&&undefined!==t?t: {

  }),"onmozfullscreenchange"in e,"mozInnerScreenX"in e,"CSSMozDocumentRule"in e,"CanvasCaptureMediaStream"in e])>=4
}
function fn() {
  const n=document;
  return n.fullscreenElement||n.msFullscreenElement||n.mozFullScreenElement||n.webkitFullscreenElement||null
}
function dn() {
  const n=cn(),t=ln(),e=window,r=navigator,o="connection";
  return n?Z$1([!("SharedWorker"in e),r[o]&&"ontypechange"in r[o],!("sinkId"in new Audio)])>=2:!!t&&Z$1(["onorientationchange"in e,"orientation"in e,/android/i.test(r.appVersion)])>=2
}
function mn() {
  const n=navigator,t=window,e=Audio.prototype, {
    visualViewport:r
  }
  =t;
  return Z$1(["srLatency"in e,"srChannelCount"in e,"devicePosture"in n,r&&"segments"in r,"getTextInformation"in Image.prototype])>=3
}
function vn() {
  const n=window,t=n.OfflineAudioContext||n.webkitOfflineAudioContext;
  if(!t)return -2;
  if(sn()&&!an()&&!function() {
    const n=window;
    return Z$1(["DOMRectList"in n,"RTCPeerConnectionIceEvent"in n,"SVGGeometryElement"in n,"ontransitioncancel"in n])>=3
  }
  ())return -1;
  const e=new t(1,5e3,44100),r=e.createOscillator();
  r.type="triangle",r.frequency.value=1e4;
  const o=e.createDynamicsCompressor();
  o.threshold.value=-50,o.knee.value=40,o.ratio.value=12,o.attack.value=0,o.release.value=.25,r.connect(o),o.connect(e.destination),r.start(0);
  const[i,u]=function(n) {
    const t=3,e=500,r=500,o=5e3;
    let i=()=> {

    };
    const u=new Promise(((u,c)=> {
      let s=false,a=0,l=0;
      n.oncomplete=n=>u(n.renderedBuffer);
      const f=()=> {
        setTimeout((()=>c(hn("timeout"))),Math.min(r,l+o-Date.now()));
      },d=()=> {
        try {
          const r=n.startRendering();
          switch(j$1(r)&&M$1(r),n.state) {
            case "running":l=Date.now(),s&&f();
            break;
            case "suspended":document.hidden||a++,s&&a>=t?c(hn("suspended")):setTimeout(d,e);
          }

        } catch(r) {
          c(r);
        }

      };
      d(),i=()=> {
        s||(s=true,l>0&&f());
      };
    }));
    return [u,i]
  }
  (e),c=M$1(i.then((n=>function(n) {
    let t=0;
    for(let e=0;e<n.length;++e)t+=Math.abs(n[e]);
    return t
  }
  (n.getChannelData(0).subarray(4500))),(n=> {
    if("timeout"===n.name||"suspended"===n.name)return -3;
    throw n
  })));
  return ()=>(u(),c)
}
function hn(n) {
  const t=new Error(n);
  return t.name=n,t
}
async function pn(n,t,e=50) {
  var r,o,i;
  const u=document;
  for(;!u.body;)await _$1(e);
  const c=u.createElement("iframe");
  try {
    for((await new Promise(((n,e)=> {
      let r=false;
      const o=()=> {
        r=true,n();
      };
      c.onload=o,c.onerror=n=> {
        r=true,e(n);
      };
      const {
        style:i
      }
      =c;
      i.setProperty("display","block","import ant"),i.position="absolute",i.top="0",i.left="0",i.visibility="hidden",t&&"srcdoc"in c?c.srcdoc=t:c.src="about:blank",u.body.appendChild(c);
      const s=()=> {
        var n,t;
        r||("complete"===(null===(t=null===(n=c.contentWindow)||undefined===n?undefined:n.document)||undefined===t?undefined:t.readyState)?o():setTimeout(s,10));
      };
      s();
    })));
    !(null===(o=null===(r=c.contentWindow)||undefined===r?undefined:r.document)||undefined===o?undefined:o.body);)await _$1(e);
    return await n(c,c.contentWindow)
  } finally {
    null===(i=c.parentNode)||undefined===i||i.removeChild(c);
  }

}
function gn(n) {
  const[t,e]=function(n) {
    var t,e;
    const r=`Unexpected syntax '${n}'`,o=/^\s*([a-z-]*)(.*)$/i.exec(n),i=o[1]||undefined,u= {

    },c=/([.:#][\w-]+|\[.+?\])/gi,s=(n,t)=> {
      u[n]=u[n]||[],u[n].push(t);
    };
    for(;;) {
      const n=c.exec(o[2]);
      if(!n)break;
      const i=n[0];
      switch(i[0]) {
        case ".":s("class",i.slice(1));
        break;
        case "#":s("id",i.slice(1));
        break;
        case "[": {
          const n=/^\[([\w-]+)([~|^$*]?=("(.*?)"|([\w-]+)))?(\s+[is])?\]$/.exec(i);
          if(!n)throw new Error(r);
          s(n[1],null!==(e=null!==(t=n[4])&&undefined!==t?t:n[5])&&undefined!==e?e:"");
          break
        }
        default:throw new Error(r)
      }

    }
    return [i,u]
  }
  (n),r=document.createElement(null!=t?t:"div");
  for(const o of Object.keys(e)) {
    const n=e[o].join(" ");
    "style"===o?wn(r.style,n):r.setAttribute(o,n);
  }
  return r
}
function wn(n,t) {
  for(const e of t.split(";")) {
    const t=/^\s*([\w-]+)\s*:\s*(.+?)(\s*!([\w-]+))?\s*$/.exec(e);
    if(t) {
      const[,e,r,,o]=t;
      n.setProperty(e,r,o||"");
    }

  }

}
function yn(n) {
  let t,e,r=false;
  const[o,i]=function() {
    const n=document.createElement("canvas");
    return n.width=1,n.height=1,[n,n.getContext("2d")]
  }
  ();
  return !function(n,t) {
    return !(!t||!n.toDataURL)
  }
  (o,i)?t=e="unsupported":(r=function(n) {
    return n.rect(0,0,10,10),n.rect(2,2,6,6),!n.isPointInPath(5,5,"evenodd")
  }
  (i),n?t=e="skipped":[t,e]=function(n,t) {
    !function(n,t) {
      n.width=240,n.height=60,t.textBaseline="alphabetic",t.fillStyle="#f60",t.fillRect(100,1,62,20),t.fillStyle="#069",t.font='11pt "Times New Roman"';
      const e=`Cwm fjordbank gly ${String.fromCharCode(55357,56835)}`;
      t.fillText(e,2,15),t.fillStyle="rgba(102, 204, 0, 0.2)",t.font="18pt Arial",t.fillText(e,4,45);
    }
    (n,t);
    const e=bn(n),r=bn(n);
    if(e!==r)return ["unstable","unstable"];
    !function(n,t) {
      n.width=122,n.height=110,t.globalCompositeOperation="multiply";
      for(const[e,r,o]of [["#f2f",40,40],["#2ff",80,40],["#ff2",60,80]])t.fillStyle=e,t.beginPath(),t.arc(r,o,40,0,2*Math.PI,true),t.closePath(),t.fill();
      t.fillStyle="#f9c",t.arc(60,60,60,0,2*Math.PI,true),t.arc(60,60,20,0,2*Math.PI,true),t.fill("evenodd");
    }
    (n,t);
    const o=bn(n);
    return [o,e]
  }
  (o,i)), {
    winding:r,geometry:t,text:e
  }

}
function bn(n) {
  return n.toDataURL()
}
function En() {
  const n=screen,t=n=>W$1(F(n),null),e=[t(n.width),t(n.height)];
  return e.sort().reverse(),e
}
let Rn,Sn;
function In() {
  return function() {
    if(undefined!==Sn)return;
    const n=()=> {
      const t=kn();
      An(t)?Sn=setTimeout(n,2500):(Rn=t,Sn=undefined);
    };
    n();
  }
  (),async()=> {
    let n=kn();
    if(An(n)) {
      if(Rn)return [...Rn];
      fn()&&(await function() {
        const n=document;
        return (n.exitFullscreen||n.msExitFullscreen||n.mozCancelFullScreen||n.webkitExitFullscreen).call(n)
      }
      (),n=kn());
    }
    return An(n)||(Rn=n),n
  }

}
function kn() {
  const n=screen;
  return [W$1(D$1(n.availTop),null),W$1(D$1(n.width)-D$1(n.availWidth)-W$1(D$1(n.availLeft),0),null),W$1(D$1(n.height)-D$1(n.availHeight)-W$1(D$1(n.availTop),0),null),W$1(D$1(n.availLeft),null)]
}
function An(n) {
  for(let t=0;t<4;++t)if(n[t])return false;
  return true
}
function Cn(n) {
  n.style.setProperty("visibility","hidden","import ant"),n.style.setProperty("display","block","import ant");
}
function Ln(n) {
  return matchMedia(`(inverted-colors: ${n})`).matches
}
function Pn(n) {
  return matchMedia(`(forced-colors: ${n})`).matches
}
function xn(n) {
  return matchMedia(`(prefers-contrast: ${n})`).matches
}
function Tn(n) {
  return matchMedia(`(prefers-reduced-motion: ${n})`).matches
}
function On(n) {
  return matchMedia(`(prefers-reduced-transparency: ${n})`).matches
}
function _n(n) {
  return matchMedia(`(dynamic-range: ${n})`).matches
}
const jn=Math,Vn=()=>0;
const Nn=new Set([10752,2849,2884,2885,2886,2928,2929,2930,2931,2932,2960,2961,2962,2963,2964,2965,2966,2967,2968,2978,3024,3042,3088,3089,3106,3107,32773,32777,32777,32823,32824,32936,32937,32938,32939,32968,32969,32970,32971,3317,33170,3333,3379,3386,33901,33902,34016,34024,34076,3408,3410,3411,3412,3413,3414,3415,34467,34816,34817,34818,34819,34877,34921,34930,35660,35661,35724,35738,35739,36003,36004,36005,36347,36348,36349,37440,37441,37443,7936,7937,7938]),Mn=new Set([34047,35723,36063,34852,34853,34854,34229,36392,36795,38449]),Fn=["FRAGMENT_SHADER","VERTEX_SHADER"],Dn=["LOW_FLOAT","MEDIUM_FLOAT","HIGH_FLOAT","LOW_INT","MEDIUM_INT","HIGH_INT"],Wn="WEBGL_debug_renderer_info";
function Zn(n) {
  if(n.webgl)return n.webgl.context;
  const t=document.createElement("canvas");
  let e;
  t.addEventListener("webglCreateContextError",(()=>e=undefined));
  for(const o of ["webgl","experimental-webgl"]) {
    try {
      e=t.getContext(o);
    } catch(r) {

    }
    if(e)break
  }
  return n.webgl= {
    context:e
  },e
}
function Gn(n,t,e) {
  const r=n.getShaderPrecisionFormat(n[t],n[e]);
  return r?[r.rangeMin,r.rangeMax,r.precision]:[]
}
function Hn(n) {
  return Object.keys(n.__proto__).filter(Un)
}
function Un(n) {
  return "string"==typeof n&&!n.match(/[^A-Z0-9_x]/)
}
function Bn() {
  return ln()
}
function $n(n) {
  return "function"==typeof n.getParameter
}
const Yn=async function( {
  debug:n
}
= {

}) {
  if(!sn()&&!dn())return;
  const t=function() {
    const n=atob;
    return  {
      abpIndo:["#Iklan-Melayang","#Kolom-Iklan-728","#SidebarIklan-wrapper",'[title="ALIENBOLA" i]',n("I0JveC1CYW5uZXItYWRz")],abpvn:[".quangcao","#mobileCatfish",n("LmNsb3NlLWFkcw=="),'[id^="bn_bottom_fixed_"]',"#pmadv"],adBlockFinland:[".mainostila",n("LnNwb25zb3JpdA=="),".ylamainos",n("YVtocmVmKj0iL2NsaWNrdGhyZ2guYXNwPyJd"),n("YVtocmVmXj0iaHR0cHM6Ly9hcHAucmVhZHBlYWsuY29tL2FkcyJd")],adBlockPersian:["#navbar_notice_50",".kadr",'TABLE[width="140px"]',"#divAgahi",n("YVtocmVmXj0iaHR0cDovL2cxLnYuZndtcm0ubmV0L2FkLyJd")],adBlockWarningRemoval:["#adblock-honeypot",".adblocker-root",".wp_adblock_detect",n("LmhlYWRlci1ibG9ja2VkLWFk"),n("I2FkX2Jsb2NrZXI=")],adGuardAnnoyances:[".hs-sosyal","#cookieconsentdiv",'div[class^="app_gdpr"]',".as-oil",'[data-cypress="soft-push-notification-modal"]'],adGuardBase:[".BetterJsPopOverlay",n("I2FkXzMwMFgyNTA="),n("I2Jhbm5lcmZsb2F0MjI="),n("I2NhbXBhaWduLWJhbm5lcg=="),n("I0FkLUNvbnRlbnQ=")],adGuardChinese:[n("LlppX2FkX2FfSA=="),n("YVtocmVmKj0iLmh0aGJldDM0LmNvbSJd"),"#widget-quan",n("YVtocmVmKj0iLzg0OTkyMDIwLnh5eiJd"),n("YVtocmVmKj0iLjE5NTZobC5jb20vIl0=")],adGuardFrench:["#pavePub",n("LmFkLWRlc2t0b3AtcmVjdGFuZ2xl"),".mobile_adhesion",".widgetadv",n("LmFkc19iYW4=")],adGuardGerman:['aside[data-portal-id="leaderboard"]'],adGuardJapanese:["#kauli_yad_1",n("YVtocmVmXj0iaHR0cDovL2FkMi50cmFmZmljZ2F0ZS5uZXQvIl0="),n("Ll9wb3BJbl9pbmZpbml0ZV9hZA=="),n("LmFkZ29vZ2xl"),n("Ll9faXNib29zdFJldHVybkFk")],adGuardMobile:[n("YW1wLWF1dG8tYWRz"),n("LmFtcF9hZA=="),'amp-embed[type="24smi"]',"#mgid_iframe1",n("I2FkX2ludmlld19hcmVh")],adGuardRussian:[n("YVtocmVmXj0iaHR0cHM6Ly9hZC5sZXRtZWFkcy5jb20vIl0="),n("LnJlY2xhbWE="),'div[id^="smi2adblock"]',n("ZGl2W2lkXj0iQWRGb3hfYmFubmVyXyJd"),"#psyduckpockeball"],adGuardSocial:[n("YVtocmVmXj0iLy93d3cuc3R1bWJsZXVwb24uY29tL3N1Ym1pdD91cmw9Il0="),n("YVtocmVmXj0iLy90ZWxlZ3JhbS5tZS9zaGFyZS91cmw/Il0="),".etsy-tweet","#inlineShare",".popup-social"],adGuardSpanishPortuguese:["#barraPublicidade","#Publicidade","#publiEspecial","#queTooltip",".cnt-publi"],adGuardTrackingProtection:["#qoo-counter",n("YVtocmVmXj0iaHR0cDovL2NsaWNrLmhvdGxvZy5ydS8iXQ=="),n("YVtocmVmXj0iaHR0cDovL2hpdGNvdW50ZXIucnUvdG9wL3N0YXQucGhwIl0="),n("YVtocmVmXj0iaHR0cDovL3RvcC5tYWlsLnJ1L2p1bXAiXQ=="),"#top100counter"],adGuardTurkish:["#backkapat",n("I3Jla2xhbWk="),n("YVtocmVmXj0iaHR0cDovL2Fkc2Vydi5vbnRlay5jb20udHIvIl0="),n("YVtocmVmXj0iaHR0cDovL2l6bGVuemkuY29tL2NhbXBhaWduLyJd"),n("YVtocmVmXj0iaHR0cDovL3d3dy5pbnN0YWxsYWRzLm5ldC8iXQ==")],bulgarian:[n("dGQjZnJlZW5ldF90YWJsZV9hZHM="),"#ea_intext_div",".lapni-pop-over","#xenium_hot_offers"],easyList:[".yb-floorad",n("LndpZGdldF9wb19hZHNfd2lkZ2V0"),n("LnRyYWZmaWNqdW5reS1hZA=="),".textad_headline",n("LnNwb25zb3JlZC10ZXh0LWxpbmtz")],easyListChina:[n("LmFwcGd1aWRlLXdyYXBbb25jbGljayo9ImJjZWJvcy5jb20iXQ=="),n("LmZyb250cGFnZUFkdk0="),"#taotaole","#aafoot.top_box",".cfa_popup"],easyListCookie:[".ezmob-footer",".cc-CookieWarning","[data-cookie-number]",n("LmF3LWNvb2tpZS1iYW5uZXI="),".sygnal24-gdpr-modal-wrap"],easyListCzechSlovak:["#onlajny-stickers",n("I3Jla2xhbW5pLWJveA=="),n("LnJla2xhbWEtbWVnYWJvYXJk"),".sklik",n("W2lkXj0ic2tsaWtSZWtsYW1hIl0=")],easyListDutch:[n("I2FkdmVydGVudGll"),n("I3ZpcEFkbWFya3RCYW5uZXJCbG9jaw=="),".adstekst",n("YVtocmVmXj0iaHR0cHM6Ly94bHR1YmUubmwvY2xpY2svIl0="),"#semilo-lrectangle"],easyListGermany:["#SSpotIMPopSlider",n("LnNwb25zb3JsaW5rZ3J1ZW4="),n("I3dlcmJ1bmdza3k="),n("I3Jla2xhbWUtcmVjaHRzLW1pdHRl"),n("YVtocmVmXj0iaHR0cHM6Ly9iZDc0Mi5jb20vIl0=")],easyListItaly:[n("LmJveF9hZHZfYW5udW5jaQ=="),".sb-box-pubbliredazionale",n("YVtocmVmXj0iaHR0cDovL2FmZmlsaWF6aW9uaWFkcy5zbmFpLml0LyJd"),n("YVtocmVmXj0iaHR0cHM6Ly9hZHNlcnZlci5odG1sLml0LyJd"),n("YVtocmVmXj0iaHR0cHM6Ly9hZmZpbGlhemlvbmlhZHMuc25haS5pdC8iXQ==")],easyListLithuania:[n("LnJla2xhbW9zX3RhcnBhcw=="),n("LnJla2xhbW9zX251b3JvZG9z"),n("aW1nW2FsdD0iUmVrbGFtaW5pcyBza3lkZWxpcyJd"),n("aW1nW2FsdD0iRGVkaWt1b3RpLmx0IHNlcnZlcmlhaSJd"),n("aW1nW2FsdD0iSG9zdGluZ2FzIFNlcnZlcmlhaS5sdCJd")],estonian:[n("QVtocmVmKj0iaHR0cDovL3BheTRyZXN1bHRzMjQuZXUiXQ==")],fanboyAnnoyances:["#ac-lre-player",".navigate-to-top","#subscribe_popup",".new sletter_holder","#back-top"],fanboyAntiFacebook:[".util-bar-module-firefly-visible"],fanboyEnhancedTrackers:[".open.pushModal","#issuem-leaky-paywall-articles-zero-remaining-nag","#sovrn_container",'div[class$="-hide"][zoompage-fontsize][style="display: block;"]',".BlockNag__Card"],fanboySocial:["#FollowUs","#meteored_share","#social_follow",".article-sharer",".community__social-desc"],frellwitSwedish:[n("YVtocmVmKj0iY2FzaW5vcHJvLnNlIl1bdGFyZ2V0PSJfYmxhbmsiXQ=="),n("YVtocmVmKj0iZG9rdG9yLXNlLm9uZWxpbmsubWUiXQ=="),"article.category-samarbete",n("ZGl2LmhvbGlkQWRz"),"ul.adsmodern"],greekAdBlock:[n("QVtocmVmKj0iYWRtYW4ub3RlbmV0LmdyL2NsaWNrPyJd"),n("QVtocmVmKj0iaHR0cDovL2F4aWFiYW5uZXJzLmV4b2R1cy5nci8iXQ=="),n("QVtocmVmKj0iaHR0cDovL2ludGVyYWN0aXZlLmZvcnRobmV0LmdyL2NsaWNrPyJd"),"DIV.agores300","TABLE.advright"],hungarian:["#cemp_doboz",".optimonk-iframe-container",n("LmFkX19tYWlu"),n("W2NsYXNzKj0iR29vZ2xlQWRzIl0="),"#hirdetesek_box"],iDontCareAboutCookies:['.alert-info[data-block-track*="CookieNotice"]',".ModuleTemplateCookieIndicator",".o--cookies--container","#cookies-policy-sticky","#stickyCookieBar"],icelandicAbp:[n("QVtocmVmXj0iL2ZyYW1ld29yay9yZXNvdXJjZXMvZm9ybXMvYWRzLmFzcHgiXQ==")],latvian:[n("YVtocmVmPSJodHRwOi8vd3d3LnNhbGlkemluaS5sdi8iXVtzdHlsZT0iZGlzcGxheTogYmxvY2s7IHdpZHRoOiAxMjBweDsgaGVpZ2h0OiA0MHB4OyBvdmVyZmxvdzogaGlkZGVuOyBwb3NpdGlvbjogcmVsYXRpdmU7Il0="),n("YVtocmVmPSJodHRwOi8vd3d3LnNhbGlkemluaS5sdi8iXVtzdHlsZT0iZGlzcGxheTogYmxvY2s7IHdpZHRoOiA4OHB4OyBoZWlnaHQ6IDMxcHg7IG92ZXJmbG93OiBoaWRkZW47IHBvc2l0aW9uOiByZWxhdGl2ZTsiXQ==")],listKr:[n("YVtocmVmKj0iLy9hZC5wbGFuYnBsdXMuY28ua3IvIl0="),n("I2xpdmVyZUFkV3JhcHBlcg=="),n("YVtocmVmKj0iLy9hZHYuaW1hZHJlcC5jby5rci8iXQ=="),n("aW5zLmZhc3R2aWV3LWFk"),".revenue_unit_item.dable"],listeAr:[n("LmdlbWluaUxCMUFk"),".right-and-left-sponsers",n("YVtocmVmKj0iLmFmbGFtLmluZm8iXQ=="),n("YVtocmVmKj0iYm9vcmFxLm9yZyJd"),n("YVtocmVmKj0iZHViaXp6bGUuY29tL2FyLz91dG1fc291cmNlPSJd")],listeFr:[n("YVtocmVmXj0iaHR0cDovL3Byb21vLnZhZG9yLmNvbS8iXQ=="),n("I2FkY29udGFpbmVyX3JlY2hlcmNoZQ=="),n("YVtocmVmKj0id2Vib3JhbWEuZnIvZmNnaS1iaW4vIl0="),".site-pub-interstitiel",'div[id^="crt-"][data-criteo-id]'],officialPolish:["#ceneo-placeholder-ceneo-12",n("W2hyZWZePSJodHRwczovL2FmZi5zZW5kaHViLnBsLyJd"),n("YVtocmVmXj0iaHR0cDovL2Fkdm1hbmFnZXIudGVjaGZ1bi5wbC9yZWRpcmVjdC8iXQ=="),n("YVtocmVmXj0iaHR0cDovL3d3dy50cml6ZXIucGwvP3V0bV9zb3VyY2UiXQ=="),n("ZGl2I3NrYXBpZWNfYWQ=")],ro:[n("YVtocmVmXj0iLy9hZmZ0cmsuYWx0ZXgucm8vQ291bnRlci9DbGljayJd"),n("YVtocmVmXj0iaHR0cHM6Ly9ibGFja2ZyaWRheXNhbGVzLnJvL3Ryay9zaG9wLyJd"),n("YVtocmVmXj0iaHR0cHM6Ly9ldmVudC4ycGVyZm9ybWFudC5jb20vZXZlbnRzL2NsaWNrIl0="),n("YVtocmVmXj0iaHR0cHM6Ly9sLnByb2ZpdHNoYXJlLnJvLyJd"),'a[href^="/url/"]'],ruAd:[n("YVtocmVmKj0iLy9mZWJyYXJlLnJ1LyJd"),n("YVtocmVmKj0iLy91dGltZy5ydS8iXQ=="),n("YVtocmVmKj0iOi8vY2hpa2lkaWtpLnJ1Il0="),"#pgeldiz",".yandex-rtb-block"],thaiAds:["a[href*=macau-uta-popup]",n("I2Fkcy1nb29nbGUtbWlkZGxlX3JlY3RhbmdsZS1ncm91cA=="),n("LmFkczMwMHM="),".bumq",".img-kosana"],webAnnoyancesUltralist:["#mod-social-share-2","#social-tools",n("LmN0cGwtZnVsbGJhbm5lcg=="),".zergnet-recommend",".yt.btn-link.btn-md.btn"]
    }

  }
  (),e=Object.keys(t),r=[].concat(...e.map((n=>t[n]))),o=await async function(n) {
    var t;
    const e=document,r=e.createElement("div"),o=new Array(n.length),i= {

    };
    Cn(r);
    for(let u=0;u<n.length;++u) {
      const t=gn(n[u]);
      "DIALOG"===t.tagName&&t.show();
      const i=e.createElement("div");
      Cn(i),i.appendChild(t),r.appendChild(i),o[u]=t;
    }
    for(;!e.body;)await _$1(50);
    e.body.appendChild(r);
    try {
      for(let t=0;t<n.length;++t)o[t].offsetParent||(i[n[t]]=true);
    } finally {
      null===(t=r.parentNode)||undefined===t||t.removeChild(r);
    }
    return i
  }
  (r);
  n&&function(n,t) {
    let e="DOM blockers debug:\n```";
    for(const r of Object.keys(n)) {
      e+=`\n${r}:`;
      for(const o of n[r])e+=`\n  ${t[o]?"🚫":"➡️"} ${o}`;
    }
    console.log(`${e}\n\`\`\``);
  }
  (t,o);
  const i=e.filter((n=> {
    const e=t[n];
    return Z$1(e.map((n=>o[n])))>.6*e.length
  }));
  return i.sort(),i
},Xn=function() {
  return navigator.oscpu
},Jn=function() {
  const n=navigator,t=[],e=n.language||n.userLanguage||n.browserLanguage||n.systemLanguage;
  if(undefined!==e&&t.push([e]),Array.isArray(n.languages))cn()&&function() {
    const n=window;
    return Z$1([!("MediaSettingsRange"in n),"RTCEncodedAudioFrame"in n,""+n.Intl=="[object Intl]",""+n.Reflect=="[object Reflect]"])>=3
  }
  ()||t.push(n.languages);
  else if("string"==typeof n.languages) {
    const e=n.languages;
    e&&t.push(e.split(","));
  }
  return t
},qn=function() {
  return window.screen.colorDepth
},zn=function() {
  return W$1(D$1(navigator.deviceMemory),undefined)
},Kn=function() {
  return W$1(F(navigator.hardwareConcurrency),undefined)
},Qn=function() {
  var n;
  const t=null===(n=window.Intl)||undefined===n?undefined:n.DateTimeFormat;
  if(t) {
    const n=(new t).resolvedOptions().timeZone;
    if(n)return n
  }
  const e=-function() {
    const n=(new Date).getFullYear();
    return Math.max(D$1(new Date(n,0,1).getTimezoneOffset()),D$1(new Date(n,6,1).getTimezoneOffset()))
  }
  ();
  return `UTC${e>=0?"+":""}${e}`
},nt=function() {
  try {
    return !!window.sessionStorage
  } catch(n) {
    return true
  }

},tt=function() {
  try {
    return !!window.localStorage
  } catch(n) {
    return true
  }

},et=function() {
  return !!window.openDatabase
},rt=function() {
  return navigator.cpuClass
},ot=function() {
  const {
    platform:n
  }
  =navigator;
  return "MacIntel"===n&&sn()&&!an()?function() {
    if("iPad"===navigator.platform)return true;
    const n=screen,t=n.width/n.height;
    return Z$1(["MediaSource"in window,!!Element.prototype.webkitRequestFullscreen,t>.65&&t<1.53])>=2
  }
  ()?"iPad":"iPhone":n
},it=function() {
  const n=navigator.plugins;
  if(!n)return;
  const t=[];
  for(let e=0;e<n.length;++e) {
    const r=n[e];
    if(!r)continue;
    const o=[];
    for(let n=0;n<r.length;++n) {
      const t=r[n];
      o.push( {
        type:t.type,suffixes:t.suffixes
      });
    }
    t.push( {
      name:r.name,description:r.description,mimeTypes:o
    });
  }
  return t
},ut=function() {
  const n=navigator;
  let t,e=0;
  undefined!==n.maxTouchPoints?e=F(n.maxTouchPoints):undefined!==n.msMaxTouchPoints&&(e=n.msMaxTouchPoints);
  try {
    document.createEvent("TouchEvent"),t=true;
  } catch(r) {
    t=false;
  }
  return  {
    maxTouchPoints:e,touchEvent:t,touchStart:"ontouchstart"in window
  }

},ct=function() {
  return navigator.vendor||""
},st=function() {
  const n=[];
  for(const t of ["chrome","safari","__crWeb","__gCrWeb","yandex","__yb","__ybro","__firefox__","__edgeTrackingPreventionStatistics","webkit","oprt","samsungAr","ucweb","UCShellJava","puffinDevice"]) {
    const e=window[t];
    e&&"object"==typeof e&&n.push(t);
  }
  return n.sort()
},at=function() {
  const n=document;
  try {
    n.cookie="cookietest=1; SameSite=Strict;";
    const t=-1!==n.cookie.indexOf("cookietest=");
    return n.cookie="cookietest=1; SameSite=Strict; expires=Thu, 01-Jan-1970 00:00:01 GMT",t
  } catch(t) {
    return false
  }

},lt=function() {
  for(const n of ["rec2020","p3","srgb"])if(matchMedia(`(color-gamut: ${n})`).matches)return n
},ft=function() {
  return !!Ln("inverted")||!Ln("none")&&undefined
},dt=function() {
  return !!Pn("active")||!Pn("none")&&undefined
},mt=function() {
  if(matchMedia("(min-monochrome: 0)").matches) {
    for(let n=0;n<=100;++n)if(matchMedia(`(max-monochrome: ${n})`).matches)return n;
    throw new Error("Too high value")
  }

},vt=function() {
  return xn("no-preference")?0:xn("high")||xn("more")?1:xn("low")||xn("less")?-1:xn("forced")?10:undefined
},ht=function() {
  return !!Tn("reduce")||!Tn("no-preference")&&undefined
},pt=function() {
  return !!On("reduce")||!On("no-preference")&&undefined
},gt=function() {
  return !!_n("high")||!_n("standard")&&undefined
},wt=function() {
  const n=jn.acos||Vn,t=jn.acosh||Vn,e=jn.asin||Vn,r=jn.asinh||Vn,o=jn.atanh||Vn,i=jn.atan||Vn,u=jn.sin||Vn,c=jn.sinh||Vn,s=jn.cos||Vn,a=jn.cosh||Vn,l=jn.tan||Vn,f=jn.tanh||Vn,d=jn.exp||Vn,m=jn.expm1||Vn,v=jn.log1p||Vn;
  return  {
    acos:n(.12312423423423424),acosh:t(1e308),acoshPf:(h=1e154,jn.log(h+jn.sqrt(h*h-1))),asin:e(.12312423423423424),asinh:r(1),asinhPf:(n=>jn.log(n+jn.sqrt(n*n+1)))(1),atanh:o(.5),atanhPf:(n=>jn.log((1+n)/(1-n))/2)(.5),atan:i(.5),sin:u(-1e300),sinh:c(1),sinhPf:(n=>jn.exp(n)-1/jn.exp(n)/2)(1),cos:s(10.000000000123),cosh:a(1),coshPf:(n=>(jn.exp(n)+1/jn.exp(n))/2)(1),tan:l(-1e300),tanh:f(1),tanhPf:(n=>(jn.exp(2*n)-1)/(jn.exp(2*n)+1))(1),exp:d(1),expm1:m(1),expm1Pf:(n=>jn.exp(n)-1)(1),log1p:v(10),log1pPf:(n=>jn.log(1+n))(10),powPI:(n=>jn.pow(jn.PI,n))(-100)
  };
  var h;
},yt=function() {
  return navigator.pdfViewerEnabled
},bt=function() {
  const n=new Float32Array(1),t=new Uint8Array(n.buffer);
  return n[0]=1/0,n[0]=n[0]-n[0],t[3]
},Et=function() {
  var n;
  const t=document.createElement("a"),e=null!==(n=t.attributionSourceId)&&undefined!==n?n:t.attributionsourceid;
  return undefined===e?undefined:String(e)
},Rt=function() {
  if(!(dn()||sn()))return -2;
  if(!window.AudioContext)return -1;
  const n=(new AudioContext).baseLatency;
  return null==n?-1:isFinite(n)?n:-3
},St=function() {
  if(!window.Intl)return -1;
  const n=window.Intl.DateTimeFormat;
  if(!n)return -2;
  const t=n().resolvedOptions().locale;
  return t||""===t?t:-3
},It=function( {
  cache:n
}) {
  var t,e,r,o,i,u;
  const c=Zn(n);
  if(!c)return -1;
  if(!$n(c))return -2;
  const s=Bn()?null:c.getExtension(Wn);
  return  {
    version:(null===(t=c.getParameter(c.VERSION))||undefined===t?undefined:t.toString())||"",vendor:(null===(e=c.getParameter(c.VENDOR))||undefined===e?undefined:e.toString())||"",vendorUnmasked:s?null===(r=c.getParameter(s.UNMASKED_VENDOR_WEBGL))||undefined===r?undefined:r.toString():"",renderer:(null===(o=c.getParameter(c.RENDERER))||undefined===o?undefined:o.toString())||"",rendererUnmasked:s?null===(i=c.getParameter(s.UNMASKED_RENDERER_WEBGL))||undefined===i?undefined:i.toString():"",shadingLanguageVersion:(null===(u=c.getParameter(c.SHADING_LANGUAGE_VERSION))||undefined===u?undefined:u.toString())||""
  }

},kt=function( {
  cache:n
}) {
  const t=Zn(n);
  if(!t)return -1;
  if(!$n(t))return -2;
  const e=t.getSupportedExtensions(),r=t.getContextAttributes(),o=[],i=[],u=[],c=[],s=[];
  if(r)for(const l of Object.keys(r))i.push(`${l}=${r[l]}`);
  const a=Hn(t);
  for(const l of a) {
    const n=t[l];
    u.push(`${l}=${n}${Nn.has(n)?`=${t.getParameter(n)}`:""}`);
  }
  if(e)for(const l of e) {
    if(l===Wn&&Bn()||"WEBGL_polygon_mode"===l&&(cn()||sn()))continue;
    const n=t.getExtension(l);
    if(n)for(const e of Hn(n)) {
      const r=n[e];
      c.push(`${e}=${r}${Mn.has(r)?`=${t.getParameter(r)}`:""}`);
    } else o.push(l);
  }
  for(const l of Fn)for(const n of Dn) {
    const e=Gn(t,l,n);
    s.push(`${l}.${n}=${e.join(",")}`);
  }
  return c.sort(),u.sort(), {
    contextAttributes:i,parameters:u,shaderPrecisions:s,extensions:e,extensionParameters:c,unsupportedExtensions:o
  }

};
function At(n=50) {
  return function(n,t=1/0) {
    const {
      requestIdleCallback:e
    }
    =window;
    return e?new Promise((n=>e.call(window,(()=>n()), {
      timeout:t
    }))):_$1(Math.min(n,t))
  }
  (n,2*n)
}
const Ct=function(n,t) {
  const e=function(n) {
    const t=new Uint8Array(n.length);
    for(let e=0;e<n.length;e++) {
      const r=n.charCodeAt(e);
      if(r>127)return (new TextEncoder).encode(n);
      t[e]=r;
    }
    return t
  }
  (n);
  t=t||0;
  const r=[0,e.length],o=r[1]%16,i=r[1]-o,u=[0,t],c=[0,t],s=[0,0],a=[0,0];
  let l;
  for(l=0;l<i;l+=16)s[0]=e[l+4]|e[l+5]<<8|e[l+6]<<16|e[l+7]<<24,s[1]=e[l]|e[l+1]<<8|e[l+2]<<16|e[l+3]<<24,a[0]=e[l+12]|e[l+13]<<8|e[l+14]<<16|e[l+15]<<24,a[1]=e[l+8]|e[l+9]<<8|e[l+10]<<16|e[l+11]<<24,H$1(s,q$1),U$1(s,31),H$1(s,z),$(u,s),U$1(u,27),G$1(u,c),H$1(u,K$1),G$1(u,Q$1),H$1(a,z),U$1(a,33),H$1(a,q$1),$(c,a),U$1(c,31),G$1(c,u),H$1(c,K$1),G$1(c,nn);
  s[0]=0,s[1]=0,a[0]=0,a[1]=0;
  const f=[0,0];
  switch(o) {
    case 15:f[1]=e[l+14],B$2(f,48),$(a,f);
    case 14:f[1]=e[l+13],B$2(f,40),$(a,f);
    case 13:f[1]=e[l+12],B$2(f,32),$(a,f);
    case 12:f[1]=e[l+11],B$2(f,24),$(a,f);
    case 11:f[1]=e[l+10],B$2(f,16),$(a,f);
    case 10:f[1]=e[l+9],B$2(f,8),$(a,f);
    case 9:f[1]=e[l+8],$(a,f),H$1(a,z),U$1(a,33),H$1(a,q$1),$(c,a);
    case 8:f[1]=e[l+7],B$2(f,56),$(s,f);
    case 7:f[1]=e[l+6],B$2(f,48),$(s,f);
    case 6:f[1]=e[l+5],B$2(f,40),$(s,f);
    case 5:f[1]=e[l+4],B$2(f,32),$(s,f);
    case 4:f[1]=e[l+3],B$2(f,24),$(s,f);
    case 3:f[1]=e[l+2],B$2(f,16),$(s,f);
    case 2:f[1]=e[l+1],B$2(f,8),$(s,f);
    case 1:f[1]=e[l],$(s,f),H$1(s,q$1),U$1(s,31),H$1(s,z),$(u,s);
  }
  return $(u,r),$(c,r),G$1(u,c),G$1(c,u),J$1(u),J$1(c),G$1(u,c),G$1(c,u),("00000000"+(u[0]>>>0).toString(16)).slice(-8)+("00000000"+(u[1]>>>0).toString(16)).slice(-8)+("00000000"+(c[0]>>>0).toString(16)).slice(-8)+("00000000"+(c[1]>>>0).toString(16)).slice(-8)
},Lt=new Uint32Array(2);
function Pt() {
  if(!crypto)return Math.random();
  crypto.getRandomValues(Lt);
  return (1048576*Lt[0]+(1048575&Lt[1]))/4503599627370496
}
function xt(n,t,e=Pt) {
  let r="";
  for(let o=0;o<n;o++)r+=t.charAt(e()*t.length);
  return r
}
function Tt(n) {
  return xt(n,"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
}
function Ot() {
  return [8,4,4,4,12].map((n=>xt(n,h$1))).join("-")
}
const _t=new Uint8Array(1);
function jt() {
  return crypto.getRandomValues(_t),_t[0]
}
function Vt(n,t,e,r) {
  return function() {
    const o=t<<9;
    let i=5*n;
    return i=9*(i<<7|i>>>25),r^=t,t^=e^=n,n^=r,e^=o,r=r<<11|r>>>21,(i>>>0)/4294967296
  }

}
function Nt() {
  return new TypeError("Can't pick from nothing")
}
function Mt(n,t) {
  return Math.floor(Pt()*(t-n+1))+n
}
function Ft(n) {
  return Dt(n)?function(n) {
    if(0===n.length)throw Nt();
    return n[Math.floor(Pt()*n.length)]
  }
  (n):function(n) {
    const t=Pt();
    let e=0,r=0;
    for(const[,o]of n)e+=o;
    for(const[o,i]of n) {
      if(t>=r/e&&t<(r+i)/e)return o;
      r+=i;
    }
    throw Nt()
  }
  (Object.entries(n))
}
const Dt=Array.isArray;
var Wt="3.12.6";
const Zt= {
  default:"endpoint"
},Gt= {
  default:"tEndpoint"
},Ht= {
  default:"tlsEndpoint"
};
function Ut(n) {
  return n? {
    query:true,fragment:true
  }
  :undefined
}
const Bt="_vid";
function Yt() {
  return  {
    len:0,arr:new Uint8Array(128)
  }

}
function Xt(n,t) {
  zt(n,n.len+1),n.arr[n.len++]=t;
}
function Jt(n,t) {
  zt(n,n.len+t.length),n.arr.set(t,n.len),n.len+=t.length;
}
function qt(n) {
  return n.arr.subarray(0,n.len)
}
function zt(n,t) {
  if(n.arr.length<t) {
    const e=new Uint8Array(Math.max(2*n.arr.length,t));
    e.set(n.arr),n.arr=e;
  }

}
function Kt(n) {
  const t=Yt(),e=new WeakSet,r=n=> {
    if("string"==typeof n) {
      const e=n.replace(Ae,(n=>"\\"+(Ie[n]||"u"+n.charCodeAt(0).toString(16).padStart(4,"0"))));
      return Xt(t,ee),Jt(t,w$1(e)),void Xt(t,ee)
    }
    if("number"==typeof n||true===n||false===n)return (Number.isNaN(n)||n===1/0||n===-1/0)&&(n=null),void Jt(t,w$1(String(n)));
    if("object"==typeof n&&n) {
      if(e.has(n))throw new TypeError("Recursive input");
      e.add(n);
      const {
        toJSON:o
      }
      =n;
      if("function"==typeof o)return void r(o.call(n));
      if(n instanceof Number||n instanceof String)return void r(n.valueOf());
      let i=true;
      const u=()=> {
        i?i=false:Xt(t,re);
      };
      if(Array.isArray(n)) {
        Xt(t,ge);
        for(const t of n)u(),r(t);
        Xt(t,we);
      } else  {
        Xt(t,ye);
        for(const[e,o]of Object.entries(n))ne(o)||(u(),r(e),Xt(t,oe),r(o));
        Xt(t,be);
      }
      e.delete(n);
    } else Jt(t,Ee);
  };
  return r(n),qt(t)
}
function Qt(n) {
  const t=Yt(),e=d$1(n);
  let r=0;
  const o=()=>(a(),e[r]===ee?i():te(e[r])?u():l(Ee)?(r+=Ee.length,null):l(Re)?(r+=Re.length,true):l(Se)?(r+=Se.length,false):e[r]===ge?c():e[r]===ye?s():f()),i=()=> {
    for(t.len=0;r++,e[r]!==ee;) {
      if(e[r]===ae) {
        if(r++,e[r]===de) {
          const n=parseInt(y$1(e.subarray(r+1,r+5)),16);
          Jt(t,w$1(String.fromCharCode(n))),r+=4;
          continue
        }
        const n=ke[e[r]];
        if(n) {
          Xt(t,n);
          continue
        }
        return f()
      }
      if(undefined===e[r])return f();
      Xt(t,e[r]);
    }
    return r++,y$1(qt(t))
  },u=()=> {
    const n=r;
    for(;e[r]===pe||e[r]===fe||e[r]===me||e[r]===ve||te(e[r]);)r++;
    return Number(y$1(e.subarray(n,r)))
  },c=()=> {
    const n=[];
    for(r++;;) {
      if(a(),e[r]===we) {
        r++;
        break
      }
      if(n.length) {
        if(e[r]!==re)return f();
        r++;
      }
      n.push(o());
    }
    return n
  },s=()=> {
    const n= {

    };
    let t=true;
    for(r++;;) {
      if(a(),e[r]===be) {
        r++;
        break
      }
      if(!t) {
        if(e[r]!==re)return f();
        r++,a();
      }
      if(e[r]!==ee)return f();
      const u=i();
      if(a(),e[r]!==oe)return f();
      r++,Object.defineProperty(n,u, {
        value:o(),configurable:true,enumerable:true,writable:true
      }),t=false;
    }
    return n
  },a=()=> {
    for(;e[r]===ie||e[r]===se||e[r]===ce||e[r]===ue;)r++;
  },l=n=> {
    for(let t=0;t<n.length;t++)if(e[r+t]!==n[t])return false;
    return true
  },f=()=> {
    throw new SyntaxError("Unexpected "+(r<e.length?`byte ${r}`:"end"))
  },m=o();
  return a(),undefined!==e[r]&&f(),m
}
function ne(n) {
  return undefined===n||"function"==typeof n||"symbol"==typeof n
}
function te(n) {
  return n>=le&&n<le+10||n===he
}
const ee=34,re=44,oe=58,ie=32,ue=9,ce=13,se=10,ae=92,le=48,fe=101,de=117,me=69,ve=43,he=45,pe=46,ge=91,we=93,ye=123,be=125,Ee=new Uint8Array([110,de,108,108]),Re=new Uint8Array([116,114,de,fe]),Se=new Uint8Array([102,97,108,115,fe]),Ie= {
  '"':'"',"\\":"\\","\b":"b","\f":"f","\n":"n","\r":"r","\t":"t"
},ke=(()=> {
  const n=new Uint8Array(128);
  for(const[t,e]of Object.entries(Ie))n[e.charCodeAt(0)]=t.charCodeAt(0);
  return n
})(),Ae=/[\x00-\x1F"\\]/g,Ce="Client timeout",Le="Network connection error",Pe="Network request aborted",xe="Response cannot be parsed",Te="Blocked by CSP",Oe="The endpoint parameter is not a valid URL",_e="Handle on demand agent data error";
function je(n,t,e="...") {
  return n.length<=t?n:`${n.slice(0,Math.max(0,t-e.length))}${e}`
}
function Ve(n) {
  let t="";
  for(let e=0;e<n.length;++e)if(e>0) {
    const r=n[e].toLowerCase();
    r!==n[e]?t+=` ${r}`:t+=n[e];
  } else t+=n[e].toUpperCase();
  return t
}
function Ne(n,t) {
  if(""===t)return [n,[]];
  const e=n.split(t);
  return [e[0],e.length>1?e.slice(1):[]]
}
const Me=Ve("WrongRegion"),Fe=Ve("SubscriptionNotActive"),De=Ve("UnsupportedVersion"),We=Ve("InstallationMethodRestricted"),Ze=Ve("HostnameRestricted"),Ge=Ve("IntegrationFailed"),He=Ve("VisitorNotFound"),Ue=Ve("NetworkRestricted"),Be=Ve("InvalidProxyIntegrationSecret"),$e=Ve("InvalidProxyIntegrationHeaders"),Ye=Ve("ProxyIntegrationSecretEnvironmentMismatch");
function Xe(n,t,e,r) {
  const o=r.bodyData;
  return undefined===o?er(r):function(n) {
    return n instanceof Object&&"2"===n.v&&n.products instanceof Object
  }
  (o)?function(n,t,e,r) {
    var o;
    const {
      notifications:i,requestId:u,sealedResult:c,error:s,products:a
    }
    =n,l=function(n) {
      const t=[];
      for(const e of Object.keys(n)) {
        const r=n[e];
        r&&t.push(r);
      }
      return t
    }
    (a);
    nr(i);
    for(const m of l)nr(m.notifications);
    if(s)return Je(s,u,c,e);
    for(const {
      error:m
    }
    of l)if(m)return Je(m,u,c,e);
    !function(n,t,e) {
      var r;
      for(const o of t)null===(r=o.onGetResponse)||undefined===r||r.call(o,n,e);
    }
    (n,t,r);
    const f=null===(o=a.identification)||undefined===o?undefined:o.data,d=f? {
      requestId:u,...undefined===c? {

      }
      : {
        sealedResult:c
      },...f.result
    }
    :ze(u,c,e);
    return  {
      result:d
    }

  }
  (o,n,t,e):er(r)
}
function Je(n,t,e,r) {
  switch(n.code) {
    case "NotAvailableForCrawlBots":case "NotAvailableForAIBots":return Ke(t,e,true,r);
    case "NotAvailableWithoutUA":return Ke(t,e,undefined,r);
    default:return  {
      error:Qe(qe(n),t,n),stop:"VisitorNotFound"===n.code
    }

  }

}
function qe( {
  code:n,message:t
}) {
  var e;
  return undefined===n?t:null!==(e=function(n) {
    switch(n) {
      case "TokenRequired":return "API key required";
      case "TokenNotFound":return "API key not found";
      case "TokenExpired":return "API key expired";
      case "RequestCannotBeParsed":return "Request cannot be parsed";
      case "Failed":return "Request failed";
      case "RequestTimeout":return "Request failed to process";
      case "TooManyRequests":return "Too many requests, rate limit exceeded";
      case "OriginNotAvailable":return "Not available for this origin";
      case "HeaderRestricted":return "Not available with restricted header";
      case "NotAvailableForCrawlBots":return "Not available for crawl bots";
      case "NotAvailableForAIBots":return "Not available for AI bots";
      case "NotAvailableWithoutUA":return "Not available when User-Agent is unspecified"
    }

  }
  (n))&&undefined!==e?e:Ve(n)
}
function ze(n,t,e) {
  const r= {
    requestId:n,visitorFound:false,visitorId:"",confidence: {
      score:.5,comment:"The real score is unknown"
    }

  };
  if(undefined!==t&&(r.sealedResult=t),!e)return r;
  const o="n/a";
  return  {
    ...r,incognito:false,browserName:o,browserVersion:o,device:o,ip:o,os:o,osVersion:o,firstSeenAt: {
      subscription:null,global:null
    },lastSeenAt: {
      subscription:null,global:null
    }

  }

}
function Ke(n,t,e,r) {
  return  {
    result: {
      ...ze(n,t,r),bot: {
        probability:1,...undefined===e?undefined: {
          safe:e
        }

      }

    }

  }

}
function Qe(n,t,e) {
  const r=new Error(n);
  return undefined!==t&&(r.requestId=t),undefined!==e&&(r.raw=e),r
}
function nr(n) {
  null==n||n.forEach(tr);
}
function tr( {
  level:n,message:t
}) {
  "error"===n?console.error(t):"warning"===n?console.warn(t):console.log(t);
}
function er(n) {
  return  {
    error:Qe(xe,undefined, {
      httpStatusCode:n.status,bodyBase64:R$1(n.body)
    })
  }

}
const rr="[Fingerprint]";
function ir(n=`${rr} `) {
  const t= {

  };
  return e=> {
    switch(e.e) {
      case 15:t[e.getCallId]=e.body;
      break;
      case 18:console.log(`${n}Visitor id request`,t[e.getCallId]);
      break;
      case 19:console.log(`${n}Visitor id response`,e.body);
      break;
      case 16:case 17:delete t[e.getCallId];
    }

  }

}
async function ur(n,t) {
  const {
    aq:e,ip:o
  }
  =t;
  if(null===o)throw new Error("Shared iframe is not available");
  try {
    await Promise.race([o,(i=`Iframe initialization timed out, debugCounters: ${JSON.stringify(t.dc)}`,r$1(2e3).then((()=>Promise.reject(new Error(i)))))]);
  } catch(c) {
    if(Er(c))return  {
      s:-101,v:null
    };
    throw c
  }
  var i;
  const u=await new Promise(((r,o)=> {
    const i= {
      action:n,resolve:r,reject:o
    };
    e.push(i),async function(n) {
      const {
        aq:t,ipq:e,si:r,siw:o
      }
      =n;
      if(e||0===t.length)return;
      n.ipq=true;
      for(;t.length>0;) {
        const n=t.shift();
        if(n)try {
          const t=await n.action(r,o);
          n.resolve(t);
        } catch(c) {
          n.reject(c);
        }

      }
      n.ipq=false;
    }
    (t);
  }));
  return u
}
async function cr(n,t=50) {
  n.ip=u$1(async function(n,t) {
    var e,r;
    const {
      dc:o
    }
    =n,i=document;
    for(;!i.body;)o.adb++,await sr(t);
    const u=i.createElement("iframe");
    for(await new Promise(((n,t)=> {
      let e=false;
      const r=()=> {
        e=true,n();
      };
      u.onload=r,u.onerror=n=> {
        e=true,t(n);
      };
      const {
        style:c
      }
      =u;
      c.setProperty("display","block","import ant"),c.position="absolute",c.top="0",c.left="0",c.visibility="hidden",u.src="about:blank",i.body.appendChild(u);
      const s=()=> {
        var n,t;
        o.crs++,e||("complete"===(null===(t=null===(n=u.contentWindow)||undefined===n?undefined:n.document)||undefined===t?undefined:t.readyState)?r():setTimeout(s,10));
      };
      s();
    }));
    !(null===(r=null===(e=u.contentWindow)||undefined===e?undefined:e.document)||undefined===r?undefined:r.body);)o.asib++,await sr(t);
    n.si=u,n.siw=u.contentWindow;
  }
  (n,t));
}
function sr(n,t) {
  return new Promise((e=>setTimeout(e,n,t)))
}
const ar="__fpjs_pvid";
function lr() {
  const n=window,t=n[ar];
  return n[ar]="string"==typeof t?t:Tt(10)
}
function dr(n,t,e,r) {
  const o=document,i="securitypolicyviolation";
  let u;
  const c=t=> {
    const e=new URL(n,location.href), {
      blockedURI:r
    }
    =t;
    r!==e.href&&r!==e.protocol.slice(0,-1)&&r!==e.origin||(u=t,s());
  };
  o.addEventListener(i,c);
  const s=()=>o.removeEventListener(i,c);
  return null==r||r.then(s,s),Promise.resolve().then(t).then((n=>(s(),n)),(n=>new Promise((n=> {
    const t=new MessageChannel;
    t.port1.onmessage=()=>n(),t.port2.postMessage(null);
  })).then((()=> {
    if(s(),u)return e(u);
    throw n
  }))))
}
function mr() {
  return !document.hidden
}
const vr=/Blocked a frame.*cross-origin frame/,hr=/Failed to execute\s+'([^']+)'\s+on\s+'([^']+)'/,pr=/Permission denied.*cross-origin object/,gr=/Context not access storage/,wr=/(\w+)\(\)\s+called for opaque origin/,yr=3538568711,br=986543999;
function Er(n) {
  return (n instanceof DOMException||n instanceof TypeError)&&(vr.test(n.message)||function(n) {
    const t=n.match(hr);
    return !!t&&(A(t[1])===yr&&A(t[2])===br)
  }
  (n.message)||pr.test(n.message)||gr.test(n.message)||wr.test(n.message))
}
const Rr="stripped",Sr=["path","query","fragment"];
async function Ir(n,t) {
  if(kr(t))return n;
  const e=Ar(n);
  return await Promise.all(Sr.map((async n=> {
    const r=e[n];
    var o;
    t[n]&&r&&(e[n]=await async function(n) {
      var t;
      if(""===n)return "";
      const e=null===(t=window.crypto)||undefined===t?undefined:t.subtle;
      if(!(null==e?undefined:e.digest))return Rr;
      return R$1(await e.digest("SHA-256",w$1(n))).replace(/=/g,"").replace(/\+/g,"-").replace(/\//g,"_")
    }
    ("query"===n?(o=r,o.split("&").sort().join("&")):r));
  }))),Cr(e)
}
function kr(n) {
  return !(n&&Sr.some((t=>n[t])))
}
function Ar(n) {
  const[t,e]=Ne(n,"#"),[r,o]=Ne(t,"?");
  let i,u;
  const c=/^((\w+:)?\/\/[^/]*)?((\/)(.*)|$)$/.exec(r);
  return c?(i=(c[1]||"")+(c[4]||""),u=c[5]||""):(i="",u=r), {
    origin:i,path:u,query:o.length?o.join("?"):null,fragment:e.length?e.join("#"):null
  }

}
function Cr( {
  origin:n,path:t,query:e,fragment:r
}) {
  return n+t+(null===e?"":`?${e}`)+(null===r?"":`#${r}`)
}
function Lr(n,t) {
  const e=Ar(n);
  let r=e.origin+e.path;
  return r&&!r.endsWith("/")&&(r+="/"),r+=t,e.origin="",e.path=r,Cr(e)
}
function Pr(n,t) {
  const e=Ar(n);
  let {
    query:r
  }
  =e;
  for(const[o,i]of Object.entries(t))for(const n of Array.isArray(i)?i:[i])r=`${r?`${r}&`:""}${o}=${xr(n)}`;
  return e.query=r,Cr(e)
}
function xr(n) {
  return n.split("/").map(encodeURIComponent).join("/")
}
function Tr(n) {
  return t=> {
    const e=[],r=new Map;
    const o=window.setInterval((function() {
      const t=e.shift();
      if(t) {
        const[e,o]=t,i=u$1(n(o));
        r.set(e,i);
      }

    }),1);
    function i() {
      window.clearInterval(o);
    }
    return t.then(i,i),[e,r,t]
  }

}
function Or(n) {
  const t=Math.random();
  return function(n,t,e) {
    const[r]=n;
    r.push([t,e]);
  }
  (n.container,t,n),function(n,t,e) {
    let r;
    function o() {
      window.clearInterval(r);
    }
    const[,i,u]=n,c=new Promise(((n,e)=> {
      r=window.setInterval((function() {
        const r=i.get(t);
        if(r)return i.delete(t),r.then(n,e)
      }),1);
    }));
    return c.then(o,o),null==e||e.then(o,o),u.then(o,o),c
  }
  (n.container,t,n.abort)
}
const _r=Tr(jr);
function jr(n) {
  return dr(n.url,(()=>function( {
    url:n,method:t="get",body:e,headers:r,withCredentials:o=false,timeout:i,responseFormat:u,abort:c
  }) {
    return new Promise(((s,a)=> {
      if(function(n) {
        if(URL.prototype)try {
          return new URL(n,location.href),false
        } catch(t) {
          if(t instanceof Error&&"TypeError"===t.name)return true;
          throw t
        }

      }
      (n))throw Vr("InvalidURLError","Invalid URL");
      const l=new XMLHttpRequest;
      try {
        l.open(t,n,true);
      } catch(f) {
        if(f instanceof Error&&/violate.+content security policy/i.test(f.message))throw Nr();
        throw f
      }
      if(l.withCredentials=o,l.timeout=undefined===i?0:Math.max(i,1),"binary"===u&&(l.responseType="arraybuffer"),r)for(const n of Object.keys(r))l.setRequestHeader(n,r[n]);
      l.onload=()=>s(function(n) {
        return  {
          body:n.response,status:n.status,statusText:n.statusText,getHeader:t=>function(n,t) {
            const e=new RegExp(`^${r=t,r.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")}: (.*)$`,"im").exec(n);
            var r;
            return e?e[1]:undefined
          }
          (n.getAllResponseHeaders(),t)
        }

      }
      (l)),l.ontimeout=()=>a(Vr("TimeoutError","The request timed out")),l.onabort=()=>a(Vr("AbortError","The request is aborted")),l.onerror=()=>a(Vr("TypeError",navigator.onLine?"Connection error":"Network offline")),l.send(function(n) {
        const t=()=> {
          try {
            return new Blob([]),false
          } catch(n) {
            return true
          }

        };
        if(n instanceof ArrayBuffer) {
          if(!t())return new Uint8Array(n)
        } else if((null==n?undefined:n.buffer)instanceof ArrayBuffer&&t())return n.buffer;
        return n
      }
      (e)),null==c||c.catch((()=> {

      })).then((()=> {
        l.onabort=null,l.abort();
      }));
    }))
  }
  (n)),(()=> {
    throw Nr()
  }),n.abort)
}
function Vr(n,t) {
  const e=new Error(t);
  return e.name=n,e
}
function Nr() {
  return Vr("CSPError","The request is blocked by the CSP")
}
function Fr() {
  const n=window,t=navigator;
  return b$1(["maxTouchPoints"in t,"mediaCapabilities"in t,"PointerEvent"in n,"visualViewport"in n,"onafterprint"in n])>=4
}
function Zr() {
  var n;
  const t=window;
  return b$1(["Iterator"in t,t.Error&&"isError"in t.Error,t.Atomics&&"pause"in t.Atomics,(null===(n=t.Document)||undefined===n?undefined:n.prototype)&&"fragmentDirective"in t.Document.prototype,t.CSSRule&&!("UNKNOWN_RULE"in t.CSSRule),!("SVGDocument"in t)])>=4
}
function Gr() {
  const n=window;
  return b$1([!("PushManager"in n),!("AudioBuffer"in n),!("RTCPeerConnection"in n),!("geolocation"in navigator),!("ServiceWorker"in n)])>=3
}
function Hr() {
  const n=window;
  return b$1(["ClipboardItem"in n,"PerformanceEventTiming"in n,"RTCSctpTransport"in n])>=2
}
function Br(n,t,...e) {
  n&&o$1((()=> {
    const r=t(...e);
    undefined!==r&&n(r);
  }));
}
async function $r(n,t,e,r,o) {
  let i;
  Br(n,t);
  try {
    i=await o();
  } catch(u) {
    throw Br(n,r,u),u
  }
  return Br(n,e,i),i
}
function Xr(n) {
  const t=n;
  return !!t.getCallId&&"string"==typeof t.getCallId
}
function Jr(n) {
  const t=n;
  return !!t.collectCallId&&"string"==typeof t.collectCallId
}
function zr(n,t,e,r,o=jt) {
  const i=o()%(e+1),u=d$1(n),c=1+t.length+1+i+r+u.length,s=new ArrayBuffer(c),a=new Uint8Array(s);
  let l=0;
  const f=o();
  a[l++]=f;
  for(const d of t)a[l++]=f+d;
  a[l++]=f+i;
  for(let d=0;d<i;++d)a[l++]=o();
  const m=new Uint8Array(r);
  for(let d=0;d<r;++d)m[d]=o(),a[l++]=m[d];
  for(let d=0;d<u.length;++d)a[l++]=u[d]^m[d%r];
  return s
}
function Kr(n,t,e) {
  const r=()=> {
    throw new Error("Invalid data")
  },o=d$1(n);
  o.length<t.length+2&&r();
  for(let f=0;f<t.length;++f)E$1(o[1+f],o[0])!==t[f]&&r();
  const i=1+t.length,u=E$1(o[i],o[0]);
  o.length<i+1+u+e&&r();
  const c=i+1+u,s=c+e,a=new ArrayBuffer(o.length-s),l=new Uint8Array(a);
  for(let f=0;f<l.length;++f)l[f]=o[s+f]^o[c+f%e];
  return a
}
const Qr=/The document is sandboxed and lacks the 'allow-same-origin' flag/,no=/The operation is insecure/,to=/Forbidden in a sandboxed document without the 'allow-same-origin' flag/;
function eo(n) {
  return oo((()=> {
    const t=`${n}=`;
    for(const n of document.cookie.split(";")) {
      let e=0;
      for(;" "===n[e]&&e<n.length;)++e;
      if(n.indexOf(t)===e)return n.slice(e+t.length)
    }

  }),undefined)
}
function ro(n,t,e,r) {
  oo((()=> {
    const o=`${n}=${t}`,i=`expires=${new Date(Date.now()+24*e*60*60*1e3).toUTCString()}`,u=r?`domain=${r}`:"";
    document.cookie=[o,"path=/",i,u,"SameSite=Lax"].join("; ");
  }),undefined);
}
function oo(n,t) {
  try {
    document.cookie;
  } catch(e) {
    if(function(n) {
      if(!(n instanceof DOMException))return false;
      const t=n.message;
      return Qr.test(t)||no.test(t)||to.test(t)
    }
    (e))return t;
    throw e
  }
  return n()
}
function io(n,t,e) {
  uo((t=> {
    !function(n,t) {
      ro(n,"",-1,t);
    }
    (n,t);
  })),e<0||uo((r=>(ro(n,t,e,r),eo(n)===t)));
}
function uo(n) {
  const t=location.hostname,e=ln();
  (function(n,t) {
    let e=n.length-("."===n.slice(-1)?1:0);
    do {
      if(e=e>0?n.lastIndexOf(".",e-1):-1,true===t(n.slice(e+1)))return true
    } while(e>=0);
    return false
  })(t,(r=> {
    if(!e||!/^([^.]{1,3}\.)*[^.]+\.?$/.test(r)||r===t)return n(r)
  }))||n();
}
function co(n,t) {
  io(t,n,365),fo(t,n);
}
function so(n) {
  return `${n}_t`
}
function ao(n) {
  return `${n}_lr`
}
function lo(n) {
  var t,e;
  try {
    return null!==(e=null===(t=null===localStorage||undefined===localStorage?undefined:localStorage.getItem)||undefined===t?undefined:t.call(localStorage,n))&&undefined!==e?e:undefined
  } catch(r) {

  }

}
function fo(n,t) {
  var e;
  try {
    null===(e=null===localStorage||undefined===localStorage?undefined:localStorage.setItem)||undefined===e||e.call(localStorage,n,t);
  } catch(r) {

  }

}
function mo() {
  return `js/${Wt}`
}
const vo=[3,7];
function ho(n,t) {
  const e=ao(n);
  if(0===t.size)return;
  const r=po(e).filter((n=>!t.has(n[0])));
  0!==r.length?fo(e,JSON.stringify(r)):function(n) {
    var t;
    try {
      null===(t=null===localStorage||undefined===localStorage?undefined:localStorage.removeItem)||undefined===t||t.call(localStorage,n);
    } catch(e) {

    }

  }
  (e);
}
function po(n) {
  const t=lo(n);
  if(!t)return [];
  try {
    const n=t?JSON.parse(t):[];
    return Array.isArray(n)?n:[]
  } catch(e) {
    return []
  }

}
function go(n) {
  return "agentId"in n
}
function wo(n,t,e,r) {
  const o=function*(n,t,e) {
    let r=0,o=0;
    for(;r<n.length&&o<t.length;)e(n[r],t[o])?(yield n[r],r++):(yield t[o],o++);
    for(;r<n.length;r++)yield n[r];
    for(;o<t.length;o++)yield t[o];
  }
  (n.map((n=>( {
    t:ko(n.time),s:"visible"===n.state?"v":"h"
  }))),t,((n,t)=>n.t<t.t)),i=[];
  let u;
  const c=()=> {
    0===i.length&&undefined!==u&&i.push( {
      t:e,s:u
    });
  };
  for(;i.length<100;) {
    const n=o.next();
    if(n.done)break;
    const t=n.value,s=t.t,a=t.s;
    if(s>r)break;
    s<e?u=a:a!==u&&(c(),i.push(t),u=a);
  }
  return c(),i
}
function yo(n) {
  const t=bo(n.map((n=>n.url)).filter((n=>Boolean(n))));
  return n.map(((e,r)=> {
    const o=n.length>1&&r<n.length-1&&!("error"in e);
    return Ro(e.url,ko(e.startedAt),ko(e.finishedAt),o?"Unknown":e.error,t[e.url])
  }))
}
function bo(n) {
  const t= {

  };
  return new Set(n).forEach((n=> {
    const e=function(n) {
      if(!URL.prototype)return n;
      try {
        return new URL(n,window.location.origin).toString()
      } catch(t) {
        return n
      }

    }
    (n),r=performance.getEntriesByName(e,"resource");
    t[n]=r;
  })),t
}
function Eo(n,t,e,r,o,i) {
  var u;
  const c=[];
  for(const s of n) {
    const n=s.event;
    if(n.e!==e&&n.e!==r&&n.e!==o)continue;
    if(n.stage!==i)continue;
    (c[u=n.tryNumber]||(c[u]= {

    }))[n.e]=s;
  }
  return c.map((n=> {
    var i,u,c,s,a,l;
    const f=null===(i=n[e])||undefined===i?undefined:i.timestamp,d=null!==(c=null===(u=n[r])||undefined===u?undefined:u.timestamp)&&undefined!==c?c:null===(s=n[o])||undefined===s?undefined:s.timestamp,m=null===(a=n[e])||undefined===a?undefined:a.event.url,v=null===(l=n[o])||undefined===l?undefined:l.event.error;
    return f&&d&&m?Ro(m,f,d,v,t[m]):null
  })).filter((n=>Boolean(n)))
}
function Ro(n,t,e,r,o) {
  const i=function(n,t,e) {
    if(!n)return;
    let r;
    for(let o=n.length-1;o>=0;o--) {
      const i=n[o];
      if(i.startTime<t-1)break;
      i.responseEnd<=e+1&&(r=i);
    }
    return r
  }
  (o,t,e);
  return  {
    s:So(null==i?undefined:i.startTime)||Math.round(t),e:So(null==i?undefined:i.responseEnd)||Math.round(e),u:n||null,er:r?String(r):null,ds:So(null==i?undefined:i.domainLookupStart),de:So(null==i?undefined:i.domainLookupEnd),cs:So(null==i?undefined:i.connectStart),css:So(null==i?undefined:i.secureConnectionStart),ce:So(null==i?undefined:i.connectEnd),qs:So(null==i?undefined:i.requestStart),ss:So(null==i?undefined:i.responseStart)
  }

}
function So(n) {
  return "number"==typeof n?0===n?null:Math.round(n):null
}
function Io(n) {
  var t;
  const e=null===(t=n[13])||undefined===t?undefined:t.event.result;
  if(!e)return  {

  };
  const r= {

  };
  for(const o in e)r[o]=Math.round(e[o].duration);
  return r
}
function ko(n) {
  var t;
  const e=null!==(t=performance.timeOrigin)&&undefined!==t?t:Date.now()-performance.now();
  return Math.round(n.getTime()-e)
}
const Ao=function() {
  const n=function(n) {
    const t= {

    },e=[],r=[];
    let o=false;
    const i=v$1(document,"visibilitychange",u);
    function u() {
      r.push( {
        t:Math.round(performance.now()),s:mr()?"v":"h"
      });
    }
    function c(n) {
      if(o)return;
      switch(s( {
        timestamp:Math.round(performance.now()),event:n
      }),n.e) {
        case 9:case 18:e.push(n.url);
        break;
        case 4:case 5:a(n.agentId,n.getCallId,"get");
        break;
        case 22:case 23:a(n.agentId,n.collectCallId,"collect");
      }

    }
    function s(n) {
      const e=n.event;
      if(!go(e))return;
      const {
        agentId:r
      }
      =e;
      if(t[r]||(t[r]= {
        commonEvents:[],getCalls: {

        },collectCalls: {

        }

      }),Xr(e)) {
        const {
          getCallId:o
        }
        =e;
        let i=t[r].getCalls[o];
        return i||(i=[]),i.push(n),void(t[r].getCalls[o]=i)
      }
      if(Jr(e)) {
        const {
          collectCallId:o
        }
        =e;
        let i=t[r].collectCalls[o];
        return i||(i=[]),i.push(n),void(t[r].collectCalls[o]=i)
      }
      t[r].commonEvents.push(n);
    }
    function a(o,i,u) {
      var c,s,a,l,f,d,m,v,h,p,g,w,y,b,E,R,S,I,k,A,C;
      const L=function(n,t,e,r) {
        const o=[];
        n[t]&&(o.push(...n[t].commonEvents),"get"===r&&e&&o.push(...n[t].getCalls[e]||[]),"collect"===r&&e&&o.push(...n[t].collectCalls[e]||[]));
        return o
      }
      (t,o,i,u),P= {

      };
      for(const n of L) {
        P[n.event.e]=n;
      }
      const x=null!==(c=P[4])&&undefined!==c?c:P[5],T=null!==(s=P[22])&&undefined!==s?s:P[23],O=P[3]&&x,_=P[21]&&T,j=O||_;
      if(!(P[0]&&P[1]&&P[12]&&j))return;
      const {
        token:V,apiKey:N=V,storageKey:M=Bt,modules:F,ldi:D,aggressiveOptimization:W=false,optimizeRepeatedVisits:Z=false
      }
      =P[0].event.options;
      if(!N)return;
      const G=Math.min(P[0].timestamp,ko(null!==(a=null==D?undefined:D.attempts[0].startedAt)&&undefined!==a?a:new Date("8524-04-28"))),H=null===(l=P[5])||undefined===l?undefined:l.event.error,U=null===(f=P[4])||undefined===f?undefined:f.event.result,B=null===(d=P[23])||undefined===d?undefined:d.event.error,$=null!==(m=P[13])&&undefined!==m?m:P[14],Y=bo(e),X= {
        am:_?"collect":"get",v:"1",dt:(new Date).toISOString(),ci:mo(),pi:lr(),ai:o,ri:Tt(12),c:N,rid:null!==(h=null!==(v=null==U?undefined:U.requestId)&&undefined!==v?v:null==H?undefined:H.requestId)&&undefined!==h?h:null,er:null!==(p=null==H?undefined:H.message)&&undefined!==p?p:null,cr:null!==(g=null==B?undefined:B.message)&&undefined!==g?g:null,mo:F.map((n=>n.key)).filter((n=>Boolean(n))),sa:yo(null!==(w=null==D?undefined:D.attempts)&&undefined!==w?w:[]),ls:P[0].timestamp,le:P[1].timestamp,ca:Eo(L,Y,9,10,11),ss:P[12].timestamp,se:null!==(y=null==$?undefined:$.timestamp)&&undefined!==y?y:null,sd:Io(P),gs:null!==(E=null===(b=P[3])||undefined===b?undefined:b.timestamp)&&undefined!==E?E:null,ge:null!==(R=null==x?undefined:x.timestamp)&&undefined!==R?R:null,cs:null!==(I=null===(S=P[21])||undefined===S?undefined:S.timestamp)&&undefined!==I?I:null,ce:null!==(k=null==T?undefined:T.timestamp)&&undefined!==k?k:null,fa:Eo(L,Y,18,19,20,0),ia:Eo(L,Y,18,19,20,1),vs:wo(null!==(A=null==D?undefined:D.visibilityStates)&&undefined!==A?A:[],r,G,null!==(C=null==x?undefined:x.timestamp)&&undefined!==C?C:null==T?undefined:T.timestamp),ab:P[1].event.ab,ao:W,or:Z
      };
      n(X,M);
    }
    return u(), {
      addEvent:c,destroy:()=> {
        o=true,i();
      }

    }

  }
  (((n,t)=> {
    !function(n,t) {
      const e=ao(t),r=po(e)||[];
      r.splice(0,r.length-2);
      const o=zr(Kt(n),vo,3,7);
      r.push([n.ri,R$1(o)]),fo(e,JSON.stringify(r));
    }
    (n,t);
  }));
  let t=new Set;
  return  {
    toRequest(n) {
      const e=function(n) {
        const t=ao(n),e=po(t)||[],r=[];
        return e.forEach((n=> {
          try {
            const t=Qt(Kr(S$1(n[1]),vo,7));
            r.push(t);
          } catch(t) {

          }

        })),r
      }
      (n);
      return t=new Set(e.map((n=>n.ri))), {
        lr:e
      }

    },onGetResponse(n,e) {
      ho(e,t);
    },onCollectResponse(n) {
      ho(n,t);
    },addEvent:n.addEvent,destroy:n.destroy
  }

};
function Mo(t,e,r,o=1/0,u) {
  const c= {
    failedAttempts:[]
  },[s,a]=function(n) {
    const t=function(n) {
      const t=[...n];
      return  {
        current:()=>t[0],postpone() {
          const n=t.shift();
          undefined!==n&&t.push(n);
        },exclude() {
          t.shift();
        }

      }

    }
    (n),e=f$1(200,1e4),r=new Set;
    return [t.current(),(n,o,i)=> {
      let u;
      if(o)u=function(n) {
        const t=n.getHeader("retry-after");
        if(!t)return;
        if(/^\s*\d+(\.\d+)?\s*$/.test(t))return 1e3*parseFloat(t);
        const e=new Date(t);
        return isNaN(e)?undefined:e.getTime()-Date.now()
      }
      (o),undefined!==u?t.postpone():t.exclude();
      else if(i instanceof Error&&("CSPError"===i.name||"InvalidURLError"===i.name))t.exclude(),u=0;
      else  {
        const e=Date.now()-n.getTime()<50,o=t.current();
        o&&e&&!r.has(o)&&(r.add(o),u=0),t.postpone();
      }
      const c=t.current();
      return undefined===c?undefined:[c,null!=u?u:n.getTime()+e()-Date.now()]
    }]
  }
  (t),l=(d=[null==u?undefined:u.then((n=>c.aborted= {
    resolve:true,value:n
  }),(n=>c.aborted= {
    resolve:false,error:n
  })),(async()=> {
    if(undefined===s)return;
    let t=s;
    for(let s=0;s<o;++s) {
      const o=new Date;
      let f,d;
      try {
        f=await i$1((()=>e(t,s,u)),u);
      } catch(l) {
        d=l,c.failedAttempts.push( {
          level:0,endpoint:t,error:l
        });
      }
      if(f) {
        const n=r(f);
        if("result"in n) {
          c.result=n.result;
          break
        }
        if(c.failedAttempts.push( {
          level:1,endpoint:t,error:n.error
        }),n.stop)break
      }
      const m=a(o,f,d);
      if(!m)break;
      await i$1(n(m[1]),u),t=m[0];
    }

  })()],Promise.race(d.filter((n=>!!n)))).then((()=>c));
  var d;
  return  {
    then:l.then.bind(l),current:c
  }

}
const Fo=/\(([^(^\s^}]+):(\d)+:(\d)+\)/i,Do=/@([^(^\s^}]+):(\d)+:(\d)+/i;
function Wo() {
  const n=new Error,t=function(n) {
    if(n.fileName)return n.fileName.split(" ")[0];
    return n.sourceURL?n.sourceURL:null
  }
  (n);
  if(t)return t;
  if(n.stack) {
    const t=function(n) {
      const[t,e]=n.split("\n"),r=Fo.exec(e)||Do.exec(t);
      return r?r[1]:undefined
    }
    (n.stack);
    if(t)return t
  }
  return null
}
const Zo="awesomium",Go="cef",Ho="cefsharp",Uo="coachjs",Bo="fminer",$o="geb",Yo="nightmarejs",Xo="phantomas",Jo="phantomjs",qo="rhino",zo="selenium",Ko="webdriverio",Qo="webdriver",ni="headless_chrome";
class ti extends Error {
  const ructor(n,t) {
    super(t),this.state=n,this.name="BotdError",Object.setPrototypeOf(this,ti.prototype);
  }

}
function ei(n,t) {
  return -1!==n.indexOf(t)
}
function ri(n,t) {
  if("find"in n)return n.find(t);
  for(let e=0;e<n.length;e++)if(t(n[e],e,n))return n[e]
}
function oi(n) {
  return Object.getOwnPropertyNames(n)
}
function ii(n,...t) {
  for(const e of t)if("string"==typeof e) {
    if(ei(n,e))return true
  } else  {
    if(null!=ri(n,(n=>e.test(n))))return true
  }
  return false
}
const ui=function() {
  return navigator.userAgent
},ci=function() {
  const n=navigator.appVersion;
  if(null==n)throw new ti(-1,"navigator.appVersion is undefined");
  return n
},si=function() {
  if(undefined===navigator.connection)throw new ti(-1,"navigator.connection is undefined");
  if(undefined===navigator.connection.rtt)throw new ti(-1,"navigator.connection.rtt is undefined");
  return navigator.connection.rtt
},ai=function() {
  return  {
    outerWidth:window.outerWidth,outerHeight:window.outerHeight,innerWidth:window.innerWidth,innerHeight:window.innerHeight
  }

},li=function() {
  if(undefined===navigator.plugins)throw new ti(-1,"navigator.plugins is undefined");
  if(undefined===navigator.plugins.length)throw new ti(-3,"navigator.plugins.length is undefined");
  return navigator.plugins.length
},fi=function() {
  try {
    null[0]();
  } catch(n) {
    if(n instanceof Error&&null!=n.stack)return n.stack.toString()
  }
  throw new ti(-3,"errorTrace signal unexpected behaviour")
},di=function() {
  const {
    productSub:n
  }
  =navigator;
  if(undefined===n)throw new ti(-1,"navigator.productSub is undefined");
  return n
},mi=function() {
  if(undefined===window.external)throw new ti(-1,"window.external is undefined");
  const {
    external:n
  }
  =window;
  if("function"!=typeof n.toString)throw new ti(-2,"window.external.toString is not a function");
  return n.toString()
},vi=function() {
  if(undefined===navigator.mimeTypes)throw new ti(-1,"navigator.mimeTypes is undefined");
  const {
    mimeTypes:n
  }
  =navigator;
  let t=Object.getPrototypeOf(n)===MimeTypeArray.prototype;
  for(let e=0;e<n.length;e++)t&&(t=Object.getPrototypeOf(n[e])===MimeType.prototype);
  return t
},hi=async function() {
  if(undefined===window.Notification)throw new ti(-1,"window.Notification is undefined");
  if(undefined===navigator.permissions)throw new ti(-1,"navigator.permissions is undefined");
  const {
    permissions:n
  }
  =navigator;
  if("function"!=typeof n.query)throw new ti(-2,"navigator.permissions.query is not a function");
  try {
    const t=await n.query( {
      name:"notifications"
    });
    return "denied"===window.Notification.permission&&"prompt"===t.state
  } catch(t) {
    throw new ti(-3,"notificationPermissions signal unexpected behaviour")
  }

},pi=function() {
  if(undefined===document.documentElement)throw new ti(-1,"document.documentElement is undefined");
  const {
    documentElement:n
  }
  =document;
  if("function"!=typeof n.getAttributeNames)throw new ti(-2,"document.documentElement.getAttributeNames is not a function");
  return n.getAttributeNames()
},gi=function() {
  if(undefined===Function.prototype.bind)throw new ti(-2,"Function.prototype.bind is undefined");
  return Function.prototype.bind.toString()
},wi=function() {
  const {
    process:n
  }
  =window,t="window.process is";
  if(undefined===n)throw new ti(-1,`${t} undefined`);
  if(n&&"object"!=typeof n)throw new ti(-3,`${t} not an object`);
  return n
},yi=function() {
  const n= {
    [Zo]: {
      window:["awesomium"]
    },[Go]: {
      window:["RunPerfTest"]
    },[Ho]: {
      window:["CefSharp"]
    },[Uo]: {
      window:["emit"]
    },[Bo]: {
      window:["fmget_targets"]
    },[$o]: {
      window:["geb"]
    },[Yo]: {
      window:["__nightmare","nightmare"]
    },[Xo]: {
      window:["__phantomas"]
    },[Jo]: {
      window:["callPhantom","_phantom"]
    },[qo]: {
      window:["spawn"]
    },[zo]: {
      window:["_Selenium_IDE_Recorder","_selenium","calledSelenium",/^([a-z]){3}_.*_(Array|Promise|Symbol)$/],document:["__selenium_evaluate","selenium-evaluate","__selenium_unwrapped"]
    },[Ko]: {
      window:["wdioElectron"]
    },[Qo]: {
      window:["webdriver","__webdriverFunc","__lastWatirAlert","__lastWatirConfirm","__lastWatirPrompt","_WEBDRIVER_ELEM_CACHE","ChromeDriverw"],document:["__webdriver_script_fn","__driver_evaluate","__webdriver_evaluate","__fxdriver_evaluate","__driver_unwrapped","__webdriver_unwrapped","__fxdriver_unwrapped","__webdriver_script_fn","__webdriver_script_func","__webdriver_script_function","$cdc_asdjflasutopfhvcZLmcf","$cdc_asdjflasutopfhvcZLmcfl_","$chrome_asyncScriptInfo","__$webdriverAsyncExecutor"]
    },[ni]: {
      window:["domAutomation","domAutomationController"]
    }

  };
  let t;
  const e= {

  },r=oi(window);
  let o=[];
  for(t in undefined!==window.document&&(o=oi(window.document)),n) {
    const i=n[t];
    if(undefined!==i) {
      const n=undefined!==i.window&&ii(r,...i.window),u=!(undefined===i.document||!o.length)&&ii(o,...i.document);
      e[t]=n||u;
    }

  }
  return e
};
function bi(n) {
  const t= {

  };
  for(const e of Object.keys(n)) {
    const r=n[e];
    if(r) {
      const n="error"in r?Ei(r.error):r.value;
      t[e]=n;
    }

  }
  return t
}
function Ei(n) {
  return  {
    e:Ri(n)
  }

}
function Ri(n) {
  let t;
  try {
    n&&"object"==typeof n&&"message"in n?(t=String(n.message),"name"in n&&(t=`${n.name}: ${t}`)):t=String(n);
  } catch(n) {
    t=`Code 3017: ${n}`;
  }
  return je(t,500)
}
function Si(n) {
  return rn(n,(n=>( {
    s:0,v:n
  })))
}
function Ii(n,t) {
  return rn(n,(n=>( {
    s:null==n?t:0,v:null!=n?n:null
  })))
}
function ki(n) {
  return rn(n,(n=>"number"==typeof n? {
    s:n,v:null
  }
  : {
    s:0,v:n
  }))
}
function Ai(n) {
  const t=n=>( {
    s:0,v:n
  }),e=n=> {
    if(!(n instanceof ti))throw n;
    const {
      state:t
    }
    =n;
    if("number"!=typeof t)throw new Error(`Unexpected non-numeric error state ${JSON.stringify(t)}. Error message: ${n.message}`);
    return  {
      s:t,v:null
    }

  };
  return ()=> {
    try {
      const r=n();
      return function(n) {
        return !!n&&"function"==typeof n.then
      }
      (r)?r.then(t,e):t(r)
    } catch(r) {
      return e(r)
    }

  }

}
async function Ci( {
  modules:n,components:t= {

  },customComponent:e,apiKey:r,tls:o,tag:i,extendedResult:u,exposeComponents:c,linkedId:s,algorithm:a,imi:l,storageKey:f,products:d,urlHashing:m,ii:v,ab:h,fast:p,requestId:g
}) {
  const w= {
    c:r,t:Li(i),cbd:u?1:undefined,lid:s,a:a,m:l.m,l:l.l,ec:c?1:undefined,mo:n.map((n=>n.key)).filter((n=>Boolean(n))),pr:d,s56:o,s67:e? {
      s:0,v:e
    }
    : {
      s:-1,v:null
    },sc:Pi(),uh:xi(m),ii:v,gt:1,ab:h,hu:p?0:g?1:undefined,ri:g,...bi(t)
  };
  return await Promise.all(n.map((async( {
    toRequest:n
  })=> {
    n&&Object.assign(w,await n(f,m));
  }))),w
}
function Li(n) {
  return n&&"object"==typeof n?n:null!=n? {
    tag:n
  }
  :undefined
}
function Pi() {
  const n=Wo();
  return  {
    u:n?je(n,1e3):null
  }

}
function xi(n) {
  if(n)return  {
    p:n.path?1:undefined,q:n.query?1:undefined,f:n.fragment?1:undefined
  }

}
async function Ti(n) {
  if(!Oi())return [false,n];
  const[t,e]=function() {
    try {
      return [true,new CompressionStream("deflate-raw")]
    } catch(n) {
      return [false,new CompressionStream("deflate")]
    }

  }
  (),r=await async function(n,t) {
    const e=t.writable.getWriter();
    e.write(n),e.close();
    const r=t.readable.getReader(),o=[];
    let i=0;
    for(;;) {
      const {
        value:n,done:t
      }
      =await r.read();
      if(t)break;
      o.push(n),i+=n.byteLength;
    }
    if(1===o.length)return o[0];
    const u=new Uint8Array(i);
    let c=0;
    for(const s of o)u.set(s,c),c+=s.byteLength;
    return u
  }
  (n,e),o=t?r:function(n) {
    return new Uint8Array(n.buffer,n.byteOffset+2,n.byteLength-6)
  }
  (r);
  return [true,o]
}
function Oi() {
  return "undefined"!=typeof CompressionStream
}
const _i=[3,13],ji=[3,14];
function Vi(n,t) {
  return zr(n,t?ji:_i,3,9)
}
function Ni(n,t) {
  return Kr(n,t?ji:_i,9)
}
function Mi(n) {
  return n.byteLength>1024&&Oi()
}
async function Fi(n,t,e,r,o) {
  if(0===n.length)throw new TypeError("The list of endpoints is empty");
  const i=n.map((n=>function(n, {
    apiKey:t
  }) {
    return Pr(n, {
      ci:mo(),q:t
    })
  }
  (n,t))),u=await Ci(t),c=Kt(u),s=t.fast?0:1;
  return await $r(o,(()=>( {
    e:15,stage:s,body:u,isCompressed:Mi(c)
  })),(n=>( {
    e:16,stage:s,result:n
  })),(n=>( {
    e:17,stage:s,error:n
  })),(async()=>function( {
    result:n,failedAttempts:t,aborted:e
  }) {
    if(n)return n;
    const r=t[0];
    if(!r)throw e&&!e.resolve?e.error:new Error("aborted");
    const {
      level:o,error:i
    }
    =r;
    if(0===o&&i instanceof Error) {
      switch(i.name) {
        case "CSPError":throw new Error(Te);
        case "InvalidURLError":throw new Error(Oe);
        case "AbortError":throw new Error(Pe)
      }
      throw new Error(Le)
    }
    throw i
  }
  (await Mo(i,Di.bind(null,c,o,s,e),Xe.bind(null,t.modules,!!t.extendedResult,t.storageKey),1/0,r))))
}
function Di(n,t,e,r,o,i,u) {
  return $r(t,(()=>( {
    e:18,stage:e,tryNumber:i,url:o
  })),(( {
    status:n,getHeader:t,body:r,bodyData:o,wasSecret:u
  })=>( {
    e:19,stage:e,tryNumber:i,status:n,retryAfter:t("retry-after"),body:null!=o?o:r,wasSecret:u
  })),(n=>( {
    e:20,stage:e,tryNumber:i,error:n
  })),(async()=> {
    const t=await async function( {
      body:n,...t
    }) {
      const[e,r]=Mi(n)?await Ti(n):[false,n],o=await Or( {
        ...t,body:Vi(r,e),responseFormat:"binary"
      });
      let i=o.body,u=false;
      try {
        i=Ni(i,false),u=true;
      } catch(c) {

      }
      return  {
        ...o,body:i,wasSecret:u
      }

    }
    ( {
      url:o,method:"post",headers: {
        "Content-Type":"text/plain"
      },body:n,withCredentials:true,abort:u,container:r
    });
    return function(n) {
      let t;
      try {
        t=Qt(n.body);
      } catch(e) {

      }
      return  {
        ...n,bodyData:t
      }

    }
    (t)
  }))
}
function Wi(n,t,e) {
  const r= {
    ...e,cache: {

    }

  },[o,i]=function(n) {
    const t= {

    },e= {

    },r= {

    };
    for(const {
      sources:i
    }
    of n)i&&(Object.assign(t,i.stage1),Object.assign(e,i.stage2),Object.assign(r,i.stage3));
    const o=e;
    return Object.assign(o,r),[t,o]
  }
  (n),c=function(n) {
    return n?1e5:50
  }
  (t),s=en(o,r,[],c),a=u$1(At(8).then((()=>en(i,r,[],c))));
  return async()=> {
    const[n,t]=await Promise.all([s(),a.then((n=>n()))]);
    !function(n) {
      const {
        si:t,aq:e
      }
      =n;
      for(t&&t.parentNode&&t.parentNode.removeChild(t),n.si=null,n.siw=null,n.ip=null;e.length>0;) {
        const n=e.shift();
        n&&n.reject(new Error("Iframe cleanup called"));
      }
      n.ipq=false;
    }
    (r.sis);
    const e=t;
    return Object.assign(e,n),e
  }

}
function Zi(n,t) {
  let e=n;
  for(;e;) {
    const n=Object.getOwnPropertyNames(e);
    for(let e=0;e<n.length;e++) {
      const r=n[e];
      if(A(r)==t)return r
    }
    e=Object.getPrototypeOf(e);
  }
  return ""
}
function Gi(n,t) {
  const e=n[Zi(n,t)];
  return "function"==typeof e?e.bind(n):e
}
function Hi(n,t) {
  let e;
  return r=>(e||(e=function(n,t) {
    return Qt(Kr(new Uint32Array(n),[],t))
  }
  (n,t)),T$1(e[r]))
}
function Ui(n,t,e) {
  if(n.length!==t.length||n.length!==e.length)throw new Error("Invalid encryption configuration: all input arrays must have the same length.");
  const r=new Array(n.length).fill(undefined);
  return o=> {
    var i;
    if(r.every((n=>null===n)))return null;
    for(let u=0;u<n.length;u++)if(null!==r[u]&&(r[u]||(r[u]=Bi(n[u],t[u],e[u])),null!==r[u]))return T$1(null===(i=r[u])||undefined===i?undefined:i[o]);
    return null
  }

}
function Bi(n,t,e) {
  const r=w$1(t());
  try {
    return Qt(function(n,t,e) {
      const r=d$1(n),o=new ArrayBuffer(r.length-e),i=new Uint8Array(o);
      for(let u=0;u<r.length;++u)i[u]=r[u]^t[u%t.length];
      return o
    }
    (new Uint32Array(n),r,e))
  } catch(o) {
    if(l$1(o)&&"SyntaxError"===o.name)return null;
    throw o
  }

}
var $i=Hi([3237452699,2611787672,3045311674,2962332150,4003383289,4090353905,3805249708,3028587956,2899958253,2946027702,4002601983,4204452091,4039413417,3970602410,3953912762,2631244730,3973421252,2844251834,2861027766,2946406891,3050675130,3806041579,2961425392,4023946731,3800865722,4208313581,2776941242,3806041513,4208313085,2743259834,3806041513,4208314361,3012023994,3968505257,3045300922,2799294954,4001684968,2648037617],4);
const Yi=[202,206];
function Xi(n) {
  const t=function(n,t) {
    return n(t)
  },e=function(n,t) {
    return n<t
  },r=function(n,t) {
    return n/t
  },o=function(n,t,e) {
    return n(t,e)
  },i=function(n,t) {
    return n+t
  },u=function(n,t) {
    return n+t
  },c=function(n,t) {
    return n+t
  },s=function(n,t) {
    return n-t
  },a=function(n,t,e,r) {
    return n(t,e,r)
  },l=function(n,t) {
    return n(t)
  },f=function(n,t) {
    return n(t)
  },d=function(n,t) {
    return n+t
  },m=function(n,t) {
    return n+t
  },v=function(n,t) {
    return n+t
  },h=function(n,t) {
    return n+t
  },p=function(n,t) {
    return n(t)
  },g=function(n,t,e) {
    return n(t,e)
  },y=t(Ct,n),b=new Uint8Array(16);
  for(let w=0;e(w,y.length);w+=2)b[r(w,2)]=o(parseInt,i(i(u(i("",y[w]),""),y[c(w,1)]),""),16);
  const E=t(R$1,b),S=a(qi,b[o(parseInt,y[s(y.length,1)],16)],8,22),I=E.slice(0,Math.min(s(E.length,2),S)),k=o(zi,l(w$1,I),Yi),A=l(R$1,l(Ki,f(C,k))).slice(0,2);
  return o(Lr,n,g(Ji,d(m(v(h("",I),""),A),"").replace(new RegExp(l($i,1),"g"),"-").replace(new RegExp(p($i,2),"g"),"_"),b))
}
function Ji(n,t) {
  const e=function(n,t) {
    return n<t
  },r=function(n,t,e,r) {
    return n(t,e,r)
  },o=function(n,t) {
    return n&t
  },i=function(n,t) {
    return n+t
  };
  let u=0,c=0,s="";
  for(;e(u,n.length);)c=r(qi,t[o(u,15)],4,7),s+=n.slice(u,i(u,c)),s+="/",u+=c;
  return s.slice(0,-1)
}
function qi(n,t,e) {
  const r=function(n,t) {
    return n+t
  },o=function(n,t) {
    return n*t
  },i=function(n,t) {
    return n/t
  },u=function(n,t) {
    return n-t
  };
  return r(t,Math.floor(o(i(n,256),r(u(e,t),1))))
}
function zi(n,t) {
  const e=function(n,t) {
    return n<t
  },r=function(n,t) {
    return n+t
  },o=function(n,t) {
    return n+t
  }
  (n.length,t.length),i=new Uint8Array(o);
  for(let u=0;e(u,n.length);u++)i[u]=n[u];
  for(let u=0;e(u,t.length);u++)i[r(u,n.length)]=t[u];
  return i
}
function Ki(n) {
  const t=function(n,t) {
    return n>>t
  },e=function(n,t) {
    return n>>t
  };
  return new Uint8Array([function(n,t) {
    return n>>t
  }
  (n,24),t(n,16),e(n,8),n])
}
function Qi(n,t) {
  const e=function(n,t,e) {
    return n(t,e)
  };
  return !!n&&function(n,t) {
    return n===t
  }
  (e(Gi,n,3814588639),e(Gi,t,3814588639))
}
function nu(n) {
  const t=function(n,t) {
    return n(t)
  },e=function(n,t) {
    return n!==t
  },r=function(n,t) {
    return n+t
  },o=function(n,t) {
    return n+t
  },i=function(n,t) {
    return n+t
  },u=function(n,t) {
    return n(t)
  };
  let c=t($i,3);
  return e(n,t($i,4))&&(c=r(o(i(r("",n),"."),c),"")),r(i(u($i,5),c),"/")
}
function tu$1(n) {
  const t=function(n,t) {
    return n+t
  },e=function(n,t) {
    return n(t)
  };
  return t(t("",function(n,t) {
    return n(t)
  }
  ($i,6)[n]),e($i,7))
}
const eu=(()=>( {
  noop:["a","b"]
}))();
function ru$1(n,t,e,o,i,c,f,d,m,v,h,p,g) {
  const w=1e4,y= {
    modules:n,apiKey:o,ii:d,imi:m,storageKey:f,ab:h,urlHashing:v
  };
  function b(n) {
    if(!g)return;
    const t=Tt(8);
    switch(n) {
      case "get":return function(n,t) {
        return e=> {
          const r= {
            ...e,getCallId:t
          };
          return n(r)
        }

      }
      (g,t);
      case "collect":return function(n,t) {
        return e=> {
          const r= {
            ...e,collectCallId:t
          };
          return n(r)
        }

      }
      (g,t)
    }

  }
  const E=n=>r$1(null!=n?n:w).then((()=>Promise.reject(new Error(Ce)))),R=async(t,e,r)=> {
    var o;
    const i=E(t.timeout);
    r(await S(t,i,e));
    for(const u of n)null===(o=u.onCollectResponse)||undefined===o||o.call(u,f);
  },S=async( {
    timeout:n=1e4,tag:t,linkedId:e
  },r,o)=> {
    const i=u$1(Promise.all([O(o),T(n,false,o)])),[c,s]=await Promise.race([r,i]),a=await Ci( {
      ...y,components:c,tag:t,tls:s,linkedId:L$1(e)
    });
    return await async function(n,t) {
      const e=[mo(),[]],r=Kt(e),o=Kt(n),[i,u]=Mi(o)?await Ti(o):[false,o],c=Vi(u,i);
      return Br(t,(()=>( {
        e:24,agentMetadata:e,body:n,isCompressed:i
      }))),`${I$1(r)}:${I$1(c)}`
    }
    (a,o)
  },k=async(n,t,e)=> {
    const r=s$1();
    try {
      const o=_r(r),i=E(n.timeout),u=C(n,o,t),c=await A(n,o,i,t);
      c?(e(c),await u(c.requestId,i)):e(await u(undefined,i));
    } finally {
      r.resolve();
    }

  },A=async( {
    tag:n,linkedId:t
  },e,r,o)=> {
    if(!p)return;
    const u=await x();
    let c=false;
    r.catch((()=>c=true));
    try {
      return await Fi(i, {
        ...y,tls:u,tag:n,linkedId:L$1(t),fast:true
      },e,r,o)
    } catch(s) {
      if(c)throw s;
      return void(l$1(s)&&s.message===He||console.warn(s))
    }

  },C=( {
    timeout:n=1e4,tag:t,linkedId:e,disableTls:r,extendedResult:o,exposeComponents:s,environment:a,products:l
  },f,d)=> {
    const m=u$1(Promise.all([O(d),T(n,r,d)]));
    return async(n,r)=> {
      const[u,v]=await Promise.race([r,m]);
      return await Fi(i, {
        ...y,components:u,customComponent:a,tag:t,tls:v,linkedId:L$1(e),extendedResult:o,exposeComponents:s,algorithm:c,products:P$1(l,"products"),requestId:n
      },f,r,d)
    }

  },x=()=>null==e?undefined:e(0,50,false,undefined),T=(n,t,r)=>null==e?undefined:e(.1*n,.4*n,t,r),O=async n=> {
    try {
      const e=await t();
      return Br(n,(()=>( {
        e:13,result:e
      }))),e
    } catch(e) {
      throw Br(n,(()=>( {
        e:14,error:e
      }))),e
    }

  };
  return  {
    get:(n= {

    })=> {
      const t=b("get");
      return $r(t,(()=>( {
        e:3,options:n
      })),(n=>( {
        e:4,result:n
      })),(n=>( {
        e:5,error:n
      })),(()=>a$1((e=>k(n,t,e)))))
    },collect:(n= {

    })=> {
      const t=b("collect");
      return $r(t,(()=>( {
        e:21,options:n
      })),(n=>( {
        e:22,result:n
      })),(n=>( {
        e:23,error:n
      })),(()=>a$1((e=>R(n,t,e)))))
    }

  }

}
function ou$1() {
  const n=/{(.*?)}/.exec(location.hash);
  return !!n&&3025844545===A(n[1])
}
const iu=async function(n) {
  const t=function(n) {
    const t=n.filter((n=>!!n));
    return t.length?(...n)=> {
      for(const e of t)o$1((()=>e(...n)));
    }
    :undefined
  }
  ([ou$1()&&ir(),...((null==n?undefined:n.modules)||[]).map((n=>n.addEvent))]),e=t&&function(n,t) {
    return e=> {
      const r= {
        ...e,agentId:t
      };
      return n(r)
    }

  }
  (t,Tt(8)),[r]=await $r(e,(()=>( {
    e:0,version:Wt,options:n
  })),(([,n])=>( {
    e:1,ab:n
  })),(n=>( {
    e:2,error:n
  })),(()=> {
    var t;
    const {
      token:r,apiKey:o=r,region:i="us",tlsEndpoint:u=Ht,disableTls:c,storageKey:s=Bt,endpoint:a=Zt,te:l=Gt,integrationInfo:f=[],algorithm:d,imi:m= {
        m:"s"
      },stripUrlParams:v,urlHashing:h=Ut(v),modules:p,abTests:g= {

      },externalABSelections:w= {

      },optimizeRepeatedVisits:y=false,aggressiveOptimization:b=false,extendedSignalCollection:E=true
    }
    =n;
    if(!o||"string"!=typeof o)throw new Error("API key required");
    const R=function(n,t,e) {
      const r= {
        ...e
      },o=Object.entries(n);
      for(const[u,c]of o) {
        const n=t[u];
        if(n)try {
          r[u]=Ft(n);
          continue
        } catch(i) {
          console.error(i);
        }
        r[u]=Ft(c);
      }
      return r
    }
    (function(n) {
      const t= {
        ...eu
      };
      for(const e of n)Object.assign(t,e.ab);
      return t
    }
    (p),g,w),S=function(n,t) {
      const e=function(n,t,e) {
        return n(t,e)
      },r=function(n,t) {
        return n(t)
      };
      return (Array.isArray(n)?n:[n]).map((n=>e(Qi,n,Zt)?r(nu,t):r(String,n)))
    }
    (a,i),I=null===(t=function(n) {
      for(const t of n)if(t.tls)return t.tls
    }
    (p))||undefined===t?undefined:t(u,S,o,c,undefined,e);
    Br(e,(()=>( {
      e:12
    })));
    const k=function(n,t) {
      const e=function(n,t) {
        return n(t)
      },r=function(n,t) {
        return n(t)
      };
      return o=n,Qi(o,Gt)?e(tu$1,t):r(String,n);
      var o;
    }
    (l,i),A= {
      aq:[],ipq:false,si:null,siw:null,ip:null,dc: {
        adb:0,crs:0,asib:0
      }

    };
    cr(A);
    return [ru$1(p,Wi(p,b, {
      urlHashing:h,ab:R,te:k,sis:A,esc:E
    }),I,o,S,L$1(d),s,f,m,h,R,y,e),R]
  }));
  return r
},uu$1=function(n,t= {

}) {
  const {
    storageKey:e=Bt,do:r
  }
  =t;
  try {
    const t=function(n) {
      const t=S$1(n);
      let e=t;
      try {
        e=Ni(t,false);
      } catch(r) {

      }
      try {
        return Qt(e)
      } catch(o) {

      }
      return null
    }
    (n);
    null!==t?(t.visitorToken&&co(t.visitorToken,so(e)),nr(t.notifications),Br(r,(()=>( {
      e:25,result: {
        response:t
      }

    })))):Br(r,(()=>( {
      e:25,result: {
        error:new Error("Failed to decode response")
      }

    })));
  } catch(o) {
    throw Br(r,(()=>( {
      e:25,result: {
        error:o instanceof Error?o:new Error(String(o))
      }

    }))),Qe(_e,undefined,o)
  }

},cu=["32926","32928"];
const su=Ii(Yn,-1),au$1=rn(vn,(n=>-1===n||-2===n||-3===n? {
  s:n,v:null
}
: {
  s:0,v:n
})),lu=rn(In,(n=>( {
  s:0,v:n.map((n=>null===n?-1:n))
}))),fu=Ii(Xn,-1),du$1=Si(Jn),mu=Ii(qn,-1),vu=Ii(zn,-1),hu$1=rn(En,(n=>( {
  s:0,v:n.map((n=>null===n?-1:n))
}))),pu=Ii(Kn,-1),gu$1=Si(Qn),wu=Si(nt),yu$1=Si(tt),bu$1=Si(et),Eu=Ii(rt,-1),Ru$1=Ii(ot,-1),Su$1=Ii(it,-1),Iu$1=rn((()=>yn()),(n=> {
  const {
    geometry:t,text:e
  }
  =n,r="unsupported"===t?-1:"unstable"===t?-2:0;
  return  {
    s:r,v: {
      ...n,geometry:0===r?Ct(t):"",text:0===r?Ct(e):""
    }

  }

})),ku$1=Si(ut),Au$1=Si(ct),Cu$1=Si(st),Lu$1=Si(at),Pu=Ii(lt,-1),xu$1=Ii(ft,-1),Tu=Ii(dt,-1),Ou$1=Ii(mt,-1),_u$1=Ii(vt,-1),ju=Ii(ht,-1),Vu$1=Ii(pt,-1),Nu$1=Ii(gt,-1),Mu$1=rn(wt,(n=>( {
  s:0,v:Ct(Object.keys(n).map((t=>`${t}=${n[t]}`)).join(","))
}))),Fu=Ii(yt,-1),Du$1=Si(bt),Wu$1=Ii(Et,-1),Zu$1=rn(Rt,(n=>-1===n||-2===n||-3===n? {
  s:n,v:null
}
: {
  s:0,v:n
})),Gu=ki(It),Hu=rn((Uu$1=kt,n=> {
  const t=n.cache;
  if(t.webGlRawValues)return T$1(t.webGlRawValues);
  const e=Uu$1(n);
  return "number"==typeof e?e:function(n,t) {
    const e=t;
    if(e.webGlRawValues)return T$1(e.webGlRawValues);
    const r=n.parameters.map((n=> {
      const[t,e,r]=n.split("=",3);
      return undefined!==r||cu.includes(e)?`${t}(${e})=null`:`${t}=${e}`
    })),o=n.extensionParameters.map((n=> {
      const[t,e,r]=n.split("=",3);
      return undefined!==r&&"34047"!==e?`${t}(${e})=${r}`:`${t}=${e}`
    }));
    return e.webGlRawValues= {
      contextAttributes:n.contextAttributes,parameters:r,parameters2:n.parameters,shaderPrecisions:n.shaderPrecisions,extensions:n.extensions||[],extensionParameters:o,extensionParameters2:n.extensionParameters,unsupportedExtensions:n.unsupportedExtensions
    },T$1(e.webGlRawValues)
  }
  (e,n.cache)
}),(n=>"number"==typeof n? {
  s:n,v:null
}
: {
  s:0,v: {
    contextAttributes:Ct(n.contextAttributes.join("&")),parameters:Ct(n.parameters.join("&")),parameters2:Ct(n.parameters2.join("&")),shaderPrecisions:Ct(n.shaderPrecisions.join("&")),extensions:Ct(n.extensions.join(",")),extensionParameters:Ct(n.extensionParameters.join(",")),extensionParameters2:Ct(n.extensionParameters2.join("&")),unsupportedExtensions:n.unsupportedExtensions
  }

}));
var Uu$1;
const Bu$1=ki(St),$u=Ai(ui),Yu$1=Ai(ci),Xu=Ai(si),Ju$1=Ai(hi),qu$1=Ai(li),zu=Ai(fi),Ku=Ai(di),Qu=Ai(pi),nc=Ai(mi),tc=Ai(vi),ec=Ai(gi),rc=Ai(wi),oc=Ai(ai),ic=Ai(yi),uc=Si(on),cc=Si(un),sc=Si(cn),ac=Si(sn),lc=Si(an),fc=Si(ln),dc=Si(dn),mc=Si(Gr),vc=Si(mn);
function hc() {
  const n=window;
  if(!cn())return pc(false);
  try {
    if([66,114,97,118,101].map((n=>String.fromCharCode(n))).join("")in n)return pc(true);
    const t=document.createElement("canvas");
    t.width=4,t.height=4,t.style.display="inline";
    const e=t.toDataURL();
    if(""===e)return pc(true);
    const r=S$1(e.split(",")[1]),o=g$1(r,[73,68,65,84,24]);
    if(-1===o)return pc(false);
    const i=g$1(r,[73,69,78,68]);
    if(-1===i)return pc(false);
    const u=r.slice(o+5,i);
    return pc(1321!==u.reduce(((n,t)=>n+t),0))
  } catch(t) {
    return pc(false)
  }

}
function pc(n) {
  return  {
    s:0,v:n
  }

}
function gc() {
  return wc("dark")? {
    s:0,v:true
  }
  :wc("light")? {
    s:0,v:false
  }
  : {
    s:-1,v:null
  }

}
function wc(n) {
  return matchMedia(`(prefers-color-scheme: ${n})`).matches
}
function yc() {
  const n=Date.now();
  return  {
    s:0,v:[bc(n),bc(n-6e4*(new Date).getTimezoneOffset())]
  }

}
function bc(n) {
  const t=Number(n);
  return isNaN(t)?-1:t
}
const Ec="mmMwWLliI0O&1",Rc="48px",Sc=["monospace","sans-serif","serif"],Ic=["sans-serif-thin","ARNO PRO","Agency FB","Arabic Typesetting","Arial Unicode MS","AvantGarde Bk BT","BankGothic Md BT","Batang","Bitstream Vera Sans Mono","Calibri","Century","Century Gothic","Clarendon","EUROSTILE","Franklin Gothic","Futura Bk BT","Futura Md BT","GOTHAM","Gill Sans","HELV","Haettenschweiler","Helvetica Neue","Humanst521 BT","Leelawadee","Letter Gothic","Levenim MT","Lucida Bright","Lucida Sans","Menlo","MS Mincho","MS Outlook","MS Reference Specialty","MS UI Gothic","MT Extra","MYRIAD PRO","Marlett","Meiryo UI","Microsoft Uighur","Minion Pro","Monotype Corsiva","PMingLiU","Pristina","SCRIPTINA","Segoe UI Light","Serifa","SimHei","Small Fonts","Staccato222 BT","TRAJAN PRO","Univers CE 55 Medium","Vrinda","ZWAdobeF"];
async function kc(n) {
  return await function(n) {
    return ur(((n, {
      document:t
    })=> {
      const e=t.body;
      e.style.fontSize=Rc;
      const r=t.createElement("div");
      r.style.setProperty("visibility","hidden","import ant");
      const o= {

      },i= {

      },u=n=> {
        const e=t.createElement("span"), {
          style:o
        }
        =e;
        return o.position="absolute",o.top="0",o.left="0",o.fontFamily=n,e.textContent=Ec,r.appendChild(e),e
      },c=(n,t)=>u(`'${n}',${t}`),s=()=> {
        const n= {

        };
        for(const t of Ic)n[t]=Sc.map((n=>c(t,n)));
        return n
      },a=n=>Sc.some(((t,e)=>n[e].offsetWidth!==o[t]||n[e].offsetHeight!==i[t])),l=(()=>Sc.map(u))(),f=s();
      e.appendChild(r);
      for(let m=0;m<Sc.length;m++)o[Sc[m]]=l[m].offsetWidth,i[Sc[m]]=l[m].offsetHeight;
      const d=Ic.filter((n=>a(f[n])));
      return e.removeChild(r),e.style.fontSize="", {
        s:0,v:d
      }

    }),n.sis)
  }
  (n)
}
const Ac="mmMwWLliI0fiflO&1",Cc= {
  default:[],apple:[ {
    font:"-apple-system-body"
  }],serif:[ {
    fontFamily:"serif"
  }],sans:[ {
    fontFamily:"sans-serif"
  }],mono:[ {
    fontFamily:"monospace"
  }],min:[ {
    fontSize:"1px"
  }],system:[ {
    fontFamily:"system-ui"
  }]
};
async function Lc() {
  try {
    return  {
      s:0,v:await Pc(((n,t)=> {
        const e= {

        },r= {

        };
        for(const o of Object.keys(Cc)) {
          const[r= {

          },i=Ac]=Cc[o],u=n.createElement("span");
          u.textContent=i,u.style.whiteSpace="nowrap";
          for(const n of Object.keys(r)) {
            const t=r[n];
            undefined!==t&&(u.style[n]=t);
          }
          e[o]=u,t.append(n.createElement("br"),u);
        }
        for(const o of Object.keys(Cc))r[o]=e[o].getBoundingClientRect().width;
        return r
      }))
    }

  } catch(n) {
    if(Er(n))return  {
      s:-101,v:null
    };
    throw n
  }

}
function Pc(n,t=4e3) {
  return pn(((e,r)=> {
    const o=r.document,i=o.body,u=i.style;
    u.width=`${t}px`,u.webkitTextSizeAdjust="none",u.setProperty("text-size-adjust","none"),cn()?i.style.setProperty("zoom",""+1/r.devicePixelRatio):sn()&&i.style.setProperty("zoom","reset");
    const c=o.createElement("div");
    return c.textContent=[...Array(t/20<<0)].map((()=>"word")).join(" "),i.appendChild(c),n(o,i)
  }),'<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">')
}
function xc() {
  const {
    performance:n
  }
  =window;
  if(!(null==n?undefined:n.now))return  {
    s:-1,v:null
  };
  let t=1,e=1,r=n.now(),o=r;
  for(let i=0;i<5e4;i++)if((r=o)<(o=n.now())) {
    const n=o-r;
    n>t?n<e&&(e=n):n<t&&(e=t,t=n);
  }
  return  {
    s:0,v:[t,e]
  }

}
var Tc=Hi([1910186786,4206938268,3099470367,511281317,2493621742,2512262268],6);
function Oc() {
  var n,t,e=function(n,t) {
    return n===t
  },r=function(n,t) {
    return n===t
  },o=function(n,t,e) {
    return n(t,e)
  };
  const i=e(t=function(n,t) {
    return n===t
  }
  (n=window[function(n,t) {
    return n(t)
  }
  (Tc,0)],null)||r(n,undefined)?undefined:o(Gi,n,3933025333),null)||r(t,undefined)?undefined:o(Gi,t,3098533860);
  return e(i,null)||e(i,undefined)? {
    s:-1,v:null
  }
  : {
    s:0,v:i
  }

}
function _c( {
  cache:n
}) {
  const t=Zn(n);
  return t?(function(n) {
    n.clearColor(0,0,1,1);
    const t=n.createProgram();
    if(!t)return;
    function e(e,r) {
      const o=n.createShader(35633-e);
      t&&o&&(n.shaderSource(o,r),n.compileShader(o),n.attachShader(t,o));
    }
    e(0,"attribute vec2 p;uniform float t;void main(){float s=sin(t);float c=cos(t);gl_Position=vec4(p*mat2(c,s,-s,c),1,1);}"),e(1,"void main(){gl_FragColor=vec4(1,0,0,1);}"),n.linkProgram(t),n.useProgram(t),n.enableVertexAttribArray(0);
    const r=n.getUniformLocation(t,"t"),o=n.createBuffer(),i=34962;
    n.bindBuffer(i,o),n.bufferData(i,new Float32Array([0,1,-1,-1,1,-1]),35044),n.vertexAttribPointer(0,2,5126,false,0,0),n.clear(16384),n.uniform1f(r,3.65),n.drawArrays(4,0,3);
  }
  (t), {
    s:0,v:Ct(t.canvas.toDataURL())
  }): {
    s:-1,v:null
  }

}
function jc(n) {
  return Nc(n,Mc)
}
function Vc(n) {
  return Nc(n,Fc)
}
async function Nc( {
  cache:n
},r) {
  const {
    speechSynthesis:o
  }
  =window;
  if("function"!=typeof (null==o?undefined:o.getVoices))return  {
    s:-1,v:null
  };
  n.tts||(n.tts=async function(n) {
    const r=()=>n.getVoices();
    if(function(n) {
      return !n.addEventListener||ln()&&Gr()||sn()
    }
    (n))return  {
      v:r()
    };
    const o= {
      v:null
    };
    let i;
    try {
      await new Promise(((u,c)=> {
        let s;
        const a=()=> {
          const n=r();
          n.length?(o.v=n,null==s||s(),s=t$1(u,50)):s||(s=e$1(u,600));
        };
        i=v$1(n,"voiceschanged",(()=> {
          try {
            a();
          } catch(n) {
            c(n);
          }

        })),a();
      }));
    } finally {
      i&&e$1(i,1e4);
    }
    return o
  }
  (o));
  const i=await n.tts;
  return ()=>i.v?r(i.v): {
    s:-2,v:null
  }

}
function Mc(n) {
  const t=n=>n.replace(/([,\\])/g,"\\$1"),e=n.map((n=>[t(n.voiceURI),t(n.name),t(n.lang),n.localService?"1":"0",n.default?"1":"0"].join(","))).sort();
  return  {
    s:n.length?0:1,v:Ct(JSON.stringify(e))
  }

}
function Fc(n) {
  const t=n.some((n=>1655763047===A(n.name.slice(0,6))));
  return  {
    s:n.length?0:1,v:t
  }

}
const Dc=["brands","mobile","platform","platformVersion","architecture","bitness","model","uaFullVersion","fullVersionList"];
async function Wc() {
  var n;
  const {
    userAgentData:t
  }
  =navigator;
  if(!t||"object"!=typeof t)return  {
    s:-1,v:null
  };
  const e= {

  },r=[];
  return "function"==typeof t.getHighEntropyValues&&await Promise.all(Dc.map((async n=> {
    try {
      const r=(await t.getHighEntropyValues([n]))[n];
      undefined!==r&&(e[n]="string"==typeof r?r:JSON.stringify(r));
    } catch(o) {
      if(!(o instanceof Error&&"NotAllowedError"===o.name))throw o;
      r.push(n);
    }

  }))), {
    s:0,v: {
      b:t.brands.map((n=>( {
        b:n.brand,v:n.version
      }))),m:t.mobile,p:null!==(n=t.platform)&&undefined!==n?n:null,h:e,nah:r
    }

  }

}
async function Zc( {
  urlHashing:n
}) {
  const t=function(n) {
    var t,e;
    const r=[];
    let o=n;
    for(;;)try {
      const n=null===(t=o.location)||undefined===t?undefined:t.href,i=null===(e=o.document)||undefined===e?undefined:e.referrer;
      if(undefined===n||undefined===i)return  {
        s:1,v:r
      };
      r.push( {
        l:n,f:i
      });
      const u=o.parent;
      if(!u||u===o)return  {
        s:0,v:r
      };
      o=u;
    } catch(i) {
      if(Hc(i))return  {
        s:1,v:r
      };
      throw i
    }

  }
  (window);
  return  {
    ...t,v:await Gc(t.v,n)
  }

}
async function Gc(n,t) {
  return Promise.all(n.map((async n=> {
    const[e,r]=await Promise.all([Ir(n.l,t),Ir(n.f,t)]);
    return  {
      l:e,f:r
    }

  })))
}
function Hc(n) {
  if(!n||"object"!=typeof n)return false;
  const t=n;
  return !(!on()&&!un()||"Error"!==t.name&&"TypeError"!==t.name||"Permission denied"!==t.message)||"SecurityError"===t.name
}
function Uc() {
  return function( {
    location:n,origin:t
  }) {
    const e=n.origin,r=n.ancestorOrigins;
    let o=null;
    if(r) {
      o=new Array(r.length);
      for(let n=0;n<r.length;++n)o[n]=r[n];
    }
    return  {
      s:0,v: {
        w:null==t?null:t,l:null==e?null:e,a:o
      }

    }

  }
  (window)
}
function Bc() {
  return  {
    s:0,v:eval.toString().length
  }

}
function $c() {
  const {
    webdriver:n
  }
  =navigator;
  return null===n? {
    s:-1,v:null
  }
  :undefined===n? {
    s:-2,v:null
  }
  : {
    s:0,v:n
  }

}
function Yc() {
  const n=function(n,t,e) {
    return n(t,e)
  },t=function(n,t) {
    return n===t
  },e=function(n,t) {
    return n===t
  },o=function(n,t,e) {
    return n(t,e)
  };
  return o(c$1,function(n,t,e) {
    return n(t,e)
  }
  (r$1,250, {
    s:-2,v:null
  }),(async()=> {
    const r=n(Gi,navigator,1417288500);
    return (t(r,null)||e(r,undefined)?undefined:o(Gi,r,3686698663))?await n(Gi,r,3686698663)().then((()=>( {
      s:0,v:""
    })),(n=>( {
      s:0,v:Gi(n,3065852031)
    }))): {
      s:-1,v:null
    }

  }))
}
function Xc() {
  const n=(new Image).style;
  return qc([Zi(t=n,2882756133),Zi(t,3858258232)],[18,23,22,11,23,17,3,20,4,22,19,11,25,13,23,22,7,7,17,18,4,18,11,8,11,8,3,5,2,4,3,3,5,6,5,3,1,2,2,0,0]);
  var t;
}
function Jc(n,t,e) {
  const r=Zi(n,t);
  if(!r)return "";
  const o=S$1(e),i=Array(o.length);
  for(let u=0;u<o.length;u++)i[u]=o[u]^r.charCodeAt(u%r.length);
  return String.fromCharCode.apply(null,i)
}
function qc(n,t) {
  const e=n.join(""),r=e.split(""),o=Array(e.length);
  for(let i=0;i<o.length;++i)o[i]=r.splice(t[i%t.length],1);
  return o.join("")
}
var zc=Ui([[290799128,256122120,104421910,67116302,755371265,505093152,152897830,504707661,470222364,504898635,1531393810,35461445,285283613,151395398,386279171,454440300,1259148302,67715140,117915663,1445400833,70599515,280581,270008841,369435995,272236574,119803980,704973062,135268614,184563807,1026755337,824180753,521019142,404440330,1310525212,689393240,992889883,118162967,75079,371069214,14400,67440946,336725549,100928582,419697754,37884160,822483751,151655985,440867606,34934535,1544297499,69023765,1530421525,521022789,352788490,152182535,1095068179,168111383,102371362,1379942426,218301962,410405200,674697750,150995736,1460669954,289295192,422585355,276197185,1241580055,503401029,169544981,956309037,1628772625,269702473,1481182751,12887,860704273,607786827,1079856400,370150428,234881091,407897606,354309752,1157892134,252333381,1264080656,304025857,1627786793,302143352,172563473,34688007,17172047,337261841,285893380,117845831,1448695310,152569103,1095068178,68628788,120395278,352653340,1245924639,288361223,2951185,3425555]],[Xc],[1]);
function Kc() {
  return zc(0)
}
function Qc() {
  const n=function(n,t) {
    return n(t)
  },t=function(n,t) {
    return n instanceof t
  },e=function(n,t) {
    return n===t
  },r=function(n,t) {
    return n(t)
  };
  if(!function(n,t) {
    return n in t
  }
  (n(zc,1),window))return false;
  try {
    return new(window[n(zc,1)]),true
  } catch(o) {
    if(t(o,Error)&&e(o.name,r(zc,2)))return false;
    throw o
  }

}
async function ns(n) {
  const t=function(n,t) {
    return n(t)
  },e=function(n,t) {
    return n(t)
  },r=function(n,t) {
    return n(t)
  },o=function(n,t) {
    return n!==t
  },[i,u,c]=t(ts,n);
  return o(u,0)? {
    n:i,l:u
  }
  :await new Promise((n=> {
    const o=function(n,t) {
      return e(n,t)
    };
    c[r(zc,3)]((r=> {
      t(n, {
        n:i,l:r[e(zc,4)]
      });
    }),(()=> {
      o(n, {
        n:i,l:-1
      });
    }));
  }))
}
function ts(n) {
  const t=function(n,t) {
    return n(t)
  },e=function(n,t,e) {
    return n(t,e)
  },r=function(n,t) {
    return n(t)
  },o=function(n,t) {
    return n(t)
  },i=function(n,t) {
    return n(t)
  },u=function(n,t) {
    return n(t)
  },c=function(n,t) {
    return n(t)
  },s=function(n,t) {
    return n(t)
  },a=function(n,t) {
    return n instanceof t
  },l=function(n,t) {
    return n===t
  },f=function(n,t) {
    return n(t)
  },d=function(n,t) {
    return n!==t
  },m=function(n,t) {
    return n===t
  },v=function(n,t) {
    return n(t)
  },h=function(n,t) {
    return n(t)
  },p=function(n,t) {
    return n===t
  },g=function(n,t) {
    return n(t)
  };
  var w;
  const[y]=n.split("/").slice(-1),b=new(window[t(zc,1)]),E=e(Zi,new(window[t(zc,5)])("")[r(zc,6)](""),3626513111),R=document[o(zc,7)](E);
  R[t(zc,8)]=i(zc,3);
  const S=new(window[u(zc,9)])([],n,c(zc,10));
  try {
    b[t(zc,11)][s(zc,12)](S);
  } catch(I) {
    if(a(I,Error)&&l(I.name,f(zc,2))&&d(l(w=I[i(zc,13)],null)||m(w,undefined)?undefined:w.indexOf(c(zc,14)),-1))return [y,-3,null];
    throw I
  }
  return R[i(zc,15)]=b[v(zc,15)],l(typeof R[h(zc,16)],o(zc,17))?[y,-4,null]:p(R[g(zc,16)].length,0)?[y,-2,null]:[y,0,R[c(zc,16)][0]]
}
var es=Hi([752472786,243421427,1304376727,44907654,246431386,1168077535,16463263,1619723729,1257995473,1606171802,1236083594,66480798,250966748,1912304588],4);
async function rs() {
  const n=function(n) {
    return n()
  },t=function(n,t) {
    return n(t)
  },e=function(n,t,e) {
    return n(t,e)
  },o=function(n,t,e) {
    return n(t,e)
  },i=function(n) {
    return n()
  }
  (Kc);
  return i?n(Qc)?await o(c$1,e(r$1,350, {
    s:-2,v:null
  }),(async()=>( {
    s:0,v:await Promise.all(i.map(ns))
  }))):await o(c$1,e(r$1,350, {
    s:-1,v:null
  }),(async()=>( {
    s:-1,v:await Promise.all([t(os,i[0])])
  }))):await e(c$1,e(r$1,350, {
    s:-3,v:null
  }),(async()=>( {
    s:-3,v:await Promise.all([n(os)])
  })))
}
async function os(n=es(0)) {
  const t=function(n,t) {
    return n(t)
  },e=function(n,t) {
    return n+t
  },r=function(n,t) {
    return n+t
  },o=function(n,t) {
    return n+t
  },i=function(n,t) {
    return n(t)
  },u=function(n,t,e) {
    return n(t,e)
  },c=function(n,t) {
    return n===t
  },s=function(n,t) {
    return n(t)
  },a=function(n,t) {
    return n===t
  },l=function(n,t) {
    return n===t
  };
  var f,d;
  const[m]=n.split("/").slice(-1);
  try {
    const v=new(window[t(es,1)])([],n),h=new(window[t(es,2)])(e(r(r(e(e(o(i(es,3),u(Gi,v,4081332993)||""),""),m),t(es,4)),u(Gi,v,3034174415)),""));
    return c(c(f=u(Gi,h,3518522040),null)||c(f,undefined)?undefined:f.substring(1),"")? {
      n:m,l:-2
    }
    : {
      n:m,l:s(A,a(d=u(Gi,h,3518522040),null)||l(d,undefined)?undefined:d.substring(1))
    }

  } catch(v) {
    return  {
      n:m,l:-1
    }

  }

}
function is() {
  const n=function(n,t) {
    return n===t
  },t=function(n,t,e) {
    return n(t,e)
  }
  (Gi,navigator,3087401394);
  return n(t,undefined)||n(t,null)? {
    s:-1,v:null
  }
  : {
    s:0,v:t
  }

}
function us() {
  const n=function(n,t,e) {
    return n(t,e)
  },t=function(n,t) {
    return n===t
  },e=function(n,t,e) {
    return n(t,e)
  },r=n(Gi,window,4177808745);
  if(!(t(r,null)||t(r,undefined)?undefined:n(Gi,r,1108488788)))return  {
    s:-1,v:null
  };
  const o=[0,97,115,109,1,0,0,0,1,4,1,96,0,0,3,2,1,0,10],i=[[9,1,7,0,65,0,253,15,26,11,0,10,4,110,97,109,101,2,3,1,0,0],[240,67,0,0,0,12,1,10,0,252,2,3,1,1,0,0,110,26,11,161,10],[6,1,4,0,18,0,11,0,10,4,110,97,109,101,2,3,1,0,0],[8,1,6,0,65,0,192,26,11,0,10,4,110,97,109,101,2,3,1,0,0],[7,1,5,0,208,112,26,11,0,10,4,110,97,109,101,2,3,1,0,0]];
  let u=0;
  for(const c of i)u<<=1,u|=e(Gi,r,1108488788)(Uint8Array.of(...o,...c))?1:0;
  return  {
    s:0,v:u
  }

}
function cs() {
  const n=function(n,t) {
    return n-t
  },t=function(n,t) {
    return n*t
  },e=function(n,t) {
    return n>=t
  },r=function(n,t) {
    return n===t
  },o=function(n,t) {
    return n%t
  },i=function(n,t) {
    return n|t
  },u=function(n,t) {
    return n**t
  },c=[];
  let s=Math.random();
  for(let a=n(t(6,4096),1);e(a,0);--a)if(r(o(a,4096),0)) {
    const e=Math.random();
    c.push(i(t(n(s,e),u(2,31)),0)),s=e;
  }
  return  {
    s:0,v:c
  }

}
function ss() {
  const n=window.devicePixelRatio;
  return null==n? {
    s:-1,v:null
  }
  : {
    s:0,v:n
  }

}
function as() {
  const n=navigator,t=["webkitPersistentStorage","connectionSpeed","xr","hid"],e=[];
  for(const o of Object.getOwnPropertyNames(Object.getPrototypeOf(n)))if(!t.includes(o))try {
    const t=n[o];
    "function"==typeof t&&undefined!==t.name&&e.push(t.name);
  } catch(r) {
    return  {
      s:-1,v:[r instanceof Error?r.message:String(r)]
    }

  }
  return  {
    s:0,v:e
  }

}
function ls() {
  try {
    return objectToInspect, {
      s:0,v:true
    }

  } catch(n) {
    return  {
      s:0,v:false
    }

  }

}
function fs() {
  return "undefined"==typeof CSS? {
    s:-1,v:null
  }
  : {
    s:0,v:CSS.supports("backdrop-filter","blur(2px)")
  }

}
function ds() {
  if("function"!=typeof window.SharedArrayBuffer)return  {
    s:-2,v:null
  };
  const n=new window.SharedArrayBuffer(1);
  return undefined===n.byteLength? {
    s:-1,v:null
  }
  : {
    s:0,v:n.byteLength
  }

}
function ms() {
  if("function"!=typeof window.matchMedia)return  {
    s:-2,v:null
  };
  const n=window.matchMedia("(-webkit-min-device-pixel-ratio: 2), (min-device-pixel-ratio: 2), (min-resolution: 192dpi)");
  return undefined===n.matches? {
    s:-1,v:null
  }
  : {
    s:0,v:n.matches
  }

}
function vs() {
  try {
    throw "a"
  } catch(n) {
    try {
      return n.toSource(), {
        s:0,v:true
      }

    } catch(t) {
      return  {
        s:0,v:false
      }

    }

  }

}
async function hs(n) {
  return ur(((n,t)=> {
    const e=t.document.createElement("div");
    e.style.border=".5px dotted transparent",t.document.body.appendChild(e);
    const r=e.offsetHeight;
    return t.document.body.removeChild(e), {
      s:0,v:r
    }

  }),n.sis)
}
function ps() {
  return undefined===navigator.mimeTypes? {
    s:-1,v:null
  }
  :undefined===navigator.mimeTypes.length? {
    s:-3,v:null
  }
  : {
    s:0,v:navigator.mimeTypes.length
  }

}
function gs() {
  return  {
    s:0,v:!(!navigator.userAgentData||"object"!=typeof navigator.userAgentData)
  }

}
function ws() {
  if(undefined===navigator.plugins)return  {
    s:-1,v:null
  };
  const {
    plugins:n
  }
  =navigator;
  let t=Object.getPrototypeOf(n)===PluginArray.prototype;
  for(let e=0;e<n.length;e++)t&&(t=Object.getPrototypeOf(n[e])===Plugin.prototype);
  return  {
    s:0,v:t
  }

}
function ys() {
  return  {
    s:0,v:[typeof SourceBuffer,typeof SourceBufferList]
  }

}
function bs() {
  return undefined===window.close? {
    s:-1,v:null
  }
  : {
    s:0,v:window.close.toString()
  }

}
function Es() {
  const n=navigator.language;
  return n? {
    s:0,v:n
  }
  : {
    s:-1,v:null
  }

}
function Rs() {
  const n=navigator.languages;
  return n? {
    s:0,v:n
  }
  : {
    s:-1,v:null
  }

}
async function Ss() {
  const t=function(n,t,e) {
    return n(t,e)
  },e=function(n,t) {
    return n===t
  },r=function(n,t,e) {
    return n(t,e)
  },o=function(n,t,e) {
    return n(t,e)
  },i=function(n,t) {
    return n!==t
  },u=function(n,t) {
    return n===t
  },c=function(n,t) {
    return n===t
  },s=function(n,t,e) {
    return n(t,e)
  },a=function(n,t,e) {
    return n(t,e)
  },l=function(n,t) {
    return n(t)
  },f=navigator,d=t(Gi,f,1417288500),m=t(Gi,f,2706846255);
  if(!m&&!(e(d,null)||e(d,undefined)?undefined:r(Gi,d,3538568711)))return  {
    s:-1,v:null
  };
  if(m) {
    const e=await Promise.race([o(n,250,undefined),new Promise((n=> {
      t(Gi,m,1291883197)(((t,e)=>n(e)));
    }))]);
    if(i(e,undefined))return  {
      s:0,v:e
    }

  }
  try {
    if(u(d,null)||c(d,undefined)?undefined:r(Gi,d,3538568711)) {
      const t=await Promise.race([s(n,250,undefined),a(Gi,d,3538568711)().then((n=>Gi(n,1813778413)))]);
      if(i(t,undefined))return  {
        s:1,v:t
      }

    }
    return  {
      s:-2,v:null
    }

  } catch(v) {
    if(l(Er,v))return  {
      s:-101,v:null
    };
    throw v
  }

}
async function Is() {
  const t=function(n) {
    return n()
  },e=function(n,t,e) {
    return n(t,e)
  },r=function(n,t) {
    return n===t
  };
  if(function(n) {
    return n()
  }
  (cn)&&t(Hr))return  {
    s:-3,v:null
  };
  const o=await Promise.race([e(n,100,null),t(ks)]);
  return r(o,null)? {
    s:-2,v:null
  }
  :r(o,undefined)? {
    s:-1,v:null
  }
  : {
    s:0,v:o
  }

}
async function ks() {
  const n=function(n,t,e,r,o) {
    return n(t,e,r,o)
  },t=function(n,t,e) {
    return n(t,e)
  }
  (Gi,window,2796484463);
  if(t)return new Promise((e=> {
    n(t,0,1,(()=>e(true)),(()=>e(false)));
  }))
}
function As(n) {
  return ur(((n,t)=> {
    const e=t.screen,r=n=> {
      const t=parseInt(n);
      return "number"==typeof t&&isNaN(t)?-1:t
    };
    return  {
      s:0,v: {
        w:r(e.width),h:r(e.height)
      }

    }

  }),n.sis)
}
var Cs=Hi([3924185679,3632893699,2980828376,2699881398,2597186493,3081479162,2868636342,4104912311,2917654778,3120294056,3186092732,3169643453,4210205690,3086875321,2867519889,3068977853,2897456556,2783771306,3033247220,4104908215,3152862458,2900426157,2868628129,2242641335],4);
function Ls() {
  const n=function(n,t) {
    return n(t)
  },t=function(n,t) {
    return n(t)
  };
  try {
    return n(Ps,!!window[n(Cs,0)])
  } catch(e) {
    return t(Ps,true)
  }

}
function Ps(n) {
  return  {
    s:0,v:n
  }

}
function xs() {
  const n=function(n) {
    return n()
  },t=function(n,t,e) {
    return n(t,e)
  };
  return t(c$1,t(r$1,250, {
    s:-3,v:null
  }),(async()=>n(sn)||n(ln)?n(Ts): {
    s:-1,v:null
  }))
}
async function Ts() {
  const n=function(n,t,e) {
    return n(t,e)
  },t=function(n,t,e) {
    return n(t,e)
  },e=function(n,t) {
    return n(t)
  },r=function(n,t) {
    return n(t)
  },o=function(n,t) {
    return n instanceof t
  },i=function(n,t) {
    return n(t)
  },u=function(n,t,e) {
    return n(t,e)
  },c=function(n,t) {
    return n(t)
  },s=function(n,t,e) {
    return n(t,e)
  },a=function(n,t) {
    return n(t)
  },l=function(n) {
    return n()
  },f=function(n,t) {
    return n===t
  },d=function(n,t) {
    return n(t)
  },m=function(n,t) {
    return n(t)
  },v=function(n,t) {
    return n(t)
  },h=function(n,t) {
    return n+t
  },p=function(n,t) {
    return n+t
  },g=function(n,t) {
    return n(t)
  },w=window[a(Cs,0)];
  if(!w)return  {
    s:-2,v:null
  };
  const y=h(p("",g(Tt,16)),"");
  return new Promise(((h,p)=> {
    const g=function(n,t) {
      return c(n,t)
    };
    try {
      const c=s(Gi,w,2758837156)(y,1);
      c[a(Cs,1)]=()=> {
        g(h, {
          s:-5,v:null
        });
      },c[e(Cs,2)]=c=> {
        const s=n(Gi,n(Gi,c,1181691900),325763347);
        try {
          return n(Gi,t(Gi,s,138212912)("-",e(Cs,3)),2928708052)(new(window[r(Cs,4)])),void r(h, {
            s:0,v:""
          })
        } catch(a) {
          if(o(a,Error))return void i(h, {
            s:0,v:u(Gi,a,3065852031)
          });
          r(p,a);
        } finally {
          n(Gi,s,318865860)(),u(Gi,w,3885781331)(y);
        }

      };
    } catch(b) {
      if(!l(sn))return void i(h, {
        s:-5,v:null
      });
      if(o(b,Error)&&f(b.name,d(Cs,5)))return void m(h, {
        s:-4,v:null
      });
      v(p,b);
    }

  }))
}
function Os() {
  const n=function(n) {
    return n()
  },t=function(n,t,e) {
    return n(t,e)
  },e=function(n,t,e) {
    return n(t,e)
  },r=function(n,t,e,r,o) {
    return n(t,e,r,o)
  },o="test";
  if(!n(sn)||n(Fr))return  {
    s:-1,v:null
  };
  const i=t(Gi,window,693717494),u=e(Gi,window,1703339950);
  try {
    r(i,null,null,null,null);
  } catch(c) {
    return  {
      s:0,v:true
    }

  }
  try {
    return e(Gi,u,2330630162)(o,"1"),e(Gi,u,588657539)(o), {
      s:0,v:false
    }

  } catch(s) {
    return  {
      s:0,v:true
    }

  }

}
function _s() {
  const n=Object.getOwnPropertyDescriptor(document,"createElement");
  return n? {
    s:0,v:!("writeable"in n)
  }
  : {
    s:-1,v:null
  }

}
function js() {
  return  {
    s:0,v:Boolean(navigator.onLine)
  }

}
var Vs=Hi([2051009255,196400063,2525527446,4044416111,199305624,3777599729,664183563,2527137204,2959068455,280520411,4185511866,2144517134,3586067896,2987975794,1370780368,4217690097,2128325203,3518040290,2987517477,485718477,3408514487,1624764753,2525516212,3089101692,314277853,3777352609,1742208334,3751877875,4284477294,451175574,3090727933,1792130846,3451262692,4048669481,1370783684,4184381064,1876294928,2595627001,3189040251,285179857,3022493366,635026462,3602651639,2954672238,249917143,3022514673,664183579,3685769165,2736568422,1408460740,3831682485,1926610701,2533302452,3122262854,83050709,3022493344,1087813162,3516795391,2552037231,1608872657,3309737727,1657845296,3451270903,4048663672,149384902,3682584502,1792915224,3886684381,3054101874,519391961,3027814326,1859318097,3332770295,3205678702,1609525469,4167997183,2077073694,2578913506,3122262886,1606035925,4285518270,2077593628,3636076535,3054821986,1606035911,4184396215,1826273817,3686077407,2959063593,179857115,3765358778,634502420,3701674487,4048663658,351432409,4185430450,1859625224,2527613364,2803104104,702703057,3027158186,2127950151,2612794610,3897157222,435775636,2876823478,2077880609,2164071586,2404366395,1374366102,4184381096,1708238611,3299486178,4048008302,418538178,3865484220,1754589257,3619035641,4045515640,1291156949,3543761149,1475469901,2533318580,2701786985,1609793493,2788918761,697885517,3652325360,2803688558,1319905745,4264138979,1674820120,2162778082,4048660019,166879939,2687604411,667542345,3684786157,2802770793,249917146,3307835121,1323797546,4051773653,2318390612,1608081380,4247361710,1927784984,3652585957,3055482186,1370781895,4151957233,664188427,3602649012,3171542398,1608874193,3243808511,1223786530,3952488387,2200224840,1370768608,3849242609,1708898830,3517121730,2287055992,267615126,3799571872,650165528,3517977850,4044940645,1609377769,3798129338,1791013433,3517121730,2286400632,334719126,3126236848,1874965087,3582989055,3122657147,350380760,2888419254,1754703910,3517387769,2854871653,1203007172,4068398577,1721482260,3622324710,2954424932,1607087815,4148151486,629466963,2532385188,2382416758],5);
function Ns(n) {
  const t=function(n,t) {
    return n(t)
  };
  return function(n,t,e) {
    return n(t,e)
  }
  (Gi,n,2660613247)||(n[t(Vs,0)]= {

  })
}
const Ms=[[Vs(1),n=>Ys(false,n)],[Vs(2),()=>Ys(true)],[Vs(3),()=>Gs(Vs(4))],[Vs(5),()=>Gs(Vs(6))],[Vs(7),()=>Gs(Vs(8))],[Vs(9),()=>Gs(Vs(10))]];
function Fs() {
  const n=function(n,t) {
    return n in t
  },t=function(n,t) {
    return n(t)
  },e=function(n,t) {
    return n in t
  },r=function(n,t) {
    return n(t)
  },o=function(n,t) {
    return n in t
  },i=function(n,t) {
    return n(t)
  };
  return (n(t(Vs,11),window)||n(t(Vs,12),window)||e(r(Vs,13),window))&&o(i(Vs,14),navigator)
}
function Ds() {
  const n=function(n,t) {
    return n in t
  },t=function(n,t) {
    return n(t)
  },e=function(n,t) {
    return n===t
  },r=function(n,t,e) {
    return n(t,e)
  };
  var o;
  return !function(n) {
    return n()
  }
  (cn)||!n(t(Vs,15),document)||(e(o=document[t(Vs,15)],null)||e(o,undefined)?undefined:r(Gi,o,2256349940)().includes(t(Vs,16)))
}
function Ws() {
  const n=function(n,t) {
    return n in t
  },t=function(n,t) {
    return n(t)
  },e=function(n,t,e) {
    return n(t,e)
  };
  return n(t(Vs,17),navigator)&&n(t(Vs,18),e(Gi,navigator,2900309608))
}
function Zs(n,t= {

},e) {
  const r=function(n,t) {
    return n!==t
  },o=function(n) {
    return n()
  },i=function(n,t) {
    return n!==t
  },u=function(n,t) {
    return n!==t
  },c=function(n,t,e) {
    return n(t,e)
  };
  var s;
  return r(e,null)&&r(e,undefined)||(e=[o(Xs)]),i(s=t[n],null)&&u(s,undefined)?s:t[n]=c(Gi,navigator,3994889901)(n,e)
}
async function Gs(n,t,e) {
  const r=function(n,t,e,r) {
    return n(t,e,r)
  };
  for(const i of n)try {
    return !!(await r(Zs,i,t,e))
  } catch(o) {

  }
  return false
}
const Hs=Vs(19);
async function Us() {
  const n=function(n) {
    return n()
  },t=function(n) {
    return n()
  },e=function(n) {
    return n()
  },r=function(n,t) {
    return n(t)
  },o=function(n,t) {
    return n(t)
  },i=function(n,t) {
    return n(t)
  },u=function(n,t,e) {
    return n(t,e)
  },c=function(n,t,e) {
    return n(t,e)
  },s=function(n,t) {
    return n(t)
  },a=function(n,t) {
    return n(t)
  },l=function(n,t) {
    return n in t
  },f=function(n,t) {
    return n(t)
  };
  if(n(ln)||t(dn))return false;
  let d=false;
  if(e(Ws)) {
    const n= {
      type:r(Vs,20),audio:o(Vs,21),video:r(Vs,22),keySystemConfiguration: {
        keySystem:Hs,video:i(Vs,23)
      }

    },t=await u(Gi,u(Gi,navigator,2900309608),3516168465)(n);
    d=c(m$1,t,s(Vs,24))&&t[a(Vs,24)];
  }
  return d&&!l(f(Vs,25),navigator)||!n(cn)
}
function Bs(n=false) {
  const t=function(n,t,e) {
    return n(t,e)
  },e=function(n,t) {
    return n(t)
  },r=function(n,t) {
    return n(t)
  },o=function(n) {
    return n()
  }
  (Xs);
  return t(Gi,o,621177879)&&(t(Gi,o,621177879)[0][e(Vs,26)]=e(Vs,27)),n&&(o[e(Vs,28)]=r(Vs,29)),o
}
async function $s(n,t=false) {
  const e=function(n) {
    return n()
  },r=function(n,t) {
    return n(t)
  },o=function(n,t,e,r) {
    return n(t,e,r)
  };
  if(!e(Fs)||!e(Ds))return  {
    s:-1,v:null
  };
  if(!(await e(Us)))return  {
    s:-2,v:null
  };
  const i=r(Bs,t);
  try {
    return  {
      s:0,v:await o(Zs,Hs,n,[i])
    }

  } catch(u) {
    return  {
      s:-3,v:null
    }

  }

}
async function Ys(n=false,t) {
  const e=function(n,t,e) {
    return n(t,e)
  };
  return function(n,t) {
    return n===t
  }
  (function(n,t,e) {
    return n(t,e)
  }
  (Gi,await e($s,t,n),453955339),0)
}
function Xs() {
  return Vs(30)
}
async function Js( {
  cache:n
}) {
  const t=function(n,t) {
    return n(t)
  },e=function(n) {
    return n()
  },o=function(n,t,e) {
    return n(t,e)
  };
  if(!function(n) {
    return n()
  }
  (Fs)||!e(Ds))return ()=>( {
    s:-1,v:null
  });
  if(e(dn))return ()=>( {
    s:-3,v:null
  });
  const i=t(Ns,n);
  return o(c$1,o(r$1,250, {
    s:-2,v:null
  }),(async()=> {
    const n=await Promise.all(Ms.map((async n=> {
      const[e,r]=n;
      return [e,await t(r,i)]
    }))),e= {

    };
    for(const[t,r]of n)e[t]=r;
    return  {
      s:0,v:e
    }

  }))
}
var qs=Hi([1348463336,3803023018,4141740428,4039893696,3740108228,2696994793,2396890353,3287272953,2760289937,3639185880,3800550087,3229721822,3655845628,3956859780,3417230991,3987529206,3465536455,3286746798,3788241285,4155412936,2931392987,2279597529,2175059177,4024282809,2296682185,4202925994,3049385931,3321024229,4001931456,3270216648,2932772850,2345464011,3303269088,2766070917,4157718512],5);
function zs() {
  var n,t;
  const e=qs(0),r= {

  };
  for(const[o,i]of e)for(const e of i) {
    const i=null===(t=null===(n=Object.getOwnPropertyDescriptor(window[o],e))||undefined===n?undefined:n.get)||undefined===t?undefined:t.toString();
    undefined!==i&&(r[`${o}.${e}`]=i);
  }
  return  {
    s:0,v:r
  }

}
const Ks=4191585516,Qs=new Set([4106781067,3209949814,2612078219,2382064880,3225112721,1018714844,2899793226,2094258580,3169460974,3079760821,392195965,3461410589,3582327722,1731918890,1767246934,3419607467,1110225616,1455947556,450291099,176445009,1998723369,2961538051,3413933903,2299562828,3945560591,485550147,3336694844,3737152292,2669437517,3860417393,Ks]);
function na() {
  const n=[],t=Object.getOwnPropertyNames(window);
  for(let e=0;e<t.length;e++) {
    const r=t[e],o=A(r);
    if(Qs.has(o)&&n.push(r),o===Ks) {
      const r=t[e+1]||"";
      n.push(r);
    }

  }
  return  {
    s:0,v:n
  }

}
function ta(n) {
  return ur(((n,t)=> {
    const e= {

    },r=t.document.createElement("div");
    t.document.body.appendChild(r);
    const o= {
      AccentColor:"ac",AccentColorText:"act",ActiveText:"at",ActiveBorder:"ab",ActiveCaption:"aca",AppWorkspace:"aw",Background:"b",ButtonHighlight:"bh",ButtonShadow:"bs",ButtonBorder:"bb",ButtonFace:"bf",ButtonText:"bt",FieldText:"ft",GrayText:"gt",Highlight:"h",HighlightText:"ht",InactiveBorder:"ib",InactiveCaption:"ic",InactiveCaptionText:"ict",InfoBackground:"ib",InfoText:"it",LinkText:"lt",Mark:"m",Menu:"me",Scrollbar:"s",ThreeDDarkShadow:"tdds",ThreeDFace:"tdf",ThreeDHighlight:"tdh",ThreeDLightShadow:"tdls",ThreeDShadow:"tds",VisitedText:"vt",Window:"w",WindowFrame:"wf",WindowText:"wt",Selecteditem:"si",Selecteditemtext:"sit"
    };
    for(const u of Object.keys(o)) {
      e[o[u]]=(i=u,r.style.color=i,t.getComputedStyle(r).color);
    }
    var i;
    return t.document.body.removeChild(r), {
      s:0,v:e
    }

  }),n.sis)
}
function ea(n) {
  return ur(((n,t)=> {
    const {
      webdriver:e
    }
    =t.navigator;
    return null===e? {
      s:-1,v:null
    }
    :undefined===e? {
      s:-2,v:null
    }
    : {
      s:0,v:e
    }

  }),n.sis)
}
function ra() {
  return function(n,t) {
    const e=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(n),t);
    if(!e||!e.get)return  {
      s:-1,v:null
    };
    const r=window.Function,o=window.Object;
    let i=false;
    try {
      i=delete window.Function&&delete window.Object;
    } catch(c) {
      i=false;
    }
    if(!i)return u(), {
      s:-2,v:null
    };
    try {
      return e.get.toString(), {
        s:0,v:false
      }

    } catch(s) {
      return  {
        s:0,v:true
      }

    } finally {
      u();
    }
    function u() {
      try {
        window.Function=r,window.Object=o;
      } catch(c) {

      }

    }

  }
  (navigator,"hardwareConcurrency")
}
function oa(n,t) {
  const e= {

  },r=["x","y","left","right","bottom","height","top","width"],o=n.getBoundingClientRect();
  for(const u of r)u in o&&(e[u]=o[u]);
  const i=t.getComputedStyle(n,null).getPropertyValue("font-family");
  return e.font=i,e
}
function ia(n) {
  let t="";
  for(let e=128512;e<=128591;e++) {
    const n=String.fromCodePoint(e);
    t+=n;
  }
  return ur(((n,e)=> {
    const r=e.document.createElement("span");
    r.style.whiteSpace="nowrap",r.innerText=t,e.document.body.append(r);
    const o=oa(r,e);
    return e.document.body.removeChild(r), {
      s:0,v:o
    }

  }),n.sis)
}
function ua(n) {
  const t=document.createDocumentFragment(),e=u(t,"mrow"),r=u(e,"munderover"),o=u(r,"mmultiscripts");
  u(o,"mo","∏");
  const i=[["𝔈","υ","τ","ρ","σ"],["𝔇","π","ο","ν","ξ"],["𝔄","δ","γ","α","β"],["𝔅","θ","η","ε","ζ"],["𝔉","ω","ψ","ϕ","χ"],["ℭ","μ","λ","ι","κ"]];
  function u(n,t,e="") {
    const r=document.createElement(t);
    return r.textContent=e,n.append(r),r
  }
  function c(n,t,e,r,o) {
    const i=document.createElement("mmultiscripts");
    return u(i,"mi",n),u(i,"mi",t),u(i,"mi",e),u(i,"mprescripts"),u(i,"mi",r),u(i,"mi",o),i
  }
  for(const s of i) {
    const n=c(...s);
    o.append(n);
  }
  return ur(((n,e)=> {
    const r=document.createElement("math");
    r.setAttribute("style","white-space: nowrap"),r.append(t),e.document.body.append(r);
    const o=oa(r,e);
    return e.document.body.removeChild(r), {
      s:0,v:o
    }

  }),n.sis)
}
var ca=Hi([1024705730,641842159,2578743392,3876471597,2070139803],6);
function sa() {
  const n=function(n,t) {
    return n(t)
  },t=function(n,t,e) {
    return n(t,e)
  }
  (Gi,navigator,2698072953);
  return t? {
    s:0,v:n(aa,t)
  }
  : {
    s:-1,v:null
  }

}
function aa(n) {
  const t=function(n,t,e) {
    return n(t,e)
  },e=function(n,t) {
    return n(t)
  },r=function(n,t,e) {
    return n(t,e)
  },o=function(n,t) {
    return n<t
  },i=function(n,t,e) {
    return n(t,e)
  },u=t(Gi,Object,1110892003)(n,e(ca,0));
  if(u&&r(Gi,u,2813370411))return true;
  for(let c=0;o(c,n.length);c++) {
    const e=r(Gi,Object,1110892003)(n,c);
    if(e&&(i(Gi,e,2813370411)||t(Gi,e,1651707638)))return true
  }
  return false
}
var Sa=Hi([2849665133,3102332852,3030028940,2360597915,3649086422,4118989755,2159729800,2492790230,3150617845,3422263962,3398214861,3000338617,2163578059,3720000219,2782764965,3422263962,3600523980,2895432685,2292567243,3617170646,3986333093,2578762955,2596645530,2227996313,2259142812,3700204490,3100285842,3422263963,3903489002,2496302258,2360989318,3615531995,4120169401,2192956830,3971720145,3000875412,2277047195,3431641814,4124477118,2273483461,3481713107,2781523129,3321219718,3599275162,4157376185,2293418634,3418993356,3067464120,3120021895,4221285085,3000403896,2260651146,2496373974,3051664885,2293418634,3735466700,2345307313,3287931573,3669330832,3151268020,2192890251,2525727716,3051664893,3382957959,3448764377,3201075897,3045840518,3837111258,2966063285,2276644252,3402212556,3201145010,3048463771,2462561764,2816128395,2359614875,3837109206,4221223093,2209732555,2594026717,2782776315,2862995355,2592912343,2781727739,3422263941,3683431633,3202123702,2359548301,3617301981,4120169381,2595804298,2496377821,3100936949,2257903002,3683432918,3117908131,2331350219,3431510730,2748951986,2294283144,3565992406,2564589462,2612190863,3687578522,2999682747,2277103530,3516773597,3220146104,2625885836,3601643978,2325387955],3);
async function Ia( {
  te:n
}) {
  const t=function(n) {
    return n()
  },e=function(n,t) {
    return n===t
  },o=function(n,t,e) {
    return n(t,e)
  },i=t(Ot),u=await o(c$1,o(r$1,300,-4),ka.bind(null,i,n));
  return ()=> {
    const n=t(u);
    return e(n,0)||e(n,-4)? {
      s:n,v: {
        u:i,e:[],s:[]
      }

    }
    : {
      s:n,v:null
    }

  }

}
async function ka(n,t) {
  const e=function(n,t,e) {
    return n(t,e)
  },r=function(n,t) {
    return n!==t
  },o=function(n,t,e) {
    return n(t,e)
  },i=function(n,t,e) {
    return n(t,e)
  },u=e(Aa,n,t), {
    s:c,v:s
  }
  =e(Pa,u,true);
  if(r(c,0))return c;
  const a=o(ja,s,t);
  try {
    const {
      s:n,v:t
    }
    =await o(Gi,a,142982734)();
    return r(n,0)?n:(await o(Gi,s,76151562)(t),0)
  } finally {
    i(Gi,a,107910612)();
  }

}
function Aa(n,t) {
  const e=function(n,t) {
    return n(t)
  },r=function(n,t) {
    return n(t)
  },o=function(n,t) {
    return n(t)
  },i=function(n,t) {
    return n(t)
  }
  (Sa,0);
  i[e(Sa,1)]=r(Ca,t),i[o(Sa,2)]=n;
  const u= {

  };
  return u[r(Sa,3)]=[i],u
}
function Ca(n) {
  const t=function(n,t) {
    return n+t
  },e=function(n,t) {
    return n(t)
  },r=function(n,t,e) {
    return n(t,e)
  };
  return t(t(e(Sa,4),r(Pr,n,e(Sa,5))),"")
}
const La=Sa(6);
function Pa(n,t) {
  const e=function(n,t) {
    return n(t)
  },r=function(n,t) {
    return n(t)
  },o=function(n,t) {
    return n instanceof t
  },i=function(n,t) {
    return n===t
  },u=t?window[function(n,t) {
    return n(t)
  }
  (Sa,7)]||window[e(Sa,8)]:window[r(Sa,7)];
  if(!u)return  {
    s:-3,v:null
  };
  let c;
  try {
    c=new u(n);
  } catch(s) {
    if(o(s,Error)) {
      if(i(s.name,La))return  {
        s:-6,v:null
      };
      if(e(Ta,s))return  {
        s:-9,v:null
      }

    }
    throw s
  }
  return  {
    s:0,v:c
  }

}
function xa(n,t) {
  const e=function(n,t) {
    return n===t
  },r=function(n,t,e) {
    return n(t,e)
  },o=function(n,t) {
    return n===t
  },i=function(n,t) {
    return n instanceof t
  };
  var u;
  try {
    return e(u=r(Gi,n,34843658),null)||o(u,undefined)||u.call(n,t||Math.random().toString()),0
  } catch(c) {
    if(i(c,Error)&&o(c.name,La))return -7;
    throw c
  }

}
function Ta(n) {
  const t=function(n,t) {
    return n(t)
  },e=function(n,t,e) {
    return n(t,e)
  };
  return function(n,t) {
    return n===t
  }
  (n.name,t(Sa,9))&&e(Gi,new RegExp(t(Sa,10)),3632233996)(e(Gi,n,3065852031))
}
function Oa(n) {
  const t=function(n,t,e) {
    return n(t,e)
  };
  try {
    t(Gi,n,318865860)();
  } catch(e) {

  }

}
async function _a(n,t) {
  const e=function(n,t,e) {
    return n(t,e)
  },r=function(n,t) {
    return n instanceof t
  },o=function(n,t,e) {
    return n(t,e)
  },i=function(n,t) {
    return n(t)
  },u=function(n,t) {
    return n===t
  };
  let c;
  try {
    c=e(Gi,n,882066760)(t);
  } catch(a) {
    if(!r(a,Error)||!o(Gi,new RegExp(i(Sa,11),"i"),3632233996)(o(Gi,a,3065852031)))throw a;
    c=new Promise(((r,o)=> {
      e(Gi,n,882066760)(r,o,t);
    }));
  }
  const s=await c;
  return u(s,undefined)? {
    s:-8,v:null
  }
  : {
    s:0,v:s
  }

}
function ja(n,t) {
  const r=function(n,t) {
    return n(t)
  },o=function(n,t) {
    return n===t
  },i=function(n,t,e) {
    return n(t,e)
  },u=function(n,t,e) {
    return n(t,e)
  },c=function(n,t) {
    return n===t
  },s=function(n,t) {
    return n(t)
  },a=function(n,t) {
    return n!==t
  },l=function(n,t) {
    return n in t
  },f=function(n,t) {
    return n(t)
  },d=function(n,t) {
    return n in t
  },m=function(n,t,e) {
    return n(t,e)
  },v=function(n) {
    return n()
  },h=function(n,t) {
    return n===t
  },p=function(n,t,e) {
    return n(t,e)
  },g=function(n,t) {
    return n(t)
  },w=function(n,t,e,r) {
    return n(t,e,r)
  },y=function(n,t) {
    return n(t)
  },b=function(n,t) {
    return n!==t
  },E=function(n,t) {
    return n!==t
  },R=function(n,t,e) {
    return n(t,e)
  },S=function(n,t) {
    return n(t)
  },I=function(n,t,e) {
    return n(t,e)
  };
  function k(n,t) {
    return r(A,n)&&o(i(Gi,n,3920415024),400)&&u(Gi,n,4101391790).includes(t)
  }
  function A(n) {
    return c(typeof n,s(Sa,12))&&a(n,null)&&l(f(Sa,13),n)&&d(s(Sa,14),n)
  }
  let C=null,L=false;
  async function P() {
    const t=r(xa,n);
    if(b(t,0))return  {
      s:t,v:null
    };
    const {
      s:e,v:o
    }
    =await r(_a,n);
    return E(e,0)? {
      s:e,v:null
    }
    : {
      s:0,v:o
    }

  }
  t&&function(n,t,e) {
    return n(t,e)
  }
  (Gi,n,123626528)(S(Sa,15),(e=> {
    m(k,e,t)&&(C?(v(C),C=null,r(Oa,n)):L=true);
  }));
  const x= {
    [y(Sa,17)]:()=>Oa(n),[r(Sa,18)]:async()=> {
      const t=await v(P);
      return b(R(Gi,t,453955339),0)&&r(Oa,n),t
    }

  };
  return t?I(Gi,Object,1914874273)(x, {
    [f(Sa,19)]:function() {
      h(p(Gi,n,4184312542),g(Sa,16))||(L?y(Oa,n):C=w(e$1,Oa,5e3,n));
    }

  }):x
}
var Va=Ui([[1158230590,352328197,922751784,234887733,1045777409,235013451,1077693209,86185296,321396490,462366,488115742,1213075980,4402479,184943903,188551425,1398147351,268897603,491523647,306988571,1261376568,269223502,570890009,34866732,470426899,403966778,253756433,304419089,491347009,508233756,403654977,421396492,1329803025,184551506,1057755406,136120322,118163754,373378420,453843998,1159464460,319444544,855642889,402851378,1191248155,151015493,219352090,67375366,17696018,1263095066,420348421,21908811,168961297,171640095,14413]],[function() {
  const n=(new Image).style;
  return qc([Zi(t=n,2487676862),Zi(t,41374024)],[5,23,47,9,35,9,44,7,37,41,19,25,32,26,30,32,8,31,12,15,40,18,15,20,9,4,2,13,21,17,18,34,40,2,48]);
  var t;
}],[2]);
async function Na() {
  const n=function(n,t) {
    return n(t)
  },t=function(n,t) {
    return n(t)
  },e=function(n,t,e) {
    return n(t,e)
  },r=function(n,t) {
    return n<t
  },o=function(n,t,e) {
    return n(t,e)
  },i=function(n,t) {
    return n-t
  };
  if(function(n) {
    return n()
  }
  (Zr))return [-1,NaN];
  const u=new Uint8Array([0]),c=n(Va,0),s=await navigator[t(Va,1)](t(Va,2),c),a=await s[t(Va,3)]();
  let l=await e(Fa,a,u);
  const f=r(l,10);
  if(f) {
    const n=i(i(o(Mt,10,2500),l),1);
    for(let t=0;r(t,n);t++)o(Da,a,u);
    l=await o(Fa,a,u);
  }
  return [f?1:0,l]
}
function Ma() {
  const n=function(n,t) {
    return n(t)
  };
  return function(n,t) {
    return n==t
  }
  (typeof navigator[function(n,t) {
    return n(t)
  }
  (Va,1)],n(Va,4))
}
async function Fa(n,t) {
  const e=function(n,t) {
    return n(t)
  },r=function(n,t) {
    return n(t)
  },o=n[e(Va,5)]();
  return await o[r(Va,6)](e(Va,7),t),r(Number,o[r(Va,8)])
}
function Da(n,t) {
  const e=function(n,t) {
    return n(t)
  };
  (function(n,t) {
    n(t);
  })(u$1,n[function(n,t) {
    return n(t)
  }
  (Va,5)]()[e(Va,6)](e(Va,7),t));
}
async function Wa() {
  const n=function(n) {
    return n()
  },t=function(n,t) {
    return n===t
  },e=function(n,t,e) {
    return n(t,e)
  },o=function(n,t,e) {
    return n(t,e)
  };
  return function(n) {
    return n()
  }
  (Ma)?e(c$1,o(r$1,500, {
    s:-2,v:null
  }),(async()=> {
    const e=await n(Na);
    return t(e[0],-1)? {
      s:-3,v:null
    }
    : {
      s:0,v:e
    }

  })):()=>( {
    s:-1,v:null
  })
}
var Za=Ui([[89472536,67911963,202988290,386077465,1866537770,1224742518,488243476,419627011,184819487,437598027,340225859,172033032,437716482,471155211,1095068177,1092107040,419499526,423762697,100665116,490210839,1194790674,673115,85280006,1510540548,2756129,939992591,1246643516,1108281098,52370449,641031181,822350097,201595136,1447512348,1107565334,605101077,923815180,201460231,369557787,421401919,370608902,386208007,1158809130,67652933,420829977,1325996060,705104933,100734005,18485518,1079117841,520555597,117716299,441132557,117836552,454886414,1079380231,235285315,167851373,438045445,354104902,218503945,1450723136,1261309460,853525,339100932,1443038736,103498560,3566862,1175192861,252709131,16777237,1984516105,1829509143,185926151,436356353,185073670,1779174662,991969605,50610456,1275666182,419565839,202771726,1124408096,135546735,168313092,253563142,135813653,822480166,72178038,222758157,52298251,454823449,56244746,1427123716,67914571,353589766,51775754,625419022,219166498,1258491144,521093188,151601409,456523793,678234648,169481234,118557701,391005526,241568771,422784012,438716682,1309089280,806492,990010373,638390299,134885451,1481180934,17176407,655231834,2049314574,84410418,220531716,167778574,105923661,106502459,185600556,170279180,1046087172,151977997,35061763,1263338788,84282176,52366156,1544356616,420816433,50605842,1229146882,1511529224,186319630,4664589,35268139,100748290,1379942427,1174536207,322636309,208471067,373756952,7684,1481509910,69665358,440083533,1174866696,403505177,1129127711,956961098,571674714,285606663,67257606,151460637,725827670,862785030,168106503,289803037,203297033,1197361671,1327110967,169477163,84548876,1840656,1325404447,537919532,1158350651,118114894,454640143,269026054,471146315,372321280,1196229131,421140297,17891399,256321038,167983925,135074069,1379942427,1174536207,523897886,187303186,16788313,1007685120,1447054106,1193610767,121055758,235738112,118572573,1091181577,956569372,1632457991,1191843846,387122178,420174362,755830297,929124171,222888474,50727960,118447621,1229986830,202905462,51517293,1159661069,219156518,1296957445,772541034,285869946,471598093,437591628,102564608,341211207,72035854,453396244,286989059,252909895,100927823,207059041,440798984,347163,218169348,389222492,3416153,1128989210,404424777,102242906,1193875213,338048784,17827353,1077939469,33558354,973080134,923734551,118361931,390678349,407312666,756351505,606227719,1078676741,1275397643,369236248,102176796,152328767,505090338,1195966464,68884054,402849858,604117287,387586598,184555596,52366851,290079565,39467274,337061379,1044450054,822546697,1309087752,202009165,100891182,1259996933,521093188,51986689,390009692,187041819,1296385283,1528366088,1539,1194856717,20458516,188762957,374080774,100861208,604249353,906778884,134487574,1444022019,51205721,688201243,275581722,638910490,553654793,438246915,1191185666,68310648,100862061,1157897218,203233559,1296957442,1829962602,35198010,17122832,1079118092,101515597,370942795,117714965,54019863,889585674,1079385113,386672195,236790637,420024595,406539288,689707789,956765442,1198474037,1091441944,102564636,119409668,205263381,108670990,151781382,1313753605,457245696,855645709,391058950,235019008,471534109,474699863,756351517,540018203,272974679,51463965,386470914,67506497,1297423660,1224806753,520230941,878058775,289625664,571801658,289411104,88480259,1641997,388317194,1477786881,50998065,521022728,202398474,33949981,1095115776,1582986863,239750725,289150477,469830174,14416]],[Xc],[2]);
function Ga() {
  return Za(0)
}
async function Ha() {
  const n=function(n,t) {
    return n(t)
  },t=function(n) {
    return n()
  }
  (Ga),e=await Promise.all(t.map(Ua)),r= {

  };
  return t.forEach(((t,o)=> {
    const i=n(A,t).toString(16);
    r[i]=e[o];
  })),r
}
function Ua(n) {
  const t=function(n,t) {
    return n+t
  },e=function(n,t) {
    return n+t
  },r=function(n,t) {
    return n(t)
  },o=function(n,t) {
    return n(t)
  },i=function(n,t) {
    return n(t)
  },u=function(n,t) {
    return n!==t
  },c=function(n,t) {
    return n(t)
  };
  return new Promise((s=> {
    const a=t(e(r(Za,1),n),o(Za,2));
    try {
      const[,n,t]=i(ts,a);
      if(u(n,0))return void c(s,n);
      t[r(Za,3)]((()=>s(0)),(()=>s(-1)));
    } catch(l) {
      c(s,-2);
    }

  }))
}
async function Ba() {
  const n=function(n) {
    return n()
  },t=function(n) {
    return n()
  },e=function(n,t,e) {
    return n(t,e)
  };
  return await e(c$1,e(r$1,500, {
    s:-2,v:null
  }),(async()=>n(Ga)?n(Qc)? {
    s:0,v:await t(Ha)
  }
  : {
    s:-1,v:null
  }
  : {
    s:-3,v:null
  }))
}
function $a() {
  return  {
    s:0,v:"serviceWorker"in Navigator.prototype
  }

}
function Ya() {
  return  {
    s:0,v:Boolean(window.isSecureContext)
  }

}
var Xa=Ui([[37637135,1447917654,1074862848,221320987,185417728,1279479069,287641348,1585126709,277761,1427768864,1124076042,2035529,455018507,23675461,120393521,1444036433,1141263183,303105822,319645969,1275726848,36457547,388709920,101924677,1077349638,303367169,135938595,1112349448,153357637,121505586,1480802129,1141246529,839976462,805901,167780891,1160643090,438979704,100941378,1381385537,33619995,505875729,119147817,153229835,20323964,453520970,1308901389,134224668,324158218,140184588,136785483,455937847,1145648204,1494293834,320544012,1971969,319380746,359333889,104340027,1544500554,1141003010,1209157132,67441480,1511480093,104666369,1328827942,1075133262,152198427,149830,1477446935,1427587336,1194921745,1547195181,353853786,470698257,1510890510,1159481353,521949703,526588437,192026238,239739657,442307401,256466199,1481069662,1091916807,191889498,175708721,1578723163,1142444571,403526171,474109016,436863826,1513165895,1227047982,1410678607,1310151680,1326799388,156435474,491723532,153230682,91688828,286089482,471550231,1511481182,945321480,218765652,526583891,1131496748,1561928206,1498942025,241044293,373446478,340072261,510001485,1114971518,789340426,1464415314,121639178,474109261,339869763,510074189,1131496749,1561862926,1482164809,241043525,373445966,1430675269,981021962,289151081,206126103,1314788169,308153156,524440649,373424195,493296973,1131496750,1562058766,290982473,974735686,324366422,140184588,1466392143,1131765368,286482698,1325800471,394831,169369099,54987290,657872206,120986675,1565553235,1209411907,253564417,1280836866,470686025,237312859,522912050,201357853,1141003025,1511147020,386751269,1310132765,292225025,270091815,865110,1465648906,67108874,184644125,1192692237,309397319,1601199207,404362525,1330912518,34669650,1212173143,1113211225,1316896855,104596079,39597315,1195772422,1364869959,1430658377,184767552,1513967123,321592373,1510961754,218960155,420305921,1258684700,1108743697,506609673,1547125293,1478042203,1494042381,1327128087,1225806877,387334407,191907615,108599857,101923614,291246082,1381515331,1447304521,1514364485,1348950091,1165318776,1145925391,391666511,1465401923,1413749065,1497586757,1348951883,1081432952,1129147407,374889295,1364738371,1346640201,1531141957,1549950795,1378683704,100689750,151848977,420305920,474366537,1073758992,140973855,1579227002,219771980,1499072079,391076631,390618884,475275347,337911369,489691709,454256461,1207961623,6036480,1329684253,1510738463,1010648577,791688480,1565554302,1431968600,236390922,1477205770,1258697756,359674705,2890289,1326676557,1393764638,1225000704,625476693,167839243,1328283662,75056996,121710658,1276451417,319888927,386887006,1176443398,661342039,372705078,1543910474,1465139282,357826574,487414111,186456605,1529830456,1282104626,101128728,1142492674,122947073,370019595,559220289,661996366,322568504,437138263,22894923,1427576601,1725955,1907229,523115079,388700960,67910512,1432095759,139985219,487414091,469762058,443565827,293290614,16209,1326529286,822482699,151870732,1275724032,238767179,456461092,1480802125,1426131009,441995264,152915527,167780869,1165052930,389480762,1447896833,1074862848,69211931,387799325,1279479052,70125060,388696895,1447917639,1075187217,236586839,1229602839,993994827,322112307,658250785,285621072,1968588097,874523178,657942583,657137952,1265183017,571878774,656737658,56118071,336660254,1195642624,436608286,523123202,388700960,390297089,1427442705,202711306,386744597,1276396363,556535562,388825661,1448835153,1393888269,1124073738,105513240,437127707,153234434,489367856,1480796758,1427181121,85596973,268918562,386802457,1161763592,3820664,286604102,1443954741,39214669,285820951,135933196,1161366273,171461752,1480796497,1965894465,824910122,540507936,723659301,1265187369,654911862,302460769,1377901318,1125192974,725421897,1008740640,1164397610,1059916595,286337602,1326791431,1297487624,286088775,458048331,388629257,293290614,16209,1140930566,69667613,507776785,504765259,1165052930,389285664,419442256,56118035,251731212,1464995601,223167252,321198856,595280502,758325110,1915829052,606223904,642384199,825638694,1158167604,455756920,1480802137,1899308097,540090416,1195642657,167840283,102439938,1585126695,390275448,1393888271,337122105,1045565184,1113342297,1266171991,1584021604,1447888658,1159005711,1532363296,282183,1112349960,138353989,34999078,121856001,1141245463,1294536525,151473735,439229702,254283539,104270649,1447917648,1443954709,106323533,271276288,662811,523123219,388700960,390297089,1427442705,203108618,17189896,17563948,1161366275,511382904,402929730,1146508097,85659905,407527168,185421125,891619072,389873713,117443153,56118032,822089500,151870732,1275724032,37243979,472919072,454237511,223746326,319881805,135938563,185336072,157893189,1585125691,353582593,56118036,1125129226,1707849,402849818,37633794,386537254,1447917655,1912866830,67113755,273285447,504234503,1160710935,490359928,19080019,1393626885,339090747,386747139,139281227,337772558,1349864508,419639120,223747338,117510221,1192904707,251809093,506998551,1585122618,556866817,1812203566,1125193216,540675913,1112353576,87956805,321592373,1447917658,1076889111,857805595,1195642665,17367296,359219781,388767537,270544464,1140857090,119159581,3477258],[386942744,1229409564,135333655,220795160,755369005,1162041120,503777537,1079123715,101517389,52050726,1427192580,236473163,17109769,173424715,371009796,1292251441,203046987,50927385,503982872,1446053403,2376539,169555715,117837325,355405073,438900482,405154853,1145049870,34409291,436733206,2017924890,638784598,973210372,286198279,134625543,1778647041,1009795397,268569364,290080074,202965528,507332635,134354452,152965423,402923329,102564125,236739842,706150459,290790203,240978695,52177998,454823436,1197226506,251672392,419431940,285429263,286416394,290006535,454303788,1090915598,354048009,1091132175,356080479,1362842883,236919825,1209617177,1075316761,1093555476,337803338,1427785501,1461339656,1327303942,2047102737,571952141,1411208983,1326531854,1276973337,957501722,745215771,457971551,407048258,1413810758,189744919,1549274479,1208835629,122683732,290717969,1259620628,638538288,504780064,289608031,404029529,1326585167,1276018207,1460741645,67916804,1511283736,5195038,273234948,18622334,507904847,352344385,1426083608,1329023043,947075610,202117450,224136543,1162101260,1076894017,225976393,122166853,524816962,356848732,759700802,1934427230,839535692,39204446,173872912,827003996,778964035,457907295,1396720145,1175783745,475925317,240979582,341646696,1346527045,877014553,34144849,994774908,138743678,457380169,375002446,172294213,223881039,1179478043,1108677450,1146689345,924407616,357832018,155268902,1497649743,1094734404,220025925,438702086,70325591,1643545,408686104,873550429,472322827,1550150419,16787279,34278407,1180648471,637797448,705626696,68491267,202001233,153046535,1929861143,640029993,1109330433,340264718,221009951,287179034,392108605,33756966,84029457,1074532368,341187916,1850366843,185875050,105454599,253041247,1598032221,1531017813,1582329169,520750428,38280011,172363532,1397193033,1599825007,201611598,1293566492,152902925,1513770251,1228544271,386943257,1528448786,1477775372,271666946,1530556186,1142562583,337331719,1090600968,2015169296,974674202,89939485,4923146,505091400,2018055445,1735348549,1363894105,1447319620,1480607296,1381915715,1364935032,1364940655,1564958533,1482178904,1447053120,1951357028,1430470776,1598381646,1532780110,1111776323,1113088073,1112109901,1346787403,1409356039,504713500,1259350291,386693676,273026379,1577274897,121837076,1479285852,473648920,390531163,55525907,105650965,460533334,104543053,118166278,51401991,102436100,894245895,1766327564,1560547859,790446857,822095617,1632649257,544018770,218371856,1594628871,1241852697,390673753,318898225,1543849261,420228884,1090781211,558652764,655163434,1325931325,508117330,525344259,520690773,85014549,84018010,1126112264,878009691,135922955,1259218440,425033074,491261958,134813266,220011032,1211127597,1534153233,487532364,270076938,306978074,439238914,980298315,677136966,218171141,16778500,1951154752,1996624386,202705923,437853723,336330837,756226304,606995002,374278681,189012548,386466882,387778316,474766640,72698209,520751643,118564625,824054024,788928801,1158290237,18434638,85723410,1581910529,50410823,206135566,119147077,270153991,1313754636,101132047,1297688929,135073796,355993372,437918484,1450723095,103155988,169542172,1465403663,353242630,103158868,1500917265,1026695245,404360509,973741573,822219547,390290262,1009987360,909389373,623721020,1682123578,67903563,824389676,1078217532,436798749,1197361674,354289187,521285926,236526109,173431126,353177886,771897901,352983332,1242711104,706153743,387711750,1431205399,84157967,1226512898,391600150,404031771,218106372,463655,1162482194,67700042,201393710,20649781,472001799,1293750808,118966599,286787601,506267706,376860481,469959197,169290252,1293748502,738480196,1866662918,1027487047,607402026,691414576,220997944,2019637031,926361687,68033578,473498121,1192693518,790779512,892871434,1229409572,603983891,68944909,755120940,1263341619,470555456,424820800,34144769,341211207,50603539,236599298,287706393,391663133,319831107,1297053222,201657107,487396891,1245924636,438372881,1467564803,206261002,18488836,625886550,807019577,638652732,758393632,792740939,808860735,1982210107,705844568,1162154527,606742093,757868074,1783451184,808257051,53943568,1313479195,206441271,387124483,337319170,1011697446,1196966233,1162304324,1298094684,1632580729,51255864,1380653101,152833856,1581915406,402663239,120202771,407720773,285678367,1076433227,252062531,456402476,17498899,67241733,1245924639,53545988,39931221,438965010,454105369,201932032,205132824,376860481,469959197,17640204,184618269,990256173,1628639760,88411209,403573006,155930199,739118874,694227212,117787993,805699599,168304137,370358301,1130059303,922943536,118365952,1259412253,69162560,755641148,136131120,1145772055,504699968,521797641,303512068,424111939,1196236296,352784457,1314410014,1091380740,168261231,520359188,353973005,222041630,1450723078,909312026,169674243,5654345,67961882,1261175836,439837007,488644127,503778831,439157540,637539342,625171286,437131532,1447512327,17498374,1682118685,842400075,1075120659,50678596,371142940,1229982465,874984310,705102862,1225657094,740710232,1296969773,555096682,102565685,1246054939,221512470,540872219,1431860777,402861320,424494405,285213966,137697306,102578176,152771889,3489800]],[function() {
  return function(n,t) {
    const e=Gi(n,704082790);
    return qc([Zi(t,3017323393),Jc(n,859837811,"QjslADtOBipACA")||Jc(e,72906005,"Tjo/DSpIETFCCQ")],[20,1,24,23,23,21,14,8,11,8,6,13,1,1,12,4,9,10,6,2,1,2,0,1,2,1,1])
  }
  (navigator,document.createElement("frameset"))
},Xc],[1,1]);
function Ja() {
  const n=function(n,t) {
    return n(t)
  };
  return n(Xa,0)&&navigator[n(Xa,0)]
}
function qa() {
  const n=function(n,t) {
    return n(t)
  },t=function(n,t) {
    return n(t)
  };
  return document[n(Xa,1)](n(Xa,2))[n(Xa,3)](t(Xa,4))
}
async function za(n,t) {
  const e=function(n,t) {
    return n===t
  },r=function(n,t) {
    return n===t
  },o=function(n,t) {
    return n(t)
  },i=function(n,t,e,r) {
    return n(t,e,r)
  },u=function(n,t) {
    return n(t)
  },c=Array.from(e(n,null)||r(n,undefined)?undefined:n[o(Xa,5)].values()),[s,a]=await Promise.all([i(Qa,n,c,t),u(tl,n)]);
  return [s,a,c]
}
const Ka=16;
async function Qa(n,t,e) {
  const r=function(n,t) {
    return n(t)
  },o=function(n,t) {
    return n(t)
  },i=function(n,t) {
    return n*t
  },u=function(n,t) {
    return n(t)
  },c=function(n,t) {
    return n(t)
  },s=function(n,t) {
    return n(t)
  },a=function(n,t) {
    return n(t)
  },l=function(n,t) {
    return n(t)
  },f=function(n,t) {
    return n(t)
  },d=function(n,t) {
    return n/t
  },m=function(n,t) {
    return n+t
  },v=function(n,t) {
    return n(t)
  },h=function(n,t) {
    return n(t)
  },p=function(n,t) {
    return n(t)
  },g=function(n,t) {
    return n(t)
  },w=function(n,t) {
    return n(t)
  },y=function(n,t) {
    return n(t)
  },b=function(n,t) {
    return n(t)
  },E=function(n,t) {
    return n|t
  },S=function(n,t) {
    return n(t)
  },I=function(n,t) {
    return n(t)
  },k=function(n,t) {
    return n(t)
  },A=function(n,t) {
    return n(t)
  },C=function(n,t) {
    return n(t)
  },L=function(n,t) {
    return n(t)
  },P=function(n,t) {
    return n(t)
  },x=function(n,t) {
    return n(t)
  },T=function(n,t) {
    return n(t)
  },O=function(n,t) {
    return n*t
  },_=function(n,t) {
    return n(t)
  },j=function(n,t) {
    return n(t)
  },V=function(n,t) {
    return n(t)
  },N=function(n,t) {
    return n(t)
  },M=function(n,t) {
    return n(t)
  },F=function(n,t) {
    return n(t)
  },D=function(n,t) {
    return n<t
  },W=function(n,t) {
    return n(t)
  },Z=function(n,t) {
    return n(t)
  },G=function(n,t) {
    return n(t)
  },H=function(n,t) {
    return n(t)
  },U=function(n,t) {
    return n(t)
  },B=function(n,t) {
    return n(t)
  },$=function(n,t) {
    return n(t)
  },Y=function(n,t) {
    return n(t)
  },X=function(n,t) {
    return n(t)
  },J=function(n,t) {
    return n(t)
  },q=function(n,t) {
    return n===t
  },z=function(n,t) {
    return n(t)
  },K=function(n,t) {
    return n(t)
  },Q=function(n,t) {
    return n(t)
  },nn=function(n,t) {
    return n(t)
  },tn=function(n,t) {
    return n(t)
  },en=function(n,t) {
    return n(t)
  },rn=function(n,t) {
    return n+t
  },on=function(n,t) {
    return n+t
  },un=function(n,t) {
    return n(t)
  },cn=function(n,t) {
    return n*t
  },sn=function(n,t) {
    return n+t
  },an=function(n,t) {
    return n+t
  },ln=function(n,t) {
    return n(t)
  },fn=function(n,t) {
    return n(t)
  },dn=function(n,t) {
    return n<t
  },mn=function(n,t) {
    return n(t)
  },vn=function(n,t) {
    return n(t)
  },hn=function(n,t) {
    return n*t
  },pn=function(n,t) {
    return n*t
  },gn=function(n,t) {
    return n+t
  },wn=function(n,t) {
    return n+t
  },yn=function(n,t) {
    return n+t
  },bn=await n[f(Xa,6)]( {
    requiredFeatures:t
  }),En=Math.PI,Rn=[[0,1,0,d(En,7)],[1,0,0,d(En,8)],[0,1,1,d(En,4)],[1,2,1,d(En,8)]],Sn=Rn.length,In=new Uint8Array(i(Sn,m(m(16,Ka),8))),kn=navigator[v(Xa,0)][o(Xa,7)]();
  e[a(Xa,8)]( {
    device:bn,format:kn
  });
  const An=bn[h(Xa,9)]( {
    label:p(Xa,10),code:g(Xa,11)
  }),Cn=bn[w(Xa,12)]( {
    label:s(Xa,13),layout:y(Xa,14),vertex: {
      module:An
    },fragment: {
      module:An,targets:[ {
        format:kn
      }]
    },primitive:b(Xa,15)
  }),Ln=[[255,0,0,255],[0,255,0,255],[0,0,255,255]],Pn=new Uint8Array(v(Array,i(7,9)).fill(undefined).map(((n,t)=>Ln[t%3])).flat()),xn=bn[u(Xa,16)]( {
    label:s(Xa,17),size:[7,9],format:w(Xa,18),usage:E(window[S(Xa,19)][I(Xa,20)],window[c(Xa,19)][o(Xa,21)])
  });
  bn[k(Xa,22)][A(Xa,23)]( {
    texture:xn
  },Pn, {
    bytesPerRow:i(7,4)
  }, {
    width:7,height:9
  });
  const Tn=bn[C(Xa,24)](L(Xa,25)),On=bn[P(Xa,26)]( {
    layout:Cn[s(Xa,27)](0),entries:[ {
      binding:0,resource:Tn
    }, {
      binding:1,resource:xn[c(Xa,28)]()
    }]
  }),_n=Rn.map((n=> {
    const t=bn[r(Xa,29)]( {
      label:o(Xa,30),size:i(4,Float32Array[u(Xa,31)]),usage:window[c(Xa,32)][s(Xa,33)],mappedAtCreation:true
    });
    return new Float32Array(t[u(Xa,34)]())[a(Xa,35)](n),t[o(Xa,36)](),bn[a(Xa,26)]( {
      layout:Cn[l(Xa,27)](1),entries:[ {
        binding:0,resource: {
          buffer:t
        }

      }]
    })
  })),jn=bn[x(Xa,37)](T(Xa,38)),Vn=bn[b(Xa,29)]( {
    size:O(jn[_(Xa,39)],8),usage:E(window[k(Xa,32)][j(Xa,40)],window[V(Xa,32)][P(Xa,41)])
  }),Nn=bn[V(Xa,29)]( {
    size:i(Vn[j(Xa,42)],Sn),usage:E(window[C(Xa,32)][N(Xa,21)],window[M(Xa,32)][M(Xa,43)])
  }),Mn= {
    label:S(Xa,44),colorAttachments:F(Xa,45),timestampWrites: {
      querySet:jn,beginningOfPassWriteIndex:0,endOfPassWriteIndex:1
    }

  };
  for(let R=0;D(R,_n.length);R++) {
    const n=_n[R];
    Mn[w(Xa,46)][0][W(Xa,47)]=e[u(Xa,48)]()[Z(Xa,28)]();
    const t=bn[G(Xa,49)](M(Xa,50)),r=t[H(Xa,51)](Mn);
    r[c(Xa,52)](Cn),r[g(Xa,53)](0,On),r[U(Xa,53)](1,n);
    const o=window[B(Xa,54)][B(Xa,55)]();
    r[$(Xa,56)](48),r[Y(Xa,57)](),t[X(Xa,58)](jn,0,jn[J(Xa,39)],Vn,0),q(Nn[z(Xa,59)],K(Xa,60))&&t[Q(Xa,61)](Vn,0,Nn,i(R,16),Vn[G(Xa,42)]);
    const s=t[$(Xa,62)]();
    bn[nn(Xa,22)][A(Xa,63)]([s]);
    const a=tn(nl,e[en(Xa,2)]);
    In[K(Xa,35)](a,m(8,O(R,rn(on(16,Ka),8)))),In[un(Xa,35)](new Uint8Array(new Float64Array([o])[w(Xa,64)]),cn(R,sn(an(16,Ka),8)));
  }
  if(q(Nn[ln(Xa,59)],l(Xa,60))) {
    await Nn[$(Xa,65)](window[fn(Xa,66)][l(Xa,67)]);
    const n=Nn[j(Xa,34)](),t=new Uint8Array(n);
    for(let e=0;dn(e,Sn);e++)In[mn(Xa,35)](t[vn(Xa,68)](hn(e,Ka),pn(gn(e,1),Ka)),wn(rn(8,16),O(e,m(yn(16,Ka),8))));
    Nn[mn(Xa,36)]();
  }
  return fn(R$1,In)
}
function nl(n) {
  return function(n,t) {
    return n(t)
  }
  (x$1,function(n,t) {
    return n(t)
  }
  (Ct,n[function(n,t) {
    return n(t)
  }
  (Xa,69)]()))
}
async function tl(n) {
  const t=function(n,t) {
    return n!==t
  },e=function(n,t) {
    return n(t)
  };
  var r;
  return function(n,t) {
    return n!==t
  }
  (r=n[function(n,t) {
    return n(t)
  }
  (Xa,70)],null)&&t(r,undefined)?r:await n[e(Xa,71)]()
}
const el=new RegExp(Hi([39174333,51812406,885210665,4099360837,1242130291,1365653239,2003041115,1707369036,3273002536,359933e3,1948332465],5)(0));
function rl() {
  const n=function(n) {
    return n()
  },t=function(n,t) {
    return n!==t
  },e=function(n,t,e) {
    return n(t,e)
  },o=function(n,t,e) {
    return n(t,e)
  },i=function(n,t,e) {
    return n(t,e)
  },u=function(n,t) {
    return n instanceof t
  },s=function(n,t) {
    return n(t)
  };
  return function(n,t,e) {
    return n(t,e)
  }
  (c$1,e(r$1,1e3, {
    s:-2,v:null
  }),(async()=> {
    const r=await n(il);
    if(t(e(Gi,r,453955339),0))return r;
    try {
      const[n,t]=e(Gi,r,1801730948),[u,c,s]=await e(za,n,t);
      return  {
        s:0,v: {
          s:s,f:u,v:o(Gi,c,4112659446),a:i(Gi,c,1956208378)
        }

      }

    } catch(c) {
      if(u(c,TypeError)&&s(ul,i(Gi,c,3065852031)))return  {
        s:-7,v:null
      };
      throw c
    }

  }))
}
async function ol() {
  const n=function(n,t,e) {
    return n(t,e)
  },t=function(n,t) {
    return n instanceof t
  },e=function(n) {
    return n()
  },r=function(n,t,e) {
    return n(t,e)
  },o=n(Gi,navigator,3179935986);
  if(!o)return  {
    s:-3,v:null
  };
  let i=null;
  try {
    i=await n(Gi,o,1678473624)();
  } catch(u) {
    if(t(u,Error)&&e(ln))return  {
      s:-3,v:r(Gi,u,3065852031)
    };
    throw u
  }
  return i? {
    s:0,v:i
  }
  : {
    s:-4,v:null
  }

}
async function il() {
  const n=function(n) {
    return n()
  },t=function(n,t) {
    return n===t
  },e=function(n,t,e) {
    return n(t,e)
  },r=function(n,t,e) {
    return n(t,e)
  },o=function(n) {
    return n()
  },i=await n(ol);
  let u=null;
  if(!t(e(Gi,i,453955339),0))return i;
  u=r(Gi,i,1801730948);
  if(!o(Ja))return  {
    s:-1,v:null
  };
  const c=n(qa);
  return c? {
    s:0,v:[u,c]
  }
  : {
    s:-5,v:null
  }

}
function ul(n) {
  const t=function(n,t) {
    return n===t
  },e=function(n,t) {
    return n(t)
  },r=n.match(el);
  return !!r&&t(e(A,r[1]),4169850297)
}
function cl() {
  var n;
  return  {
    s:0,v:null!==(n=performance.timeOrigin)&&undefined!==n?n:Date.now()-performance.now()
  }

}
var sl=Hi([1058085656,755065913,591387725,129841502,4267773802,944664064,1500447153,1699147887,1224620868,4264117283,677258056,1080570024,1964094248,134111503,3007202158,269444104],5);
async function al(n) {
  const t=function(n) {
    return n()
  },e=function(n,t) {
    return n(t)
  };
  return function(n) {
    return n()
  }
  (cn)||t(sn)?await e(ll,n): {
    s:-1,v:null
  }

}
function ll(n) {
  const t=function(n,t) {
    return n(t)
  },e=function(n) {
    return n()
  },r=function(n,t,e) {
    return n(t,e)
  },o=function(n,t) {
    return n(t)
  },i=function(n,t,e) {
    return n(t,e)
  },c=function(n,t) {
    return n(t)
  },s=function(n,t) {
    return n(t)
  },a=function(n,t) {
    return n(t)
  };
  return function(n,t,e) {
    return n(t,e)
  }
  (ur,((n,l)=> {
    const f=function(n,t) {
      return a(n,t)
    },d=new Promise((n=> {
      const u=function(n,e) {
        return t(n,e)
      };
      let a;
      e(cn)?(a=new Error,a.name=" ",r(Gi,Object,1973166116)(a,o(sl,0), {
        get:n.bind(null,true)
      })):(a=r(Gi,l[o(sl,1)],1297038992)(o(sl,2)),a.toString=()=>"",i(Gi,Object,1973166116)(a,t(sl,3), {
        get:()=> {
          u(n,true);
          const t=new Error;
          throw t.name="",t
        }

      })),l[c(sl,4)](l[c(sl,5)].debug,0,a),l[s(sl,4)]((()=> {
        f(n,false);
      }));
    }));
    return o(u$1,d).then((n=>( {
      s:0,v:n
    })))
  }),function(n,t,e) {
    return n(t,e)
  }
  (Gi,n,3569745779))
}
const fl=new Set([2882888216,2306836488,1040191956,1447924955]);
function dl() {
  return  {
    s:0,v:O$1(Navigator.prototype,fl)
  }

}
var ml=Hi([337235919,2760532337,875971243,3754618647,55785531,2093468645,3611500405],7);
function vl() {
  const n=function(n,t) {
    return n!==t
  },t=function(n,t) {
    return n(t)
  },e=function(n,t,e) {
    return n(t,e)
  }
  (Gi,new(window[function(n,t) {
    return n(t)
  }
  (ml,0)])(""),3966979758);
  return n(typeof e,t(ml,1))? {
    s:-1,v:null
  }
  : {
    s:0,v: {
      isTrusted:e
    }

  }

}
var hl=Hi([346417124,3652618933,3415905489,3253897955,2294399372,4070113219,3251407103,3790651278,3281774077,3704133079,3942300820,3367225321,4294875871,2331302290,3768121793,3888880373,3201419702,3231249615,3437080024,3100701610,3314799614,3758005657,2210585768,4271564258,3438535137,3202800573,3366777040,3303964898,2682776755,3951621071,2159973508,4008833771,3834510307,3721574652,3975475112,3700541151,4124803294,3095585942,3247897010,3807349469,2666921394,4072405711,2195887329,3154092449,4294345125,3888048838,3053383582,3253728495,3755524068,2532356992,3435067859,4275287775,2625825195,3434202529,2160370131,2496716211,3113534649,4075273716,3919438518,3752838589,3723725017,2465382589,3869810136,3740114311,2948853427,3773496770,3803351801,3952999656,3740726744,2264707582,3201236378,3332498654,3857093830,3972063642,3719283692,3236399861,2408578979,3722477823,4189761762,3783784893,3166361052,3976174325,3992312192,3924749508,4276728450,2564278682,2994979003,4089872596,2710490283,3249730500,4072511186,2699427004,3432903858,4089558744,2598495113,3216571058,3875126671,2916413345,3019038131,4278096123,2714560668,3499681728,3520970703,2935474610,3734566863,4058549465,2397888693,3649293503,3790334595,3033720459,3649291238,2229842819,2563889641,3264725957,3623783675,2180889534,3197950130,2179985116,3085158067,3549095404,3535397375,2516315025,3700870369,2398731507,3196105632,3331032025,3858610141,2949954204,4193226680,2211417304,2866061727,3686171852,3520654823,3791248297,3214074061,4223644355,2513361645,4204459429,3355152593,2543437536,3918648781,4004747161,2596587405,3366839520,3874003956,2564812727,3331441115,4223968132,2542187179,3485269211,4124110847,2381307884,2997600697,3723726493,3185957288,3387744482,4075417541,3084055278,3014969267,2582359544,3951294654,3332217343,3669592518,3787970999,4176905458,2178456300,2716330417,3651767969,3741234428,2851648183,2777211119,2180229583,2946350571,3869178341,3621566446,2529215113,3723682e3,4124946404,3939286952,3332032457,4053920986,3204036799,3015689465,4039568325,2541866927,3438010588,3590034112,3988905614,3012558810,3304832485,2514985405,4002541807,3973679769,3017591728,3314470877,4193238482,2983185323,3264972264,3523058939,3162627819,4076263902,2647437262,3018252672,3668479922,4022960577,2681128378,3770581153,3252335833,3218734243,4069981417,3655439325,2751195028,3466326249,3623659993,2646785979,3298870747,4208626831,2599543454,2776731315,3887244174,2862472074,3734230266,3522074095,2681794463,3198743013,3251027585,2541803933,3682660317,4092635365,3218268138,4209959352,3485381324,3992056763,3550215898,2197416672,3184325562,3887632123,2580524480,3185951914,4018929093,3506082243,4120164232,4021671336,3755912151,2899963828,2834666750,3321478363,4224970168,4020933798,3689123266,2915296700,3422263976,3838548215,3133982865,3415790008,2177603831,2834997692,3650017490,3487625157,3906333850,3182528216,4157315303,2566904730,3348889560,3536107236,2212357867,3903450322,3538718683,3184319646,3348299721,4176648412,2206643087,3919638749,3821647567,4220247017,4021982374,3953703640],3);
function pl( {
  cache:n,esc:t=true
}) {
  const e=function(n,t,e) {
    return n(t,e)
  };
  if(!t)return  {
    s:-5,v:null
  };
  const r= {
    s:-2,v:null
  };
  return function(n,t) {
    return n(t)
  }
  (gl,function(n,t) {
    return n(t)
  }
  (Ns,n)).then((n=> {
    e(yl,r,n);
  })).catch((n=>yl(r,Ei(n)))),r
}
async function gl(n) {
  const t=function(n,t,e) {
    return n(t,e)
  },e=function(n,t) {
    return n(t)
  },r=function(n,t) {
    return n(t)
  },o=await t($s,n,false);
  switch(t(Gi,o,453955339)) {
    case-3:return  {
      s:-4,v:null
    };
    case-1:return  {
      s:-1,v:null
    };
    case-2:return  {
      s:-3,v:null
    }

  }
  const i=e(S$1,r(hl,0));
  return  {
    s:0,v:r(R$1,await t(wl,t(Gi,o,1801730948),i))
  }

}
async function wl(n,t) {
  const e=function(n,t) {
    return n!==t
  },r=function(n,t) {
    return n(t)
  },o=function(n,t,e) {
    return n(t,e)
  },i=function(n,t) {
    return n(t)
  },u=function(n,t) {
    return n===t
  },c=function(n,t,e) {
    return n(t,e)
  },s=function(n) {
    return n()
  },a=function(n,t,e) {
    return n(t,e)
  },l=function(n) {
    return n()
  },f=function(n) {
    return n()
  },d=function(n,t,e) {
    return n(t,e)
  },m=function(n,t) {
    return n(t)
  },v=function(n,t) {
    return n(t)
  },h=function(n,t,e) {
    return n(t,e)
  },p=await c(Gi,n,552725026)(),g=o(Gi,p,3695949181)();
  try {
    const n=new Promise(((n,v)=> {
      const h=function(n) {
        return f(n)
      },p=function(n,t) {
        return i(n,t)
      };
      let w,y=false;
      const b=()=> {
        y=true,e(w,undefined)&&window[r(hl,1)](w),o(Gi,g,244589941)(i(hl,2),E);
      },E=e=> {
        if(!y)if(u(o(Gi,c(Gi,e,3065852031),740233146),2))c(Gi,g,2552575352)(t).catch((n=> {
          h(b),p(v,n);
        }));
        else  {
          s(b);
          const t=new Uint8Array(a(Gi,e,3065852031));
          r(n,t);
        }

      };
      d(Gi,g,123626528)(m(hl,2),E),w=window[i(hl,3)]((()=> {
        y||l(b);
      }),5e3);
    })),p=r(S$1,i(hl,4));
    return await a(Gi,g,2250224811)(v(hl,5),p),await n
  } finally {
    try {
      await h(Gi,g,318865860)();
    } catch(w) {

    }

  }

}
function yl(n,t) {
  for(const e of Object.keys(n))delete n[e];
  Gi(Object,1914874273)(n,t);
}
var bl=Hi([3268306020,1189123365,3125061564,2812436647,1370270536,3104304876,2864333227,1189143047,3863391919,3133019362,232973317,2689380846,4109895146,502529820,4262523388,3806594546,334622221,3994352377,4074964461,100137739,2705777380,4025355697,502660630,4145147134,4043052789,502594832,3875927031,3958246626,2028005125],3);
function El() {
  var n=function(n,t,e) {
    return n(t,e)
  },t=function(n,t) {
    return n(t)
  },e=function(n,t) {
    return n(t)
  },r=function(n,t,e) {
    return n(t,e)
  },o=function(n,t,e) {
    return n(t,e)
  };
  const i=document[function(n,t) {
    return n(t)
  }
  (bl,0)]("a");
  return n(Gi,i,868071530)[t(bl,1)]=e(bl,2), {
    s:0,v:r(Gi,o(Gi,i,868071530),2350531887)
  }

}
async function Rl(n) {
  return ur(((n,t)=> {
    const e=t.document.createElement("div");
    e.style.width="100px",e.style.height="100px",e.style.overflow="scroll",e.style.visibility="hidden",t.document.body.appendChild(e);
    const r=e.offsetWidth===e.clientWidth;
    return t.document.body.removeChild(e), {
      s:0,v:r
    }

  }),n.sis)
}
function Sl() {
  return  {
    s:0,v:new URL("C:/").protocol
  }

}
async function Il(n) {
  return ur(((n,t)=> {
    if(!ln())return  {
      s:-1,v:null
    };
    const e=t.document.createElement("input");
    e.type="radio",t.document.body.appendChild(e);
    const r=t.getComputedStyle(e).getPropertyValue("font-family");
    return t.document.body.removeChild(e), {
      s:0,v:r
    }

  }),n.sis)
}
async function kl() {
  try {
    const n=new FontFace("font","local('Arial')");
    return await n.load(), {
      s:0,v:true
    }

  } catch(n) {
    return  {
      s:0,v:false
    }

  }

}
var Al=Hi([4216757916,2482823581,3322768783,3940655043,2767747340,149091984,3502500195,1661791409,2978971883,4181675939,4172402883,2313775364,95272926,2491872360,792833511,4287662331,4050917852,2915032708,2164222495,1336127956,3386158881,792833466,3817182206,3224306427],7);
function Cl() {
  const n=function(n,t) {
    return n(t)
  },t=function(n,t,e) {
    return n(t,e)
  },e=function(n,t) {
    return n(t)
  },r=function(n) {
    return n()
  },o=function(n,t,e,r,o) {
    return n(t,e,r,o)
  },i=function(n,t) {
    return n<t
  },u=function(n,t) {
    return n<t
  },c=function(n,t) {
    return n*t
  },s=function(n) {
    return n()
  },a=function(n,t) {
    return n*t
  },l=function(n) {
    return n()
  },f=function(n,t) {
    return n*t
  },d=function(n,t) {
    return n(t)
  },m=function(n,t) {
    return n+t
  },v=function(n,t) {
    return n+t
  },h=function(n,t) {
    return n(t)
  },p=function(n,t) {
    return n(t)
  },g=function(n,t,e) {
    return n(t,e)
  },w=function(n,t,e) {
    return n(t,e)
  },y=document[n(Al,0)](n(Al,1)),b=t(Gi,y,1590906722)(n(Al,2));
  if(!b)return  {
    s:-1,v:null
  };
  y[n(Al,3)]=4,y[e(Al,4)]=4;
  const E=r(Ll),R=o(Vt,E[0],E[1],E[2],E[3]);
  for(let I=0;i(I,4);I++)for(let n=0;u(n,4);n++) {
    const t=Math.floor(c(s(R),256)),e=Math.floor(a(l(R),256)),o=Math.floor(f(r(R),256));
    b[d(Al,5)]=m(m(m(m(m(v(h(Al,6),t),","),e),","),o),p(Al,7)),g(Gi,b,2027710893)(n,I,1,1);
  }
  const S=g(Gi,b,2240176009)(0,0,w(Gi,y,2350531887),t(Gi,y,4115522831));
  return  {
    s:0,v: {
      s:E,p:Array.from(g(Gi,S,2918445923)),d:4
    }

  }

}
function Ll() {
  const n=function(n,t,e) {
    return n(t,e)
  },t=function(n,t) {
    return n(t)
  },e=function(n,t) {
    return n|t
  },r=function(n,t) {
    return n|t
  },o=new Uint32Array(4);
  return n(Gi,window[t(Al,8)],2617745417)(o),[e(o[0],0),e(o[1],0),r(o[2],0),e(o[3],0)]
}
var Pl=Hi([1423962864,3121043048,221491638,3386365733,3464442684,302891971,3755202414,3563601691,2051732871,3386365733,3464442684,302891971,3755202414,3563601691,2051732868,3386365733,3464442684,302891971,3755202414,3563601691,2051732869,3386365733,3464442684,386778051,3369584757,3749590820,2051719876,3386365733,3731439402,587711473,2643773815,3261479754,839309556,3268531310,4168430392,286056415,3250836853,3609557578,791464407,3638287209,3546874635,991616720,3620785989,3933479949,1060684755,3638222711,3679138566,572382927,3700725285,3275959817,1057345752,3737315684,3747624730,806274292,3787835490,3545703437,1057281222,3506102121,3463592209,994745748,3504718438,3748341253,772662738,3569667955,3361867291,839506405,3320170594,2556571913,923112346,3705137535,3361880600,604889541,3587691092,3461620749,1947064023,3504052267,3581084944,856674500,3620785989,3933479949,1044104147,3285442150,3714458171,1950651347,3805207402,3681892636,859624657,3284389503,3747030285,922804932,3804553059,3747624732,994745748,3756245606,3362271233,807269339,3267682145,3916772152,856477918,3502434677,2519020303,772398228,3621770322,4167705607,856610755,3755997301,3714662156,856873189,3700725285,3461623305,822723545,3619944546,4168430350,1057808351,3638943081,2519020306,939646100,3621770322,4167705607,856610755,3620795765,4218630939,940562650,3319324522,3609557578,574349279,3604465768,3698463757,421188816,3569736801,3547010844,856022993,2643775081,3261479754,572183776,3304374882,3361878030,1950651333,4090420074,3747688477,738321092,2476382306,3967760133,857523155,3317889919,3479519002,1947980994,3504052267,3361865744,336647362,3570457714,3363116826,574343383,3570586485,3609557578,941738455,3804553075,3747624732,839506405,3740649570,3563595269,622649299,3700725285,3561893385,85644482,3570522995,3731242555,926860243,3554136949,2557752068,923112346,3722049919,3460703239,1040961730,3319324522,2552984603,353423579,3285833320,3681755689,856021461,3371486825,3933483804,926663635,3571108458,3609557578,959171031,3317942890,3362259213,958060253,3320171122,3714458631,738321107,2476382306,4185863941,588831961,3758088051,3680778526,940038338,3285445236,3514120511,587711441,2476382327,4185863941,588831961,3739344755,3361750298,85509337,3922968686,3609557578,959171031,3317942890,3362259213,958060253,3638938226,2556310290,923112346,3705272703,3748864792,1025171169,3302606944,3228435736,2051730387,3386365733,3395959083,17679811,3604858984,3396483354,604889541,3571176259,3580765446,1950651352,4090420074,4251138049,639491780,3302681204,3361865755,336647362,3570457714,2519016730,772398228,3285831252,4167184649,856610755,3758082421,3714458670,570873051,3604467284,2552984589,84988123,3502560627,3477418767,604886992,3889754996,3748865037,924639950,2643779424,3261479754,604489189,3855867238,3480432141,521917636,3502570601,3563207439,924639938,2643779424,3261479754,604489189,3855867238,3480432141,521917636,3285445737,3917427484,856674498,2476402469,3547669019,2051725016,4156936997,3630905865,386126551,3318143843,3877970957],6);
const xl=Pl(0);
async function Tl(n) {
  const t=function(n,t) {
    return n!==t
  },e=function(n,t,e) {
    return n(t,e)
  };
  var r;
  return function(n,t) {
    return n!==t
  }
  (r=function(n,t,e) {
    return n(t,e)
  }
  (Gi,n,3414765911),null)&&t(r,undefined)?r:await e(Gi,n,3779360887)()
}
async function Ol() {
  const n=function(n) {
    return n()
  },t=function(n,t) {
    return n===t
  },e=function(n,t,e) {
    return n(t,e)
  },r=function(n,t) {
    return n===t
  },o=function(n,t) {
    return n(t)
  },i=function(n,t,e) {
    return n(t,e)
  },u=function(n,t,e) {
    return n(t,e)
  },c=function(n,t,e) {
    return n(t,e)
  },s=function(n,t) {
    return n in t
  },a=function(n,t,e) {
    return n(t,e)
  },l=function(n,t,e) {
    return n(t,e)
  },f=function(n,t) {
    return n(t)
  },d=function(n,t) {
    return n in t
  },m=function(n,t) {
    return n(t)
  },v=function(n,t,e) {
    return n(t,e)
  },h=await n(ol);
  if(t(e(Gi,h,453955339),-3)) {
    let n=null;
    return r(typeof e(Gi,h,1801730948),o(Pl,1))&&(n=i(Gi,h,1801730948)), {
      s:-1,v:n
    }

  }
  if(r(u(Gi,h,453955339),-4))return  {
    s:-2,v:null
  };
  const p=c(Gi,h,1801730948),g=[];
  if(p)for(const y of xl)g.push(s(y,a(Gi,p,1455634619))?l(Gi,p,1455634619)[y]:null);
  const w=await f(Tl,p);
  return  {
    s:0,v: {
      ds:l(Gi,w,1843675174),dv:u(Gi,w,154121870),f:d(m(Pl,2),w)?v(Gi,w,4163855836):null,l:g
    }

  }

}
var _l=Hi([1435303418,2123044869,1559249858,283799713,233274796,1387864800,182614752,469727664,1304044256,1320890352,536361710,468150447,469727664,1287529184,1391864050,316833504,1554463399,468677044,249968557,497755126,502168749,149562801,1319447026,867379436,1555245292,402471662,1373928870,334069173,300431609,233340326,1190883071,145306848,300842155,485388269,497755055,502168749,251471281,1319444978,1320826610,1555245292,402471662,1373928870,1170172079,451181538,1140358055,1340632746,1218783724,1303532780,1555782380,402471662,1373928870,1170172079,451181538,1140358055,1340632739,1321152236,1555245810,402471662,1373928870,1170172079,451181538,1140358055,1340632739,1321152236,1555573746,199899886,1373925798,1173127085,451181538,1140358055,234776749,531182816,300055735,1257993709,300431609,233340326,1257993727,1321154211,1386819052,451835360,533232043,401177010,402616750,598305703],4);
const jl=1e6,Vl= {
  width:1920,height:1080,bitrate:5*jl,framerate:30
},Nl= {
  width:3840,height:2160,bitrate:20*jl,framerate:60
},Ml=_l(0);
function Fl(n,t=Vl,e=null,r=Ml) {
  const o= {
    type:(i=_l,u=1,i(u)),video: {
      contentType:n,...t
    }

  };
  var i,u;
  return e? {
    ...o,audio: {
      contentType:e,...r
    }

  }
  :o
}
function Dl() {
  const n=function(n,t) {
    return n(t)
  },t=function(n,t) {
    return n(t)
  },e=function(n,t) {
    return n(t)
  },r=function(n,t) {
    return n(t)
  },o=function(n,t) {
    return n(t)
  },i=function(n,t) {
    return n(t)
  },u=function(n,t,e) {
    return n(t,e)
  },c=function(n,t,e,r) {
    return n(t,e,r)
  },s=function(n,t) {
    return n(t)
  },a=function(n,t) {
    return n(t)
  },l=function(n,t) {
    return n(t)
  };
  return [n(Fl,function(n,t) {
    return n(t)
  }
  (_l,2)),t(Fl,e(_l,3)),r(Fl,t(_l,4)),o(Fl,i(_l,5)),t(Fl,n(_l,6)),u(Fl,o(_l,7),Nl),c(Fl,s(_l,4),Vl,a(_l,8)),c(Fl,o(_l,6),Vl,l(_l,9))]
}
const Wl=Dl();
async function Zl() {
  const n=function(n,t,e) {
    return n(t,e)
  },t=function(n,t,e) {
    return n(t,e)
  },e=function(n,t,e) {
    return n(t,e)
  },r=function(n,t) {
    return n instanceof t
  },o=function(n,t) {
    return n(t)
  };
  if(!function(n,t) {
    return n in t
  }
  (o(_l,10),navigator))return  {
    s:-1,v:null
  };
  return  {
    s:0,v:await Promise.all(Wl.map((async i=> {
      try {
        const r=await n(Gi,n(Gi,navigator,2900309608),3516168465)(i);
        let o=0;
        return t(Gi,r,4146387716)&&(o+=1),t(Gi,r,1965183968)&&(o+=2),e(Gi,r,2920301991)&&(o+=4),o
      } catch(u) {
        return r(u,Error)?n(Gi,u,3065852031):o(String,u)
      }

    })))
  }

}
const Gl=function() {
  return  {
    key:"bd",sources: {
      stage1: {
        s94:Ia,s167:pl
      },stage2: {
        s106:Ju$1,s154:Js,s158:ea,s160:Vc,s97:Ba,s70:rl,s152:hs,s163:al
      },stage3: {
        s1:fu,s2:du$1,s4:vu,s5:hu$1,s7:pu,s15:Ru$1,s19:ku$1,s27:Au$1,s74:Gu,s75:Hu,s24:Bc,s44:gc,s45:yc,s57:ss,s59:uc,s60:cc,s61:sc,s62:ac,s63:lc,s64:fc,s65:dc,s68:mc,s69:Zc,s72:$c,s82:Es,s83:Rs,s99:Ya,s101:$u,s103:Yu$1,s104:Xu,s117:qu$1,s119:zu,s123:Ku,s131:Qu,s133:nc,s136:tc,s148:ec,s149:rc,s150:oc,s157:ic,s102:gs,s118:ws,s120:vs,s130:ys,s132:bs,s135:ps,s139:fs,s142:ms,s144:ds,s145:as,s146:ls,s151:_s,s153:js,s155:zs,s156:na,s159:ra,s162:sa,s165:vl,s166:dl
      }

    }

  }

};
function Hl(n,t,e,r,o,i) {
  const u=r?[]:function(n,t,e) {
    return function(n,t) {
      const e=function(n,t,e) {
        return n(t,e)
      },r=function(n,t) {
        return n(t)
      },o=function(n,t) {
        return n(t)
      },i=Array.isArray(n)?n:[n],u=[];
      for(const c of i)if(e(Qi,c,Ht))for(const n of t)u.push(r(Xi,n));
      else u.push(o(String,c));
      return u
    }
    (n,t).map((n=>Pr(n, {
      q:e
    })))
  }
  (n,t,e);
  if(0===u.length)return ()=>Promise.resolve( {
    s:-1,v:null
  });
  Br(i,(()=>( {
    e:6
  })));
  const c=s$1(),a=_r(c),l=Date.now(),f=Mo(u,Ul.bind(null,5e3,i,a),Bl,Math.max(10,u.length),o);
  return f.then((()=>c.resolve()),(()=>c.resolve())),async function(n,t,e,r) {
    if(e)return  {
      s:-1,v:null
    };
    try {
      await Promise.race([f,$l(l,n,t)]);
      const e=function( {
        result:n,failedAttempts:t
      }) {
        if(undefined!==n)return n;
        const e=t[0];
        if(!e)return  {
          s:-3,v:null
        };
        if(1===e.level)return e.error;
        const {
          error:r,endpoint:o
        }
        =e;
        if(r instanceof Error) {
          const {
            name:n,message:t
          }
          =r;
          switch(n) {
            case "AbortError":return  {
              s:-2,v:t
            };
            case "TimeoutError":return  {
              s:-3,v:t
            };
            case "CSPError":return  {
              s:-6,v:t
            };
            case "InvalidURLError":return  {
              s:-7,v:`Invalid URL: ${je(o,255)}`
            };
            case "TypeError":return  {
              s:-4,v:t
            }

          }

        }
        return Ei(r)
      }
      (f.current);
      return Br(r,(()=>( {
        e:7,result:e
      }))),e
    } catch(o) {
      throw Br(r,(()=>( {
        e:8,error:o
      }))),o
    }

  }

}
function Ul(n,t,e,r,o,i) {
  return $r(t,(()=>( {
    e:9,tryNumber:o,url:r,timeout:n
  })),(( {
    status:n,getHeader:t,body:e
  })=>( {
    e:10,tryNumber:o,status:n,retryAfter:t("retry-after"),body:e
  })),(n=>( {
    e:11,tryNumber:o,error:n
  })),(()=>Or( {
    url:r,timeout:n,abort:i,container:e
  })))
}
function Bl( {
  status:n,body:t
}) {
  if(200===n&&/^[a-zA-Z0-9+/]{1,1022}={0,2}$/.test(t))return  {
    result: {
      s:0,v:t
    }

  };
  return  {
    error: {
      s:-5,v:je(`${n}: ${t}`,255)
    }

  }

}
function $l(n,t,e) {
  return r$1(Math.min(Math.max(t,n+1e4-Date.now()),e))
}
function Yl(n) {
  const t=so(n);
  let[e,r]=function(n) {
    return [eo(n),lo(n)]
  }
  (t);
  return e=Xl(e),r=Xl(r),undefined!==e&&undefined!==r? {
    s:0,v:e||r
  }
  :undefined!==e? {
    s:1,v:e
  }
  :undefined!==r? {
    s:2,v:r
  }
  : {
    s:-1,v:null
  }

}
function Xl(n) {
  return n&&n.length<=1e3?n:undefined
}
const Jl=function() {
  return  {
    key:"id",sources: {
      stage1: {
        s94:Ia
      },stage2: {
        s52:jc,s6:lu,s58:Wc,s20:kc,s36:su,s51:Lc,s21:au$1,s79:rs,s69:Zc,s23:Is,s29:Ss,s84:As,s85:xs,s89:Yc,s17:Iu$1,s87:ta,s92:ua,s93:ia,s95:Wa,s97:Ba,s70:rl,s204:Rl,s206:Il,s207:kl,s210:Ol,s211:Zl
      },stage3: {
        s22:us,s30:is,s33:hc,s44:gc,s45:yc,s49:xc,s50:Oc,s57:ss,s59:uc,s60:cc,s61:sc,s62:ac,s63:lc,s64:fc,s65:dc,s66:Wu$1,s68:mc,s71:Uc,s24:Bc,s72:$c,s1:fu,s2:du$1,s3:mu,s4:vu,s5:hu$1,s7:pu,s9:gu$1,s10:wu,s11:yu$1,s12:Ls,s13:bu$1,s14:Eu,s15:Ru$1,s16:Su$1,s19:ku$1,s27:Au$1,s28:Cu$1,s32:Lu$1,s37:Pu,s41:xu$1,s39:Tu,s42:Ou$1,s38:_u$1,s43:ju,s40:Nu$1,s46:Mu$1,s80:Fu,s81:Du$1,s82:Es,s83:Rs,s86:Os,s91:Vu$1,s96:Zu$1,s98:$a,s99:Ya,s200:cl,s201:vc,s202:Bu$1,s205:Sl,s203:El,s209:Cl,s74:Gu,s75:Hu,s76:_c
      }

    },tls:Hl,async toRequest(n,t) {
      const e=location.href,r=document.referrer,[o,i]=await Promise.all([e&&Ir(e,t),r&&Ir(r,t)]);
      return  {
        url:o,cr:i||undefined,s55:Yl(n),s48:cs()
      }

    },onGetResponse(n,t) {
      var e,r,o;
      !function(n,t) {
        const e=so(n);
        t&&co(t,e);
      }
      (t,null===(o=null===(r=null===(e=n.products)||undefined===e?undefined:e.identification)||undefined===r?undefined:r.data)||undefined===o?undefined:o.visitorToken);
    }

  }

};
const Ql="API key required",nf="API key not found",tf="API key expired",ef="Request cannot be parsed",rf="Request failed",of="Request failed to process",uf="Too many requests, rate limit exceeded",cf="Not available for this origin",sf="Not available with restricted header",af=Ql,lf=nf,ff=tf;
const u=(()=>( {

}))(),r="df994e8";
function h() {
  const u=window;
  return bu(["ApplePayError"in u,"CSSPrimitiveValue"in u,"Counter"in u,0===navigator.vendor.indexOf("Apple"),"RGBColor"in u,"WebKitMediaKeys"in u])>=4
}
function k(u,r) {
  E(u,u.len+r.length),u.arr.set(r,u.len),u.len+=r.length;
}
function R(u,r) {
  const V=function(u,r,V) {
    return u(r,V)
  },N=function(u,r) {
    return u(r)
  },h=function(u,r,V) {
    return u(r,V)
  },k=function(u,r) {
    return u(r)
  },R=function(u,r,V) {
    return u(r,V)
  };
  return new Promise(((U,x)=> {
    const A=new Uint8Array(r),D=V(L,u,1916208593)(Mu,N(qu,4)),S=h(L,D,4272307067)(Mu),a=new(window[N(qu,5)])([A],k(qu,6));
    R(L,S,2928708052)( {
      k:Math.random().toString(36).slice(2),v:a
    }),D[k(qu,7)]=()=>U(),D[N(qu,3)]=()=>x(L(D,1574812785));
  }))
}
function U(u,r,V) {
  const N=u.getShaderPrecisionFormat(u[r],u[V]);
  return N?[N.rangeMin,N.rangeMax,N.precision]:[]
}
function x(u) {
  if("function"==typeof TextDecoder) {
    const r=(new TextDecoder).decode(u);
    if(r)return r
  }
  const r=P(u);
  return decodeURIComponent(escape(String.fromCharCode.apply(null,r)))
}
function D(u) {
  if(u.webgl)return u.webgl.context;
  const r=document.createElement("canvas");
  let V;
  r.addEventListener("webglCreateContextError",(()=>V=undefined));
  for(const h of ["webgl","experimental-webgl"]) {
    try {
      V=r.getContext(h);
    } catch(N) {

    }
    if(V)break
  }
  return u.webgl= {
    context:V
  },V
}
function S(u) {
  return u>=ru&&u<ru+10||u===hu
}
function L(u,r) {
  const V=function(u,r) {
    let V=u;
    for(;V;) {
      const u=Object.getOwnPropertyNames(V);
      for(let V=0;V<u.length;V++) {
        const N=u[V];
        if(s(N)==r)return N
      }
      V=Object.getPrototypeOf(V);
    }
    return ""
  }
  (u,r),N=u[V];
  return "function"==typeof N?N.bind(u):N
}
function a() {
  const u=function(u) {
    return u()
  },r=function(u,r) {
    return u(r)
  },V=function(u,r) {
    return u===r
  },N=function(u,r) {
    return u===r
  },h=function(u,r,V) {
    return u(r,V)
  },k=function(u,r) {
    return u===r
  },U=function(u,r,V) {
    return u(r,V)
  },x=function(u,r) {
    return u-r
  };
  return U(l,h(Cu,400, {
    s:-4,v:null
  }),(async()=> {
    var A,D;
    if(!u(i))return  {
      s:-3,v:null
    };
    const S=window[r(qu,8)];
    if(!S||!(V(D=V(A=window[r(qu,9)],null)||N(A,undefined)?undefined:h(L,A,1417288500),null)||k(D,undefined)?undefined:h(L,D,3538568711)))return  {
      s:-1,v:null
    };
    const a=await u(tu),o=r(Zu,8),C=await h(g,S,o);
    try {
      await h(R,C,du);
    } finally {
      h(L,C,318865860)();
    }
    await r(d,Iu);
    const q=await u(tu);
    U(L,S,3885781331)(o);
    return  {
      s:0,v: {
        before:a,after:q,delta:Math.max(0,x(q,a))
      }

    }

  }))
}
function o(u,r,V=Q) {
  let N="";
  for(let h=0;h<u;h++)N+=r.charAt(V()*r.length);
  return N
}
function q(u,r,...V) {
  const N=Date.now()+r;
  let h=0;
  const k=()=> {
    h=setTimeout((()=> {
      Date.now()<N?k():u(...V);
    }),N-Date.now());
  };
  return k(),()=>clearTimeout(h)
}
function M(u) {
  const r=P(u);
  c=c||function() {
    let u;
    const r=new Uint32Array(256);
    for(let V=0;V<256;V++) {
      u=V;
      for(let r=0;r<8;r++)u=1&u?3988292384^u>>>1:u>>>1;
      r[V]=u;
    }
    return r
  }
  ();
  let V=-1;
  for(let N=0;N<r.length;N++)V=V>>>8^c[255&(V^r[N])];
  return (-1^V)>>>0
}
function d(u,r) {
  return new Promise((V=>q(V,u,r)))
}
function I(u,r) {
  return (u-r+256)%256
}
function Z(u,r) {
  let V;
  return N=>(V||(V=function(u,r) {
    return function(u) {
      const r= {
        len:0,arr:new Uint8Array(128)
      },V=P(u);
      let N=0;
      const h=()=>(L(),V[N]===uu?R():S(V[N])?U():a(ku)?(N+=ku.length,null):a(Ru)?(N+=Ru.length,true):a(Uu)?(N+=Uu.length,false):91===V[N]?A():123===V[N]?D():o()),R=()=> {
        for(r.len=0;N++,V[N]!==uu;) {
          if(92===V[N]) {
            if(N++,V[N]===Nu) {
              const u=parseInt(x(V.subarray(N+1,N+5)),16);
              k(r,Ou(String.fromCharCode(u))),N+=4;
              continue
            }
            const u=Au[V[N]];
            if(u) {
              H(r,u);
              continue
            }
            return o()
          }
          if(undefined===V[N])return o();
          H(r,V[N]);
        }
        return N++,x(function(u) {
          return u.arr.subarray(0,u.len)
        }
        (r))
      },U=()=> {
        const u=N;
        for(;46===V[N]||V[N]===Vu||69===V[N]||43===V[N]||S(V[N]);)N++;
        return Number(x(V.subarray(u,N)))
      },A=()=> {
        const u=[];
        for(N++;;) {
          if(L(),93===V[N]) {
            N++;
            break
          }
          if(u.length) {
            if(44!==V[N])return o();
            N++;
          }
          u.push(h());
        }
        return u
      },D=()=> {
        const u= {

        };
        let r=true;
        for(N++;;) {
          if(L(),125===V[N]) {
            N++;
            break
          }
          if(!r) {
            if(44!==V[N])return o();
            N++,L();
          }
          if(V[N]!==uu)return o();
          const k=R();
          if(L(),58!==V[N])return o();
          N++,Object.defineProperty(u,k, {
            value:h(),configurable:true,enumerable:true,writable:true
          }),r=false;
        }
        return u
      },L=()=> {
        for(;32===V[N]||10===V[N]||13===V[N]||9===V[N];)N++;
      },a=u=> {
        for(let r=0;r<u.length;r++)if(V[N+r]!==u[r])return false;
        return true
      },o=()=> {
        throw new SyntaxError("Unexpected "+(N<V.length?`byte ${N}`:"end"))
      },C=h();
      L(),undefined!==V[N]&&o();
      return C
    }
    (function(u,r,V) {
      const N=()=> {
        throw new Error("Invalid data")
      },h=P(u);
      h.length<r.length+2&&N();
      for(let S=0;S<r.length;++S)I(h[1+S],h[0])!==r[S]&&N();
      const k=1+r.length,R=I(h[k],h[0]);
      h.length<k+1+R+V&&N();
      const U=k+1+R,x=U+V,A=new ArrayBuffer(h.length-x),D=new Uint8Array(A);
      for(let S=0;S<D.length;++S)D[S]=h[x+S]^h[U+S%V];
      return A
    }
    (new Uint32Array(u),[],r))
  }
  (u,r)),ou(V[N]))
}
function t(u,r,...V) {
  const N=document,h="visibilitychange",k=()=>N.hidden?U():R(), {
    start:R,stop:U
  }
  =function(u,r,V,...N) {
    let h,k=false,R=u,U=0;
    const x=()=> {
      k||h||(U=Date.now(),h=q((()=> {
        k=true,V(...N);
      }),R));
    };
    return r&&x(), {
      start:x,stop:()=> {
        !k&&h&&(h(),h=undefined,R-=Date.now()-U);
      }

    }

  }
  (r,!N.hidden,(()=> {
    N.removeEventListener(h,k),u(...V);
  }));
  return N.addEventListener(h,k),()=> {
    N.removeEventListener(h,k),U();
  }

}
function Y(u) {
  return Object.keys(u.__proto__).filter(K)
}
function _(u) {
  return u.map((u=> {
    var r;
    return null!==(r=T[u])&&undefined!==r?r:u
  }))
}
function K(u) {
  return "string"==typeof u&&!u.match(/[^A-Z0-9_x]/)
}
function s(u) {
  return M(Ou(u))
}
function P(u) {
  return u instanceof ArrayBuffer?new Uint8Array(u):new Uint8Array(u.buffer,u.byteOffset,u.byteLength)
}
function Q() {
  if(!crypto)return Math.random();
  crypto.getRandomValues(Du);
  return (1048576*Du[0]+(1048575&Du[1]))/4503599627370496
}
function E(u,r) {
  if(u.arr.length<r) {
    const V=new Uint8Array(Math.max(2*u.arr.length,r));
    V.set(u.arr),u.arr=V;
  }

}
const f=new Set([10752,2849,2884,2885,2886,2928,2929,2930,2931,2932,2960,2961,2962,2963,2964,2965,2966,2967,2968,2978,3024,3042,3088,3089,3106,3107,32773,32777,32777,32823,32824,32936,32937,32938,32939,32968,32969,32970,32971,3317,33170,3333,3379,3386,33901,33902,34016,34024,34076,3408,3410,3411,3412,3413,3414,3415,34467,34816,34817,34818,34819,34877,34921,34930,35660,35661,35724,35738,35739,36003,36004,36005,36347,36348,36349,37440,37441,37443,7936,7937,7938]),y=new Set([34047,35723,36063,34852,34853,34854,34229,36392,36795,38449]),b=["FRAGMENT_SHADER","VERTEX_SHADER"],W=["LOW_FLOAT","MEDIUM_FLOAT","HIGH_FLOAT","LOW_INT","MEDIUM_INT","HIGH_INT"],O="WEBGL_debug_renderer_info";
function H(u,r) {
  E(u,u.len+1),u.arr[u.len++]=r;
}
function J(u) {
  return r=> {
    const V=r.cache;
    if(V.webGlRawValues)return ou(V.webGlRawValues);
    const N=u(r);
    return "number"==typeof N?N:function(u,r) {
      const V=r;
      if(V.webGlRawValues)return ou(V.webGlRawValues);
      const N=u.parameters.map((u=> {
        const[r,V,N]=u.split("=",3);
        return undefined!==N||w.includes(V)?`${r}(${V})=null`:`${r}=${V}`
      })),h=u.extensionParameters.map((u=> {
        const[r,V,N]=u.split("=",3);
        return undefined!==N&&V!==e?`${r}(${V})=${N}`:`${r}=${V}`
      }));
      return V.webGlRawValues= {
        contextAttributes:u.contextAttributes,parameters:N,parameters2:u.parameters,shaderPrecisions:u.shaderPrecisions,extensions:u.extensions||[],extensionParameters:h,extensionParameters2:u.extensionParameters,unsupportedExtensions:u.unsupportedExtensions
      },ou(V.webGlRawValues)
    }
    (N,r.cache)
  }

}
const p=2,G=4;
function g(u,r) {
  const V=function(u,r,V) {
    return u(r,V)
  },N=function(u,r,V) {
    return u(r,V)
  },h=function(u,r) {
    return u(r)
  },k=function(u,r,V) {
    return u(r,V)
  },R=function(u,r) {
    return u(r)
  },U=function(u,r) {
    return u(r)
  },x=function(u,r) {
    return u(r)
  };
  return new Promise(((A,D)=> {
    const S=function(u,r,N) {
      return V(u,r,N)
    },a=function(u,r,N) {
      return V(u,r,N)
    },o=function(u,r,V) {
      return N(u,r,V)
    },C=function(u,r) {
      return h(u,r)
    },q=k(L,u,2758837156)(r);
    q[R(qu,0)]=()=> {
      const u=S(L,q,325763347);
      a(L,o(L,u,3440387547),2398775934)(Mu)||S(L,u,138212912)(Mu,C(qu,1));
    },q[U(qu,2)]=()=>A(L(q,325763347)),q[x(qu,3)]=()=>D(L(q,1574812785));
  }))
}
const B$1=65535;
let c;
async function l(u,r) {
  let V,N,h;
  try {
    V=r().then((u=>N=[true,u]),(u=>N=[false,u]));
  } catch(R) {
    N=[false,R];
  }
  const k=u.then((u=>h=[true,u]),(u=>h=[false,u]));
  return await Promise.race([V,k]),()=> {
    if(N) {
      if(N[0])return N[1];
      throw N[1]
    }
    if(h) {
      if(h[0])return h[1];
      throw h[1]
    }
    throw new Error("96375")
  }

}
function i() {
  var u,r;
  const V=window;
  return bu(["buildID"in navigator,"MozAppearance"in(null!==(r=null===(u=document.documentElement)||undefined===u?undefined:u.style)&&undefined!==r?r: {

  }),"onmozfullscreenchange"in V,"mozInnerScreenX"in V,"CSSMozDocumentRule"in V,"CanvasCaptureMediaStream"in V])>=4
}
const w=["32926","32928"],e="34047";
const T= {
  "alpha=true":0,"antialias=true":1,"depth=true":2,"desynchronized=false":3,"failIfMajorPerformanceCaveat=false":4,"powerPreference=default":5,"premultipliedAlpha=true":6,"preserveDrawingBuffer=false":7,"stencil=false":8,"xrCompatible=false":9,"ACTIVE_ATTRIBUTES=35721":10,"ACTIVE_TEXTURE(34016)=null":11,"ACTIVE_UNIFORMS=35718":12,"ALIASED_LINE_WIDTH_RANGE(33902)=null":13,"ALIASED_POINT_SIZE_RANGE(33901)=null":14,"ALPHA=6406":15,"ALPHA_BITS(3413)=null":16,"ALWAYS=519":17,"ARRAY_BUFFER=34962":18,"ARRAY_BUFFER_BINDING=34964":19,"ATTACHED_SHADERS=35717":20,"BACK=1029":21,"BLEND(3042)=null":22,"BLEND_COLOR(32773)=null":23,"BLEND_DST_ALPHA(32970)=null":24,"BLEND_DST_RGB(32968)=null":25,"BLEND_EQUATION(32777)=null":26,"BLEND_EQUATION_ALPHA(34877)=null":27,"BLEND_EQUATION_RGB(32777)=null":28,"BLEND_SRC_ALPHA(32971)=null":29,"BLEND_SRC_RGB(32969)=null":30,"BLUE_BITS(3412)=null":31,"BOOL=35670":32,"BOOL_VEC2=35671":33,"BOOL_VEC3=35672":34,"BOOL_VEC4=35673":35,"BROWSER_DEFAULT_WEBGL=37444":36,"BUFFER_SIZE=34660":37,"BUFFER_USAGE=34661":38,"BYTE=5120":39,"CCW=2305":40,"CLAMP_TO_EDGE=33071":41,"COLOR_ATTACHMENT0=36064":42,"COLOR_BUFFER_BIT=16384":43,"COLOR_CLEAR_VALUE(3106)=null":44,"COLOR_WRITEMASK(3107)=null":45,"COMPILE_STATUS=35713":46,"COMPRESSED_TEXTURE_FORMATS(34467)=null":47,"CONSTANT_ALPHA=32771":48,"CONSTANT_COLOR=32769":49,"CONTEXT_LOST_WEBGL=37442":50,"CULL_FACE(2884)=null":51,"CULL_FACE_MODE(2885)=null":52,"CURRENT_PROGRAM=35725":53,"CURRENT_VERTEX_ATTRIB=34342":54,"CW=2304":55,"DECR=7683":56,"DECR_WRAP=34056":57,"DELETE_STATUS=35712":58,"DEPTH_ATTACHMENT=36096":59,"DEPTH_BITS(3414)=null":60,"DEPTH_BUFFER_BIT=256":61,"DEPTH_CLEAR_VALUE(2931)=null":62,"DEPTH_COMPONENT16=33189":63,"DEPTH_COMPONENT=6402":64,"DEPTH_FUNC(2932)=null":65,"DEPTH_RANGE(2928)=null":66,"DEPTH_STENCIL=34041":67,"DEPTH_STENCIL_ATTACHMENT=33306":68,"DEPTH_TEST(2929)=null":69,"DEPTH_WRITEMASK(2930)=null":70,"DITHER(3024)=null":71,"DONT_CARE=4352":72,"DST_ALPHA=772":73,"DST_COLOR=774":74,"DYNAMIC_DRAW=35048":75,"ELEMENT_ARRAY_BUFFER=34963":76,"ELEMENT_ARRAY_BUFFER_BINDING=34965":77,"EQUAL=514":78,"FASTEST=4353":79,"FLOAT=5126":80,"FLOAT_MAT2=35674":81,"FLOAT_MAT3=35675":82,"FLOAT_MAT4=35676":83,"FLOAT_VEC2=35664":84,"FLOAT_VEC3=35665":85,"FLOAT_VEC4=35666":86,"FRAGMENT_SHADER=35632":87,"FRAMEBUFFER=36160":88,"FRAMEBUFFER_ATTACHMENT_OBJECT_NAME=36049":89,"FRAMEBUFFER_ATTACHMENT_OBJECT_TYPE=36048":90,"FRAMEBUFFER_ATTACHMENT_TEXTURE_CUBE_MAP_FACE=36051":91,"FRAMEBUFFER_ATTACHMENT_TEXTURE_LEVEL=36050":92,"FRAMEBUFFER_BINDING=36006":93,"FRAMEBUFFER_COMPLETE=36053":94,"FRAMEBUFFER_INCOMPLETE_ATTACHMENT=36054":95,"FRAMEBUFFER_INCOMPLETE_DIMENSIONS=36057":96,"FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT=36055":97,"FRAMEBUFFER_UNSUPPORTED=36061":98,"FRONT=1028":99,"FRONT_AND_BACK=1032":100,"FRONT_FACE(2886)=null":101,"FUNC_ADD=32774":102,"FUNC_REVERSE_SUBTRACT=32779":103,"FUNC_SUBTRACT=32778":104,"GENERATE_MIPMAP_HINT(33170)=null":105,"GEQUAL=518":106,"GREATER=516":107,"GREEN_BITS(3411)=null":108,"HIGH_FLOAT=36338":109,"HIGH_INT=36341":110,"IMPLEMENTATION_COLOR_READ_FORMAT(35739)=null":111,"IMPLEMENTATION_COLOR_READ_TYPE(35738)=null":112,"INCR=7682":113,"INCR_WRAP=34055":114,"INT=5124":115,"INT_VEC2=35667":116,"INT_VEC3=35668":117,"INT_VEC4=35669":118,"INVALID_ENUM=1280":119,"INVALID_FRAMEBUFFER_OPERATION=1286":120,"INVALID_OPERATION=1282":121,"INVALID_VALUE=1281":122,"INVERT=5386":123,"KEEP=7680":124,"LEQUAL=515":125,"LESS=513":126,"LINEAR=9729":127,"LINEAR_MIPMAP_LINEAR=9987":128,"LINEAR_MIPMAP_NEAREST=9985":129,"LINES=1":130,"LINE_LOOP=2":131,"LINE_STRIP=3":132,"LINE_WIDTH(2849)=null":133,"LINK_STATUS=35714":134,"LOW_FLOAT=36336":135,"LOW_INT=36339":136,"LUMINANCE=6409":137,"LUMINANCE_ALPHA=6410":138,"MAX_COMBINED_TEXTURE_IMAGE_UNITS(35661)=null":139,"MAX_CUBE_MAP_TEXTURE_SIZE(34076)=null":140,"MAX_FRAGMENT_UNIFORM_VECTORS(36349)=null":141,"MAX_RENDERBUFFER_SIZE(34024)=null":142,"MAX_TEXTURE_IMAGE_UNITS(34930)=null":143,"MAX_TEXTURE_SIZE(3379)=null":144,"MAX_VARYING_VECTORS(36348)=null":145,"MAX_VERTEX_ATTRIBS(34921)=null":146,"MAX_VERTEX_TEXTURE_IMAGE_UNITS(35660)=null":147,"MAX_VERTEX_UNIFORM_VECTORS(36347)=null":148,"MAX_VIEWPORT_DIMS(3386)=null":149,"MEDIUM_FLOAT=36337":150,"MEDIUM_INT=36340":151,"MIRRORED_REPEAT=33648":152,"NEAREST=9728":153,"NEAREST_MIPMAP_LINEAR=9986":154,"NEAREST_MIPMAP_NEAREST=9984":155,"NEVER=512":156,"NICEST=4354":157,"NONE=0":158,"NOTEQUAL=517":159,"NO_ERROR=0":160,"ONE=1":161,"ONE_MINUS_CONSTANT_ALPHA=32772":162,"ONE_MINUS_CONSTANT_COLOR=32770":163,"ONE_MINUS_DST_ALPHA=773":164,"ONE_MINUS_DST_COLOR=775":165,"ONE_MINUS_SRC_ALPHA=771":166,"ONE_MINUS_SRC_COLOR=769":167,"OUT_OF_MEMORY=1285":168,"PACK_ALIGNMENT(3333)=null":169,"POINTS=0":170,"POLYGON_OFFSET_FACTOR(32824)=null":171,"POLYGON_OFFSET_FILL(32823)=null":172,"POLYGON_OFFSET_UNITS(10752)=null":173,"RED_BITS(3410)=null":174,"RENDERBUFFER=36161":175,"RENDERBUFFER_ALPHA_SIZE=36179":176,"RENDERBUFFER_BINDING=36007":177,"RENDERBUFFER_BLUE_SIZE=36178":178,"RENDERBUFFER_DEPTH_SIZE=36180":179,"RENDERBUFFER_GREEN_SIZE=36177":180,"RENDERBUFFER_HEIGHT=36163":181,"RENDERBUFFER_INTERNAL_FORMAT=36164":182,"RENDERBUFFER_RED_SIZE=36176":183,"RENDERBUFFER_STENCIL_SIZE=36181":184,"RENDERBUFFER_WIDTH=36162":185,"RENDERER(7937)=null":186,"REPEAT=10497":187,"REPLACE=7681":188,"RGB565=36194":189,"RGB5_A1=32855":190,"RGB8=32849":191,"RGB=6407":192,"RGBA4=32854":193,"RGBA8=32856":194,"RGBA=6408":195,"SAMPLER_2D=35678":196,"SAMPLER_CUBE=35680":197,"SAMPLES(32937)=null":198,"SAMPLE_ALPHA_TO_COVERAGE(32926)=null":199,"SAMPLE_BUFFERS(32936)=null":200,"SAMPLE_COVERAGE(32928)=null":201,"SAMPLE_COVERAGE_INVERT(32939)=null":202,"SAMPLE_COVERAGE_VALUE(32938)=null":203,"SCISSOR_BOX(3088)=null":204,"SCISSOR_TEST(3089)=null":205,"SHADER_TYPE=35663":206,"SHADING_LANGUAGE_VERSION(35724)=null":207,"SHORT=5122":208,"SRC_ALPHA=770":209,"SRC_ALPHA_SATURATE=776":210,"SRC_COLOR=768":211,"STATIC_DRAW=35044":212,"STENCIL_ATTACHMENT=36128":213,"STENCIL_BACK_FAIL(34817)=null":214,"STENCIL_BACK_FUNC(34816)=null":215,"STENCIL_BACK_PASS_DEPTH_FAIL(34818)=null":216,"STENCIL_BACK_PASS_DEPTH_PASS(34819)=null":217,"STENCIL_BACK_REF(36003)=null":218,"STENCIL_BACK_VALUE_MASK(36004)=null":219,"STENCIL_BACK_WRITEMASK(36005)=null":220,"STENCIL_BITS(3415)=null":221,"STENCIL_BUFFER_BIT=1024":222,"STENCIL_CLEAR_VALUE(2961)=null":223,"STENCIL_FAIL(2964)=null":224,"STENCIL_FUNC(2962)=null":225,"STENCIL_INDEX8=36168":226,"STENCIL_PASS_DEPTH_FAIL(2965)=null":227,"STENCIL_PASS_DEPTH_PASS(2966)=null":228,"STENCIL_REF(2967)=null":229,"STENCIL_TEST(2960)=null":230,"STENCIL_VALUE_MASK(2963)=null":231,"STENCIL_WRITEMASK(2968)=null":232,"STREAM_DRAW=35040":233,"SUBPIXEL_BITS(3408)=null":234,"TEXTURE0=33984":235,"TEXTURE10=33994":236,"TEXTURE11=33995":237,"TEXTURE12=33996":238,"TEXTURE13=33997":239,"TEXTURE14=33998":240,"TEXTURE15=33999":241,"TEXTURE16=34000":242,"TEXTURE17=34001":243,"TEXTURE18=34002":244,"TEXTURE19=34003":245,"TEXTURE1=33985":246,"TEXTURE20=34004":247,"TEXTURE21=34005":248,"TEXTURE22=34006":249,"TEXTURE23=34007":250,"TEXTURE24=34008":251,"TEXTURE25=34009":252,"TEXTURE26=34010":253,"TEXTURE27=34011":254,"TEXTURE28=34012":255,"TEXTURE29=34013":256,"TEXTURE2=33986":257,"TEXTURE30=34014":258,"TEXTURE31=34015":259,"TEXTURE3=33987":260,"TEXTURE4=33988":261,"TEXTURE5=33989":262,"TEXTURE6=33990":263,"TEXTURE7=33991":264,"TEXTURE8=33992":265,"TEXTURE9=33993":266,"TEXTURE=5890":267,"TEXTURE_2D=3553":268,"TEXTURE_BINDING_2D=32873":269,"TEXTURE_BINDING_CUBE_MAP=34068":270,"TEXTURE_CUBE_MAP=34067":271,"TEXTURE_CUBE_MAP_NEGATIVE_X=34070":272,"TEXTURE_CUBE_MAP_NEGATIVE_Y=34072":273,"TEXTURE_CUBE_MAP_NEGATIVE_Z=34074":274,"TEXTURE_CUBE_MAP_POSITIVE_X=34069":275,"TEXTURE_CUBE_MAP_POSITIVE_Y=34071":276,"TEXTURE_CUBE_MAP_POSITIVE_Z=34073":277,"TEXTURE_MAG_FILTER=10240":278,"TEXTURE_MIN_FILTER=10241":279,"TEXTURE_WRAP_S=10242":280,"TEXTURE_WRAP_T=10243":281,"TRIANGLES=4":282,"TRIANGLE_FAN=6":283,"TRIANGLE_STRIP=5":284,"UNPACK_ALIGNMENT(3317)=null":285,"UNPACK_COLORSPACE_CONVERSION_WEBGL(37443)=null":286,"UNPACK_FLIP_Y_WEBGL(37440)=null":287,"UNPACK_PREMULTIPLY_ALPHA_WEBGL(37441)=null":288,"UNSIGNED_BYTE=5121":289,"UNSIGNED_INT=5125":290,"UNSIGNED_SHORT=5123":291,"UNSIGNED_SHORT_4_4_4_4=32819":292,"UNSIGNED_SHORT_5_5_5_1=32820":293,"UNSIGNED_SHORT_5_6_5=33635":294,"VALIDATE_STATUS=35715":295,"VENDOR(7936)=null":296,"VERSION(7938)=null":297,"VERTEX_ATTRIB_ARRAY_BUFFER_BINDING=34975":298,"VERTEX_ATTRIB_ARRAY_ENABLED=34338":299,"VERTEX_ATTRIB_ARRAY_NORMALIZED=34922":300,"VERTEX_ATTRIB_ARRAY_POINTER=34373":301,"VERTEX_ATTRIB_ARRAY_SIZE=34339":302,"VERTEX_ATTRIB_ARRAY_STRIDE=34340":303,"VERTEX_ATTRIB_ARRAY_TYPE=34341":304,"VERTEX_SHADER=35633":305,"VIEWPORT(2978)=null":306,"ZERO=0":307,"ACTIVE_TEXTURE=34016=33984":308,"ALIASED_LINE_WIDTH_RANGE=33902=1,1":309,"ALIASED_POINT_SIZE_RANGE=33901=1,511":310,"ALPHA_BITS=3413=8":311,"BLEND=3042=false":312,"BLEND_COLOR=32773=0,0,0,0":313,"BLEND_DST_ALPHA=32970=0":314,"BLEND_DST_RGB=32968=0":315,"BLEND_EQUATION=32777=32774":316,"BLEND_EQUATION_ALPHA=34877=32774":317,"BLEND_EQUATION_RGB=32777=32774":318,"BLEND_SRC_ALPHA=32971=1":319,"BLEND_SRC_RGB=32969=1":320,"BLUE_BITS=3412=8":321,"COLOR_CLEAR_VALUE=3106=0,0,0,0":322,"COLOR_WRITEMASK=3107=true,true,true,true":323,"COMPRESSED_TEXTURE_FORMATS=34467=":324,"CULL_FACE=2884=false":325,"CULL_FACE_MODE=2885=1029":326,"DEPTH_BITS=3414=24":327,"DEPTH_CLEAR_VALUE=2931=1":328,"DEPTH_FUNC=2932=513":329,"DEPTH_RANGE=2928=0,1":330,"DEPTH_TEST=2929=false":331,"DEPTH_WRITEMASK=2930=true":332,"DITHER=3024=true":333,"FRONT_FACE=2886=2305":334,"GENERATE_MIPMAP_HINT=33170=4352":335,"GREEN_BITS=3411=8":336,"IMPLEMENTATION_COLOR_READ_FORMAT=35739=6408":337,"IMPLEMENTATION_COLOR_READ_TYPE=35738=5121":338,"LINE_WIDTH=2849=1":339,"MAX_COMBINED_TEXTURE_IMAGE_UNITS=35661=32":340,"MAX_CUBE_MAP_TEXTURE_SIZE=34076=16384":341,"MAX_FRAGMENT_UNIFORM_VECTORS=36349=1024":342,"MAX_RENDERBUFFER_SIZE=34024=16384":343,"MAX_TEXTURE_IMAGE_UNITS=34930=16":344,"MAX_TEXTURE_SIZE=3379=16384":345,"MAX_VARYING_VECTORS=36348=30":346,"MAX_VERTEX_ATTRIBS=34921=16":347,"MAX_VERTEX_TEXTURE_IMAGE_UNITS=35660=16":348,"MAX_VERTEX_UNIFORM_VECTORS=36347=1024":349,"MAX_VIEWPORT_DIMS=3386=16384,16384":350,"PACK_ALIGNMENT=3333=4":351,"POLYGON_OFFSET_FACTOR=32824=0":352,"POLYGON_OFFSET_FILL=32823=false":353,"POLYGON_OFFSET_UNITS=10752=0":354,"RED_BITS=3410=8":355,"RENDERER=7937=WebKit WebGL":356,"SAMPLES=32937=4":357,"SAMPLE_ALPHA_TO_COVERAGE=32926":358,"SAMPLE_BUFFERS=32936=1":359,"SAMPLE_COVERAGE=32928":360,"SAMPLE_COVERAGE_INVERT=32939=false":361,"SAMPLE_COVERAGE_VALUE=32938=1":362,"SCISSOR_BOX=3088=0,0,300,150":363,"SCISSOR_TEST=3089=false":364,"SHADING_LANGUAGE_VERSION=35724=WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)":365,"STENCIL_BACK_FAIL=34817=7680":366,"STENCIL_BACK_FUNC=34816=519":367,"STENCIL_BACK_PASS_DEPTH_FAIL=34818=7680":368,"STENCIL_BACK_PASS_DEPTH_PASS=34819=7680":369,"STENCIL_BACK_REF=36003=0":370,"STENCIL_BACK_VALUE_MASK=36004=4294967295":371,"STENCIL_BACK_WRITEMASK=36005=4294967295":372,"STENCIL_BITS=3415=0":373,"STENCIL_CLEAR_VALUE=2961=0":374,"STENCIL_FAIL=2964=7680":375,"STENCIL_FUNC=2962=519":376,"STENCIL_PASS_DEPTH_FAIL=2965=7680":377,"STENCIL_PASS_DEPTH_PASS=2966=7680":378,"STENCIL_REF=2967=0":379,"STENCIL_TEST=2960=false":380,"STENCIL_VALUE_MASK=2963=4294967295":381,"STENCIL_WRITEMASK=2968=4294967295":382,"SUBPIXEL_BITS=3408=4":383,"UNPACK_ALIGNMENT=3317=4":384,"UNPACK_COLORSPACE_CONVERSION_WEBGL=37443=37444":385,"UNPACK_FLIP_Y_WEBGL=37440=false":386,"UNPACK_PREMULTIPLY_ALPHA_WEBGL=37441=false":387,"VENDOR=7936=WebKit":388,"VERSION=7938=WebGL 1.0 (OpenGL ES 2.0 Chromium)":389,"VIEWPORT=2978=0,0,300,150":390,"FRAGMENT_SHADER.LOW_FLOAT=127,127,23":391,"FRAGMENT_SHADER.MEDIUM_FLOAT=127,127,23":392,"FRAGMENT_SHADER.HIGH_FLOAT=127,127,23":393,"FRAGMENT_SHADER.LOW_INT=31,30,0":394,"FRAGMENT_SHADER.MEDIUM_INT=31,30,0":395,"FRAGMENT_SHADER.HIGH_INT=31,30,0":396,"VERTEX_SHADER.LOW_FLOAT=127,127,23":397,"VERTEX_SHADER.MEDIUM_FLOAT=127,127,23":398,"VERTEX_SHADER.HIGH_FLOAT=127,127,23":399,"VERTEX_SHADER.LOW_INT=31,30,0":400,"VERTEX_SHADER.MEDIUM_INT=31,30,0":401,"VERTEX_SHADER.HIGH_INT=31,30,0":402,ANGLE_instanced_arrays:403,EXT_blend_minmax:404,EXT_clip_control:405,EXT_color_buffer_half_float:406,EXT_depth_clamp:407,EXT_disjoint_timer_query:408,EXT_float_blend:409,EXT_frag_depth:410,EXT_polygon_offset_clamp:411,EXT_shader_texture_lod:412,EXT_texture_compression_bptc:413,EXT_texture_compression_rgtc:414,EXT_texture_filter_anisotropic:415,EXT_texture_mirror_clamp_to_edge:416,EXT_sRGB:417,KHR_parallel_shader_compile:418,OES_element_index_uint:419,OES_fbo_render_mipmap:420,OES_standard_derivatives:421,OES_texture_float:422,OES_texture_float_linear:423,OES_texture_half_float:424,OES_texture_half_float_linear:425,OES_vertex_array_object:426,WEBGL_blend_func_extended:427,WEBGL_color_buffer_float:428,WEBGL_compressed_texture_astc:429,WEBGL_compressed_texture_etc:430,WEBGL_compressed_texture_etc1:431,WEBGL_compressed_texture_pvrtc:432,WEBGL_compressed_texture_s3tc:433,WEBGL_compressed_texture_s3tc_srgb:434,WEBGL_debug_renderer_info:435,WEBGL_debug_shaders:436,WEBGL_depth_texture:437,WEBGL_draw_buffers:438,WEBGL_lose_context:439,WEBGL_multi_draw:440,WEBGL_polygon_mode:441,"CLIP_DEPTH_MODE_EXT=37725":442,"CLIP_ORIGIN_EXT=37724":443,"COLOR_ATTACHMENT0_WEBGL=36064":444,"COLOR_ATTACHMENT10_WEBGL=36074":445,"COLOR_ATTACHMENT11_WEBGL=36075":446,"COLOR_ATTACHMENT12_WEBGL=36076":447,"COLOR_ATTACHMENT13_WEBGL=36077":448,"COLOR_ATTACHMENT14_WEBGL=36078":449,"COLOR_ATTACHMENT15_WEBGL=36079":450,"COLOR_ATTACHMENT1_WEBGL=36065":451,"COLOR_ATTACHMENT2_WEBGL=36066":452,"COLOR_ATTACHMENT3_WEBGL=36067":453,"COLOR_ATTACHMENT4_WEBGL=36068":454,"COLOR_ATTACHMENT5_WEBGL=36069":455,"COLOR_ATTACHMENT6_WEBGL=36070":456,"COLOR_ATTACHMENT7_WEBGL=36071":457,"COLOR_ATTACHMENT8_WEBGL=36072":458,"COLOR_ATTACHMENT9_WEBGL=36073":459,"COMPLETION_STATUS_KHR=37297":460,"COMPRESSED_R11_EAC=37488":461,"COMPRESSED_RED_GREEN_RGTC2_EXT=36285":462,"COMPRESSED_RED_RGTC1_EXT=36283":463,"COMPRESSED_RG11_EAC=37490":464,"COMPRESSED_RGB8_ETC2=37492":465,"COMPRESSED_RGB8_PUNCHTHROUGH_ALPHA1_ETC2=37494":466,"COMPRESSED_RGBA8_ETC2_EAC=37496":467,"COMPRESSED_RGBA_ASTC_10x10_KHR=37819":468,"COMPRESSED_RGBA_ASTC_10x5_KHR=37816":469,"COMPRESSED_RGBA_ASTC_10x6_KHR=37817":470,"COMPRESSED_RGBA_ASTC_10x8_KHR=37818":471,"COMPRESSED_RGBA_ASTC_12x10_KHR=37820":472,"COMPRESSED_RGBA_ASTC_12x12_KHR=37821":473,"COMPRESSED_RGBA_ASTC_4x4_KHR=37808":474,"COMPRESSED_RGBA_ASTC_5x4_KHR=37809":475,"COMPRESSED_RGBA_ASTC_5x5_KHR=37810":476,"COMPRESSED_RGBA_ASTC_6x5_KHR=37811":477,"COMPRESSED_RGBA_ASTC_6x6_KHR=37812":478,"COMPRESSED_RGBA_ASTC_8x5_KHR=37813":479,"COMPRESSED_RGBA_ASTC_8x6_KHR=37814":480,"COMPRESSED_RGBA_ASTC_8x8_KHR=37815":481,"COMPRESSED_RGBA_BPTC_UNORM_EXT=36492":482,"COMPRESSED_RGBA_PVRTC_2BPPV1_IMG=35843":483,"COMPRESSED_RGBA_PVRTC_4BPPV1_IMG=35842":484,"COMPRESSED_RGBA_S3TC_DXT1_EXT=33777":485,"COMPRESSED_RGBA_S3TC_DXT3_EXT=33778":486,"COMPRESSED_RGBA_S3TC_DXT5_EXT=33779":487,"COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT=36494":488,"COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT=36495":489,"COMPRESSED_RGB_ETC1_WEBGL=36196":490,"COMPRESSED_RGB_PVRTC_2BPPV1_IMG=35841":491,"COMPRESSED_RGB_PVRTC_4BPPV1_IMG=35840":492,"COMPRESSED_RGB_S3TC_DXT1_EXT=33776":493,"COMPRESSED_SIGNED_R11_EAC=37489":494,"COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT=36286":495,"COMPRESSED_SIGNED_RED_RGTC1_EXT=36284":496,"COMPRESSED_SIGNED_RG11_EAC=37491":497,"COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR=37851":498,"COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR=37848":499,"COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR=37849":500,"COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR=37850":501,"COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR=37852":502,"COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR=37853":503,"COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR=37840":504,"COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR=37841":505,"COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR=37842":506,"COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR=37843":507,"COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR=37844":508,"COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR=37845":509,"COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR=37846":510,"COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR=37847":511,"COMPRESSED_SRGB8_ALPHA8_ETC2_EAC=37497":512,"COMPRESSED_SRGB8_ETC2=37493":513,"COMPRESSED_SRGB8_PUNCHTHROUGH_ALPHA1_ETC2=37495":514,"COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT=36493":515,"COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT=35917":516,"COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT=35918":517,"COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT=35919":518,"COMPRESSED_SRGB_S3TC_DXT1_EXT=35916":519,"CURRENT_QUERY_EXT=34917":520,"DEPTH_CLAMP_EXT=34383":521,"DRAW_BUFFER0_WEBGL(34853)=1029":522,"DRAW_BUFFER10_WEBGL=34863":523,"DRAW_BUFFER11_WEBGL=34864":524,"DRAW_BUFFER12_WEBGL=34865":525,"DRAW_BUFFER13_WEBGL=34866":526,"DRAW_BUFFER14_WEBGL=34867":527,"DRAW_BUFFER15_WEBGL=34868":528,"DRAW_BUFFER1_WEBGL(34854)=1029":529,"DRAW_BUFFER2_WEBGL=34855":530,"DRAW_BUFFER3_WEBGL=34856":531,"DRAW_BUFFER4_WEBGL=34857":532,"DRAW_BUFFER5_WEBGL=34858":533,"DRAW_BUFFER6_WEBGL=34859":534,"DRAW_BUFFER7_WEBGL=34860":535,"DRAW_BUFFER8_WEBGL=34861":536,"DRAW_BUFFER9_WEBGL=34862":537,"FRAGMENT_SHADER_DERIVATIVE_HINT_OES(35723)=4352":538,"FRAMEBUFFER_ATTACHMENT_COLOR_ENCODING_EXT=33296":539,"FRAMEBUFFER_ATTACHMENT_COMPONENT_TYPE_EXT=33297":540,"HALF_FLOAT_OES=36193":541,"LOWER_LEFT_EXT=36001":542,"MAX_COLOR_ATTACHMENTS_WEBGL(36063)=8":543,"MAX_DRAW_BUFFERS_WEBGL(34852)=8":544,"MAX_DUAL_SOURCE_DRAW_BUFFERS_WEBGL=35068":545,"MAX_EXT=32776":546,"MAX_TEXTURE_MAX_ANISOTROPY_EXT=34047":547,"MIN_EXT=32775":548,"MIRROR_CLAMP_TO_EDGE_EXT=34627":549,"NEGATIVE_ONE_TO_ONE_EXT=37726":550,"ONE_MINUS_SRC1_ALPHA_WEBGL=35067":551,"ONE_MINUS_SRC1_COLOR_WEBGL=35066":552,"POLYGON_OFFSET_CLAMP_EXT=36379":553,"QUERY_COUNTER_BITS_EXT=34916":554,"QUERY_RESULT_AVAILABLE_EXT=34919":555,"QUERY_RESULT_EXT=34918":556,"RGB16F_EXT=34843":557,"RGBA16F_EXT=34842":558,"RGBA32F_EXT=34836":559,"SRC1_ALPHA_WEBGL=34185":560,"SRC1_COLOR_WEBGL=35065":561,"SRGB8_ALPHA8_EXT=35907":562,"SRGB_ALPHA_EXT=35906":563,"SRGB_EXT=35904":564,"TEXTURE_MAX_ANISOTROPY_EXT=34046":565,"TIMESTAMP_EXT(36392)=0":566,"TIME_ELAPSED_EXT=35007":567,"UNMASKED_RENDERER_WEBGL=37446":568,"UNMASKED_VENDOR_WEBGL=37445":569,"UNSIGNED_INT_24_8_WEBGL=34042":570,"UNSIGNED_NORMALIZED_EXT=35863":571,"UPPER_LEFT_EXT=36002":572,"VERTEX_ARRAY_BINDING_OES(34229)=null":573,"VERTEX_ATTRIB_ARRAY_DIVISOR_ANGLE=35070":574,"ZERO_TO_ONE_EXT=37727":575,"DRAW_BUFFER0_WEBGL=34853=1029":576,"DRAW_BUFFER1_WEBGL=34854=1029":577,"FRAGMENT_SHADER_DERIVATIVE_HINT_OES=35723=4352":578,"MAX_COLOR_ATTACHMENTS_WEBGL=36063=8":579,"MAX_DRAW_BUFFERS_WEBGL=34852=8":580,"MAX_TEXTURE_MAX_ANISOTROPY_EXT=34047=16":581,"TIMESTAMP_EXT=36392=0":582,"VERTEX_ARRAY_BINDING_OES=34229=null":583,"ALIASED_POINT_SIZE_RANGE=33901=1,64":584,"MAX_COMBINED_TEXTURE_IMAGE_UNITS=35661=80":585,"MAX_CUBE_MAP_TEXTURE_SIZE=34076=8192":586,"MAX_RENDERBUFFER_SIZE=34024=8192":587,"MAX_TEXTURE_SIZE=3379=8192":588,"MAX_VARYING_VECTORS=36348=32":589,"RENDERER=7937=Apple M1, or similar":590,"SHADING_LANGUAGE_VERSION=35724=WebGL GLSL ES 1.0":591,"VENDOR=7936=Mozilla":592,"VERSION=7938=WebGL 1.0":593,"FRAGMENT_SHADER.LOW_INT=24,24,0":594,"FRAGMENT_SHADER.MEDIUM_INT=24,24,0":595,"FRAGMENT_SHADER.HIGH_INT=24,24,0":596,"VERTEX_SHADER.LOW_INT=24,24,0":597,"VERTEX_SHADER.MEDIUM_INT=24,24,0":598,"VERTEX_SHADER.HIGH_INT=24,24,0":599,WEBGL_provoking_vertex:600,"DRAW_BUFFER1_WEBGL(34854)=0":601,"FIRST_VERTEX_CONVENTION_WEBGL=36429":602,"LAST_VERTEX_CONVENTION_WEBGL=36430":603,"PROVOKING_VERTEX_WEBGL=36431":604,"RGB32F_EXT=34837":605,"DRAW_BUFFER1_WEBGL=34854=0":606,"SHADING_LANGUAGE_VERSION=35724=WebGL GLSL ES 1.0 (1.0)":607,WEBKIT_WEBGL_compressed_texture_pvrtc:608
};
const m=J((function( {
  cache:u
}) {
  const r=D(u);
  if(!r)return -1;
  if(!v(r))return -2;
  const V=r.getSupportedExtensions(),N=r.getContextAttributes(),k=[],R=[],x=[],A=[],S=[];
  if(N)for(const h of Object.keys(N))R.push(`${h}=${N[h]}`);
  const L=Y(r);
  for(const h of L) {
    const u=r[h];
    x.push(`${h}=${u}${f.has(u)?`=${r.getParameter(u)}`:""}`);
  }
  if(V)for(const U of V) {
    if(U===O&&Bu()||"WEBGL_polygon_mode"===U&&(Ju()||h()))continue;
    const u=r.getExtension(U);
    if(u)for(const V of Y(u)) {
      const N=u[V];
      A.push(`${V}=${N}${y.has(N)?`=${r.getParameter(N)}`:""}`);
    } else k.push(U);
  }
  for(const h of b)for(const u of W) {
    const V=U(r,h,u);
    S.push(`${h}.${u}=${V.join(",")}`);
  }
  return A.sort(),x.sort(), {
    contextAttributes:R,parameters:x,shaderPrecisions:S,extensions:V,extensionParameters:A,unsupportedExtensions:k
  }

}));
async function j(u) {
  if("undefined"==typeof CompressionStream)return [false,u];
  const[r,V]=function() {
    try {
      return [true,new CompressionStream("deflate-raw")]
    } catch(u) {
      return [false,new CompressionStream("deflate")]
    }

  }
  (),N=await async function(u,r) {
    const V=r.writable.getWriter();
    V.write(u),V.close();
    const N=r.readable.getReader(),h=[];
    let k=0;
    for(;;) {
      const {
        value:u,done:r
      }
      =await N.read();
      if(r)break;
      h.push(u),k+=u.byteLength;
    }
    if(1===h.length)return h[0];
    const R=new Uint8Array(k);
    let U=0;
    for(const x of h)R.set(x,U),U+=x.byteLength;
    return R
  }
  (u,V),h=r?N:function(u) {
    return new Uint8Array(u.buffer,u.byteOffset+p,u.byteLength-(p+G))
  }
  (N);
  return [true,h]
}
function v(u) {
  return "function"==typeof u.getParameter
}
const uu=34,ru=48,Vu=101,Nu=117,hu=45,ku=new Uint8Array([110,Nu,108,108]),Ru=new Uint8Array([116,114,Nu,Vu]),Uu=new Uint8Array([102,97,108,115,Vu]),xu= {
  '"':'"',"\\":"\\","\b":"b","\f":"f","\n":"n","\r":"r","\t":"t"
},Au=(()=> {
  const u=new Uint8Array(128);
  for(const[r,V]of Object.entries(xu))u[V.charCodeAt(0)]=r.charCodeAt(0);
  return u
})(),Du=new Uint32Array(2);
var Su=Z([1461986338,4081446820,3060249855,2434448380,2536213192,2636940027,3510472393,2868956552,2670113008,2417663949,2167505355,3748103115,2803739270,2586414331,2250682580,2535097288,2452724941,3508571338,2868956552,2619781360,2889318600,2502138566,2501549505,2267316424,3060253574,2417671164,2167047115,2502987259,2889321154,2502528716,2619967995,3748109253,2803739270,2636811515,2235009751,2234293189,2518790337,3509427156,2868956552,2518790384,2888670164,2653193159,3513372116,2886842337,2570487488,2267776715,2653723643,2182782401,2318895825,3060253574,2535111676,2620366029,2888925645,2519238352,2251600086,2889653697,2485619411,3748126152,2803739270,2619967995,2434440133,2536213192,3060253574,2501557244,2887945942,2268433088,3513372108,2886842337,2317975764,2888532163,2149812683,2417662913,2200473288,3060253574,2166012924,2518778305,2637607126,3509099979,2868956552,2704716016,3748113891,2803739270,2452462843,2889321152,2268957392,2887818705,3508633800,2868956552,2519838960,2167446492,2619781313,2520227785,2620169431,2200416458,3748105424,2803739270,2334170107,2520226512,2653588731,2149621204,2636809943,2267192827,3513372103,2886842337,2268957392,2887818705,2267645634,2451217857,2620819146,2200608208,3748105421,2803739270,2334170107,2520226512,2167177979,2889318614,2653193159,2620502228,2485226235,3513372097,2886842337,2268957392,2887818705,2654437578,3748125077,2702025862,2166661115,2519303109,2604052680,2166393797,2653588731,2519303892,3177694086,2604052722,2166393797,2200601083,2201394625,2586938561,2585430738,2166397898,2452193492,2636809936,3160916870,2535111905,2603720641,2334170107,2520226512,3160916870,2518334689,2519239368,2585435082,2334165962,2636946171,3513372112,2887166699,2888469954,2536213206,2652544449,2452135885,3513372116,2887166699,2636422103,2537000640,2166393851,2267322829,2149620173,3160916870,2266676449,2251397057,2501544662,2267316424,3160916870,2266676449,2251397057,2501544662,2267316424,2636940283,3510079169,3054161288,2519838967,2167446492,2452467905,2501544392,2267316424,3160916870,2266676449,2251397057,2602207958,2888008645,2452259778,2586423504,2166655690,3160916870,2233122017,2519834049,2166665436,2889649878,2519698891,3748109255,2684395654,2453113851,2250748115,2166393282,2636951767,2520615616,3513372096,2887166699,2200473303,2233109192,2452397509,2149614534,3160916870,2149235937,2518781644,2250813654,2150407112,2671084229,2636951745,2201455312,2267317195,3509289165,2768948616,2250813686,2234293192,3241315021,2758263686,3204623841,2519305723,2501544906,2888204753,2519832513,2535492554,2758263686,3204623841,2586414331,2250682580,2535097288,2452724941,3508571338,3054685576,2886314214,2619965639,2250748118,2166393282,2619967995,3748109253,2969614470,2417664995,2167767755,2520161473,2519838912,2167446492,2149888193,3748105424,2969614470,2417664995,2167767755,2520161473,2519838912,2167446492,2267066561,3513372103,3020401395,2619781352,2520227785,2535496919,2334170107,2520226512,2419165947,3513372053,3020401395,2619781352,2520227785,2535496919,2334170107,2520226512,2167644155,3748105424,2969614470,2417664995,2167767755,2520161473,2519838912,2167446492,3224809665,3748105424,2969614470,2417664995,2167767755,2520161473,2519838912,2167446492,3224809665,2149223632,3509029078,3054685576,2886314214,2250738368,2520232131,2166393802,2585435585,3509225930,3054685576,2886314214,2250738368,2604052675,2166393797,3513372119,3020401395,2518790376,2888670164,2268957392,3508575697,3054685576,2886314214,2216992192,2502987259,2151123650,2758263686,3204623841,2453113851,2636951763,2636422103,2887879367,2520157894,2166397435,2889714384,2520157894,2150336251,2418773712,3513372097,3020401395,2518855912,2250748112,2166393282,2435882235,2267319291,2149888197,3508961757,3054685576,2886314214,2520154312,2636811515,2268957392,2758263686,3204623841,2670756603,2535098064,3509751510,3054685576,2886314214,2267650761,2166468813,2585434309,2452724938,2535492810,2758263686,3204623841,2670756603,2535098064,2888994518,2268496333,2519105989,2452074688,2233109207,2519834049,2452074716,2585430743,2452724938,3508571338,3054685576,2886314214,2267650761,2519505357,3513372115,3020401395,2620764392,2619512520,2619912394,3748104896,2969614470,2199561187,2620621014,2485880527,2166397435,3510471376,3054685576,2886314214,2536213206,2149227969,2520223436,2334175424,2519433428,3748109258,2969614470,2149229539,2518781644,2587209942,2888403676,2451996872,2268508360,2485427659,3513372097,3020401395,2268508392,2586214849,2519838920,2167446492,3508699597,3054685576,2886314214,2518779602,2519838923,2167446492,3513372097,3020401395,2519904488,2536148166,2889256129,2518779602,2166599883,3508568773,3054685576,2802623718,2969614587,2417664995,2167767755,2520161473,2519838912,2167446492,2234888385,3508968406,2422719481,2267318998,2519313089,2267777737,2422719366,2452849093,3513372119,2485619411,2926042568],4);
const Lu=Su(0),au=new Map;
for(let wu=0;wu<Lu.length;wu++)L(au,3860080092)(Lu[wu],wu);
function ou(u) {
  if(u instanceof Array)return u.map(ou);
  if(u&&"object"==typeof u) {
    const r= {

    };
    for(const V of Object.keys(u))r[V]=ou(u[V]);
    return r
  }
  return u
}
function Cu(u,r) {
  return new Promise((V=>t(V,u,r)))
}
var qu=Z([2883259659,2550605763,1387096069,1716888695,2791916199,1134977858,626847525,2474525352,95122246,625795389,2888108990,1152808009,1951704676,2888109025,1437688393,721793384,2724353505,1320251459,721790579,2892719585,1559176517,2002695973,3778872742,1270052678,1934008430,3966322858,1119315016,1934945907,2925937329,99580421,1749331304,2792052654,199320147,1665772069,2808242086,199312739,1900457253,3076931754,2061595976],3);
const Mu="s",du=2,Iu=120;
function Zu(u) {
  return o(u,"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
}
async function tu() {
  const u=function(u,r,V) {
    return u(r,V)
  },r=function(u,r) {
    return u!==r
  },V=function(u,r) {
    return u!==r
  };
  var N;
  try {
    const h=await u(L,u(L,navigator,1417288500),3538568711)();
    return r(N=u(L,h,3505086064),null)&&V(N,undefined)?N:0
  } catch(h) {
    return 0
  }

}
var Yu=Z([2349388240,2966887570,1894840652,3914854885,4160643051,1761405304,2926638053,3890888382,1978068850,3510566115],3);
const _u=function() {
  return  {
    key:"ex",ab:u,sources: {
      stage2: {
        exp_s1013:a,exp_s1014:yu
      },stage3: {
        exp_s1015:Wu,exp_s1016:gu
      }

    },toRequest:()=>( {
      epv:r
    })
  }

};
async function yu() {
  const u=function(u,r) {
    return u!==r
  },r=function(u,r,V) {
    return u(r,V)
  },V=function(u,r) {
    return u(r)
  },N=window[function(u,r) {
    return u(r)
  }
  (Yu,0)];
  if(!N||u(typeof r(L,N,3192107409),V(Yu,1)))return  {
    s:-1,v:null
  };
  return  {
    s:0,v:await r(L,N,3192107409)()
  }

}
function bu(u) {
  return u.reduce(((u,r)=>u+(r?1:0)),0)
}
async function Wu(u) {
  const r=m(u);
  if("number"==typeof r)return  {
    s:r,v:null
  };
  const V=[_(r.contextAttributes),_(r.parameters),_(r.parameters2),_(r.shaderPrecisions),_(r.extensions),_(r.extensionParameters),_(r.extensionParameters2),r.unsupportedExtensions],N=JSON.stringify(V),h=(new TextEncoder).encode(N),[k,R]=await j(h);
  if(!k)return  {
    s:-3,v:null
  };
  const U=function(u) {
    const r=P(u),V=Math.ceil(r.length/B$1),N=[];
    for(let h=0;h<V;h++) {
      const u=h*B$1,V=r.slice(u,Math.min(u+B$1,r.length));
      N.push(String.fromCharCode.apply(null,V));
    }
    return btoa(N.join(""))
  }
  (R);
  return U.length>4096? {
    s:-4,v:null
  }
  : {
    s:0,v:U
  }

}
function Ou(u) {
  const r=new Uint8Array(u.length);
  for(let V=0;V<u.length;V++) {
    const N=u.charCodeAt(V);
    if(N>127)return (new TextEncoder).encode(u);
    r[V]=N;
  }
  return r
}
function Ju() {
  const u=window,r=navigator;
  return bu(["webkitPersistentStorage"in r,"webkitTemporaryStorage"in r,0===(r.vendor||"").indexOf("Google"),"webkitResolveLocalFileSystemURL"in u,"BatteryManager"in u,"webkitMediaStream"in u,"webkitSpeechGrammar"in u])>=5
}
function gu() {
  const u=function(u,r) {
    return u(r)
  },r=function(u,r) {
    return u(r)
  },V=function(u,r,V) {
    return u(r,V)
  },N=function(u,r) {
    return u!==r
  },h=function(u,r) {
    return u/r
  },k=function(u,r,V) {
    return u(r,V)
  },R=function(u,r) {
    return u===r
  },U=function(u,r) {
    return u|r
  },x=function(u,r) {
    return u/r
  },A=function(u,r) {
    return u&r
  },D=function(u,r) {
    return u>>>r
  },S=function(u,r) {
    return u|r
  },a=function(u,r) {
    return u<<r
  };
  var o;
  const C=V(L,document[u(Su,1)](r(Su,2)),1590906722)(u(Su,3));
  if(!C)return  {
    s:-1,v:null
  };
  const q=N(o=V(L,C,3313063598)(),null)&&N(o,undefined)?o:[],M=Math.ceil(h(Lu.length,32)),d=new Uint32Array(M);
  let I=false;
  for(const Z of q) {
    const u=k(L,au,4248514160)(Z);
    if(R(u,undefined)) {
      I=true;
      continue
    }
    const r=U(x(u,32),0),V=A(u,31);
    d[r]=D(S(d[r],a(1,V)),0);
  }
  return I? {
    s:-2,v: {
      b:d
    }

  }
  : {
    s:0,v: {
      b:d
    }

  }

}
function Bu() {
  return i()
}
function B(n) {
  return Promise.resolve().then((function() {
    var i= {
      region:"us"
    };
    if(n)for(var t in n)n.hasOwnProperty(t)&&undefined!==n[t]&&(i[t]=n[t]);
    return i.apiKey="xx-fpjs-api-token-xx",i.imi= {
      m:"e"
    },i.modules=[Gl(),_u(),Jl(),Ao()],i
  })).then(iu)
}
export {
  tf as ERROR_API_KEY_EXPIRED,nf as ERROR_API_KEY_INVALID,Ql as ERROR_API_KEY_MISSING,ef as ERROR_BAD_REQUEST_FORMAT,xe as ERROR_BAD_RESPONSE_FORMAT,Ce as ERROR_CLIENT_TIMEOUT,Te as ERROR_CSP_BLOCK,Ze as ERROR_FORBIDDEN_ENDPOINT,sf as ERROR_FORBIDDEN_HEADER,cf as ERROR_FORBIDDEN_ORIGIN,rf as ERROR_GENERAL_SERVER_FAILURE,_e as ERROR_HANDLE_AGENT_DATA,We as ERROR_INSTALLATION_METHOD_RESTRICTED,Ge as ERROR_INTEGRATION_FAILURE,Oe as ERROR_INVALID_ENDPOINT,$e as ERROR_INVALID_PROXY_INTEGRATION_HEADERS,Be as ERROR_INVALID_PROXY_INTEGRATION_SECRET,Pe as ERROR_NETWORK_ABORT,Le as ERROR_NETWORK_CONNECTION,Ue as ERROR_NETWORK_RESTRICTED,Ye as ERROR_PROXY_INTEGRATION_SECRET_ENVIRONMENT_MISMATCH,uf as ERROR_RATE_LIMIT,of as ERROR_SERVER_TIMEOUT,Fe as ERROR_SUBSCRIPTION_NOT_ACTIVE,ff as ERROR_TOKEN_EXPIRED,lf as ERROR_TOKEN_INVALID,af as ERROR_TOKEN_MISSING,De as ERROR_UNSUPPORTED_VERSION,Me as ERROR_WRONG_REGION,Zt as defaultEndpoint,Ht as defaultTlsEndpoint,uu$1 as handleAgentData,B as load
};
