    19e0:	44 0f b6 04 37       	movzbl (%rdi,%rsi,1),%r8d
    19e5:	41 83 c8 01          	or     $0x1,%r8d
    19e9:	c7 44 24 fc 00 00 00 	movl   $0x0,-0x4(%rsp)
    19f0:	00 
    19f1:	8b 3a                	mov    (%rdx),%edi
    19f3:	45 31 c9             	xor    %r9d,%r9d
    19f6:	45 31 d2             	xor    %r10d,%r10d
    19f9:	0f 1f 80 00 00 00 00 	nopl   0x0(%rax)
    1a00:	89 f8                	mov    %edi,%eax
    1a02:	c1 e0 0d             	shl    $0xd,%eax
    1a05:	31 f8                	xor    %edi,%eax
    1a07:	89 c1                	mov    %eax,%ecx
    1a09:	c1 e9 11             	shr    $0x11,%ecx
    1a0c:	31 c1                	xor    %eax,%ecx
    1a0e:	89 c8                	mov    %ecx,%eax
    1a10:	c1 e0 05             	shl    $0x5,%eax
    1a13:	31 c8                	xor    %ecx,%eax
    1a15:	c7 44 24 f8 00 00 00 	movl   $0x0,-0x8(%rsp)
    1a1c:	00 
    1a1d:	b9 c8 00 00 00       	mov    $0xc8,%ecx
    1a22:	89 c7                	mov    %eax,%edi
    1a24:	66 2e 0f 1f 84 00 00 	cs nopw 0x0(%rax,%rax,1)
    1a2b:	00 00 00 
    1a2e:	66 90                	xchg   %ax,%ax
    1a30:	89 fe                	mov    %edi,%esi
    1a32:	c1 e6 0d             	shl    $0xd,%esi
    1a35:	31 fe                	xor    %edi,%esi
    1a37:	89 f7                	mov    %esi,%edi
    1a39:	c1 ef 11             	shr    $0x11,%edi
    1a3c:	31 f7                	xor    %esi,%edi
    1a3e:	89 fe                	mov    %edi,%esi
    1a40:	c1 e6 05             	shl    $0x5,%esi
    1a43:	31 fe                	xor    %edi,%esi
    1a45:	89 32                	mov    %esi,(%rdx)
    1a47:	01 74 24 f8          	add    %esi,-0x8(%rsp)
    1a4b:	89 f7                	mov    %esi,%edi
    1a4d:	c1 e7 0d             	shl    $0xd,%edi
    1a50:	31 f7                	xor    %esi,%edi
    1a52:	89 fe                	mov    %edi,%esi
    1a54:	c1 ee 11             	shr    $0x11,%esi
    1a57:	31 fe                	xor    %edi,%esi
    1a59:	89 f7                	mov    %esi,%edi
    1a5b:	c1 e7 05             	shl    $0x5,%edi
    1a5e:	31 f7                	xor    %esi,%edi
    1a60:	89 3a                	mov    %edi,(%rdx)
    1a62:	01 7c 24 f8          	add    %edi,-0x8(%rsp)
    1a66:	83 c1 fe             	add    $0xfffffffe,%ecx
    1a69:	75 c5                	jne    1a30 <sample_pos+0x50>
    1a6b:	8b 4c 24 f8          	mov    -0x8(%rsp),%ecx
    1a6f:	0f b6 c0             	movzbl %al,%eax
    1a72:	44 39 c0             	cmp    %r8d,%eax
    1a75:	0f 92 c0             	setb   %al
    1a78:	45 85 c9             	test   %r9d,%r9d
    1a7b:	0f 94 c1             	sete   %cl
    1a7e:	20 c1                	and    %al,%cl
    1a80:	0f b6 c1             	movzbl %cl,%eax
    1a83:	01 44 24 fc          	add    %eax,-0x4(%rsp)
    1a87:	41 09 c1             	or     %eax,%r9d
    1a8a:	41 83 c2 01          	add    $0x1,%r10d
    1a8e:	41 81 fa 00 02 00 00 	cmp    $0x200,%r10d
    1a95:	0f 85 65 ff ff ff    	jne    1a00 <sample_pos+0x20>
    1a9b:	8b 44 24 fc          	mov    -0x4(%rsp),%eax
    1a9f:	b8 00 02 00 00       	mov    $0x200,%eax
    1aa4:	c3                   	ret