.syntax unified
.arm
.text
.global _start
.type _start,%function
_start:
 mov r5,r0
 ldr r1,[sp]
 add r2,sp,#4
 mov r6,sp
 bic sp,sp,#7
 sub sp,sp,#16
 mov r4,#0
 str r4,[sp]
 str r5,[sp,#4]
 str r6,[sp,#8]
 ldr r0,=main
 ldr r3,=probe_init
 bl __libc_start_main
 mov r7,#1
 mov r0,#99
 svc #0
.size _start,.-_start
.section .note.GNU-stack,"",%progbits
.section .interp,"aR",%progbits
.asciz "/lib/ld-linux.so.3"
