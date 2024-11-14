perm(std::array<double, 4ul>):
  mov rax, rdi
  vpermpd ymm0, ymmword ptr [rsp + 8], 57
  vmovups ymmword ptr [rdi], ymm0
  vzeroupper
  ret