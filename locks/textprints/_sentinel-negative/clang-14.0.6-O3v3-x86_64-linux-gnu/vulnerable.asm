    16f0:	55                   	push   %rbp
    16f1:	41 57                	push   %r15
    16f3:	41 56                	push   %r14
    16f5:	53                   	push   %rbx
    16f6:	48 83 ec 28          	sub    $0x28,%rsp
    16fa:	49 89 f6             	mov    %rsi,%r14
    16fd:	48 89 fb             	mov    %rdi,%rbx
    1700:	0f b6 3f             	movzbl (%rdi),%edi
    1703:	0f b6 36             	movzbl (%rsi),%esi
    1706:	e8 75 ff ff ff       	call   1680 <byte_work>
    170b:	0f b6 7b 01          	movzbl 0x1(%rbx),%edi
    170f:	41 0f b6 76 01       	movzbl 0x1(%r14),%esi
    1714:	41 0f b6 2e          	movzbl (%r14),%ebp
    1718:	44 0f b6 3b          	movzbl (%rbx),%r15d
    171c:	e8 5f ff ff ff       	call   1680 <byte_work>
    1721:	0f b6 7b 02          	movzbl 0x2(%rbx),%edi
    1725:	c5 f9 6e c5          	vmovd  %ebp,%xmm0
    1729:	c4 c3 79 20 46 01 01 	vpinsrb $0x1,0x1(%r14),%xmm0,%xmm0
    1730:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    1736:	41 0f b6 76 02       	movzbl 0x2(%r14),%esi
    173b:	c4 c1 79 6e c7       	vmovd  %r15d,%xmm0
    1740:	c4 e3 79 20 43 01 01 	vpinsrb $0x1,0x1(%rbx),%xmm0,%xmm0
    1747:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    174c:	e8 2f ff ff ff       	call   1680 <byte_work>
    1751:	0f b6 7b 03          	movzbl 0x3(%rbx),%edi
    1755:	41 0f b6 76 03       	movzbl 0x3(%r14),%esi
    175a:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    1760:	c4 c3 79 20 46 02 02 	vpinsrb $0x2,0x2(%r14),%xmm0,%xmm0
    1767:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    176d:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    1772:	c4 e3 79 20 43 02 02 	vpinsrb $0x2,0x2(%rbx),%xmm0,%xmm0
    1779:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    177e:	e8 fd fe ff ff       	call   1680 <byte_work>
    1783:	0f b6 7b 04          	movzbl 0x4(%rbx),%edi
    1787:	41 0f b6 76 04       	movzbl 0x4(%r14),%esi
    178c:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    1792:	c4 c3 79 20 46 03 03 	vpinsrb $0x3,0x3(%r14),%xmm0,%xmm0
    1799:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    179f:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    17a4:	c4 e3 79 20 43 03 03 	vpinsrb $0x3,0x3(%rbx),%xmm0,%xmm0
    17ab:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    17b0:	e8 cb fe ff ff       	call   1680 <byte_work>
    17b5:	0f b6 7b 05          	movzbl 0x5(%rbx),%edi
    17b9:	41 0f b6 76 05       	movzbl 0x5(%r14),%esi
    17be:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    17c4:	c4 c3 79 20 46 04 04 	vpinsrb $0x4,0x4(%r14),%xmm0,%xmm0
    17cb:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    17d1:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    17d6:	c4 e3 79 20 43 04 04 	vpinsrb $0x4,0x4(%rbx),%xmm0,%xmm0
    17dd:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    17e2:	e8 99 fe ff ff       	call   1680 <byte_work>
    17e7:	0f b6 7b 06          	movzbl 0x6(%rbx),%edi
    17eb:	41 0f b6 76 06       	movzbl 0x6(%r14),%esi
    17f0:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    17f6:	c4 c3 79 20 46 05 05 	vpinsrb $0x5,0x5(%r14),%xmm0,%xmm0
    17fd:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    1803:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    1808:	c4 e3 79 20 43 05 05 	vpinsrb $0x5,0x5(%rbx),%xmm0,%xmm0
    180f:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    1814:	e8 67 fe ff ff       	call   1680 <byte_work>
    1819:	0f b6 7b 07          	movzbl 0x7(%rbx),%edi
    181d:	41 0f b6 76 07       	movzbl 0x7(%r14),%esi
    1822:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    1828:	c4 c3 79 20 46 06 06 	vpinsrb $0x6,0x6(%r14),%xmm0,%xmm0
    182f:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    1835:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    183a:	c4 e3 79 20 43 06 06 	vpinsrb $0x6,0x6(%rbx),%xmm0,%xmm0
    1841:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    1846:	e8 35 fe ff ff       	call   1680 <byte_work>
    184b:	0f b6 7b 08          	movzbl 0x8(%rbx),%edi
    184f:	41 0f b6 76 08       	movzbl 0x8(%r14),%esi
    1854:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    185a:	c4 c3 79 20 46 07 07 	vpinsrb $0x7,0x7(%r14),%xmm0,%xmm0
    1861:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    1867:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    186c:	c4 e3 79 20 43 07 07 	vpinsrb $0x7,0x7(%rbx),%xmm0,%xmm0
    1873:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    1878:	e8 03 fe ff ff       	call   1680 <byte_work>
    187d:	0f b6 7b 09          	movzbl 0x9(%rbx),%edi
    1881:	41 0f b6 76 09       	movzbl 0x9(%r14),%esi
    1886:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    188c:	c4 c3 79 20 46 08 08 	vpinsrb $0x8,0x8(%r14),%xmm0,%xmm0
    1893:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    1899:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    189e:	c4 e3 79 20 43 08 08 	vpinsrb $0x8,0x8(%rbx),%xmm0,%xmm0
    18a5:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    18aa:	e8 d1 fd ff ff       	call   1680 <byte_work>
    18af:	0f b6 7b 0a          	movzbl 0xa(%rbx),%edi
    18b3:	41 0f b6 76 0a       	movzbl 0xa(%r14),%esi
    18b8:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    18be:	c4 c3 79 20 46 09 09 	vpinsrb $0x9,0x9(%r14),%xmm0,%xmm0
    18c5:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    18cb:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    18d0:	c4 e3 79 20 43 09 09 	vpinsrb $0x9,0x9(%rbx),%xmm0,%xmm0
    18d7:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    18dc:	e8 9f fd ff ff       	call   1680 <byte_work>
    18e1:	0f b6 7b 0b          	movzbl 0xb(%rbx),%edi
    18e5:	41 0f b6 76 0b       	movzbl 0xb(%r14),%esi
    18ea:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    18f0:	c4 c3 79 20 46 0a 0a 	vpinsrb $0xa,0xa(%r14),%xmm0,%xmm0
    18f7:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    18fd:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    1902:	c4 e3 79 20 43 0a 0a 	vpinsrb $0xa,0xa(%rbx),%xmm0,%xmm0
    1909:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    190e:	e8 6d fd ff ff       	call   1680 <byte_work>
    1913:	0f b6 7b 0c          	movzbl 0xc(%rbx),%edi
    1917:	41 0f b6 76 0c       	movzbl 0xc(%r14),%esi
    191c:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    1922:	c4 c3 79 20 46 0b 0b 	vpinsrb $0xb,0xb(%r14),%xmm0,%xmm0
    1929:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    192f:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    1934:	c4 e3 79 20 43 0b 0b 	vpinsrb $0xb,0xb(%rbx),%xmm0,%xmm0
    193b:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    1940:	e8 3b fd ff ff       	call   1680 <byte_work>
    1945:	0f b6 7b 0d          	movzbl 0xd(%rbx),%edi
    1949:	41 0f b6 76 0d       	movzbl 0xd(%r14),%esi
    194e:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    1954:	c4 c3 79 20 46 0c 0c 	vpinsrb $0xc,0xc(%r14),%xmm0,%xmm0
    195b:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    1961:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    1966:	c4 e3 79 20 43 0c 0c 	vpinsrb $0xc,0xc(%rbx),%xmm0,%xmm0
    196d:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    1972:	e8 09 fd ff ff       	call   1680 <byte_work>
    1977:	0f b6 7b 0e          	movzbl 0xe(%rbx),%edi
    197b:	41 0f b6 76 0e       	movzbl 0xe(%r14),%esi
    1980:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    1986:	c4 c3 79 20 46 0d 0d 	vpinsrb $0xd,0xd(%r14),%xmm0,%xmm0
    198d:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    1993:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    1998:	c4 e3 79 20 43 0d 0d 	vpinsrb $0xd,0xd(%rbx),%xmm0,%xmm0
    199f:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    19a4:	e8 d7 fc ff ff       	call   1680 <byte_work>
    19a9:	0f b6 7b 0f          	movzbl 0xf(%rbx),%edi
    19ad:	41 0f b6 76 0f       	movzbl 0xf(%r14),%esi
    19b2:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    19b8:	c4 c3 79 20 46 0e 0e 	vpinsrb $0xe,0xe(%r14),%xmm0,%xmm0
    19bf:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    19c5:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    19ca:	c4 e3 79 20 43 0e 0e 	vpinsrb $0xe,0xe(%rbx),%xmm0,%xmm0
    19d1:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    19d6:	e8 a5 fc ff ff       	call   1680 <byte_work>
    19db:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    19e1:	c4 c3 79 20 46 0f 0f 	vpinsrb $0xf,0xf(%r14),%xmm0,%xmm0
    19e8:	c5 f9 6f 0c 24       	vmovdqa (%rsp),%xmm1
    19ed:	c4 e3 71 20 4b 0f 0f 	vpinsrb $0xf,0xf(%rbx),%xmm1,%xmm1
    19f4:	c5 f9 ef c1          	vpxor  %xmm1,%xmm0,%xmm0
    19f8:	c5 f9 70 c8 ee       	vpshufd $0xee,%xmm0,%xmm1
    19fd:	c5 f9 eb c1          	vpor   %xmm1,%xmm0,%xmm0
    1a01:	c5 f9 70 c8 55       	vpshufd $0x55,%xmm0,%xmm1
    1a06:	c5 f9 eb c1          	vpor   %xmm1,%xmm0,%xmm0
    1a0a:	c5 f1 72 d0 10       	vpsrld $0x10,%xmm0,%xmm1
    1a0f:	c5 f9 eb c1          	vpor   %xmm1,%xmm0,%xmm0
    1a13:	c5 f1 71 d0 08       	vpsrlw $0x8,%xmm0,%xmm1
    1a18:	c5 f9 eb c1          	vpor   %xmm1,%xmm0,%xmm0
    1a1c:	c4 e3 79 14 c0 00    	vpextrb $0x0,%xmm0,%eax
    1a22:	ff c8                	dec    %eax
    1a24:	c1 e8 08             	shr    $0x8,%eax
    1a27:	83 e0 01             	and    $0x1,%eax
    1a2a:	48 83 c4 28          	add    $0x28,%rsp
    1a2e:	5b                   	pop    %rbx
    1a2f:	41 5e                	pop    %r14
    1a31:	41 5f                	pop    %r15
    1a33:	5d                   	pop    %rbp
    1a34:	c3                   	ret