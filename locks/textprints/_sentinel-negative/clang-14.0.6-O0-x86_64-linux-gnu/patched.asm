    16c0:	55                   	push   %rbp
    16c1:	48 89 e5             	mov    %rsp,%rbp
    16c4:	48 83 ec 20          	sub    $0x20,%rsp
    16c8:	48 89 7d f8          	mov    %rdi,-0x8(%rbp)
    16cc:	48 89 75 f0          	mov    %rsi,-0x10(%rbp)
    16d0:	c6 45 ef 00          	movb   $0x0,-0x11(%rbp)
    16d4:	48 c7 45 e0 00 00 00 	movq   $0x0,-0x20(%rbp)
    16db:	00 
    16dc:	48 83 7d e0 10       	cmpq   $0x10,-0x20(%rbp)
    16e1:	0f 83 56 00 00 00    	jae    173d <check_tag+0x7d>
    16e7:	48 8b 45 f8          	mov    -0x8(%rbp),%rax
    16eb:	48 8b 4d e0          	mov    -0x20(%rbp),%rcx
    16ef:	8a 14 08             	mov    (%rax,%rcx,1),%dl
    16f2:	48 8b 45 f0          	mov    -0x10(%rbp),%rax
    16f6:	48 8b 4d e0          	mov    -0x20(%rbp),%rcx
    16fa:	0f b6 fa             	movzbl %dl,%edi
    16fd:	0f b6 34 08          	movzbl (%rax,%rcx,1),%esi
    1701:	e8 4a ff ff ff       	call   1650 <byte_work>
    1706:	48 8b 45 f8          	mov    -0x8(%rbp),%rax
    170a:	48 8b 4d e0          	mov    -0x20(%rbp),%rcx
    170e:	0f b6 04 08          	movzbl (%rax,%rcx,1),%eax
    1712:	48 8b 4d f0          	mov    -0x10(%rbp),%rcx
    1716:	48 8b 55 e0          	mov    -0x20(%rbp),%rdx
    171a:	0f b6 0c 11          	movzbl (%rcx,%rdx,1),%ecx
    171e:	31 c8                	xor    %ecx,%eax
    1720:	0f b6 c8             	movzbl %al,%ecx
    1723:	0f b6 45 ef          	movzbl -0x11(%rbp),%eax
    1727:	09 c8                	or     %ecx,%eax
    1729:	88 45 ef             	mov    %al,-0x11(%rbp)
    172c:	48 8b 45 e0          	mov    -0x20(%rbp),%rax
    1730:	48 83 c0 01          	add    $0x1,%rax
    1734:	48 89 45 e0          	mov    %rax,-0x20(%rbp)
    1738:	e9 9f ff ff ff       	jmp    16dc <check_tag+0x1c>
    173d:	0f b6 45 ef          	movzbl -0x11(%rbp),%eax
    1741:	83 e8 01             	sub    $0x1,%eax
    1744:	c1 f8 08             	sar    $0x8,%eax
    1747:	83 e0 01             	and    $0x1,%eax
    174a:	48 83 c4 20          	add    $0x20,%rsp
    174e:	5d                   	pop    %rbp
    174f:	c3                   	ret