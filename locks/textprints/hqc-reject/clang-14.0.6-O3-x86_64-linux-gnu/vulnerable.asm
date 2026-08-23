    19e0:	44 0f b6 04 37       	movzbl (%rdi,%rsi,1),%r8d
    19e5:	41 83 c8 01          	or     $0x1,%r8d
    19e9:	8b 32                	mov    (%rdx),%esi
    19eb:	31 c0                	xor    %eax,%eax
    19ed:	0f 1f 00             	nopl   (%rax)
    19f0:	89 f1                	mov    %esi,%ecx
    19f2:	c1 e1 0d             	shl    $0xd,%ecx
    19f5:	31 f1                	xor    %esi,%ecx
    19f7:	89 ce                	mov    %ecx,%esi
    19f9:	c1 ee 11             	shr    $0x11,%esi
    19fc:	31 ce                	xor    %ecx,%esi
    19fe:	41 89 f1             	mov    %esi,%r9d
    1a01:	41 c1 e1 05          	shl    $0x5,%r9d
    1a05:	41 31 f1             	xor    %esi,%r9d
    1a08:	c7 44 24 fc 00 00 00 	movl   $0x0,-0x4(%rsp)
    1a0f:	00 
    1a10:	bf c8 00 00 00       	mov    $0xc8,%edi
    1a15:	44 89 ce             	mov    %r9d,%esi
    1a18:	0f 1f 84 00 00 00 00 	nopl   0x0(%rax,%rax,1)
    1a1f:	00 
    1a20:	89 f1                	mov    %esi,%ecx
    1a22:	c1 e1 0d             	shl    $0xd,%ecx
    1a25:	31 f1                	xor    %esi,%ecx
    1a27:	89 ce                	mov    %ecx,%esi
    1a29:	c1 ee 11             	shr    $0x11,%esi
    1a2c:	31 ce                	xor    %ecx,%esi
    1a2e:	89 f1                	mov    %esi,%ecx
    1a30:	c1 e1 05             	shl    $0x5,%ecx
    1a33:	31 f1                	xor    %esi,%ecx
    1a35:	89 0a                	mov    %ecx,(%rdx)
    1a37:	01 4c 24 fc          	add    %ecx,-0x4(%rsp)
    1a3b:	89 ce                	mov    %ecx,%esi
    1a3d:	c1 e6 0d             	shl    $0xd,%esi
    1a40:	31 ce                	xor    %ecx,%esi
    1a42:	89 f1                	mov    %esi,%ecx
    1a44:	c1 e9 11             	shr    $0x11,%ecx
    1a47:	31 f1                	xor    %esi,%ecx
    1a49:	89 ce                	mov    %ecx,%esi
    1a4b:	c1 e6 05             	shl    $0x5,%esi
    1a4e:	31 ce                	xor    %ecx,%esi
    1a50:	89 32                	mov    %esi,(%rdx)
    1a52:	01 74 24 fc          	add    %esi,-0x4(%rsp)
    1a56:	83 c7 fe             	add    $0xfffffffe,%edi
    1a59:	75 c5                	jne    1a20 <sample_pos+0x40>
    1a5b:	83 c0 01             	add    $0x1,%eax
    1a5e:	8b 7c 24 fc          	mov    -0x4(%rsp),%edi
    1a62:	41 0f b6 c9          	movzbl %r9b,%ecx
    1a66:	44 39 c1             	cmp    %r8d,%ecx
    1a69:	73 85                	jae    19f0 <sample_pos+0x10>
    1a6b:	c3                   	ret