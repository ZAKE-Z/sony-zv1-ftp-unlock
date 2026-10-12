
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
static const unsigned char old0[]={67,104,128,181};
static const unsigned char new0[]={243,241,87,185};
static const unsigned char old1[]={175,51,177,128,104};
static const unsigned char new1[]={191,0,191,0,191};
static const unsigned char old2[]={40,5,221,11,96,16,96,1,32,128,189,24,70,128,189};
static const unsigned char new2[]={191,0,191,0,191,0,191,0,191,0,191,0,191,0,191};
static const unsigned char old3[]={32,128,189};
static const unsigned char new3[]={191,0,191};
static const unsigned char old4[]={176,181,130,176,0,175,7,241,8,1,20,76,5,70,0,35,17,72,124,68,1,248,1,61,245,245,78,236,184,185,251,121,80,43,8,208,86,43,1,208,76,43,9,209,12,75,227,88,107,96,12,75,8,224,12,75,227,88,107,96,11};
static const unsigned char new4[]={2,75,123,68,67,96,3,35,131,96,112,71,214,145,48,0,67,104,75,177,128,104,0,40,6,221,3,40,200,191,3,32,11,96,16,96,1,32,112,71,0,32,112,71,208,248,0,192,14,75,123,68,156,69,1,209,255,247,234,191,12};
static const unsigned char old5[]={3,224,11,75,227,88,107,96,11,75,227,88,27,104,171,96,7,241,8,7,189,70,176,189,0,191,22,3,7,1,146,2,38,0,164,41,5,0,208,10,3,0,84,196,3,0,228,242,1};
static const unsigned char new5[]={123,68,156,69,1,209,0,240,94,184,10,75,123,68,156,69,1,209,0,240,198,184,67,104,51,177,128,104,0,40,3,221,11,96,16,96,1,32,112,71,0,32,112,71,0,191,82,0,38};
static const unsigned char old6[]={216,151,1};
static const unsigned char new6[]={222,252,37};
static const unsigned char old7[]={120,241,2};
static const unsigned char new7[]={226,224,37};
static const unsigned char old8[]={176,181,130,176,0,175,7,241,8,1,16,76,5,70,0,35,13,72,124,68,1,248,1,61,245,245,212,235,128,185,251,121,80,43,1,208,86,43,4,209,9,75,227,88,107,96,9,75,3,224,9,75,227,88,107,96,8,75,227,88,27,104,171,96,7,241,8,7,189,70,176,189,22,3,7,1,158,1,38,0,248,200,3,0,76,49,1,0,244,137,3,0,8,161};
static const unsigned char new8[]={2,75,123,68,67,96,2,35,131,96,112,71,242,148,48,0,67,104,107,177,128,104,0,40,10,221,3,40,1,209,4,51,2,32,2,40,200,191,2,32,11,96,16,96,1,32,112,71,0,32,112,71,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191};
static const unsigned char old9[]={0};
static const unsigned char new9[]={191};
static const unsigned char old10[]={176,181,130,176,0,175,7,241,8,1,16,76,5,70,0,35,13,72,124,68,1,248,1,61,245,245,102,235,128,185,251,121,80,43,1,208,86,43,4,209,9,75,227,88,107,96,9,75,3,224,9,75,227,88,107,96,8,75,227,88,27,104,171,96,7,241,8,7,189,70,176,189,22,3,7,1,194,0,38,0,12,182,4,0,152,160,1,0,216,177};
static const unsigned char new10[]={2,75,123,68,67,96,3,35,131,96,112,71,82,133,48,0,67,104,75,177,128,104,0,40,6,221,3,40,200,191,3,32,11,96,16,96,1,32,112,71,0,32,112,71,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191,0,191};
static const unsigned char old11[]={0,76,17,3,0};
static const unsigned char new11[]={191,0,191,0,191};
static const unsigned char old12[]={213,179};
static const unsigned char new12[]={37,169};
static const unsigned char old13[]={216,179};
static const unsigned char new13[]={59,169};
static const unsigned char old14[]={2};
static const unsigned char new14[]={0};
static const unsigned char old15[]={248};
static const unsigned char new15[]={249};
static const unsigned char old16[]={32};
static const unsigned char new16[]={14};
static const unsigned char old17[]={1};
static const unsigned char new17[]={249};
static const unsigned char old18[]={139};
static const unsigned char new18[]={194};
static const unsigned char old19[]={8,132,151};
static const unsigned char new19[]={176,176,176};
static const unsigned char old20[]={124,182,254,127};
static const unsigned char new20[]={176,176,176,128};
static const unsigned char old21[]={152,182,254,127};
static const unsigned char new21[]={176,176,176,128};
static const unsigned char old22[]={180,182,254,127};
static const unsigned char new22[]={176,176,176,128};
static const struct Patch plan[]={{0xabc0ca,4,old0,new0},{0xabc0cf,5,old1,new1},{0xabc0d5,15,old2,new2},{0xabc0e5,3,old3,new3},{0xcaf350,61,old4,new4},{0xcaf38e,49,old5,new5},{0xcaf3c0,3,old6,new6},{0xcaf3c4,3,old7,new7},{0xcaf444,94,old8,new8},{0xcaf4a3,1,old9,new9},{0xcaf520,90,old10,new10},{0xcaf57b,5,old11,new11},{0xe422f4,2,old12,new12},{0xe42300,2,old13,new13},{0xe4230c,1,old14,new14},{0xe42324,1,old15,new15},{0xe42328,1,old16,new16},{0xe42330,1,old17,new17},{0xe4233c,1,old18,new18},{0xe67004,3,old19,new19},{0xe7b0f4,4,old20,new20},{0xe7b114,4,old21,new21},{0xe7b134,4,old22,new22}};
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
