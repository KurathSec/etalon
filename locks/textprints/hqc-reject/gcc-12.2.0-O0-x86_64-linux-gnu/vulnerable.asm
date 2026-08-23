    1790:	55                   	push   %rbp
    1791:	48 89 e5             	mov    %rsp,%rbp
    1794:	48 83 ec 28          	sub    $0x28,%rsp
    1798:	48 89 7d e8          	mov    %rdi,-0x18(%rbp)
    179c:	48 89 75 e0          	mov    %rsi,-0x20(%rbp)
    17a0:	48 89 55 d8          	mov    %rdx,-0x28(%rbp)
    17a4:	48 8b 55 e8          	mov    -0x18(%rbp),%rdx
    17a8:	48 8b 45 e0          	mov    -0x20(%rbp),%rax
    17ac:	48 01 d0             	add    %rdx,%rax
    17af:	0f b6 00             	movzbl (%rax),%eax
    17b2:	83 c8 01             	or     $0x1,%eax
    17b5:	88 45 f7             	mov    %al,-0x9(%rbp)
    17b8:	c7 45 fc 00 00 00 00 	movl   $0x0,-0x4(%rbp)
    17bf:	83 45 fc 01          	addl   $0x1,-0x4(%rbp)
    17c3:	48 8b 45 d8          	mov    -0x28(%rbp),%rax
    17c7:	48 89 c7             	mov    %rax,%rdi
    17ca:	e8 84 ff ff ff       	call   1753 <xorshift>
    17cf:	88 45 f6             	mov    %al,-0xa(%rbp)
    17d2:	c7 45 f0 00 00 00 00 	movl   $0x0,-0x10(%rbp)
    17d9:	c7 45 f8 00 00 00 00 	movl   $0x0,-0x8(%rbp)
    17e0:	eb 18                	jmp    17fa <sample_pos+0x6a>
    17e2:	48 8b 45 d8          	mov    -0x28(%rbp),%rax
    17e6:	48 89 c7             	mov    %rax,%rdi
    17e9:	e8 65 ff ff ff       	call   1753 <xorshift>
    17ee:	8b 55 f0             	mov    -0x10(%rbp),%edx
    17f1:	01 d0                	add    %edx,%eax
    17f3:	89 45 f0             	mov    %eax,-0x10(%rbp)
    17f6:	83 45 f8 01          	addl   $0x1,-0x8(%rbp)
    17fa:	81 7d f8 c7 00 00 00 	cmpl   $0xc7,-0x8(%rbp)
    1801:	7e df                	jle    17e2 <sample_pos+0x52>
    1803:	8b 45 f0             	mov    -0x10(%rbp),%eax
    1806:	0f b6 45 f6          	movzbl -0xa(%rbp),%eax
    180a:	3a 45 f7             	cmp    -0x9(%rbp),%al
    180d:	73 b0                	jae    17bf <sample_pos+0x2f>
    180f:	8b 45 fc             	mov    -0x4(%rbp),%eax
    1812:	c9                   	leave
    1813:	c3                   	ret