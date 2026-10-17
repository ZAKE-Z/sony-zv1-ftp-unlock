/* Read-only native probe. Fresh process avoids an old NSS failure cache. */
extern int printf(const char*,...),strcmp(const char*,const char*);
extern void *dlopen(const char*,int),*dlsym(void*,const char*);
extern const char *dlerror(void);
extern int dlclose(void*);
struct addrinfo {int flags,family,socktype,protocol;unsigned addrlen;void *addr;char *canon;struct addrinfo *next;};
extern int getaddrinfo(const char*,const char*,const struct addrinfo*,struct addrinfo**);
extern void freeaddrinfo(struct addrinfo*);
extern const char *gai_strerror(int);
int probe_init(void){return 0;}
int main(int argc,char **argv){
 void *handle=dlopen("libnss_dns.so.2",2);
 if(!handle){printf("NSS_DNS_LOAD_FAILED:%s\n",dlerror());return 3;}
 if(!dlsym(handle,"_nss_dns_gethostbyname4_r")){printf("NSS_DNS_SYMBOL_MISSING\n");dlclose(handle);return 4;}
 printf("NSS_DNS_LOAD_OK\n");dlclose(handle);
 if(argc<2||!strcmp(argv[1],"--module-only"))return 0;
 struct addrinfo hints={0,2,1,0,0,0,0,0},*result=0,*entry;
 int code=getaddrinfo(argv[1],"21",&hints,&result);
 printf("GAI_CODE:%d GAI_TEXT:%s\n",code,gai_strerror(code));
 if(code)return 5;
 for(entry=result;entry;entry=entry->next)if(entry->family==2&&entry->addr&&entry->addrlen>=8){
  unsigned char *ip=(unsigned char*)entry->addr+4;
  printf("GAI_IPV4:%u.%u.%u.%u\n",ip[0],ip[1],ip[2],ip[3]);
 }
 freeaddrinfo(result);return 0;
}
