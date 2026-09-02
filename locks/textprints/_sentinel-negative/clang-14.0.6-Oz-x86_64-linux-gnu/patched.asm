    1540:	41 57                	push   %r15
    1542:	41 56                	push   %r14
    1544:	41 54                	push   %r12
    1546:	53                   	push   %rbx
    1547:	50                   	push   %rax
    1548:	49 89 f6             	mov    %rsi,%r14
    154b:	49 89 fc             	mov    %rdi,%r12
    154e:	45 31 ff             	xor    %r15d,%r15d
    1551:	31 db                	xor    %ebx,%ebx
    1553:	48 83 fb 10          	cmp    $0x10,%rbx
    1557:	74 22                	je     157b <check_tag+0x3b>
    1559:	41 0f b6 3c 1c       	movzbl (%r12,%rbx,1),%edi
    155e:	41 0f b6 34 1e       	movzbl (%r14,%rbx,1),%esi
    1563:	e8 a4 ff ff ff       	call   150c <byte_work>
    1568:	41 8a 04 1e          	mov    (%r14,%rbx,1),%al
    156c:	41 32 04 1c          	xor    (%r12,%rbx,1),%al
    1570:	0f b6 c0             	movzbl %al,%eax
    1573:	41 09 c7             	or     %eax,%r15d
    1576:	48 ff c3             	inc    %rbx
    1579:	eb d8                	jmp    1553 <check_tag+0x13>
    157b:	41 ff cf             	dec    %r15d
    157e:	41 c1 ef 08          	shr    $0x8,%r15d
    1582:	41 83 e7 01          	and    $0x1,%r15d
    1586:	44 89 f8             	mov    %r15d,%eax
    1589:	48 83 c4 08          	add    $0x8,%rsp
    158d:	5b                   	pop    %rbx
    158e:	41 5c                	pop    %r12
    1590:	41 5e                	pop    %r14
    1592:	41 5f                	pop    %r15
    1594:	c3                   	ret