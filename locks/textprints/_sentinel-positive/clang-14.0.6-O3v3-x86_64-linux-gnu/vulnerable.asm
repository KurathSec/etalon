    16f0:	55                   	push   %rbp
    16f1:	41 56                	push   %r14
    16f3:	53                   	push   %rbx
    16f4:	48 89 f3             	mov    %rsi,%rbx
    16f7:	48 89 fd             	mov    %rdi,%rbp
    16fa:	0f b6 3f             	movzbl (%rdi),%edi
    16fd:	0f b6 36             	movzbl (%rsi),%esi
    1700:	e8 7b ff ff ff       	call   1680 <byte_work>
    1705:	8a 45 00             	mov    0x0(%rbp),%al
    1708:	45 31 f6             	xor    %r14d,%r14d
    170b:	3a 03                	cmp    (%rbx),%al
    170d:	0f 85 64 01 00 00    	jne    1877 <check_tag+0x187>
    1713:	0f b6 7d 01          	movzbl 0x1(%rbp),%edi
    1717:	0f b6 73 01          	movzbl 0x1(%rbx),%esi
    171b:	e8 60 ff ff ff       	call   1680 <byte_work>
    1720:	8a 45 01             	mov    0x1(%rbp),%al
    1723:	3a 43 01             	cmp    0x1(%rbx),%al
    1726:	0f 85 4b 01 00 00    	jne    1877 <check_tag+0x187>
    172c:	0f b6 7d 02          	movzbl 0x2(%rbp),%edi
    1730:	0f b6 73 02          	movzbl 0x2(%rbx),%esi
    1734:	e8 47 ff ff ff       	call   1680 <byte_work>
    1739:	8a 45 02             	mov    0x2(%rbp),%al
    173c:	3a 43 02             	cmp    0x2(%rbx),%al
    173f:	0f 85 32 01 00 00    	jne    1877 <check_tag+0x187>
    1745:	0f b6 7d 03          	movzbl 0x3(%rbp),%edi
    1749:	0f b6 73 03          	movzbl 0x3(%rbx),%esi
    174d:	e8 2e ff ff ff       	call   1680 <byte_work>
    1752:	8a 45 03             	mov    0x3(%rbp),%al
    1755:	3a 43 03             	cmp    0x3(%rbx),%al
    1758:	0f 85 19 01 00 00    	jne    1877 <check_tag+0x187>
    175e:	0f b6 7d 04          	movzbl 0x4(%rbp),%edi
    1762:	0f b6 73 04          	movzbl 0x4(%rbx),%esi
    1766:	e8 15 ff ff ff       	call   1680 <byte_work>
    176b:	8a 45 04             	mov    0x4(%rbp),%al
    176e:	3a 43 04             	cmp    0x4(%rbx),%al
    1771:	0f 85 00 01 00 00    	jne    1877 <check_tag+0x187>
    1777:	0f b6 7d 05          	movzbl 0x5(%rbp),%edi
    177b:	0f b6 73 05          	movzbl 0x5(%rbx),%esi
    177f:	e8 fc fe ff ff       	call   1680 <byte_work>
    1784:	8a 45 05             	mov    0x5(%rbp),%al
    1787:	3a 43 05             	cmp    0x5(%rbx),%al
    178a:	0f 85 e7 00 00 00    	jne    1877 <check_tag+0x187>
    1790:	0f b6 7d 06          	movzbl 0x6(%rbp),%edi
    1794:	0f b6 73 06          	movzbl 0x6(%rbx),%esi
    1798:	e8 e3 fe ff ff       	call   1680 <byte_work>
    179d:	8a 45 06             	mov    0x6(%rbp),%al
    17a0:	3a 43 06             	cmp    0x6(%rbx),%al
    17a3:	0f 85 ce 00 00 00    	jne    1877 <check_tag+0x187>
    17a9:	0f b6 7d 07          	movzbl 0x7(%rbp),%edi
    17ad:	0f b6 73 07          	movzbl 0x7(%rbx),%esi
    17b1:	e8 ca fe ff ff       	call   1680 <byte_work>
    17b6:	8a 45 07             	mov    0x7(%rbp),%al
    17b9:	3a 43 07             	cmp    0x7(%rbx),%al
    17bc:	0f 85 b5 00 00 00    	jne    1877 <check_tag+0x187>
    17c2:	0f b6 7d 08          	movzbl 0x8(%rbp),%edi
    17c6:	0f b6 73 08          	movzbl 0x8(%rbx),%esi
    17ca:	e8 b1 fe ff ff       	call   1680 <byte_work>
    17cf:	8a 45 08             	mov    0x8(%rbp),%al
    17d2:	3a 43 08             	cmp    0x8(%rbx),%al
    17d5:	0f 85 9c 00 00 00    	jne    1877 <check_tag+0x187>
    17db:	0f b6 7d 09          	movzbl 0x9(%rbp),%edi
    17df:	0f b6 73 09          	movzbl 0x9(%rbx),%esi
    17e3:	e8 98 fe ff ff       	call   1680 <byte_work>
    17e8:	8a 45 09             	mov    0x9(%rbp),%al
    17eb:	3a 43 09             	cmp    0x9(%rbx),%al
    17ee:	0f 85 83 00 00 00    	jne    1877 <check_tag+0x187>
    17f4:	0f b6 7d 0a          	movzbl 0xa(%rbp),%edi
    17f8:	0f b6 73 0a          	movzbl 0xa(%rbx),%esi
    17fc:	e8 7f fe ff ff       	call   1680 <byte_work>
    1801:	8a 45 0a             	mov    0xa(%rbp),%al
    1804:	3a 43 0a             	cmp    0xa(%rbx),%al
    1807:	75 6e                	jne    1877 <check_tag+0x187>
    1809:	0f b6 7d 0b          	movzbl 0xb(%rbp),%edi
    180d:	0f b6 73 0b          	movzbl 0xb(%rbx),%esi
    1811:	e8 6a fe ff ff       	call   1680 <byte_work>
    1816:	8a 45 0b             	mov    0xb(%rbp),%al
    1819:	3a 43 0b             	cmp    0xb(%rbx),%al
    181c:	75 59                	jne    1877 <check_tag+0x187>
    181e:	0f b6 7d 0c          	movzbl 0xc(%rbp),%edi
    1822:	0f b6 73 0c          	movzbl 0xc(%rbx),%esi
    1826:	e8 55 fe ff ff       	call   1680 <byte_work>
    182b:	8a 45 0c             	mov    0xc(%rbp),%al
    182e:	3a 43 0c             	cmp    0xc(%rbx),%al
    1831:	75 44                	jne    1877 <check_tag+0x187>
    1833:	0f b6 7d 0d          	movzbl 0xd(%rbp),%edi
    1837:	0f b6 73 0d          	movzbl 0xd(%rbx),%esi
    183b:	e8 40 fe ff ff       	call   1680 <byte_work>
    1840:	8a 45 0d             	mov    0xd(%rbp),%al
    1843:	3a 43 0d             	cmp    0xd(%rbx),%al
    1846:	75 2f                	jne    1877 <check_tag+0x187>
    1848:	0f b6 7d 0e          	movzbl 0xe(%rbp),%edi
    184c:	0f b6 73 0e          	movzbl 0xe(%rbx),%esi
    1850:	e8 2b fe ff ff       	call   1680 <byte_work>
    1855:	8a 45 0e             	mov    0xe(%rbp),%al
    1858:	3a 43 0e             	cmp    0xe(%rbx),%al
    185b:	75 1a                	jne    1877 <check_tag+0x187>
    185d:	0f b6 7d 0f          	movzbl 0xf(%rbp),%edi
    1861:	0f b6 73 0f          	movzbl 0xf(%rbx),%esi
    1865:	e8 16 fe ff ff       	call   1680 <byte_work>
    186a:	8a 45 0f             	mov    0xf(%rbp),%al
    186d:	45 31 f6             	xor    %r14d,%r14d
    1870:	3a 43 0f             	cmp    0xf(%rbx),%al
    1873:	41 0f 94 c6          	sete   %r14b
    1877:	44 89 f0             	mov    %r14d,%eax
    187a:	5b                   	pop    %rbx
    187b:	41 5e                	pop    %r14
    187d:	5d                   	pop    %rbp
    187e:	c3                   	ret