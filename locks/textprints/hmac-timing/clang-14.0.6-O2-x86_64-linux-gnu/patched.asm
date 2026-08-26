    15a0:	55                   	push   %rbp
    15a1:	41 57                	push   %r15
    15a3:	41 56                	push   %r14
    15a5:	53                   	push   %rbx
    15a6:	50                   	push   %rax
    15a7:	49 89 f6             	mov    %rsi,%r14
    15aa:	49 89 ff             	mov    %rdi,%r15
    15ad:	31 db                	xor    %ebx,%ebx
    15af:	31 ed                	xor    %ebp,%ebp
    15b1:	66 2e 0f 1f 84 00 00 	cs nopw 0x0(%rax,%rax,1)
    15b8:	00 00 00 
    15bb:	0f 1f 44 00 00       	nopl   0x0(%rax,%rax,1)
    15c0:	41 0f b6 3c 1f       	movzbl (%r15,%rbx,1),%edi
    15c5:	41 0f b6 34 1e       	movzbl (%r14,%rbx,1),%esi
    15ca:	e8 81 ff ff ff       	call   1550 <byte_work>
    15cf:	41 0f b6 04 1e       	movzbl (%r14,%rbx,1),%eax
    15d4:	41 32 04 1f          	xor    (%r15,%rbx,1),%al
    15d8:	0f b6 c0             	movzbl %al,%eax
    15db:	09 c5                	or     %eax,%ebp
    15dd:	48 83 c3 01          	add    $0x1,%rbx
    15e1:	48 83 fb 10          	cmp    $0x10,%rbx
    15e5:	75 d9                	jne    15c0 <check_tag+0x20>
    15e7:	83 c5 ff             	add    $0xffffffff,%ebp
    15ea:	c1 ed 08             	shr    $0x8,%ebp
    15ed:	83 e5 01             	and    $0x1,%ebp
    15f0:	89 e8                	mov    %ebp,%eax
    15f2:	48 83 c4 08          	add    $0x8,%rsp
    15f6:	5b                   	pop    %rbx
    15f7:	41 5e                	pop    %r14
    15f9:	41 5f                	pop    %r15
    15fb:	5d                   	pop    %rbp
    15fc:	c3                   	ret