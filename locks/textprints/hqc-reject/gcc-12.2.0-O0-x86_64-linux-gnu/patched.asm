    1790:	55                   	push   %rbp
    1791:	48 89 e5             	mov    %rsp,%rbp
    1794:	48 83 ec 38          	sub    $0x38,%rsp
    1798:	48 89 7d d8          	mov    %rdi,-0x28(%rbp)
    179c:	48 89 75 d0          	mov    %rsi,-0x30(%rbp)
    17a0:	48 89 55 c8          	mov    %rdx,-0x38(%rbp)
    17a4:	48 8b 55 d8          	mov    -0x28(%rbp),%rdx
    17a8:	48 8b 45 d0          	mov    -0x30(%rbp),%rax
    17ac:	48 01 d0             	add    %rdx,%rax
    17af:	0f b6 00             	movzbl (%rax),%eax
    17b2:	83 c8 01             	or     $0x1,%eax
    17b5:	88 45 f3             	mov    %al,-0xd(%rbp)
    17b8:	c7 45 fc 00 00 00 00 	movl   $0x0,-0x4(%rbp)
    17bf:	c7 45 e8 00 00 00 00 	movl   $0x0,-0x18(%rbp)
    17c6:	c7 45 f8 00 00 00 00 	movl   $0x0,-0x8(%rbp)
    17cd:	eb 71                	jmp    1840 <sample_pos+0xb0>
    17cf:	48 8b 45 c8          	mov    -0x38(%rbp),%rax
    17d3:	48 89 c7             	mov    %rax,%rdi
    17d6:	e8 78 ff ff ff       	call   1753 <xorshift>
    17db:	88 45 f2             	mov    %al,-0xe(%rbp)
    17de:	c7 45 e4 00 00 00 00 	movl   $0x0,-0x1c(%rbp)
    17e5:	c7 45 f4 00 00 00 00 	movl   $0x0,-0xc(%rbp)
    17ec:	eb 18                	jmp    1806 <sample_pos+0x76>
    17ee:	48 8b 45 c8          	mov    -0x38(%rbp),%rax
    17f2:	48 89 c7             	mov    %rax,%rdi
    17f5:	e8 59 ff ff ff       	call   1753 <xorshift>
    17fa:	8b 55 e4             	mov    -0x1c(%rbp),%edx
    17fd:	01 d0                	add    %edx,%eax
    17ff:	89 45 e4             	mov    %eax,-0x1c(%rbp)
    1802:	83 45 f4 01          	addl   $0x1,-0xc(%rbp)
    1806:	81 7d f4 c7 00 00 00 	cmpl   $0xc7,-0xc(%rbp)
    180d:	7e df                	jle    17ee <sample_pos+0x5e>
    180f:	8b 45 e4             	mov    -0x1c(%rbp),%eax
    1812:	0f b6 45 f2          	movzbl -0xe(%rbp),%eax
    1816:	3a 45 f3             	cmp    -0xd(%rbp),%al
    1819:	0f 92 c2             	setb   %dl
    181c:	83 7d fc 00          	cmpl   $0x0,-0x4(%rbp)
    1820:	0f 94 c0             	sete   %al
    1823:	21 d0                	and    %edx,%eax
    1825:	0f b6 c0             	movzbl %al,%eax
    1828:	89 45 ec             	mov    %eax,-0x14(%rbp)
    182b:	8b 45 ec             	mov    -0x14(%rbp),%eax
    182e:	09 45 fc             	or     %eax,-0x4(%rbp)
    1831:	8b 55 e8             	mov    -0x18(%rbp),%edx
    1834:	8b 45 ec             	mov    -0x14(%rbp),%eax
    1837:	01 d0                	add    %edx,%eax
    1839:	89 45 e8             	mov    %eax,-0x18(%rbp)
    183c:	83 45 f8 01          	addl   $0x1,-0x8(%rbp)
    1840:	81 7d f8 ff 01 00 00 	cmpl   $0x1ff,-0x8(%rbp)
    1847:	7e 86                	jle    17cf <sample_pos+0x3f>
    1849:	8b 45 e8             	mov    -0x18(%rbp),%eax
    184c:	b8 00 02 00 00       	mov    $0x200,%eax
    1851:	c9                   	leave
    1852:	c3                   	ret