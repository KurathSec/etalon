    168a:	55                   	push   %rbp
    168b:	48 89 e5             	mov    %rsp,%rbp
    168e:	48 83 ec 20          	sub    $0x20,%rsp
    1692:	48 89 7d e8          	mov    %rdi,-0x18(%rbp)
    1696:	48 89 75 e0          	mov    %rsi,-0x20(%rbp)
    169a:	c6 45 ff 00          	movb   $0x0,-0x1(%rbp)
    169e:	48 c7 45 f0 00 00 00 	movq   $0x0,-0x10(%rbp)
    16a5:	00 
    16a6:	eb 51                	jmp    16f9 <check_tag+0x6f>
    16a8:	48 8b 55 e0          	mov    -0x20(%rbp),%rdx
    16ac:	48 8b 45 f0          	mov    -0x10(%rbp),%rax
    16b0:	48 01 d0             	add    %rdx,%rax
    16b3:	0f b6 00             	movzbl (%rax),%eax
    16b6:	0f b6 d0             	movzbl %al,%edx
    16b9:	48 8b 4d e8          	mov    -0x18(%rbp),%rcx
    16bd:	48 8b 45 f0          	mov    -0x10(%rbp),%rax
    16c1:	48 01 c8             	add    %rcx,%rax
    16c4:	0f b6 00             	movzbl (%rax),%eax
    16c7:	0f b6 c0             	movzbl %al,%eax
    16ca:	89 d6                	mov    %edx,%esi
    16cc:	89 c7                	mov    %eax,%edi
    16ce:	e8 5f ff ff ff       	call   1632 <byte_work>
    16d3:	48 8b 55 e8          	mov    -0x18(%rbp),%rdx
    16d7:	48 8b 45 f0          	mov    -0x10(%rbp),%rax
    16db:	48 01 d0             	add    %rdx,%rax
    16de:	0f b6 08             	movzbl (%rax),%ecx
    16e1:	48 8b 55 e0          	mov    -0x20(%rbp),%rdx
    16e5:	48 8b 45 f0          	mov    -0x10(%rbp),%rax
    16e9:	48 01 d0             	add    %rdx,%rax
    16ec:	0f b6 00             	movzbl (%rax),%eax
    16ef:	31 c8                	xor    %ecx,%eax
    16f1:	08 45 ff             	or     %al,-0x1(%rbp)
    16f4:	48 83 45 f0 01       	addq   $0x1,-0x10(%rbp)
    16f9:	48 83 7d f0 0f       	cmpq   $0xf,-0x10(%rbp)
    16fe:	76 a8                	jbe    16a8 <check_tag+0x1e>
    1700:	0f b6 45 ff          	movzbl -0x1(%rbp),%eax
    1704:	83 e8 01             	sub    $0x1,%eax
    1707:	c1 f8 08             	sar    $0x8,%eax
    170a:	83 e0 01             	and    $0x1,%eax
    170d:	c9                   	leave
    170e:	c3                   	ret