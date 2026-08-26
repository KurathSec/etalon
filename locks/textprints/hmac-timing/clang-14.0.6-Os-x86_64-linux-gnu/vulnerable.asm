    1554:	41 57                	push   %r15
    1556:	41 56                	push   %r14
    1558:	53                   	push   %rbx
    1559:	49 89 f6             	mov    %rsi,%r14
    155c:	49 89 ff             	mov    %rdi,%r15
    155f:	0f b6 3f             	movzbl (%rdi),%edi
    1562:	0f b6 36             	movzbl (%rsi),%esi
    1565:	e8 ba ff ff ff       	call   1524 <byte_work>
    156a:	41 8a 0f             	mov    (%r15),%cl
    156d:	31 c0                	xor    %eax,%eax
    156f:	41 3a 0e             	cmp    (%r14),%cl
    1572:	75 35                	jne    15a9 <check_tag+0x55>
    1574:	31 c0                	xor    %eax,%eax
    1576:	48 89 c3             	mov    %rax,%rbx
    1579:	48 83 f8 0f          	cmp    $0xf,%rax
    157d:	74 21                	je     15a0 <check_tag+0x4c>
    157f:	41 0f b6 7c 1f 01    	movzbl 0x1(%r15,%rbx,1),%edi
    1585:	41 0f b6 74 1e 01    	movzbl 0x1(%r14,%rbx,1),%esi
    158b:	e8 94 ff ff ff       	call   1524 <byte_work>
    1590:	41 8a 4c 1f 01       	mov    0x1(%r15,%rbx,1),%cl
    1595:	48 8d 43 01          	lea    0x1(%rbx),%rax
    1599:	41 3a 4c 1e 01       	cmp    0x1(%r14,%rbx,1),%cl
    159e:	74 d6                	je     1576 <check_tag+0x22>
    15a0:	31 c0                	xor    %eax,%eax
    15a2:	48 83 fb 0f          	cmp    $0xf,%rbx
    15a6:	0f 93 c0             	setae  %al
    15a9:	5b                   	pop    %rbx
    15aa:	41 5e                	pop    %r14
    15ac:	41 5f                	pop    %r15
    15ae:	c3                   	ret