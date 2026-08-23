    1554:	55                   	push   %rbp
    1555:	41 57                	push   %r15
    1557:	41 56                	push   %r14
    1559:	53                   	push   %rbx
    155a:	50                   	push   %rax
    155b:	49 89 f6             	mov    %rsi,%r14
    155e:	49 89 ff             	mov    %rdi,%r15
    1561:	31 db                	xor    %ebx,%ebx
    1563:	31 ed                	xor    %ebp,%ebp
    1565:	41 0f b6 3c 1f       	movzbl (%r15,%rbx,1),%edi
    156a:	41 0f b6 34 1e       	movzbl (%r14,%rbx,1),%esi
    156f:	e8 b0 ff ff ff       	call   1524 <byte_work>
    1574:	41 8a 04 1e          	mov    (%r14,%rbx,1),%al
    1578:	41 32 04 1f          	xor    (%r15,%rbx,1),%al
    157c:	0f b6 c0             	movzbl %al,%eax
    157f:	09 c5                	or     %eax,%ebp
    1581:	48 ff c3             	inc    %rbx
    1584:	48 83 fb 10          	cmp    $0x10,%rbx
    1588:	75 db                	jne    1565 <check_tag+0x11>
    158a:	ff cd                	dec    %ebp
    158c:	c1 ed 08             	shr    $0x8,%ebp
    158f:	83 e5 01             	and    $0x1,%ebp
    1592:	89 e8                	mov    %ebp,%eax
    1594:	48 83 c4 08          	add    $0x8,%rsp
    1598:	5b                   	pop    %rbx
    1599:	41 5e                	pop    %r14
    159b:	41 5f                	pop    %r15
    159d:	5d                   	pop    %rbp
    159e:	c3                   	ret