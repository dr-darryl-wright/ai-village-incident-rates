import numpy as np, datetime as dt, json
M=["Oct","Nov","Dec","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug"]
mdays=np.array([31,30,31,31,28,31,30,31,30,31,31])
# CLTR incidents (Annex 1); Oct = 19 days, Aug = 9 days of collection
inc=np.array([53,109,97,121,246,293,233,204,158,306,103]); idays=np.array([19,30,31,31,28,31,30,31,30,31,9])
hi=np.array([0,1,2,4,9,16,10,16,7,18,8])
cc=np.array([23989032,21571991,21551967,27575444,30510428,44445736,49361496,34562178,44038610,49100543,82199042])
cx=np.array([1120267,1453966,1980311,2327895,5801153,14529757,31367293,239381470,46157876,62207401,74276500])
cx_may_adj=239381470-(45984321+44330985+33713297+33271172+23892370)+5*1419482
cxa=cx.copy(); cxa[7]=cx_may_adj
oc=np.array([0,0,0,261698,4441144,9039603,5772186,5812288,14271543,11796921,12711130])
# GitHub commits "Co-Authored-By: Claude": readings per month
gh={0:[901441,876558],1:[1044041,1017962],2:[1513865,1507414],3:[3075565,3203934],4:[5149143,4928127],5:[7831056,9220835],6:[9799376,7476782],7:[9650576,8905081],8:[13509185,10587969],9:[13016925,12106043],10:[11923059,7039349]}
ghm=np.array([np.mean(gh[i]) for i in range(11)]); ghlo=np.array([min(gh[i]) for i in range(11)]); ghhi=np.array([max(gh[i]) for i in range(11)])
# trends: assign each week to month of its midpoint (start+3 days)
tr={i:[] for i in range(11)}
for line in open('trends_raw.txt'):
    t,a,b,c=map(int,line.split()); d=dt.datetime.utcfromtimestamp(t)+dt.timedelta(days=3)
    key=(d.year,d.month); order=[(2025,10),(2025,11),(2025,12)]+[(2026,m) for m in range(1,9)]
    if key in order: tr[order.index(key)].append((a,b,c))
trm=np.array([np.mean(tr[i],axis=0) for i in range(11)])
print("codex May adjusted:",cx_may_adj)
series={"Incidents/day":inc/idays,"Claude Code npm/day":cc/mdays,"Codex npm/day (May adj)":cxa/mdays,"OpenClaw npm/day":oc/mdays,"Claude co-authored commits/day":ghm/mdays,"Trends claude code":trm[:,0],"Trends openclaw":trm[:,1],"Trends codex":trm[:,2]}
print(f"{'':32}"+"".join(f"{m:>9}" for m in M))
for k,v in series.items(): print(f"{k:32}"+"".join(f"{x:9.3g}" for x in v))
print("\nGrowth Nov->Jul (full months):")
for k,v in series.items():
    if v[1]>0: print(f"  {k:32} {v[9]/v[1]:6.1f}x")
print("\nStep Jan->Feb:")
for k,v in series.items():
    print(f"  {k:32} {v[4]/v[3]:6.2f}x" if v[3]>0 else f"  {k:32} from 0")
print("\nGitHub reading spread (max/min):",np.round(ghhi/ghlo,2))
# incidents per million commits
ipm=inc/idays/(ghm/mdays)*1e6
print("Incidents per million Claude co-authored commits:",dict(zip(M,np.round(ipm,1))))
print("  range from readings:",dict(zip(M,[f"{inc[i]/idays[i]/(ghhi[i]/mdays[i])*1e6:.1f}-{inc[i]/idays[i]/(ghlo[i]/mdays[i])*1e6:.1f}" for i in range(11)])))
json.dump({"months":M,"incidents_per_day":list(inc/idays),"commits_per_day":list(ghm/mdays),"commits_lo":list(ghlo/mdays),"commits_hi":list(ghhi/mdays),"cc":list(cc/mdays),"codex":list(cxa/mdays),"openclaw":list(oc/mdays),"trends":trm.tolist()},open('series.json','w'))
