    1497:	41 54                	push   %r12
    1499:	49 89 f4             	mov    %rsi,%r12
    149c:	55                   	push   %rbp
    149d:	48 89 fd             	mov    %rdi,%rbp
    14a0:	53                   	push   %rbx
    14a1:	31 db                	xor    %ebx,%ebx
    14a3:	41 0f b6 34 1c       	movzbl (%r12,%rbx,1),%esi
    14a8:	0f b6 7c 1d 00       	movzbl 0x0(%rbp,%rbx,1),%edi
    14ad:	e8 a7 ff ff ff       	call   1459 <byte_work>
    14b2:	41 8a 04 1c          	mov    (%r12,%rbx,1),%al
    14b6:	38 44 1d 00          	cmp    %al,0x0(%rbp,%rbx,1)
    14ba:	75 0e                	jne    14ca <check_tag+0x33>
    14bc:	48 ff c3             	inc    %rbx
    14bf:	48 83 fb 10          	cmp    $0x10,%rbx
    14c3:	75 de                	jne    14a3 <check_tag+0xc>
    14c5:	6a 01                	push   $0x1
    14c7:	58                   	pop    %rax
    14c8:	eb 02                	jmp    14cc <check_tag+0x35>
    14ca:	31 c0                	xor    %eax,%eax
    14cc:	5b                   	pop    %rbx
    14cd:	5d                   	pop    %rbp
    14ce:	41 5c                	pop    %r12
    14d0:	c3                   	ret