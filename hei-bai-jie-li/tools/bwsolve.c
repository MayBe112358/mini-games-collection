/* 黑白接力 快速求解器 / 关卡生成器
 * 规则同 solver.py：黑只能走白格并染黑，白相反；轮流（黑先）；不能进对方格；
 * 到终点即锁定；两人都到终点胜；轮到的人无路可走即卡死；星星任一小人踩到即得。
 *
 * gen  W H SEED_START COUNT  -> 每个可三星通关的随机关卡输出一行 JSON
 * solve                     -> 从 stdin 读关卡行，输出同样的 JSON（用于复核）
 *   关卡行格式: W H cells(# . x) bs ws bg wg s1 s2 s3
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

#define MAXC 36
#define LIMIT 600000
static int W, H, N;
static char cells[MAXC];
static int bs, ws_, bg, wg, st[3];
static int nb[MAXC][4];

static uint64_t *hkeys; static int32_t *hval; static uint64_t hcap;
static uint64_t *S; static int32_t *par; static int8_t *pdir; static int32_t *dist;
static int32_t *succ; static uint8_t *win; static int ns;

static uint64_t rng;
static double rnd(void){ rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17; return (rng >> 11) * (1.0/9007199254740992.0); }

static uint64_t enc(uint64_t mask, int b, int w, int t, int sm){ return mask | ((uint64_t)b<<36) | ((uint64_t)w<<42) | ((uint64_t)t<<48) | ((uint64_t)sm<<49); }
static uint64_t hh(uint64_t k){ k ^= k>>33; k *= 0xff51afd7ed558ccdULL; k ^= k>>33; k *= 0xc4ceb9fe1a85ec53ULL; k ^= k>>33; return k; }
static int find_or_add(uint64_t k, int *isnew){
  uint64_t i = hh(k) & (hcap-1);
  while (hval[i] >= 0) { if (hkeys[i]==k){ *isnew=0; return hval[i]; } i=(i+1)&(hcap-1); }
  if (ns >= LIMIT) return -2;
  hkeys[i]=k; hval[i]=ns; S[ns]=k; *isnew=1; return ns++;
}

static void build_nb(void){
  int dx[4]={0,1,0,-1}, dy[4]={-1,0,1,0};
  for(int i=0;i<N;i++){ int x=i%W,y=i/W; for(int d=0;d<4;d++){ int nx=x+dx[d],ny=y+dy[d];
    nb[i][d] = (nx<0||ny<0||nx>=W||ny>=H||cells[ny*W+nx]=='#') ? -1 : ny*W+nx; } }
}

/* 返回 0 成功，-1 无三星解，-2 超限 */
static int L3, L0, critical, nstates; static double goodfrac; static uint64_t visited;
static int path[4096], plen;
static int solve(void){
  build_nb();
  memset(hval, 0xff, sizeof(int32_t)*hcap); ns=0;
  uint64_t mask=0; for(int i=0;i<N;i++) if(cells[i]=='x') mask|=1ULL<<i;
  mask |= 1ULL<<bs; mask &= ~(1ULL<<ws_);
  int sm=0; for(int k=0;k<3;k++) if(st[k]==bs||st[k]==ws_) sm|=1<<k;
  int isnew; int s0=find_or_add(enc(mask,bs,ws_,0,sm),&isnew);
  dist[0]=0; par[0]=-1; win[0]=0;
  int head=0; L3=-1; L0=-1; int fullwin=-1; visited=0;
  while(head<ns){
    int si=head++; uint64_t k=S[si];
    for(int d=0;d<4;d++) succ[si*4+d]=-1;
    if(win[si]) continue;
    uint64_t m=k&((1ULL<<36)-1); int b=(k>>36)&63, w=(k>>42)&63, t=(k>>48)&1, s=(k>>49)&7;
    visited |= 1ULL<<b; visited |= 1ULL<<w;
    int bl=(b==bg), wl=(w==wg);
    if(t==0&&bl) t=1; if(t==1&&wl) t=0;
    int cur=t?w:b, oth=t?b:w;
    for(int d=0;d<4;d++){
      int n=nb[cur][d]; if(n<0||n==oth) continue;
      int blk=(m>>n)&1; if(t==0&&blk) continue; if(t==1&&!blk) continue;
      uint64_t nm = t==0 ? (m|(1ULL<<n)) : (m&~(1ULL<<n));
      int nsm=s; for(int q=0;q<3;q++) if(st[q]==n) nsm|=1<<q;
      int nbp=t==0?n:b, nwp=t==0?w:n;
      int iw = (nbp==bg && nwp==wg);
      int idx=find_or_add(enc(nm,nbp,nwp,1-t,nsm),&isnew);
      if(idx==-2) return -2;
      succ[si*4+d]=idx;
      if(isnew){ dist[idx]=dist[si]+1; par[idx]=si; pdir[idx]=d; win[idx]=iw;
        if(iw){ visited|=1ULL<<nbp; visited|=1ULL<<nwp;
          if(L0<0) L0=dist[idx]; if(nsm==7 && L3<0){ L3=dist[idx]; fullwin=idx; } } }
    }
  }
  nstates=ns;
  if(L3<0) return -1;
  /* 反向求 good：能到达三星胜利的状态 */
  int32_t *cnt=calloc(ns+1,4), *rev=malloc(sizeof(int32_t)*ns*4); uint8_t *good=calloc(ns,1);
  for(int i=0;i<ns;i++) for(int d=0;d<4;d++){ int j=succ[i*4+d]; if(j>=0) cnt[j+1]++; }
  for(int i=0;i<ns;i++) cnt[i+1]+=cnt[i];
  int32_t *pos=malloc(4*(ns+1)); memcpy(pos,cnt,4*(ns+1));
  for(int i=0;i<ns;i++) for(int d=0;d<4;d++){ int j=succ[i*4+d]; if(j>=0) rev[pos[j]++]=i; }
  int32_t *q=malloc(4*ns); int qh=0,qt=0;
  for(int i=0;i<ns;i++) if(win[i] && ((S[i]>>49)&7)==7){ good[i]=1; q[qt++]=i; }
  while(qh<qt){ int j=q[qh++]; for(int r=cnt[j];r<cnt[j+1];r++){ int p=rev[r]; if(!good[p]){ good[p]=1; q[qt++]=p; } } }
  int ng=0, nn=0; for(int i=0;i<ns;i++) if(!win[i]){ nn++; if(good[i]) ng++; }
  goodfrac = nn? (double)ng/nn : 0;
  /* 路径与关键抉择 */
  plen=0; for(int x=fullwin; par[x]>=0; x=par[x]) path[plen++]=pdir[x];
  for(int a=0,b2=plen-1;a<b2;a++,b2--){ int t=path[a]; path[a]=path[b2]; path[b2]=t; }
  critical=0;
  for(int x=par[fullwin]; x>=0; x=par[x]){
    int legal=0, bad=0;
    for(int d=0;d<4;d++){ int j=succ[x*4+d]; if(j>=0){ legal++; if(!good[j]) bad++; } }
    if(legal>=2 && bad>0) critical++;
  }
  free(cnt); free(rev); free(good); free(pos); free(q);
  return 0;
}

