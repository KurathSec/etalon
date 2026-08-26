    14a8:	41 55                	push   %r13
    14aa:	49 89 fd             	mov    %rdi,%r13
    14ad:	41 54                	push   %r12
    14af:	49 89 f4             	mov    %rsi,%r12
    14b2:	55                   	push   %rbp
    14b3:	31 ed                	xor    %ebp,%ebp
    14b5:	53                   	push   %rbx
    14b6:	31 db                	xor    %ebx,%ebx
    14b8:	51                   	push   %rcx
    14b9:	41 0f b6 34 2c       	movzbl (%r12,%rbp,1),%esi
    14be:	41 0f b6 7c 2d 00    	movzbl 0x0(%r13,%rbp,1),%edi
    14c4:	e8 a0 ff ff ff       	call   1469 <byte_work>
    14c9:	41 8a 44 2d 00       	mov    0x0(%r13,%rbp,1),%al
    14ce:	41 32 04 2c          	xor    (%r12,%rbp,1),%al
    14d2:	48 ff c5             	inc    %rbp
    14d5:	09 c3                	or     %eax,%ebx
    14d7:	48 83 fd 10          	cmp    $0x10,%rbp
    14db:	75 dc                	jne    14b9 <check_tag+0x11>
    14dd:	0f b6 c3             	movzbl %bl,%eax
    14e0:	5a                   	pop    %rdx
    14e1:	5b                   	pop    %rbx
    14e2:	ff c8                	dec    %eax
    14e4:	5d                   	pop    %rbp
    14e5:	41 5c                	pop    %r12
    14e7:	c1 e8 1f             	shr    $0x1f,%eax
    14ea:	41 5d                	pop    %r13
    14ec:	c3                   	ret