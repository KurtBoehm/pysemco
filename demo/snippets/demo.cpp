#include <concepts>
#include <cstdint>
#include <cstdlib>
#include <new>
#include <string>

#include <fmt/core.h>
#include <fmt/format.h>

template<std::integral T>
struct Abc {
  int a;
  T b;
  std::string c;

  operator bool() const {
    return a != 0;
  }
};

int main(int argc, const char** argv) {
  uint8_t* data = new (std::align_val_t(64)) uint8_t[64];
  Abc abc{.a = 0, .b = 32, .c = "abc"};
  fmt::print("{}: {}\n", argv[0], argc);
  return EXIT_SUCCESS;
}
