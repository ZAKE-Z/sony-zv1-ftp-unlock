
#ifdef _WIN32
#define fsync _commit
#define HOST_BINARY 0x8000
#else
#define HOST_BINARY 0
#endif
extern int open(const char*,int,...),close(int),fsync(int),strcmp(const char*,const char*);
extern long read(int,void*,unsigned),write(int,const void*,unsigned),lseek(int,long,int);
int probe_init(void){return 0;}
struct Patch{long offset;unsigned size;const unsigned char *old,*neu;};
static const unsigned char old0[]={4,75,5,74};
static const unsigned char new0[]={2,32,112,71};
static const struct Patch plan[]={{0x1a2e24,4,old0,new0}};
static void say(const char*s){unsigned n=0;while(s[n])n++;write(1,s,n);}
static int fetch(int fd,const struct Patch*p,unsigned char*b){return lseek(fd,p->offset,0)==p->offset && read(fd,b,p->size)==p->size;}
static int store(int fd,const struct Patch*p,const unsigned char*b){return lseek(fd,p->offset,0)==p->offset && write(fd,b,p->size)==p->size;}
static int equal(const unsigned char*a,const unsigned char*b,unsigned n){unsigned i;for(i=0;i<n;i++)if(a[i]!=b[i])return 0;return 1;}
int main(int argc,char**argv){
 unsigned char b[512];unsigned i,j,n=sizeof(plan)/sizeof(plan[0]);int fd,mode=0,done=0;
 if(argc!=3){say("LIFE_ARGS\n");return 2;}
 if(!strcmp(argv[2],"apply"))mode=1;
 else if(!strcmp(argv[2],"restore"))mode=2;
 else if(strcmp(argv[2],"check")){say("LIFE_MODE\n");return 2;}
 fd=open(argv[1],(mode?2:0)|HOST_BINARY,0);if(fd<0){say("LIFE_OPEN\n");return 3;}
 /* Validate the entire transaction before any write. Restore also accepts a
    partially applied plan, byte-by-byte old/new, after interrupted writes. */
 for(i=0;i<n;i++){
  if(plan[i].size>sizeof(b)||!fetch(fd,&plan[i],b)){say("LIFE_READ\n");close(fd);return 4;}
  for(j=0;j<plan[i].size;j++)if(mode==2 ? (b[j]!=plan[i].old[j]&&b[j]!=plan[i].neu[j]) : b[j]!=plan[i].old[j]){say("LIFE_MISMATCH_NO_WRITE\n");close(fd);return 5;}
 }
 if(!mode){say("LIFE_CHECK_OK\n");close(fd);return 0;}
 for(i=0;i<n;i++){
  unsigned k=mode==2?n-1-i:i;
  done=i+1;
  if(!store(fd,&plan[k],mode==2?plan[k].old:plan[k].neu))goto failed;
 }
 if(fsync(fd))goto failed;
 for(i=0;i<n;i++)if(!fetch(fd,&plan[i],b)||!equal(b,mode==2?plan[i].old:plan[i].neu,plan[i].size))goto failed;
 say(mode==2?"LIFE_RESTORED\n":"LIFE_APPLIED\n");close(fd);return 0;
failed:
 if(mode==1){
  int ok=1;
  while(done){unsigned k=(unsigned)--done;if(!store(fd,&plan[k],plan[k].old))ok=0;}
  if(fsync(fd))ok=0;
  for(i=0;i<n;i++)if(!fetch(fd,&plan[i],b)||!equal(b,plan[i].old,plan[i].size))ok=0;
  say(ok?"LIFE_FAILED_RESTORED\n":"LIFE_FAILED_RESTORE_UNKNOWN\n");
 }else say("LIFE_RESTORE_FAILED\n");
 close(fd);return 6;
}
