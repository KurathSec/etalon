    1580:	41 54                	push   %r12
    1582:	49 89 fc             	mov    %rdi,%r12
    1585:	55                   	push   %rbp
    1586:	48 89 f5             	mov    %rsi,%rbp
    1589:	53                   	push   %rbx
    158a:	31 db                	xor    %ebx,%ebx
    158c:	0f 1f 40 00          	nopl   0x0(%rax)
    1590:	0f b6 74 1d 00       	movzbl 0x0(%rbp,%rbx,1),%esi
    1595:	41 0f b6 3c 1c       	movzbl (%r12,%rbx,1),%edi
    159a:	e8 91 ff ff ff       	call   1530 <byte_work>
    159f:	0f b6 44 1d 00       	movzbl 0x0(%rbp,%rbx,1),%eax
    15a4:	41 38 04 1c          	cmp    %al,(%r12,%rbx,1)
    15a8:	75 16                	jne    15c0 <check_tag+0x40>
    15aa:	48 83 c3 01          	add    $0x1,%rbx
    15ae:	48 83 fb 10          	cmp    $0x10,%rbx
    15b2:	75 dc                	jne    1590 <check_tag+0x10>
    15b4:	5b                   	pop    %rbx
    15b5:	b8 01 00 00 00       	mov    $0x1,%eax
    15ba:	5d                   	pop    %rbp
    15bb:	41 5c                	pop    %r12
    15bd:	c3                   	ret
    15be:	66 90                	xchg   %ax,%ax
    15c0:	5b                   	pop    %rbx
    15c1:	31 c0                	xor    %eax,%eax
    15c3:	5d                   	pop    %rbp
    15c4:	41 5c                	pop    %r12
    15c6:	c3                   	ret