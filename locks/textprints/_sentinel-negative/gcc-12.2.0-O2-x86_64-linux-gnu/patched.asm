    1580:	41 55                	push   %r13
    1582:	49 89 fd             	mov    %rdi,%r13
    1585:	41 54                	push   %r12
    1587:	49 89 f4             	mov    %rsi,%r12
    158a:	55                   	push   %rbp
    158b:	31 ed                	xor    %ebp,%ebp
    158d:	53                   	push   %rbx
    158e:	31 db                	xor    %ebx,%ebx
    1590:	48 83 ec 08          	sub    $0x8,%rsp
    1594:	0f 1f 40 00          	nopl   0x0(%rax)
    1598:	41 0f b6 34 1c       	movzbl (%r12,%rbx,1),%esi
    159d:	41 0f b6 7c 1d 00    	movzbl 0x0(%r13,%rbx,1),%edi
    15a3:	e8 88 ff ff ff       	call   1530 <byte_work>
    15a8:	41 0f b6 44 1d 00    	movzbl 0x0(%r13,%rbx,1),%eax
    15ae:	41 32 04 1c          	xor    (%r12,%rbx,1),%al
    15b2:	48 83 c3 01          	add    $0x1,%rbx
    15b6:	09 c5                	or     %eax,%ebp
    15b8:	48 83 fb 10          	cmp    $0x10,%rbx
    15bc:	75 da                	jne    1598 <check_tag+0x18>
    15be:	40 0f b6 c5          	movzbl %bpl,%eax
    15c2:	48 83 c4 08          	add    $0x8,%rsp
    15c6:	83 e8 01             	sub    $0x1,%eax
    15c9:	5b                   	pop    %rbx
    15ca:	5d                   	pop    %rbp
    15cb:	c1 e8 1f             	shr    $0x1f,%eax
    15ce:	41 5c                	pop    %r12
    15d0:	41 5d                	pop    %r13
    15d2:	c3                   	ret