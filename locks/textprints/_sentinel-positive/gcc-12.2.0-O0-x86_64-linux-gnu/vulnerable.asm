    168a:	55                   	push   %rbp
    168b:	48 89 e5             	mov    %rsp,%rbp
    168e:	48 83 ec 20          	sub    $0x20,%rsp
    1692:	48 89 7d e8          	mov    %rdi,-0x18(%rbp)
    1696:	48 89 75 e0          	mov    %rsi,-0x20(%rbp)
    169a:	48 c7 45 f8 00 00 00 	movq   $0x0,-0x8(%rbp)
    16a1:	00 
    16a2:	eb 57                	jmp    16fb <check_tag+0x71>
    16a4:	48 8b 55 e0          	mov    -0x20(%rbp),%rdx
    16a8:	48 8b 45 f8          	mov    -0x8(%rbp),%rax
    16ac:	48 01 d0             	add    %rdx,%rax
    16af:	0f b6 00             	movzbl (%rax),%eax
    16b2:	0f b6 d0             	movzbl %al,%edx
    16b5:	48 8b 4d e8          	mov    -0x18(%rbp),%rcx
    16b9:	48 8b 45 f8          	mov    -0x8(%rbp),%rax
    16bd:	48 01 c8             	add    %rcx,%rax
    16c0:	0f b6 00             	movzbl (%rax),%eax
    16c3:	0f b6 c0             	movzbl %al,%eax
    16c6:	89 d6                	mov    %edx,%esi
    16c8:	89 c7                	mov    %eax,%edi
    16ca:	e8 63 ff ff ff       	call   1632 <byte_work>
    16cf:	48 8b 55 e8          	mov    -0x18(%rbp),%rdx
    16d3:	48 8b 45 f8          	mov    -0x8(%rbp),%rax
    16d7:	48 01 d0             	add    %rdx,%rax
    16da:	0f b6 10             	movzbl (%rax),%edx
    16dd:	48 8b 4d e0          	mov    -0x20(%rbp),%rcx
    16e1:	48 8b 45 f8          	mov    -0x8(%rbp),%rax
    16e5:	48 01 c8             	add    %rcx,%rax
    16e8:	0f b6 00             	movzbl (%rax),%eax
    16eb:	38 c2                	cmp    %al,%dl
    16ed:	74 07                	je     16f6 <check_tag+0x6c>
    16ef:	b8 00 00 00 00       	mov    $0x0,%eax
    16f4:	eb 11                	jmp    1707 <check_tag+0x7d>
    16f6:	48 83 45 f8 01       	addq   $0x1,-0x8(%rbp)
    16fb:	48 83 7d f8 0f       	cmpq   $0xf,-0x8(%rbp)
    1700:	76 a2                	jbe    16a4 <check_tag+0x1a>
    1702:	b8 01 00 00 00       	mov    $0x1,%eax
    1707:	c9                   	leave
    1708:	c3                   	ret