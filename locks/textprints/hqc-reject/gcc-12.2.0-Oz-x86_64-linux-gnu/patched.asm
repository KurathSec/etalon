    1549:	44 8a 04 37          	mov    (%rdi,%rsi,1),%r8b
    154d:	48 89 d1             	mov    %rdx,%rcx
    1550:	83 64 24 f0 00       	andl   $0x0,-0x10(%rsp)
    1555:	66 0f 6e 02          	movd   (%rdx),%xmm0
    1559:	be 00 02 00 00       	mov    $0x200,%esi
    155e:	31 ff                	xor    %edi,%edi
    1560:	41 83 c8 01          	or     $0x1,%r8d
    1564:	0f 28 d0             	movaps %xmm0,%xmm2
    1567:	83 64 24 f4 00       	andl   $0x0,-0xc(%rsp)
    156c:	ba c8 00 00 00       	mov    $0xc8,%edx
    1571:	66 0f 72 f2 0d       	pslld  $0xd,%xmm2
    1576:	0f 28 ca             	movaps %xmm2,%xmm1
    1579:	0f 57 c8             	xorps  %xmm0,%xmm1
    157c:	0f 28 d9             	movaps %xmm1,%xmm3
    157f:	66 0f 72 d3 11       	psrld  $0x11,%xmm3
    1584:	0f 57 cb             	xorps  %xmm3,%xmm1
    1587:	0f 28 e1             	movaps %xmm1,%xmm4
    158a:	66 0f 72 f4 05       	pslld  $0x5,%xmm4
    158f:	0f 28 c4             	movaps %xmm4,%xmm0
    1592:	0f 57 c1             	xorps  %xmm1,%xmm0
    1595:	66 0f 7e c0          	movd   %xmm0,%eax
    1599:	0f 28 e8             	movaps %xmm0,%xmm5
    159c:	66 0f 72 f5 0d       	pslld  $0xd,%xmm5
    15a1:	0f 28 cd             	movaps %xmm5,%xmm1
    15a4:	0f 57 c8             	xorps  %xmm0,%xmm1
    15a7:	0f 28 f1             	movaps %xmm1,%xmm6
    15aa:	66 0f 72 d6 11       	psrld  $0x11,%xmm6
    15af:	0f 57 ce             	xorps  %xmm6,%xmm1
    15b2:	0f 28 f9             	movaps %xmm1,%xmm7
    15b5:	66 0f 72 f7 05       	pslld  $0x5,%xmm7
    15ba:	0f 28 c7             	movaps %xmm7,%xmm0
    15bd:	0f 57 c1             	xorps  %xmm1,%xmm0
    15c0:	66 0f 6e 4c 24 f4    	movd   -0xc(%rsp),%xmm1
    15c6:	66 0f fe c8          	paddd  %xmm0,%xmm1
    15ca:	66 0f 7e 4c 24 f4    	movd   %xmm1,-0xc(%rsp)
    15d0:	ff ca                	dec    %edx
    15d2:	75 c5                	jne    1599 <sample_pos+0x50>
    15d4:	44 38 c0             	cmp    %r8b,%al
    15d7:	8b 54 24 f4          	mov    -0xc(%rsp),%edx
    15db:	89 fa                	mov    %edi,%edx
    15dd:	0f 92 c0             	setb   %al
    15e0:	83 f2 01             	xor    $0x1,%edx
    15e3:	21 d0                	and    %edx,%eax
    15e5:	8b 54 24 f0          	mov    -0x10(%rsp),%edx
    15e9:	0f b6 c0             	movzbl %al,%eax
    15ec:	09 c7                	or     %eax,%edi
    15ee:	01 d0                	add    %edx,%eax
    15f0:	89 44 24 f0          	mov    %eax,-0x10(%rsp)
    15f4:	ff ce                	dec    %esi
    15f6:	0f 85 68 ff ff ff    	jne    1564 <sample_pos+0x1b>
    15fc:	66 0f 7e 4c 24 f4    	movd   %xmm1,-0xc(%rsp)
    1602:	66 0f 7e 01          	movd   %xmm0,(%rcx)
    1606:	89 44 24 f0          	mov    %eax,-0x10(%rsp)
    160a:	8b 44 24 f0          	mov    -0x10(%rsp),%eax
    160e:	b8 00 02 00 00       	mov    $0x200,%eax
    1613:	c3                   	ret