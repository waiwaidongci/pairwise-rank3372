import {useState} from 'react';
import {researchStore,queueSensitivity,selectSensitivity} from '../stores/research';
import {authStore,canEdit} from '../stores/auth';
import {useTask} from '../hooks/useTask';
import {num,date} from '../utils/format';
import {runStatus} from '../constants/enums';
import StatusBadge from './common/StatusBadge';
import ErrorNotice from './common/ErrorNotice';
import type {Run} from '../types/domain';
const deltaText=(d:number)=>Math.abs(d)<1e-9?'不变':d>0?`后退 ${num(d,1)} 位`:`前进 ${num(-d,1)} 位`;
const deltaClass=(d:number)=>Math.abs(d)<1e-9?'':d>0?'delta-up':'delta-down';
export default function OmissionPanel({run}:{run:Run}){
const {sensitivities,selectedSensitivity}=researchStore.use(),{user}=authStore.use(),{error,busy,perform}=useTask(),[name,setName]=useState(run.name+' · 逐对剔除');
const items=sensitivities.filter(s=>s.run_id===run.id),current=items.find(s=>s.id===selectedSensitivity)||items[0];
const r=current?.status==='completed'?current.result:null;
const ok=r?r.pairs.filter(p=>p.status==='ok').sort((a,b)=>(b.max_abs_delta!-a.max_abs_delta!)||(b.total_abs_delta!-a.total_abs_delta!)||a.edge-b.edge):[];
const disc=r?r.pairs.filter(p=>p.status==='disconnected'):[],failed=r?r.pairs.filter(p=>p.status==='failed'):[];
const form=<form className="omission-form" onSubmit={e=>{e.preventDefault();perform(async()=>{await queueSensitivity({name,run_id:run.id});setName(run.name+' · 逐对剔除 '+new Date().toLocaleTimeString())})}}>
<label>诊断名称<input value={name} onChange={e=>setName(e.target.value)} minLength={2} maxLength={140} required/></label>
<p className="muted">沿用 #{run.id} 冻结快照与原参数：λ {run.ridge} · seed {run.seed} · {run.repeats}次重拟合；{run.snapshot.pairs.length}条比较边逐对剔除重算。只读快照，台账后续改票不影响本诊断；原研究与补票依据保持不变。</p>
<button className="primary" disabled={busy||!canEdit(user)}>{busy?'提交中…':'排队逐对剔除诊断 →'}</button>
{!canEdit(user)&&<p className="margin-note">观察员可读取诊断留档；请策展分析员排队。</p>}</form>;
return <section>
<h2 className="ruled-title">逐对剔除诊断 <small>哪一对在左右名次</small></h2>
<p className="muted">把每一对比较暂时移出冻结快照，用原参数重算能力与名次：名次变化最大的作品对排在前面。剔除后图断连时只列分组、不排总名次；单对重算失败单独标出，不混入稳定结论。</p>
<ErrorNotice error={error}/>
{items.length>0&&<label className="run-selector">诊断留档<select aria-label="选择逐对剔除诊断" value={current?.id||0} onChange={e=>selectSensitivity(Number(e.target.value))}>{items.map(s=><option key={s.id} value={s.id}>#{s.id} {s.name} · {runStatus[s.status]}</option>)}</select></label>}
{!items.length&&<div className="empty"><h2>还没有逐对剔除诊断。</h2><p>基于当前已完成研究的冻结快照排队一项诊断；原研究留档与补票依据不受影响。</p></div>}
{!items.length&&form}
{current&&!r&&<div className="empty"><StatusBadge status={current.status}/><h2>{current.name}</h2><p>{current.error||'诊断仍在队列中。完成后每对前后差异会自动出现。'}</p></div>}
{r&&current&&<>
<div className="result-byline"><b>#{current.id}　{current.name}</b><span>依据 #{r.parent.run_id} {r.parent.run_name} 冻结快照 · λ {r.ridge} · seed {r.seed} · {r.repeats}次重拟合 · {date(current.created_at)}</span></div>
<div className="result-metrics"><div><small>逐对剔除</small><b>{r.summary.pairs_total}</b><span>比较对逐一重算</span></div><div><small>可重算</small><b>{r.summary.pairs_ok}</b><span>进入影响排序</span></div><div><small>断连分组</small><b>{r.summary.pairs_disconnected}</b><span>只列分组不排总名次</span></div><div><small>单对失败</small><b>{r.summary.pairs_failed}</b><span>不纳入稳定结论</span></div></div>
{ok.length===0&&<aside className="margin-note"><b>没有可重算的作品对</b><p>所有剔除都断连或失败时，不存在可排序的影响结论；请阅读下方分组与失败记录。</p></aside>}
{ok.length>0&&<>
<h3 className="ruled-title">影响最大的作品对 <small>按最大名次变化排序</small></h3>
<div className="result-metrics">{ok.slice(0,3).map((p,k)=><div key={p.edge}><small>第{k+1}影响 · {p.votes}票</small><b>{num(p.max_abs_delta!,1)}</b><span>最大名次变化（位）<br/>{p.left_code} × {p.right_code} · {p.most_moved} 变动最大</span></div>)}</div>
<h3 className="ruled-title">每对前后对照 <small>{ok.length}对可重算 · 展开查看各作品名次</small></h3>
<div className="omission-fold">{ok.map(p=><details key={p.edge}>
<summary><span><b>{p.left_code} × {p.right_code}</b><small>{p.left_title} × {p.right_title} · {p.votes}票 · 左胜{p.left_wins}票</small></span><span className="delta-cell"><b className={deltaClass(p.max_abs_delta!)}>{num(p.max_abs_delta!,1)} 位</b><small>最大名次变化</small></span><span className="delta-cell"><b>{p.most_moved}</b><small>变动最大作品</small></span></summary>
<div className="table-scroll"><table><thead><tr><th>作品</th><th>剔除前名次</th><th>剔除后名次</th><th>名次变化</th><th>剔除后 2.5%–97.5%</th></tr></thead><tbody>{r.concepts.map((c,i)=><tr key={c.id} className={c.code===p.most_moved?'most-moved':''}><td><b>{c.code}</b><small>{c.title}</small></td><td>{num(r.baseline.ranks[i],1)}</td><td>{num(p.ranks_after![i],1)}</td><td className={deltaClass(p.rank_delta![i])}>{deltaText(p.rank_delta![i])}</td><td>{num(p.rank_low![i],1)} – {num(p.rank_high![i],1)}</td></tr>)}</tbody></table></div>
</details>)}</div>
</>}
{disc.length>0&&<>
<h3 className="ruled-title">剔除后断连的作品对 <small>{disc.length}对 · 只列分组，不排总名次</small></h3>
<p className="muted">移出该对后比较图分成互不相连的分组；组间没有共同名次，不强行合并排序，也不进入影响排序。</p>
{disc.map(p=><div className="omission-disc" key={p.edge}><p><b>{p.left_code} × {p.right_code}</b>　{p.left_title} × {p.right_title} · {p.votes}票</p><div className="omission-groups">{p.groups!.map((g,k)=><div key={k}><small>分组{k+1} · {g.length}项作品</small><p>{g.map(x=>x.code+' '+x.title).join('、')}</p></div>)}</div></div>)}
</>}
{failed.length>0&&<>
<h3 className="ruled-title">单对失败 <small>{failed.length}对 · 不纳入稳定结论</small></h3>
<p className="muted">剔除该对后重算未达一阶条件；该对单独标出，不与可重算对混合排序。</p>
{failed.map(p=><div className="omission-disc" key={p.edge}><p><b>{p.left_code} × {p.right_code}</b>　{p.left_title} × {p.right_title} · {p.votes}票</p><p className="error-text">{p.error}</p></div>)}
</>}
<div className="result-boundary"><span>诊断边注</span><p>{r.scope}。{r.interval}。重采样：{r.resampling}。</p><a href="#/proposals" className="text-link">依据影响结构提出补票 →</a></div>
<div className="fingerprint">诊断指纹 <code>{r.fingerprint}</code><br/>父研究指纹 <code>{r.parent.fingerprint}</code></div>
</>}
{items.length>0&&canEdit(user)&&<details className="edit-fold"><summary>再排一项逐对剔除诊断</summary>{form}</details>}
</section>
}
