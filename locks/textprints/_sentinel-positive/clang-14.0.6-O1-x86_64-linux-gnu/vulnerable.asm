    15c0:	41 57                	push   %r15
    15c2:	41 56                	push   %r14
    15c4:	53                   	push   %rbx
    15c5:	49 89 f6             	mov    %rsi,%r14
    15c8:	49 89 ff             	mov    %rdi,%r15
    15cb:	0f b6 3f             	movzbl (%rdi),%edi
    15ce:	0f b6 36             	movzbl (%rsi),%esi
    15d1:	e8 aa ff ff ff       	call   1580 <byte_work>
    15d6:	41 8a 0f             	mov    (%r15),%cl
    15d9:	31 c0                	xor    %eax,%eax
    15db:	41 3a 0e             	cmp    (%r14),%cl
    15de:	75 44                	jne    1624 <check_tag+0x64>
    15e0:	31 c0                	xor    %eax,%eax
    15e2:	66 2e 0f 1f 84 00 00 	cs nopw 0x0(%rax,%rax,1)
    15e9:	00 00 00 
    15ec:	0f 1f 40 00          	nopl   0x0(%rax)
    15f0:	48 89 c3             	mov    %rax,%rbx
    15f3:	48 83 f8 0f          	cmp    $0xf,%rax
    15f7:	74 22                	je     161b <check_tag+0x5b>
    15f9:	41 0f b6 7c 1f 01    	movzbl 0x1(%r15,%rbx,1),%edi
    15ff:	41 0f b6 74 1e 01    	movzbl 0x1(%r14,%rbx,1),%esi
    1605:	e8 76 ff ff ff       	call   1580 <byte_work>
    160a:	41 0f b6 4c 1f 01    	movzbl 0x1(%r15,%rbx,1),%ecx
    1610:	48 8d 43 01          	lea    0x1(%rbx),%rax
    1614:	41 3a 4c 1e 01       	cmp    0x1(%r14,%rbx,1),%cl
    1619:	74 d5                	je     15f0 <check_tag+0x30>
    161b:	31 c0                	xor    %eax,%eax
    161d:	48 83 fb 0f          	cmp    $0xf,%rbx
    1621:	0f 93 c0             	setae  %al
    1624:	5b                   	pop    %rbx
    1625:	41 5e                	pop    %r14
    1627:	41 5f                	pop    %r15
    1629:	c3                   	ret