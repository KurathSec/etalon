    1497:	41 55                	push   %r13
    1499:	49 89 fd             	mov    %rdi,%r13
    149c:	41 54                	push   %r12
    149e:	49 89 f4             	mov    %rsi,%r12
    14a1:	55                   	push   %rbp
    14a2:	31 ed                	xor    %ebp,%ebp
    14a4:	53                   	push   %rbx
    14a5:	31 db                	xor    %ebx,%ebx
    14a7:	51                   	push   %rcx
    14a8:	41 0f b6 34 2c       	movzbl (%r12,%rbp,1),%esi
    14ad:	41 0f b6 7c 2d 00    	movzbl 0x0(%r13,%rbp,1),%edi
    14b3:	e8 a1 ff ff ff       	call   1459 <byte_work>
    14b8:	41 8a 44 2d 00       	mov    0x0(%r13,%rbp,1),%al
    14bd:	41 32 04 2c          	xor    (%r12,%rbp,1),%al
    14c1:	48 ff c5             	inc    %rbp
    14c4:	09 c3                	or     %eax,%ebx
    14c6:	48 83 fd 10          	cmp    $0x10,%rbp
    14ca:	75 dc                	jne    14a8 <check_tag+0x11>
    14cc:	0f b6 c3             	movzbl %bl,%eax
    14cf:	5a                   	pop    %rdx
    14d0:	5b                   	pop    %rbx
    14d1:	ff c8                	dec    %eax
    14d3:	5d                   	pop    %rbp
    14d4:	41 5c                	pop    %r12
    14d6:	c1 e8 1f             	shr    $0x1f,%eax
    14d9:	41 5d                	pop    %r13
    14db:	c3                   	ret