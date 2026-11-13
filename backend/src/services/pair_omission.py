"""Leave-one-pair-out diagnosis on a frozen run snapshot.

Each registered pair is temporarily removed in turn and the ranking is
recomputed with the parent run's original parameters. The diagnosis reads
only the frozen snapshot, so later ledger edits never reach it. Disconnected
removals list their groups without a forced overall ranking, and single-pair
failures are marked separately instead of entering influence conclusions.
"""
import hashlib,json
import numpy as np
from src.services.comparison_graph import prepare_graph
from src.services.bt_solver import fit_bt,average_ranks

def components(n,edges):
    adj=[set() for _ in range(n)]
    for e in edges:adj[e['i']].add(e['j']);adj[e['j']].add(e['i'])
    seen=[False]*n;groups=[]
    for v in range(n):
        if seen[v]:continue
        seen[v]=True;group=[];stack=[v]
        while stack:
            x=stack.pop();group.append(x)
            for y in adj[x]:
                if not seen[y]:seen[y]=True;stack.append(y)
        groups.append(sorted(group))
    groups.sort(key=lambda g:(-len(g),g[0]))
    return groups

def diagnose_omissions(snapshot,ridge,repeats,seed,parent,heartbeat=None):
    concepts,edges,graph=prepare_graph(snapshot['concepts'],snapshot['pairs']);n=len(concepts)
    base_theta,diagnostic=fit_bt(n,edges,ridge);base_rank,_=average_ranks(base_theta)
    pairs=[]
    for pos,edge in enumerate(edges):
        remaining=[e for k,e in enumerate(edges) if k!=pos]
        left,right=concepts[edge['i']],concepts[edge['j']]
        entry={'edge':pos,'left_code':left['code'],'left_title':left['title'],'right_code':right['code'],'right_title':right['title'],'votes':edge['total'],'left_wins':edge['wins']}
        groups=components(n,remaining)
        if len(groups)>1:
            # A removed bridge splits the design: report the groups, never a forced joint ranking.
            entry['status']='disconnected'
            entry['groups']=[[{'code':concepts[v]['code'],'title':concepts[v]['title']} for v in g] for g in groups]
            pairs.append(entry)
        else:
            try:
                theta,fitdiag=fit_bt(n,remaining,ridge)
                rank,_=average_ranks(theta)
                # Per-edge derived stream: reproducible and independent of the parent
                # run's draws and of other omissions, so concurrent studies never mix.
                rng=np.random.default_rng(np.random.SeedSequence([seed,pos]))
                totals=np.array([e['total'] for e in remaining]);observed=np.array([e['wins']/e['total'] for e in remaining])
                ranks=[]
                for b in range(repeats):
                    wins=rng.binomial(totals,observed)
                    resampled=[{**e,'wins':int(w)} for e,w in zip(remaining,wins)]
                    values,_=fit_bt(n,resampled,ridge)
                    r,_=average_ranks(values);ranks.append(r)
                q=np.quantile(np.asarray(ranks),[.025,.975],axis=0)
                delta=rank-base_rank;moved=int(np.argmax(np.abs(delta)))
                entry.update(status='ok',abilities_after=[float(x) for x in theta],ranks_after=[float(x) for x in rank],
                    rank_delta=[float(x) for x in delta],rank_low=[float(x) for x in q[0]],rank_high=[float(x) for x in q[1]],
                    max_abs_delta=float(np.max(np.abs(delta))),total_abs_delta=float(np.sum(np.abs(delta))),
                    most_moved=concepts[moved]['code'],gradient_max=fitdiag['gradient_max'])
                pairs.append(entry)
            except Exception as exc:
                # Single-pair failure: marked and excluded from influence conclusions.
                pairs.append({**entry,'status':'failed','error':str(exc)[:300]})
        if heartbeat:heartbeat()
    ok=[p for p in pairs if p['status']=='ok']
    top=sorted(ok,key=lambda p:(-p['max_abs_delta'],-p['total_abs_delta'],p['edge']))
    summary={'pairs_total':len(pairs),'pairs_ok':len(ok),'pairs_disconnected':sum(1 for p in pairs if p['status']=='disconnected'),'pairs_failed':sum(1 for p in pairs if p['status']=='failed'),'top_influential':[p['edge'] for p in top[:5]]}
    canonical={'version':'leave-one-pair-out-v1','parent_fingerprint':parent.get('fingerprint',''),'snapshot':snapshot,'ridge':ridge,'repeats':repeats,'seed':seed}
    fingerprint=hashlib.sha256(json.dumps(canonical,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    return {'concepts':concepts,'parent':parent,'baseline':{'abilities':[float(x) for x in base_theta],'ranks':[float(x) for x in base_rank],'graph':graph,'diagnostic':diagnostic},'pairs':pairs,'summary':summary,'ridge':ridge,'repeats':repeats,'seed':seed,'fingerprint':fingerprint,'tie_rule':'average rank for abilities within 1e-8, same as the parent run','interval':'2.5%/97.5% empirical rank quantiles after omission, linearly interpolated; not posterior or simultaneous confidence limits','resampling':'per-omission stream derived from SeedSequence([seed, edge position]); independent Binomial(n_ij, observed wins_ij/n_ij), fixed pair totals','scope':'逐对剔除重算刻画单对票数的结构性影响；断连对只列分组不排总名次，失败对不进入影响排序；诊断只读冻结快照，台账后续改票不影响本结果'}
