    16d0:	55                   	push   %rbp
    16d1:	41 57                	push   %r15
    16d3:	41 56                	push   %r14
    16d5:	41 55                	push   %r13
    16d7:	41 54                	push   %r12
    16d9:	53                   	push   %rbx
    16da:	48 83 ec 68          	sub    $0x68,%rsp
    16de:	48 89 f3             	mov    %rsi,%rbx
    16e1:	49 89 fe             	mov    %rdi,%r14
    16e4:	0f b6 3f             	movzbl (%rdi),%edi
    16e7:	0f b6 36             	movzbl (%rsi),%esi
    16ea:	e8 91 ff ff ff       	call   1680 <byte_work>
    16ef:	41 0f b6 7e 01       	movzbl 0x1(%r14),%edi
    16f4:	0f b6 73 01          	movzbl 0x1(%rbx),%esi
    16f8:	0f b6 03             	movzbl (%rbx),%eax
    16fb:	89 44 24 48          	mov    %eax,0x48(%rsp)
    16ff:	41 0f b6 06          	movzbl (%r14),%eax
    1703:	89 44 24 64          	mov    %eax,0x64(%rsp)
    1707:	e8 74 ff ff ff       	call   1680 <byte_work>
    170c:	41 0f b6 7e 02       	movzbl 0x2(%r14),%edi
    1711:	0f b6 73 02          	movzbl 0x2(%rbx),%esi
    1715:	0f b6 43 01          	movzbl 0x1(%rbx),%eax
    1719:	89 44 24 3c          	mov    %eax,0x3c(%rsp)
    171d:	41 0f b6 46 01       	movzbl 0x1(%r14),%eax
    1722:	89 44 24 60          	mov    %eax,0x60(%rsp)
    1726:	e8 55 ff ff ff       	call   1680 <byte_work>
    172b:	41 0f b6 7e 03       	movzbl 0x3(%r14),%edi
    1730:	0f b6 73 03          	movzbl 0x3(%rbx),%esi
    1734:	0f b6 43 02          	movzbl 0x2(%rbx),%eax
    1738:	89 44 24 34          	mov    %eax,0x34(%rsp)
    173c:	41 0f b6 46 02       	movzbl 0x2(%r14),%eax
    1741:	89 44 24 5c          	mov    %eax,0x5c(%rsp)
    1745:	e8 36 ff ff ff       	call   1680 <byte_work>
    174a:	41 0f b6 7e 04       	movzbl 0x4(%r14),%edi
    174f:	0f b6 73 04          	movzbl 0x4(%rbx),%esi
    1753:	0f b6 43 03          	movzbl 0x3(%rbx),%eax
    1757:	89 44 24 2c          	mov    %eax,0x2c(%rsp)
    175b:	41 0f b6 46 03       	movzbl 0x3(%r14),%eax
    1760:	89 44 24 58          	mov    %eax,0x58(%rsp)
    1764:	e8 17 ff ff ff       	call   1680 <byte_work>
    1769:	41 0f b6 7e 05       	movzbl 0x5(%r14),%edi
    176e:	0f b6 73 05          	movzbl 0x5(%rbx),%esi
    1772:	0f b6 43 04          	movzbl 0x4(%rbx),%eax
    1776:	89 44 24 28          	mov    %eax,0x28(%rsp)
    177a:	41 0f b6 46 04       	movzbl 0x4(%r14),%eax
    177f:	89 44 24 54          	mov    %eax,0x54(%rsp)
    1783:	e8 f8 fe ff ff       	call   1680 <byte_work>
    1788:	41 0f b6 7e 06       	movzbl 0x6(%r14),%edi
    178d:	0f b6 73 06          	movzbl 0x6(%rbx),%esi
    1791:	0f b6 43 05          	movzbl 0x5(%rbx),%eax
    1795:	89 44 24 1c          	mov    %eax,0x1c(%rsp)
    1799:	41 0f b6 46 05       	movzbl 0x5(%r14),%eax
    179e:	89 44 24 50          	mov    %eax,0x50(%rsp)
    17a2:	e8 d9 fe ff ff       	call   1680 <byte_work>
    17a7:	41 0f b6 7e 07       	movzbl 0x7(%r14),%edi
    17ac:	0f b6 73 07          	movzbl 0x7(%rbx),%esi
    17b0:	0f b6 43 06          	movzbl 0x6(%rbx),%eax
    17b4:	89 44 24 14          	mov    %eax,0x14(%rsp)
    17b8:	41 0f b6 46 06       	movzbl 0x6(%r14),%eax
    17bd:	89 44 24 4c          	mov    %eax,0x4c(%rsp)
    17c1:	e8 ba fe ff ff       	call   1680 <byte_work>
    17c6:	41 0f b6 7e 08       	movzbl 0x8(%r14),%edi
    17cb:	0f b6 73 08          	movzbl 0x8(%rbx),%esi
    17cf:	0f b6 43 07          	movzbl 0x7(%rbx),%eax
    17d3:	89 44 24 0c          	mov    %eax,0xc(%rsp)
    17d7:	41 0f b6 46 07       	movzbl 0x7(%r14),%eax
    17dc:	89 44 24 44          	mov    %eax,0x44(%rsp)
    17e0:	e8 9b fe ff ff       	call   1680 <byte_work>
    17e5:	41 0f b6 7e 09       	movzbl 0x9(%r14),%edi
    17ea:	0f b6 73 09          	movzbl 0x9(%rbx),%esi
    17ee:	0f b6 43 08          	movzbl 0x8(%rbx),%eax
    17f2:	89 44 24 08          	mov    %eax,0x8(%rsp)
    17f6:	41 0f b6 46 08       	movzbl 0x8(%r14),%eax
    17fb:	89 44 24 40          	mov    %eax,0x40(%rsp)
    17ff:	e8 7c fe ff ff       	call   1680 <byte_work>
    1804:	41 0f b6 7e 0a       	movzbl 0xa(%r14),%edi
    1809:	0f b6 73 0a          	movzbl 0xa(%rbx),%esi
    180d:	0f b6 43 09          	movzbl 0x9(%rbx),%eax
    1811:	89 44 24 04          	mov    %eax,0x4(%rsp)
    1815:	41 0f b6 46 09       	movzbl 0x9(%r14),%eax
    181a:	89 44 24 38          	mov    %eax,0x38(%rsp)
    181e:	e8 5d fe ff ff       	call   1680 <byte_work>
    1823:	41 0f b6 7e 0b       	movzbl 0xb(%r14),%edi
    1828:	0f b6 73 0b          	movzbl 0xb(%rbx),%esi
    182c:	0f b6 43 0a          	movzbl 0xa(%rbx),%eax
    1830:	89 04 24             	mov    %eax,(%rsp)
    1833:	41 0f b6 46 0a       	movzbl 0xa(%r14),%eax
    1838:	89 44 24 30          	mov    %eax,0x30(%rsp)
    183c:	e8 3f fe ff ff       	call   1680 <byte_work>
    1841:	41 0f b6 7e 0c       	movzbl 0xc(%r14),%edi
    1846:	0f b6 73 0c          	movzbl 0xc(%rbx),%esi
    184a:	44 0f b6 6b 0b       	movzbl 0xb(%rbx),%r13d
    184f:	41 0f b6 46 0b       	movzbl 0xb(%r14),%eax
    1854:	89 44 24 24          	mov    %eax,0x24(%rsp)
    1858:	e8 23 fe ff ff       	call   1680 <byte_work>
    185d:	41 0f b6 7e 0d       	movzbl 0xd(%r14),%edi
    1862:	0f b6 73 0d          	movzbl 0xd(%rbx),%esi
    1866:	0f b6 6b 0c          	movzbl 0xc(%rbx),%ebp
    186a:	41 0f b6 46 0c       	movzbl 0xc(%r14),%eax
    186f:	89 44 24 20          	mov    %eax,0x20(%rsp)
    1873:	e8 08 fe ff ff       	call   1680 <byte_work>
    1878:	41 0f b6 7e 0e       	movzbl 0xe(%r14),%edi
    187d:	0f b6 73 0e          	movzbl 0xe(%rbx),%esi
    1881:	44 0f b6 7b 0d       	movzbl 0xd(%rbx),%r15d
    1886:	41 0f b6 46 0d       	movzbl 0xd(%r14),%eax
    188b:	89 44 24 18          	mov    %eax,0x18(%rsp)
    188f:	e8 ec fd ff ff       	call   1680 <byte_work>
    1894:	41 0f b6 7e 0f       	movzbl 0xf(%r14),%edi
    1899:	0f b6 73 0f          	movzbl 0xf(%rbx),%esi
    189d:	44 0f b6 63 0e       	movzbl 0xe(%rbx),%r12d
    18a2:	41 0f b6 46 0e       	movzbl 0xe(%r14),%eax
    18a7:	89 44 24 10          	mov    %eax,0x10(%rsp)
    18ab:	e8 d0 fd ff ff       	call   1680 <byte_work>
    18b0:	66 0f 6e 44 24 48    	movd   0x48(%rsp),%xmm0
    18b6:	66 0f 6e 54 24 3c    	movd   0x3c(%rsp),%xmm2
    18bc:	66 44 0f 6e 5c 24 34 	movd   0x34(%rsp),%xmm11
    18c3:	66 44 0f 6e 44 24 2c 	movd   0x2c(%rsp),%xmm8
    18ca:	66 0f 6e 5c 24 28    	movd   0x28(%rsp),%xmm3
    18d0:	66 44 0f 6e 4c 24 1c 	movd   0x1c(%rsp),%xmm9
    18d7:	66 0f 6e 74 24 14    	movd   0x14(%rsp),%xmm6
    18dd:	66 44 0f 6e 64 24 0c 	movd   0xc(%rsp),%xmm12
    18e4:	66 0f 6e 4c 24 08    	movd   0x8(%rsp),%xmm1
    18ea:	66 44 0f 6e 54 24 04 	movd   0x4(%rsp),%xmm10
    18f1:	66 0f 6e 3c 24       	movd   (%rsp),%xmm7
    18f6:	66 45 0f 6e f5       	movd   %r13d,%xmm14
    18fb:	66 0f 6e e5          	movd   %ebp,%xmm4
    18ff:	66 45 0f 6e ef       	movd   %r15d,%xmm13
    1904:	66 41 0f 6e ec       	movd   %r12d,%xmm5
    1909:	0f b6 43 0f          	movzbl 0xf(%rbx),%eax
    190d:	66 44 0f 6e f8       	movd   %eax,%xmm15
    1912:	66 0f 60 c2          	punpcklbw %xmm2,%xmm0
    1916:	66 0f 6e 54 24 64    	movd   0x64(%rsp),%xmm2
    191c:	66 45 0f 60 d8       	punpcklbw %xmm8,%xmm11
    1921:	66 44 0f 6e 44 24 60 	movd   0x60(%rsp),%xmm8
    1928:	66 41 0f 61 c3       	punpcklwd %xmm11,%xmm0
    192d:	66 44 0f 6e 5c 24 5c 	movd   0x5c(%rsp),%xmm11
    1934:	66 41 0f 60 d9       	punpcklbw %xmm9,%xmm3
    1939:	66 44 0f 6e 4c 24 58 	movd   0x58(%rsp),%xmm9
    1940:	66 41 0f 60 f4       	punpcklbw %xmm12,%xmm6
    1945:	66 44 0f 6e 64 24 54 	movd   0x54(%rsp),%xmm12
    194c:	66 0f 61 de          	punpcklwd %xmm6,%xmm3
    1950:	66 0f 6e 74 24 50    	movd   0x50(%rsp),%xmm6
    1956:	66 0f 62 c3          	punpckldq %xmm3,%xmm0
    195a:	66 0f 6e 5c 24 4c    	movd   0x4c(%rsp),%xmm3
    1960:	66 41 0f 60 ca       	punpcklbw %xmm10,%xmm1
    1965:	66 44 0f 6e 54 24 44 	movd   0x44(%rsp),%xmm10
    196c:	66 41 0f 60 fe       	punpcklbw %xmm14,%xmm7
    1971:	66 44 0f 6e 74 24 40 	movd   0x40(%rsp),%xmm14
    1978:	66 0f 61 cf          	punpcklwd %xmm7,%xmm1
    197c:	66 0f 6e 7c 24 38    	movd   0x38(%rsp),%xmm7
    1982:	66 41 0f 60 e5       	punpcklbw %xmm13,%xmm4
    1987:	66 44 0f 6e 6c 24 30 	movd   0x30(%rsp),%xmm13
    198e:	66 41 0f 60 ef       	punpcklbw %xmm15,%xmm5
    1993:	66 44 0f 6e 7c 24 24 	movd   0x24(%rsp),%xmm15
    199a:	66 0f 61 e5          	punpcklwd %xmm5,%xmm4
    199e:	66 0f 6e 6c 24 20    	movd   0x20(%rsp),%xmm5
    19a4:	66 0f 62 cc          	punpckldq %xmm4,%xmm1
    19a8:	66 0f 6e 64 24 18    	movd   0x18(%rsp),%xmm4
    19ae:	66 0f 6c c1          	punpcklqdq %xmm1,%xmm0
    19b2:	66 0f 6e 4c 24 10    	movd   0x10(%rsp),%xmm1
    19b8:	66 41 0f 60 d0       	punpcklbw %xmm8,%xmm2
    19bd:	66 45 0f 60 d9       	punpcklbw %xmm9,%xmm11
    19c2:	66 41 0f 61 d3       	punpcklwd %xmm11,%xmm2
    19c7:	66 44 0f 60 e6       	punpcklbw %xmm6,%xmm12
    19cc:	66 41 0f 60 da       	punpcklbw %xmm10,%xmm3
    19d1:	66 44 0f 61 e3       	punpcklwd %xmm3,%xmm12
    19d6:	66 41 0f 62 d4       	punpckldq %xmm12,%xmm2
    19db:	66 44 0f 60 f7       	punpcklbw %xmm7,%xmm14
    19e0:	66 45 0f 60 ef       	punpcklbw %xmm15,%xmm13
    19e5:	66 45 0f 61 f5       	punpcklwd %xmm13,%xmm14
    19ea:	66 0f 60 ec          	punpcklbw %xmm4,%xmm5
    19ee:	41 0f b6 46 0f       	movzbl 0xf(%r14),%eax
    19f3:	66 0f 6e d8          	movd   %eax,%xmm3
    19f7:	66 0f 60 cb          	punpcklbw %xmm3,%xmm1
    19fb:	66 0f 61 e9          	punpcklwd %xmm1,%xmm5
    19ff:	66 44 0f 62 f5       	punpckldq %xmm5,%xmm14
    1a04:	66 41 0f 6c d6       	punpcklqdq %xmm14,%xmm2
    1a09:	66 0f ef d0          	pxor   %xmm0,%xmm2
    1a0d:	66 0f 70 c2 ee       	pshufd $0xee,%xmm2,%xmm0
    1a12:	66 0f eb c2          	por    %xmm2,%xmm0
    1a16:	66 0f 70 c8 55       	pshufd $0x55,%xmm0,%xmm1
    1a1b:	66 0f eb c8          	por    %xmm0,%xmm1
    1a1f:	66 0f 6f c1          	movdqa %xmm1,%xmm0
    1a23:	66 0f 72 d0 10       	psrld  $0x10,%xmm0
    1a28:	66 0f eb c1          	por    %xmm1,%xmm0
    1a2c:	66 0f 6f c8          	movdqa %xmm0,%xmm1
    1a30:	66 0f 71 d1 08       	psrlw  $0x8,%xmm1
    1a35:	66 0f eb c8          	por    %xmm0,%xmm1
    1a39:	66 0f 7e c8          	movd   %xmm1,%eax
    1a3d:	0f b6 c0             	movzbl %al,%eax
    1a40:	83 c0 ff             	add    $0xffffffff,%eax
    1a43:	c1 e8 08             	shr    $0x8,%eax
    1a46:	83 e0 01             	and    $0x1,%eax
    1a49:	48 83 c4 68          	add    $0x68,%rsp
    1a4d:	5b                   	pop    %rbx
    1a4e:	41 5c                	pop    %r12
    1a50:	41 5d                	pop    %r13
    1a52:	41 5e                	pop    %r14
    1a54:	41 5f                	pop    %r15
    1a56:	5d                   	pop    %rbp
    1a57:	c3                   	ret