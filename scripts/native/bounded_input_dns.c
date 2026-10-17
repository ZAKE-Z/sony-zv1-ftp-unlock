
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
static const unsigned char old0[]={176,181,0,175,90,73,5,70,70,246,224,238,72,246,242,239,4,70,0,40,0,240,171,128,213,248,80,51,154,30,4,42,64,242,152,128,7,43,11,209,69,246,158,238,1,70,99,32,69,246,150,234,32,70,69,246,152,238,1,70,77,72,146,224,8,43,11,209,69,246,144,238,1,70,100,32,69,246,136,234,32,70,69,246,138,238,1,70,71,72,132,224,9,43,11,209,69,246,130,238,1,70,101,32,69,246,122,234,32,70,69,246,124,238,1,70,65,72,118,224,10,43,11,209,69,246,116,238,1,70,102,32,69,246,108,234,32,70,69,246,110,238,1,70,59,72,104,224,11,43,11,209,69,246,102,238,1,70,103,32,69,246,94,234,32,70,69,246,96,238,1,70,53,72,90,224,12,43,11,209,69,246,88,238,1,70,104,32,69,246,80,234,32,70,69,246,82,238,1,70,47,72,76,224,13,43,11,209,69,246,74,238,1,70,105,32,69,246,66,234,32,70,69,246,68,238,1,70,41,72,62,224,14,43,11,209,69,246,60,238,1,70,106,32,69,246,52,234,32,70,69,246,54,238,1,70,35,72,48,224,15,43,11,209,69,246,46,238,1,70,107,32,69,246,38,234,32,70,69,246,40,238,1,70,29,72,34,224,17,43,4,209,69,246,32,238,1,70,27,72,27,224,18,43,15,208,19,43,4,209,69,246,24,238,1,70,23,72,18,224,20,43,4,209,69,246,16,238,1,70,21,72,11,224,21,43,5,209,32,70,69,246,8,238,1,70,18,72,3,224,69,246,4,238,1,70,16,72,189,232,176,64,69,246,219,189,176,189,184,238,178,3,57,25,7,1,58,25,7,1,59,25,7,1,62,28,7,1,63,28,7,1,64,28,7,1,65,28,7,1,66,28,7,1,67,28,7,1,82,28,7,1,207,28,7,1,213,28,7,1,35,25,7,1,238,19,7,1};
static const unsigned char new0[]={45,233,240,65,192,176,5,70,45,73,70,246,224,238,72,246,242,239,4,70,0,40,0,240,80,128,213,248,80,99,2,46,50,208,3,46,48,208,179,30,4,43,36,217,18,46,34,208,21,46,32,208,243,31,8,43,16,216,32,70,69,246,148,238,1,70,6,241,92,0,69,246,140,234,32,70,69,246,140,238,1,70,7,62,32,163,83,248,38,0,18,224,26,79,17,46,1,209,26,79,8,224,19,46,1,209,25,79,4,224,20,46,2,209,24,79,0,224,19,79,32,70,69,246,118,238,1,70,56,70,69,246,80,238,24,224,32,70,69,246,110,238,6,70,105,70,64,34,0,35,65,248,4,59,1,58,251,209,70,177,105,70,255,34,22,248,1,59,1,248,1,59,11,177,1,58,248,209,4,72,105,70,69,246,54,238,64,176,189,232,240,129,184,238,178,3,35,25,7,1,238,19,7,1,82,28,7,1,207,28,7,1,213,28,7,1,57,25,7,1,58,25,7,1,59,25,7,1,62,28,7,1,63,28,7,1,64,28,7,1,65,28,7,1,66,28,7,1,67,28,7,1,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191};
static const unsigned char old1[]={11,132,151,128};
static const unsigned char new1[]={176,172,63,128};
static const unsigned char old2[]={4,75,5,74};
static const unsigned char new2[]={2,32,112,71};
static const struct Patch plan[]={{0x228514,428,old0,new0},{0x2da560,4,old1,new1},{0x1a2e24,4,old2,new2}};
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