static void emit(void){
  printf("{\"w\":%d,\"h\":%d,\"c\":\"",W,H);
  for(int i=0;i<N;i++) putchar(cells[i]);
  printf("\",\"bs\":%d,\"ws\":%d,\"bg\":%d,\"wg\":%d,\"st\":[%d,%d,%d],\"L\":%d,\"L0\":%d,\"crit\":%d,\"good\":%.4f,\"states\":%d,\"vis\":\"",
    bs,ws_,bg,wg,st[0],st[1],st[2],L3,L0,critical,goodfrac,nstates);
  for(int i=0;i<N;i++) putchar((visited>>i)&1?'1':'0');
  printf("\",\"path\":\"");
  for(int i=0;i<plen;i++) putchar('0'+path[i]);
  printf("\"}\n");
}

int main(int argc, char**argv){
  hcap=1<<21; hkeys=malloc(8*hcap); hval=malloc(4*hcap);
  S=malloc(8*LIMIT); par=malloc(4*LIMIT); pdir=malloc(LIMIT); dist=malloc(4*LIMIT);
  succ=malloc(4*4*LIMIT); win=malloc(LIMIT);
  if(argc>1 && !strcmp(argv[1],"solve")){
    char buf[64];
    while(scanf("%d %d %63s %d %d %d %d %d %d %d",&W,&H,buf,&bs,&ws_,&bg,&wg,&st[0],&st[1],&st[2])==10){
      N=W*H; memcpy(cells,buf,N);
      int r=solve(); if(r==0) emit(); else printf("{\"fail\":%d}\n",r);
    }
    return 0;
  }
  W=atoi(argv[2]); H=atoi(argv[3]); long s0=atol(argv[4]), cnt=atol(argv[5]); N=W*H;
  for(long sd=s0; sd<s0+cnt; sd++){
    rng = 0x9E3779B97F4A7C15ULL ^ (uint64_t)(sd*2654435761ULL + W*131 + H); for(int i=0;i<5;i++) rnd();
    double wallp = 0.05 + 0.25*rnd(), blackp = 0.3 + 0.3*rnd();
    int fr[MAXC], nf=0;
    for(int i=0;i<N;i++){ double r=rnd(); cells[i] = r<wallp ? '#' : (rnd()<blackp ? 'x':'.'); if(cells[i]!='#') fr[nf++]=i; }
    if(nf<7) continue;
    for(int i=0;i<7;i++){ int j=i+(int)(rnd()*(nf-i)); int t=fr[i]; fr[i]=fr[j]; fr[j]=t; }
    bs=fr[0]; ws_=fr[1]; bg=fr[2]; wg=fr[3]; st[0]=fr[4]; st[1]=fr[5]; st[2]=fr[6];
    cells[bs]='x'; cells[ws_]='.';
    if(solve()==0){ printf("{\"seed\":%ld,",sd); fflush(stdout);
      /* 复用 emit，去掉开头的 { */
      printf("\"w\":%d,\"h\":%d,\"c\":\"",W,H); for(int i=0;i<N;i++) putchar(cells[i]);
      printf("\",\"bs\":%d,\"ws\":%d,\"bg\":%d,\"wg\":%d,\"st\":[%d,%d,%d],\"L\":%d,\"L0\":%d,\"crit\":%d,\"good\":%.4f,\"states\":%d,\"vis\":\"",
        bs,ws_,bg,wg,st[0],st[1],st[2],L3,L0,critical,goodfrac,nstates);
      for(int i=0;i<N;i++) putchar((visited>>i)&1?'1':'0');
      printf("\",\"path\":\""); for(int i=0;i<plen;i++) putchar('0'+path[i]); printf("\"}\n");
    }
  }
  return 0;
}
