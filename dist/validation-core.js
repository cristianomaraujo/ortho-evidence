(function(root){
'use strict';
const decisions={record:['include','exclude','uncertain'],pair:['equivalent','partial','different','uncertain']};
function key(e){return [e.reviewer,e.kind,e.run,...e.ids.slice().sort()].join('|')}
function validate(e){
 if(!e||!['record','pair'].includes(e.kind)||!Array.isArray(e.ids)||e.ids.length!==(e.kind==='record'?1:2)||e.ids.some(id=>!/^\d+$/.test(id))||new Set(e.ids).size!==e.ids.length)throw Error('Referências inválidas.');
 if(typeof e.reviewer!=='string'||! /^[A-Za-z0-9_-]{2,40}$/.test(e.reviewer))throw Error('Use um código de avaliador com 2–40 letras, números, _ ou -.');
 if(!decisions[e.kind].includes(e.decision))throw Error('Escolha uma decisão.');
 if(typeof e.event_id!=='string'||!e.event_id||typeof e.run!=='string'||!e.run||!Number.isFinite(Date.parse(e.saved_at)))throw Error('Metadados inválidos.');
 if(!Array.isArray(e.hashes)||e.hashes.length!==e.ids.length||e.hashes.some(h=>typeof h!=='string'||!h))throw Error('Versão das referências ausente.');
 if(typeof e.notes!=='string'||e.notes.length>10000)throw Error('Observação inválida.');
 if(e.kind==='record'){
  if(typeof e.objective!=='string'||e.objective.length>20000||typeof e.reason!=='string')throw Error('Campos inválidos.');
  if(e.decision==='exclude'&&!e.reason.trim())throw Error('Informe o motivo da exclusão.');
  if(!['confirmed','corrected','unavailable','not_checked'].includes(e.objective_status)||!['confirmed','corrected','unavailable','not_checked'].includes(e.count_status))throw Error('Informe a situação das extrações.');
  if(e.count!==null&&(!Number.isInteger(e.count)||e.count<0||e.count>100000))throw Error('Número de estudos deve ser inteiro ou ficar vazio.');
  if(['confirmed','corrected'].includes(e.count_status)&&(e.count===null||!['studies','articles','trials','publications'].includes(e.unit)||!e.evidence.trim()))throw Error('Informe número, unidade e trecho de origem.');
  if(['confirmed','corrected'].includes(e.objective_status)&&!e.objective.trim())throw Error('Informe o objetivo conferido.');
  if(typeof e.evidence!=='string'||typeof e.unit!=='string')throw Error('Campos numéricos inválidos.');
 }
 return e;
}
function latest(events,reviewer,kind,run){let m=new Map();for(let e of events){if(e.reviewer===reviewer&&e.kind===kind&&e.run===run){let k=key(e),old=m.get(k);if(!old||e.saved_at>=old.saved_at)m.set(k,e)}}return [...m.values()]}
function merge(a,b){let m=new Map(a.map(e=>[e.event_id,e]));for(let e of b){validate(e);if(m.has(e.event_id)&&JSON.stringify(m.get(e.event_id))!==JSON.stringify(e))throw Error('Conflito no identificador de uma avaliação.');m.set(e.event_id,e)}return [...m.values()]}
function save(storage,events,event){validate(event);let next=merge(events,[event]);storage.setItem('orthoevidence.annotations.v1',JSON.stringify(next));return next}
const api={key,validate,latest,merge,save};root.ValidationCore=api;if(typeof module!=='undefined')module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
