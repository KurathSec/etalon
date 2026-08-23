    1790:	55                   	push   %rbp
    1791:	48 89 e5             	mov    %rsp,%rbp
    1794:	48 83 ec 40          	sub    $0x40,%rsp
    1798:	48 89 7d f8          	mov    %rdi,-0x8(%rbp)
    179c:	48 89 75 f0          	mov    %rsi,-0x10(%rbp)
    17a0:	48 89 55 e8          	mov    %rdx,-0x18(%rbp)
    17a4:	48 8b 45 f8          	mov    -0x8(%rbp),%rax
    17a8:	48 8b 4d f0          	mov    -0x10(%rbp),%rcx
    17ac:	0f b6 04 08          	movzbl (%rax,%rcx,1),%eax
    17b0:	83 c8 01             	or     $0x1,%eax
    17b3:	88 45 e7             	mov    %al,-0x19(%rbp)
    17b6:	c7 45 e0 00 00 00 00 	movl   $0x0,-0x20(%rbp)
    17bd:	c7 45 dc 00 00 00 00 	movl   $0x0,-0x24(%rbp)
    17c4:	c7 45 d8 00 00 00 00 	movl   $0x0,-0x28(%rbp)
    17cb:	81 7d d8 00 02 00 00 	cmpl   $0x200,-0x28(%rbp)
    17d2:	0f 8d 99 00 00 00    	jge    1871 <sample_pos+0xe1>
    17d8:	48 8b 7d e8          	mov    -0x18(%rbp),%rdi
    17dc:	e8 9f 00 00 00       	call   1880 <xorshift>
    17e1:	25 ff 00 00 00       	and    $0xff,%eax
    17e6:	88 45 d7             	mov    %al,-0x29(%rbp)
    17e9:	c7 45 d0 00 00 00 00 	movl   $0x0,-0x30(%rbp)
    17f0:	c7 45 cc 00 00 00 00 	movl   $0x0,-0x34(%rbp)
    17f7:	81 7d cc c8 00 00 00 	cmpl   $0xc8,-0x34(%rbp)
    17fe:	0f 8d 21 00 00 00    	jge    1825 <sample_pos+0x95>
    1804:	48 8b 7d e8          	mov    -0x18(%rbp),%rdi
    1808:	e8 73 00 00 00       	call   1880 <xorshift>
    180d:	89 c1                	mov    %eax,%ecx
    180f:	8b 45 d0             	mov    -0x30(%rbp),%eax
    1812:	01 c8                	add    %ecx,%eax
    1814:	89 45 d0             	mov    %eax,-0x30(%rbp)
    1817:	8b 45 cc             	mov    -0x34(%rbp),%eax
    181a:	83 c0 01             	add    $0x1,%eax
    181d:	89 45 cc             	mov    %eax,-0x34(%rbp)
    1820:	e9 d2 ff ff ff       	jmp    17f7 <sample_pos+0x67>
    1825:	8b 45 d0             	mov    -0x30(%rbp),%eax
    1828:	0f b6 45 d7          	movzbl -0x29(%rbp),%eax
    182c:	0f b6 4d e7          	movzbl -0x19(%rbp),%ecx
    1830:	39 c8                	cmp    %ecx,%eax
    1832:	0f 9c c0             	setl   %al
    1835:	24 01                	and    $0x1,%al
    1837:	0f b6 c0             	movzbl %al,%eax
    183a:	83 7d e0 00          	cmpl   $0x0,-0x20(%rbp)
    183e:	0f 95 c1             	setne  %cl
    1841:	80 f1 ff             	xor    $0xff,%cl
    1844:	80 e1 01             	and    $0x1,%cl
    1847:	0f b6 c9             	movzbl %cl,%ecx
    184a:	21 c8                	and    %ecx,%eax
    184c:	89 45 c8             	mov    %eax,-0x38(%rbp)
    184f:	8b 45 c8             	mov    -0x38(%rbp),%eax
    1852:	0b 45 e0             	or     -0x20(%rbp),%eax
    1855:	89 45 e0             	mov    %eax,-0x20(%rbp)
    1858:	8b 4d c8             	mov    -0x38(%rbp),%ecx
    185b:	8b 45 dc             	mov    -0x24(%rbp),%eax
    185e:	01 c8                	add    %ecx,%eax
    1860:	89 45 dc             	mov    %eax,-0x24(%rbp)
    1863:	8b 45 d8             	mov    -0x28(%rbp),%eax
    1866:	83 c0 01             	add    $0x1,%eax
    1869:	89 45 d8             	mov    %eax,-0x28(%rbp)
    186c:	e9 5a ff ff ff       	jmp    17cb <sample_pos+0x3b>
    1871:	8b 45 dc             	mov    -0x24(%rbp),%eax
    1874:	b8 00 02 00 00       	mov    $0x200,%eax
    1879:	48 83 c4 40          	add    $0x40,%rsp
    187d:	5d                   	pop    %rbp
    187e:	c3                   	ret