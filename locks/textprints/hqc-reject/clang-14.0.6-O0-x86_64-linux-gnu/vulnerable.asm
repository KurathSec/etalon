    1790:	55                   	push   %rbp
    1791:	48 89 e5             	mov    %rsp,%rbp
    1794:	48 83 ec 30          	sub    $0x30,%rsp
    1798:	48 89 7d f8          	mov    %rdi,-0x8(%rbp)
    179c:	48 89 75 f0          	mov    %rsi,-0x10(%rbp)
    17a0:	48 89 55 e8          	mov    %rdx,-0x18(%rbp)
    17a4:	48 8b 45 f8          	mov    -0x8(%rbp),%rax
    17a8:	48 8b 4d f0          	mov    -0x10(%rbp),%rcx
    17ac:	0f b6 04 08          	movzbl (%rax,%rcx,1),%eax
    17b0:	83 c8 01             	or     $0x1,%eax
    17b3:	88 45 e7             	mov    %al,-0x19(%rbp)
    17b6:	c7 45 e0 00 00 00 00 	movl   $0x0,-0x20(%rbp)
    17bd:	8b 45 e0             	mov    -0x20(%rbp),%eax
    17c0:	83 c0 01             	add    $0x1,%eax
    17c3:	89 45 e0             	mov    %eax,-0x20(%rbp)
    17c6:	48 8b 7d e8          	mov    -0x18(%rbp),%rdi
    17ca:	e8 71 00 00 00       	call   1840 <xorshift>
    17cf:	25 ff 00 00 00       	and    $0xff,%eax
    17d4:	88 45 df             	mov    %al,-0x21(%rbp)
    17d7:	c7 45 d8 00 00 00 00 	movl   $0x0,-0x28(%rbp)
    17de:	c7 45 d4 00 00 00 00 	movl   $0x0,-0x2c(%rbp)
    17e5:	81 7d d4 c8 00 00 00 	cmpl   $0xc8,-0x2c(%rbp)
    17ec:	0f 8d 21 00 00 00    	jge    1813 <sample_pos+0x83>
    17f2:	48 8b 7d e8          	mov    -0x18(%rbp),%rdi
    17f6:	e8 45 00 00 00       	call   1840 <xorshift>
    17fb:	89 c1                	mov    %eax,%ecx
    17fd:	8b 45 d8             	mov    -0x28(%rbp),%eax
    1800:	01 c8                	add    %ecx,%eax
    1802:	89 45 d8             	mov    %eax,-0x28(%rbp)
    1805:	8b 45 d4             	mov    -0x2c(%rbp),%eax
    1808:	83 c0 01             	add    $0x1,%eax
    180b:	89 45 d4             	mov    %eax,-0x2c(%rbp)
    180e:	e9 d2 ff ff ff       	jmp    17e5 <sample_pos+0x55>
    1813:	8b 45 d8             	mov    -0x28(%rbp),%eax
    1816:	0f b6 45 df          	movzbl -0x21(%rbp),%eax
    181a:	0f b6 4d e7          	movzbl -0x19(%rbp),%ecx
    181e:	39 c8                	cmp    %ecx,%eax
    1820:	0f 8d 09 00 00 00    	jge    182f <sample_pos+0x9f>
    1826:	8b 45 e0             	mov    -0x20(%rbp),%eax
    1829:	48 83 c4 30          	add    $0x30,%rsp
    182d:	5d                   	pop    %rbp
    182e:	c3                   	ret
    182f:	e9 89 ff ff ff       	jmp    17bd <sample_pos+0x2d>