"use strict";exports.id=1373,exports.ids=[1373],exports.modules={1373:(e,r,t)=>{t.d(r,{Z:()=>createLucideIcon});var s=t(6689);/**
 * @license lucide-react v0.441.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */let toKebabCase=e=>e.replace(/([a-z0-9])([A-Z])/g,"$1-$2").toLowerCase(),mergeClasses=(...e)=>e.filter((e,r,t)=>!!e&&t.indexOf(e)===r).join(" ");/**
 * @license lucide-react v0.441.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */var a={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor",strokeWidth:2,strokeLinecap:"round",strokeLinejoin:"round"};/**
 * @license lucide-react v0.441.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */let o=(0,s.forwardRef)(({color:e="currentColor",size:r=24,strokeWidth:t=2,absoluteStrokeWidth:o,className:i="",children:l,iconNode:c,...d},n)=>(0,s.createElement)("svg",{ref:n,...a,width:r,height:r,stroke:e,strokeWidth:o?24*Number(t)/Number(r):t,className:mergeClasses("lucide",i),...d},[...c.map(([e,r])=>(0,s.createElement)(e,r)),...Array.isArray(l)?l:[l]])),createLucideIcon=(e,r)=>{let t=(0,s.forwardRef)(({className:t,...a},i)=>(0,s.createElement)(o,{ref:i,iconNode:r,className:mergeClasses(`lucide-${toKebabCase(e)}`,t),...a}));return t.displayName=`${e}`,t}}};