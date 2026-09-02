    154d:	41 55                	push   %r13
    154f:	41 54                	push   %r12
    1551:	55                   	push   %rbp
    1552:	53                   	push   %rbx
    1553:	48 83 ec 08          	sub    $0x8,%rsp
    1557:	49 89 fd             	mov    %rdi,%r13
    155a:	49 89 f4             	mov    %rsi,%r12
    155d:	bb 00 00 00 00       	mov    $0x0,%ebx
    1562:	bd 00 00 00 00       	mov    $0x0,%ebp
    1567:	41 0f b6 34 1c       	movzbl (%r12,%rbx,1),%esi
    156c:	41 0f b6 7c 1d 00    	movzbl 0x0(%r13,%rbx,1),%edi
    1572:	e8 93 ff ff ff       	call   150a <byte_work>
    1577:	41 0f b6 44 1d 00    	movzbl 0x0(%r13,%rbx,1),%eax
    157d:	41 32 04 1c          	xor    (%r12,%rbx,1),%al
    1581:	09 c5                	or     %eax,%ebp
    1583:	48 83 c3 01          	add    $0x1,%rbx
    1587:	48 83 fb 10          	cmp    $0x10,%rbx
    158b:	75 da                	jne    1567 <check_tag+0x1a>
    158d:	40 0f b6 c5          	movzbl %bpl,%eax
    1591:	83 e8 01             	sub    $0x1,%eax
    1594:	c1 e8 1f             	shr    $0x1f,%eax
    1597:	48 83 c4 08          	add    $0x8,%rsp
    159b:	5b                   	pop    %rbx
    159c:	5d                   	pop    %rbp
    159d:	41 5c                	pop    %r12
    159f:	41 5d                	pop    %r13
    15a1:	c3                   	ret