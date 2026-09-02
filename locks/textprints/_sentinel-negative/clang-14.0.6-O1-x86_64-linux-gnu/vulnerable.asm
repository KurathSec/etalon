    15c0:	55                   	push   %rbp
    15c1:	41 57                	push   %r15
    15c3:	41 56                	push   %r14
    15c5:	53                   	push   %rbx
    15c6:	50                   	push   %rax
    15c7:	49 89 f6             	mov    %rsi,%r14
    15ca:	49 89 ff             	mov    %rdi,%r15
    15cd:	31 db                	xor    %ebx,%ebx
    15cf:	31 ed                	xor    %ebp,%ebp
    15d1:	66 2e 0f 1f 84 00 00 	cs nopw 0x0(%rax,%rax,1)
    15d8:	00 00 00 
    15db:	0f 1f 44 00 00       	nopl   0x0(%rax,%rax,1)
    15e0:	41 0f b6 3c 1f       	movzbl (%r15,%rbx,1),%edi
    15e5:	41 0f b6 34 1e       	movzbl (%r14,%rbx,1),%esi
    15ea:	e8 91 ff ff ff       	call   1580 <byte_work>
    15ef:	41 0f b6 04 1e       	movzbl (%r14,%rbx,1),%eax
    15f4:	41 32 04 1f          	xor    (%r15,%rbx,1),%al
    15f8:	0f b6 c0             	movzbl %al,%eax
    15fb:	09 c5                	or     %eax,%ebp
    15fd:	48 83 c3 01          	add    $0x1,%rbx
    1601:	48 83 fb 10          	cmp    $0x10,%rbx
    1605:	75 d9                	jne    15e0 <check_tag+0x20>
    1607:	83 c5 ff             	add    $0xffffffff,%ebp
    160a:	c1 ed 08             	shr    $0x8,%ebp
    160d:	83 e5 01             	and    $0x1,%ebp
    1610:	89 e8                	mov    %ebp,%eax
    1612:	48 83 c4 08          	add    $0x8,%rsp
    1616:	5b                   	pop    %rbx
    1617:	41 5e                	pop    %r14
    1619:	41 5f                	pop    %r15
    161b:	5d                   	pop    %rbp
    161c:	c3                   	ret