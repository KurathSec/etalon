    155c:	55                   	push   %rbp
    155d:	41 57                	push   %r15
    155f:	41 56                	push   %r14
    1561:	41 54                	push   %r12
    1563:	53                   	push   %rbx
    1564:	48 83 ec 10          	sub    $0x10,%rsp
    1568:	48 89 d3             	mov    %rdx,%rbx
    156b:	44 0f b6 3c 37       	movzbl (%rdi,%rsi,1),%r15d
    1570:	41 83 cf 01          	or     $0x1,%r15d
    1574:	45 31 e4             	xor    %r12d,%r12d
    1577:	48 89 df             	mov    %rbx,%rdi
    157a:	e8 43 00 00 00       	call   15c2 <xorshift>
    157f:	41 89 c6             	mov    %eax,%r14d
    1582:	c7 44 24 0c 00 00 00 	movl   $0x0,0xc(%rsp)
    1589:	00 
    158a:	bd c8 00 00 00       	mov    $0xc8,%ebp
    158f:	83 ed 01             	sub    $0x1,%ebp
    1592:	72 0e                	jb     15a2 <sample_pos+0x46>
    1594:	48 89 df             	mov    %rbx,%rdi
    1597:	e8 26 00 00 00       	call   15c2 <xorshift>
    159c:	01 44 24 0c          	add    %eax,0xc(%rsp)
    15a0:	eb ed                	jmp    158f <sample_pos+0x33>
    15a2:	41 ff c4             	inc    %r12d
    15a5:	8b 44 24 0c          	mov    0xc(%rsp),%eax
    15a9:	41 0f b6 c6          	movzbl %r14b,%eax
    15ad:	44 39 f8             	cmp    %r15d,%eax
    15b0:	73 c5                	jae    1577 <sample_pos+0x1b>
    15b2:	44 89 e0             	mov    %r12d,%eax
    15b5:	48 83 c4 10          	add    $0x10,%rsp
    15b9:	5b                   	pop    %rbx
    15ba:	41 5c                	pop    %r12
    15bc:	41 5e                	pop    %r14
    15be:	41 5f                	pop    %r15
    15c0:	5d                   	pop    %rbp
    15c1:	c3                   	ret