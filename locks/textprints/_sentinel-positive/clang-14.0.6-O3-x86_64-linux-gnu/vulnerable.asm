    16d0:	55                   	push   %rbp
    16d1:	41 56                	push   %r14
    16d3:	53                   	push   %rbx
    16d4:	48 89 f3             	mov    %rsi,%rbx
    16d7:	48 89 fd             	mov    %rdi,%rbp
    16da:	0f b6 3f             	movzbl (%rdi),%edi
    16dd:	0f b6 36             	movzbl (%rsi),%esi
    16e0:	e8 9b ff ff ff       	call   1680 <byte_work>
    16e5:	8a 45 00             	mov    0x0(%rbp),%al
    16e8:	45 31 f6             	xor    %r14d,%r14d
    16eb:	3a 03                	cmp    (%rbx),%al
    16ed:	0f 85 64 01 00 00    	jne    1857 <check_tag+0x187>
    16f3:	0f b6 7d 01          	movzbl 0x1(%rbp),%edi
    16f7:	0f b6 73 01          	movzbl 0x1(%rbx),%esi
    16fb:	e8 80 ff ff ff       	call   1680 <byte_work>
    1700:	8a 45 01             	mov    0x1(%rbp),%al
    1703:	3a 43 01             	cmp    0x1(%rbx),%al
    1706:	0f 85 4b 01 00 00    	jne    1857 <check_tag+0x187>
    170c:	0f b6 7d 02          	movzbl 0x2(%rbp),%edi
    1710:	0f b6 73 02          	movzbl 0x2(%rbx),%esi
    1714:	e8 67 ff ff ff       	call   1680 <byte_work>
    1719:	8a 45 02             	mov    0x2(%rbp),%al
    171c:	3a 43 02             	cmp    0x2(%rbx),%al
    171f:	0f 85 32 01 00 00    	jne    1857 <check_tag+0x187>
    1725:	0f b6 7d 03          	movzbl 0x3(%rbp),%edi
    1729:	0f b6 73 03          	movzbl 0x3(%rbx),%esi
    172d:	e8 4e ff ff ff       	call   1680 <byte_work>
    1732:	8a 45 03             	mov    0x3(%rbp),%al
    1735:	3a 43 03             	cmp    0x3(%rbx),%al
    1738:	0f 85 19 01 00 00    	jne    1857 <check_tag+0x187>
    173e:	0f b6 7d 04          	movzbl 0x4(%rbp),%edi
    1742:	0f b6 73 04          	movzbl 0x4(%rbx),%esi
    1746:	e8 35 ff ff ff       	call   1680 <byte_work>
    174b:	8a 45 04             	mov    0x4(%rbp),%al
    174e:	3a 43 04             	cmp    0x4(%rbx),%al
    1751:	0f 85 00 01 00 00    	jne    1857 <check_tag+0x187>
    1757:	0f b6 7d 05          	movzbl 0x5(%rbp),%edi
    175b:	0f b6 73 05          	movzbl 0x5(%rbx),%esi
    175f:	e8 1c ff ff ff       	call   1680 <byte_work>
    1764:	8a 45 05             	mov    0x5(%rbp),%al
    1767:	3a 43 05             	cmp    0x5(%rbx),%al
    176a:	0f 85 e7 00 00 00    	jne    1857 <check_tag+0x187>
    1770:	0f b6 7d 06          	movzbl 0x6(%rbp),%edi
    1774:	0f b6 73 06          	movzbl 0x6(%rbx),%esi
    1778:	e8 03 ff ff ff       	call   1680 <byte_work>
    177d:	8a 45 06             	mov    0x6(%rbp),%al
    1780:	3a 43 06             	cmp    0x6(%rbx),%al
    1783:	0f 85 ce 00 00 00    	jne    1857 <check_tag+0x187>
    1789:	0f b6 7d 07          	movzbl 0x7(%rbp),%edi
    178d:	0f b6 73 07          	movzbl 0x7(%rbx),%esi
    1791:	e8 ea fe ff ff       	call   1680 <byte_work>
    1796:	8a 45 07             	mov    0x7(%rbp),%al
    1799:	3a 43 07             	cmp    0x7(%rbx),%al
    179c:	0f 85 b5 00 00 00    	jne    1857 <check_tag+0x187>
    17a2:	0f b6 7d 08          	movzbl 0x8(%rbp),%edi
    17a6:	0f b6 73 08          	movzbl 0x8(%rbx),%esi
    17aa:	e8 d1 fe ff ff       	call   1680 <byte_work>
    17af:	8a 45 08             	mov    0x8(%rbp),%al
    17b2:	3a 43 08             	cmp    0x8(%rbx),%al
    17b5:	0f 85 9c 00 00 00    	jne    1857 <check_tag+0x187>
    17bb:	0f b6 7d 09          	movzbl 0x9(%rbp),%edi
    17bf:	0f b6 73 09          	movzbl 0x9(%rbx),%esi
    17c3:	e8 b8 fe ff ff       	call   1680 <byte_work>
    17c8:	8a 45 09             	mov    0x9(%rbp),%al
    17cb:	3a 43 09             	cmp    0x9(%rbx),%al
    17ce:	0f 85 83 00 00 00    	jne    1857 <check_tag+0x187>
    17d4:	0f b6 7d 0a          	movzbl 0xa(%rbp),%edi
    17d8:	0f b6 73 0a          	movzbl 0xa(%rbx),%esi
    17dc:	e8 9f fe ff ff       	call   1680 <byte_work>
    17e1:	8a 45 0a             	mov    0xa(%rbp),%al
    17e4:	3a 43 0a             	cmp    0xa(%rbx),%al
    17e7:	75 6e                	jne    1857 <check_tag+0x187>
    17e9:	0f b6 7d 0b          	movzbl 0xb(%rbp),%edi
    17ed:	0f b6 73 0b          	movzbl 0xb(%rbx),%esi
    17f1:	e8 8a fe ff ff       	call   1680 <byte_work>
    17f6:	8a 45 0b             	mov    0xb(%rbp),%al
    17f9:	3a 43 0b             	cmp    0xb(%rbx),%al
    17fc:	75 59                	jne    1857 <check_tag+0x187>
    17fe:	0f b6 7d 0c          	movzbl 0xc(%rbp),%edi
    1802:	0f b6 73 0c          	movzbl 0xc(%rbx),%esi
    1806:	e8 75 fe ff ff       	call   1680 <byte_work>
    180b:	8a 45 0c             	mov    0xc(%rbp),%al
    180e:	3a 43 0c             	cmp    0xc(%rbx),%al
    1811:	75 44                	jne    1857 <check_tag+0x187>
    1813:	0f b6 7d 0d          	movzbl 0xd(%rbp),%edi
    1817:	0f b6 73 0d          	movzbl 0xd(%rbx),%esi
    181b:	e8 60 fe ff ff       	call   1680 <byte_work>
    1820:	8a 45 0d             	mov    0xd(%rbp),%al
    1823:	3a 43 0d             	cmp    0xd(%rbx),%al
    1826:	75 2f                	jne    1857 <check_tag+0x187>
    1828:	0f b6 7d 0e          	movzbl 0xe(%rbp),%edi
    182c:	0f b6 73 0e          	movzbl 0xe(%rbx),%esi
    1830:	e8 4b fe ff ff       	call   1680 <byte_work>
    1835:	8a 45 0e             	mov    0xe(%rbp),%al
    1838:	3a 43 0e             	cmp    0xe(%rbx),%al
    183b:	75 1a                	jne    1857 <check_tag+0x187>
    183d:	0f b6 7d 0f          	movzbl 0xf(%rbp),%edi
    1841:	0f b6 73 0f          	movzbl 0xf(%rbx),%esi
    1845:	e8 36 fe ff ff       	call   1680 <byte_work>
    184a:	8a 45 0f             	mov    0xf(%rbp),%al
    184d:	45 31 f6             	xor    %r14d,%r14d
    1850:	3a 43 0f             	cmp    0xf(%rbx),%al
    1853:	41 0f 94 c6          	sete   %r14b
    1857:	44 89 f0             	mov    %r14d,%eax
    185a:	5b                   	pop    %rbx
    185b:	41 5e                	pop    %r14
    185d:	5d                   	pop    %rbp
    185e:	c3                   	ret