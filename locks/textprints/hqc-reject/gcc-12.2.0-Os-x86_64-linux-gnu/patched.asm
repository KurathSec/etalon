    1559:	44 8a 04 37          	mov    (%rdi,%rsi,1),%r8b
    155d:	31 f6                	xor    %esi,%esi
    155f:	48 89 d1             	mov    %rdx,%rcx
    1562:	66 0f 6e 02          	movd   (%rdx),%xmm0
    1566:	89 74 24 f0          	mov    %esi,-0x10(%rsp)
    156a:	31 ff                	xor    %edi,%edi
    156c:	be 00 02 00 00       	mov    $0x200,%esi
    1571:	41 83 c8 01          	or     $0x1,%r8d
    1575:	0f 28 d0             	movaps %xmm0,%xmm2
    1578:	31 d2                	xor    %edx,%edx
    157a:	66 0f 72 f2 0d       	pslld  $0xd,%xmm2
    157f:	89 54 24 f4          	mov    %edx,-0xc(%rsp)
    1583:	ba c8 00 00 00       	mov    $0xc8,%edx
    1588:	0f 28 ca             	movaps %xmm2,%xmm1
    158b:	0f 57 c8             	xorps  %xmm0,%xmm1
    158e:	0f 28 d9             	movaps %xmm1,%xmm3
    1591:	66 0f 72 d3 11       	psrld  $0x11,%xmm3
    1596:	0f 57 cb             	xorps  %xmm3,%xmm1
    1599:	0f 28 e1             	movaps %xmm1,%xmm4
    159c:	66 0f 72 f4 05       	pslld  $0x5,%xmm4
    15a1:	0f 28 c4             	movaps %xmm4,%xmm0
    15a4:	0f 57 c1             	xorps  %xmm1,%xmm0
    15a7:	66 0f 7e c0          	movd   %xmm0,%eax
    15ab:	0f 28 e8             	movaps %xmm0,%xmm5
    15ae:	66 0f 72 f5 0d       	pslld  $0xd,%xmm5
    15b3:	0f 28 cd             	movaps %xmm5,%xmm1
    15b6:	0f 57 c8             	xorps  %xmm0,%xmm1
    15b9:	0f 28 f1             	movaps %xmm1,%xmm6
    15bc:	66 0f 72 d6 11       	psrld  $0x11,%xmm6
    15c1:	0f 57 ce             	xorps  %xmm6,%xmm1
    15c4:	0f 28 f9             	movaps %xmm1,%xmm7
    15c7:	66 0f 72 f7 05       	pslld  $0x5,%xmm7
    15cc:	0f 28 c7             	movaps %xmm7,%xmm0
    15cf:	0f 57 c1             	xorps  %xmm1,%xmm0
    15d2:	66 0f 6e 4c 24 f4    	movd   -0xc(%rsp),%xmm1
    15d8:	66 0f fe c8          	paddd  %xmm0,%xmm1
    15dc:	66 0f 7e 4c 24 f4    	movd   %xmm1,-0xc(%rsp)
    15e2:	ff ca                	dec    %edx
    15e4:	75 c5                	jne    15ab <sample_pos+0x52>
    15e6:	44 38 c0             	cmp    %r8b,%al
    15e9:	8b 54 24 f4          	mov    -0xc(%rsp),%edx
    15ed:	89 fa                	mov    %edi,%edx
    15ef:	0f 92 c0             	setb   %al
    15f2:	83 f2 01             	xor    $0x1,%edx
    15f5:	21 d0                	and    %edx,%eax
    15f7:	8b 54 24 f0          	mov    -0x10(%rsp),%edx
    15fb:	0f b6 c0             	movzbl %al,%eax
    15fe:	09 c7                	or     %eax,%edi
    1600:	01 d0                	add    %edx,%eax
    1602:	89 44 24 f0          	mov    %eax,-0x10(%rsp)
    1606:	ff ce                	dec    %esi
    1608:	0f 85 67 ff ff ff    	jne    1575 <sample_pos+0x1c>
    160e:	66 0f 7e 4c 24 f4    	movd   %xmm1,-0xc(%rsp)
    1614:	66 0f 7e 01          	movd   %xmm0,(%rcx)
    1618:	89 44 24 f0          	mov    %eax,-0x10(%rsp)
    161c:	8b 44 24 f0          	mov    -0x10(%rsp),%eax
    1620:	b8 00 02 00 00       	mov    $0x200,%eax
    1625:	c3                   	ret