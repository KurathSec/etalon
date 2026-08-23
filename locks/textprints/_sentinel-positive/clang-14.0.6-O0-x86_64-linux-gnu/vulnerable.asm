    16c0:	55                   	push   %rbp
    16c1:	48 89 e5             	mov    %rsp,%rbp
    16c4:	48 83 ec 20          	sub    $0x20,%rsp
    16c8:	48 89 7d f0          	mov    %rdi,-0x10(%rbp)
    16cc:	48 89 75 e8          	mov    %rsi,-0x18(%rbp)
    16d0:	48 c7 45 e0 00 00 00 	movq   $0x0,-0x20(%rbp)
    16d7:	00 
    16d8:	48 83 7d e0 10       	cmpq   $0x10,-0x20(%rbp)
    16dd:	0f 83 61 00 00 00    	jae    1744 <check_tag+0x84>
    16e3:	48 8b 45 f0          	mov    -0x10(%rbp),%rax
    16e7:	48 8b 4d e0          	mov    -0x20(%rbp),%rcx
    16eb:	8a 14 08             	mov    (%rax,%rcx,1),%dl
    16ee:	48 8b 45 e8          	mov    -0x18(%rbp),%rax
    16f2:	48 8b 4d e0          	mov    -0x20(%rbp),%rcx
    16f6:	0f b6 fa             	movzbl %dl,%edi
    16f9:	0f b6 34 08          	movzbl (%rax,%rcx,1),%esi
    16fd:	e8 4e ff ff ff       	call   1650 <byte_work>
    1702:	48 8b 45 f0          	mov    -0x10(%rbp),%rax
    1706:	48 8b 4d e0          	mov    -0x20(%rbp),%rcx
    170a:	0f b6 04 08          	movzbl (%rax,%rcx,1),%eax
    170e:	48 8b 4d e8          	mov    -0x18(%rbp),%rcx
    1712:	48 8b 55 e0          	mov    -0x20(%rbp),%rdx
    1716:	0f b6 0c 11          	movzbl (%rcx,%rdx,1),%ecx
    171a:	39 c8                	cmp    %ecx,%eax
    171c:	0f 84 0c 00 00 00    	je     172e <check_tag+0x6e>
    1722:	c7 45 fc 00 00 00 00 	movl   $0x0,-0x4(%rbp)
    1729:	e9 1d 00 00 00       	jmp    174b <check_tag+0x8b>
    172e:	e9 00 00 00 00       	jmp    1733 <check_tag+0x73>
    1733:	48 8b 45 e0          	mov    -0x20(%rbp),%rax
    1737:	48 83 c0 01          	add    $0x1,%rax
    173b:	48 89 45 e0          	mov    %rax,-0x20(%rbp)
    173f:	e9 94 ff ff ff       	jmp    16d8 <check_tag+0x18>
    1744:	c7 45 fc 01 00 00 00 	movl   $0x1,-0x4(%rbp)
    174b:	8b 45 fc             	mov    -0x4(%rbp),%eax
    174e:	48 83 c4 20          	add    $0x20,%rsp
    1752:	5d                   	pop    %rbp
    1753:	c3                   	ret