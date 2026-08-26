    14a8:	41 54                	push   %r12
    14aa:	49 89 f4             	mov    %rsi,%r12
    14ad:	55                   	push   %rbp
    14ae:	48 89 fd             	mov    %rdi,%rbp
    14b1:	53                   	push   %rbx
    14b2:	31 db                	xor    %ebx,%ebx
    14b4:	41 0f b6 34 1c       	movzbl (%r12,%rbx,1),%esi
    14b9:	0f b6 7c 1d 00       	movzbl 0x0(%rbp,%rbx,1),%edi
    14be:	e8 a6 ff ff ff       	call   1469 <byte_work>
    14c3:	41 8a 04 1c          	mov    (%r12,%rbx,1),%al
    14c7:	38 44 1d 00          	cmp    %al,0x0(%rbp,%rbx,1)
    14cb:	75 10                	jne    14dd <check_tag+0x35>
    14cd:	48 ff c3             	inc    %rbx
    14d0:	48 83 fb 10          	cmp    $0x10,%rbx
    14d4:	75 de                	jne    14b4 <check_tag+0xc>
    14d6:	b8 01 00 00 00       	mov    $0x1,%eax
    14db:	eb 02                	jmp    14df <check_tag+0x37>
    14dd:	31 c0                	xor    %eax,%eax
    14df:	5b                   	pop    %rbx
    14e0:	5d                   	pop    %rbp
    14e1:	41 5c                	pop    %r12
    14e3:	c3                   	ret