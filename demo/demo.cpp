#include <cstdlib>
#include <string>

#include <fmt/core.h>
#include <fmt/format.h>

template<typename T>
struct Abc {
  int a;
  T b;
  std::string c;

  operator bool() const {
    return a != 0;
  }
};

int main(int argc, const char** argv) {
  Abc abc{.a = 0, .b = 32, .c = "abc"};
  fmt::print("{}: {}\n", argv[0], argc);
  return EXIT_SUCCESS;
}
