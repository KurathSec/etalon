    15a0:	41 57                	push   %r15
    15a2:	41 56                	push   %r14
    15a4:	53                   	push   %rbx
    15a5:	49 89 f6             	mov    %rsi,%r14
    15a8:	49 89 ff             	mov    %rdi,%r15
    15ab:	0f b6 3f             	movzbl (%rdi),%edi
    15ae:	0f b6 36             	movzbl (%rsi),%esi
    15b1:	e8 9a ff ff ff       	call   1550 <byte_work>
    15b6:	41 8a 0f             	mov    (%r15),%cl
    15b9:	31 c0                	xor    %eax,%eax
    15bb:	41 3a 0e             	cmp    (%r14),%cl
    15be:	75 44                	jne    1604 <check_tag+0x64>
    15c0:	31 c0                	xor    %eax,%eax
    15c2:	66 2e 0f 1f 84 00 00 	cs nopw 0x0(%rax,%rax,1)
    15c9:	00 00 00 
    15cc:	0f 1f 40 00          	nopl   0x0(%rax)
    15d0:	48 89 c3             	mov    %rax,%rbx
    15d3:	48 83 f8 0f          	cmp    $0xf,%rax
    15d7:	74 22                	je     15fb <check_tag+0x5b>
    15d9:	41 0f b6 7c 1f 01    	movzbl 0x1(%r15,%rbx,1),%edi
    15df:	41 0f b6 74 1e 01    	movzbl 0x1(%r14,%rbx,1),%esi
    15e5:	e8 66 ff ff ff       	call   1550 <byte_work>
    15ea:	41 0f b6 4c 1f 01    	movzbl 0x1(%r15,%rbx,1),%ecx
    15f0:	48 8d 43 01          	lea    0x1(%rbx),%rax
    15f4:	41 3a 4c 1e 01       	cmp    0x1(%r14,%rbx,1),%cl
    15f9:	74 d5                	je     15d0 <check_tag+0x30>
    15fb:	31 c0                	xor    %eax,%eax
    15fd:	48 83 fb 0f          	cmp    $0xf,%rbx
    1601:	0f 93 c0             	setae  %al
    1604:	5b                   	pop    %rbx
    1605:	41 5e                	pop    %r14
    1607:	41 5f                	pop    %r15
    1609:	c3                   	ret