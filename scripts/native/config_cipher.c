extern int strcmp(const char*,const char*);
extern int write(int,const void*,unsigned);
extern int read(int,void*,unsigned);
extern int open(const char*,int,...);
extern int close(int);
extern void *dlopen(const char*,int);
extern void *dlsym(void*,const char*);
extern int dlclose(void*);
extern char*dlerror(void);
extern int __cxa_atexit(void(*)(void*),void*,void*);
void probe_init(void){}
static int(*exit_os)(void);
static void os_cleanup(void*unused){if(exit_os)exit_os();}
static void say(const char*s){unsigned n=0;if(!s)return;while(s[n])n++;write(1,s,n);}
static unsigned char plain[1024],cipher[1024],decoded[1024];
int main(int argc,char**argv){
 if(argc!=4)return 2;
 int mode=!strcmp(argv[3],"encrypt")?1:!strcmp(argv[3],"decrypt")?0:-1;
 if(mode<0)return 2;
 int fd=open(argv[1],0);if(fd<0)return 3;
 int n=read(fd,plain,1024);close(fd);if(n!=1024)return 4;
 void*os=dlopen("/usr/lib/libosal_uipc.so",258);if(!os){say("OS_LOAD_FAIL\n");say(dlerror());say("\n");return 5;}
 int(*init)(void)=dlsym(os,"u_osal_init");
 int(*wait)(unsigned,int)=dlsym(os,"osal_wai_sem_tmo");
 int(*signal)(unsigned)=dlsym(os,"osal_sig_sem");
 if(!init||!wait||!signal)return 6;
 if(init()!=0){say("OS_INIT_FAIL\n");return 7;}
 exit_os=dlsym(os,"u_osal_exit");
 __cxa_atexit(os_cleanup,0,0);
 void*crypto=dlopen("/usr/lib/libcrypto.so.1.1",258);
 void*skd=dlopen("/usr/lib/libInfraSKD.so",258);
 void*bk=dlopen("/usr/lib/libbackup.so",258);
 if(!crypto||!skd||!bk){say("DEPENDENCY_LOAD_FAIL\n");say(dlerror());say("\n");return 8;}
 void*h=dlopen("/usr/lib/libBackupManager.so",2);if(!h){say("CRYPTO_LOAD_FAIL\n");say(dlerror());say("\n");return 8;}
 int(*update)(void*,int,unsigned char*,unsigned char*,int)=dlsym(h,"_ZNK13BackupManager13BackupManager12cipherUpdateEiPhS1_i");
 if(!update)return 9;
 unsigned base=(unsigned)update-0xc5d;
 int(*begin)(int*,int)=(void*)(base+0xc01);
 int(*end)(int)=(void*)(base+0xbc5);
 // A bounded semaphore probe avoids entering the library's infinite wait
 // when the existing cipher service is unavailable. Never register SKData.
 int r=wait(0x25907cd,0);if(r!=0){say("CRYPTO_SEMAPHORE_UNAVAILABLE\n");return 10;}
 if(signal(0x25907cd)!=0)return 11;
 for(unsigned i=0;i<4;i++){
  int ctx=0;r=begin(&ctx,mode);
  if(r!=0){end(ctx);say("ENCRYPT_CONTEXT_FAIL\n");return 12;}
  r=update(0,ctx,cipher+256*i,plain+256*i,256);
  int ended=end(ctx);if(r||ended){say("ENCRYPT_FAIL\n");return 13;}
  ctx=0;r=begin(&ctx,1-mode);
  if(r!=0){end(ctx);say("DECRYPT_CONTEXT_FAIL\n");return 14;}
  r=update(0,ctx,decoded+256*i,cipher+256*i,256);
  ended=end(ctx);if(r||ended){say("DECRYPT_FAIL\n");return 15;}
 }
 for(unsigned i=0;i<1024;i++)if(plain[i]!=decoded[i]){say("ROUNDTRIP_FAIL\n");return 16;}
 fd=open(argv[2],1|64|128,0600);if(fd<0)return 17;
 n=write(fd,cipher,1024);close(fd);if(n!=1024)return 18;
 for(unsigned i=0;i<1024;i++){plain[i]=0;decoded[i]=0;cipher[i]=0;}
 say("CIPHER_ROUNDTRIP_VERIFIED\n");return 0;
}
