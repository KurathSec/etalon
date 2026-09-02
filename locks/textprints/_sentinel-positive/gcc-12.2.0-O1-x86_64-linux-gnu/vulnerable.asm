    154d:	41 54                	push   %r12
    154f:	55                   	push   %rbp
    1550:	53                   	push   %rbx
    1551:	49 89 fc             	mov    %rdi,%r12
    1554:	48 89 f5             	mov    %rsi,%rbp
    1557:	bb 00 00 00 00       	mov    $0x0,%ebx
    155c:	0f b6 74 1d 00       	movzbl 0x0(%rbp,%rbx,1),%esi
    1561:	41 0f b6 3c 1c       	movzbl (%r12,%rbx,1),%edi
    1566:	e8 9f ff ff ff       	call   150a <byte_work>
    156b:	0f b6 44 1d 00       	movzbl 0x0(%rbp,%rbx,1),%eax
    1570:	41 38 04 1c          	cmp    %al,(%r12,%rbx,1)
    1574:	75 14                	jne    158a <check_tag+0x3d>
    1576:	48 83 c3 01          	add    $0x1,%rbx
    157a:	48 83 fb 10          	cmp    $0x10,%rbx
    157e:	75 dc                	jne    155c <check_tag+0xf>
    1580:	b8 01 00 00 00       	mov    $0x1,%eax
    1585:	5b                   	pop    %rbx
    1586:	5d                   	pop    %rbp
    1587:	41 5c                	pop    %r12
    1589:	c3                   	ret
    158a:	b8 00 00 00 00       	mov    $0x0,%eax
    158f:	eb f4                	jmp    1585 <check_tag+0x38>