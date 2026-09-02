    1540:	41 57                	push   %r15
    1542:	41 56                	push   %r14
    1544:	53                   	push   %rbx
    1545:	49 89 f6             	mov    %rsi,%r14
    1548:	49 89 ff             	mov    %rdi,%r15
    154b:	31 c0                	xor    %eax,%eax
    154d:	48 89 c3             	mov    %rax,%rbx
    1550:	48 83 f8 10          	cmp    $0x10,%rax
    1554:	74 1d                	je     1573 <check_tag+0x33>
    1556:	41 0f b6 3c 1f       	movzbl (%r15,%rbx,1),%edi
    155b:	41 0f b6 34 1e       	movzbl (%r14,%rbx,1),%esi
    1560:	e8 a7 ff ff ff       	call   150c <byte_work>
    1565:	41 8a 0c 1f          	mov    (%r15,%rbx,1),%cl
    1569:	48 8d 43 01          	lea    0x1(%rbx),%rax
    156d:	41 3a 0c 1e          	cmp    (%r14,%rbx,1),%cl
    1571:	74 da                	je     154d <check_tag+0xd>
    1573:	31 c0                	xor    %eax,%eax
    1575:	48 83 fb 10          	cmp    $0x10,%rbx
    1579:	0f 93 c0             	setae  %al
    157c:	5b                   	pop    %rbx
    157d:	41 5e                	pop    %r14
    157f:	41 5f                	pop    %r15
    1581:	c3                   	ret