    155c:	55                   	push   %rbp
    155d:	41 57                	push   %r15
    155f:	41 56                	push   %r14
    1561:	41 55                	push   %r13
    1563:	41 54                	push   %r12
    1565:	53                   	push   %rbx
    1566:	50                   	push   %rax
    1567:	48 89 d3             	mov    %rdx,%rbx
    156a:	44 0f b6 34 37       	movzbl (%rdi,%rsi,1),%r14d
    156f:	41 83 ce 01          	or     $0x1,%r14d
    1573:	c7 44 24 04 00 00 00 	movl   $0x0,0x4(%rsp)
    157a:	00 
    157b:	45 31 ff             	xor    %r15d,%r15d
    157e:	45 31 e4             	xor    %r12d,%r12d
    1581:	41 81 ff 00 02 00 00 	cmp    $0x200,%r15d
    1588:	74 4d                	je     15d7 <sample_pos+0x7b>
    158a:	48 89 df             	mov    %rbx,%rdi
    158d:	e8 5d 00 00 00       	call   15ef <xorshift>
    1592:	41 89 c5             	mov    %eax,%r13d
    1595:	c7 04 24 00 00 00 00 	movl   $0x0,(%rsp)
    159c:	bd c8 00 00 00       	mov    $0xc8,%ebp
    15a1:	83 ed 01             	sub    $0x1,%ebp
    15a4:	72 0d                	jb     15b3 <sample_pos+0x57>
    15a6:	48 89 df             	mov    %rbx,%rdi
    15a9:	e8 41 00 00 00       	call   15ef <xorshift>
    15ae:	01 04 24             	add    %eax,(%rsp)
    15b1:	eb ee                	jmp    15a1 <sample_pos+0x45>
    15b3:	8b 04 24             	mov    (%rsp),%eax
    15b6:	41 0f b6 c5          	movzbl %r13b,%eax
    15ba:	44 39 f0             	cmp    %r14d,%eax
    15bd:	0f 92 c0             	setb   %al
    15c0:	45 85 e4             	test   %r12d,%r12d
    15c3:	0f 94 c1             	sete   %cl
    15c6:	20 c1                	and    %al,%cl
    15c8:	0f b6 c1             	movzbl %cl,%eax
    15cb:	41 09 c4             	or     %eax,%r12d
    15ce:	01 44 24 04          	add    %eax,0x4(%rsp)
    15d2:	41 ff c7             	inc    %r15d
    15d5:	eb aa                	jmp    1581 <sample_pos+0x25>
    15d7:	8b 44 24 04          	mov    0x4(%rsp),%eax
    15db:	b8 00 02 00 00       	mov    $0x200,%eax
    15e0:	48 83 c4 08          	add    $0x8,%rsp
    15e4:	5b                   	pop    %rbx
    15e5:	41 5c                	pop    %r12
    15e7:	41 5d                	pop    %r13
    15e9:	41 5e                	pop    %r14
    15eb:	41 5f                	pop    %r15
    15ed:	5d                   	pop    %rbp
    15ee:	c3                   	ret